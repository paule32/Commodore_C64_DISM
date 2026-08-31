#!/usr/bin/env python3
# ---------------------------------------------------------------------------------
# Author: (c) 2024, 2025, 2026 Jens Kallup - paule32
# All rights reserved
#
# pe_nostub.py
# 
# Entfernt den klassischen DOS-Stub aus einer PE32/PE32+-Datei und setzt
# e_lfanew auf 0x40, sodass die PE-Signatur direkt auf den 64-Byte-MZ-Header
# folgt.
# 
# Modi:
#   compatible  - vollständigen Optional Header und bestehende Rohdaten-Offets
#                 beibehalten. Nur DOS-Stub entfernen.
#   compact     - unbenutzte Data-Directory-Einträge am Ende entfernen,
#                 SizeOfHeaders minimieren und alle Rohdaten nach vorne schieben.
# ---------------------------------------------------------------------------------
from __future__ import annotations

import argparse
import shutil
import struct
import sys

from   dataclasses import dataclass
from   pathlib     import Path


IMAGE_DOS_HEADER_SIZE           = 0x40
PE_SIGNATURE                    = b"PE\0\0"
IMAGE_FILE_HEADER_SIZE          = 20
IMAGE_SECTION_HEADER_SIZE       = 40
IMAGE_DIRECTORY_ENTRY_SECURITY  = 4
IMAGE_DIRECTORY_ENTRY_DEBUG     = 6
IMAGE_DEBUG_DIRECTORY_SIZE      = 28

def u16(data: bytes | bytearray, offset: int) -> int:
    return struct.unpack_from("<H", data, offset)[0]

def u32(data: bytes | bytearray, offset: int) -> int:
    return struct.unpack_from("<I", data, offset)[0]

def p16(data: bytearray, offset: int, value: int) -> None:
    struct.pack_into("<H", data, offset, value & 0xFFFF)

def p32(data: bytearray, offset: int, value: int) -> None:
    struct.pack_into("<I", data, offset, value & 0xFFFFFFFF)

def align_up(value: int, alignment: int) -> int:
    if alignment <= 0 or alignment & (alignment - 1):
        raise ValueError(
            f"FileAlignment muss eine Zweierpotenz sein, erhalten: {alignment}"
        )
    return (value + alignment - 1) & ~(alignment - 1)

@dataclass(frozen=True)
class Section:
    index           : int
    header_offset   : int
    name            : str
    virtual_size    : int
    virtual_address : int
    raw_size        : int
    raw_pointer     : int
    reloc_pointer   : int
    line_pointer    : int

@dataclass
class PEInfo:
    data            : bytearray
    pe_offset       : int
    coff_offset     : int
    optional_offset : int
    optional_size   : int
    optional_magic  : int
    directory_base_relative : int
    number_of_directories_offset_relative: int
    number_of_directories   : int
    file_alignment          : int
    size_of_headers         : int
    checksum_offset         : int
    section_table_offset    : int
    sections                : list[Section]
    pointer_to_symbol_table : int

    @property
    def first_raw_offset(self) -> int:
        offsets = [
            section.raw_pointer
            for section in self.sections
            if section.raw_pointer and section.raw_size
        ]
        if not offsets:
            raise ValueError("Die PE-Datei enthält keine Section-Rohdaten.")
        return min(offsets)

    def directory(self, index: int) -> tuple[int, int]:
        if index >= self.number_of_directories:
            return 0, 0
        offset = (
            self.optional_offset
            + self.directory_base_relative
            + index * 8
        )
        return u32(self.data, offset), u32(self.data, offset + 4)

    def rva_to_file_offset(self, rva: int) -> int:
        if rva < self.size_of_headers:
            return rva

        for section in self.sections:
            span = max(section.virtual_size, section.raw_size)
            if (
                section.virtual_address
                <= rva
                < section.virtual_address + span
            ):
                delta = rva - section.virtual_address
                if delta >= section.raw_size:
                    raise ValueError(
                        f"RVA 0x{rva:X} liegt im virtuellen, "
                        "aber nicht im Rohdatenbereich einer Section."
                    )
                return section.raw_pointer + delta

        raise ValueError(f"RVA 0x{rva:X} kann keiner Section zugeordnet werden.")

def parse_pe(filename: Path) -> PEInfo:
    data = bytearray(filename.read_bytes())

    if len(data) < IMAGE_DOS_HEADER_SIZE:
        raise ValueError("Datei ist kleiner als ein MZ-Header.")

    if data[0:2] != b"MZ":
        raise ValueError("Keine MZ/PE-Datei: MZ-Signatur fehlt.")

    pe_offset = u32(data, 0x3C)

    if pe_offset < IMAGE_DOS_HEADER_SIZE:
        raise ValueError(f"Ungültiger e_lfanew-Wert: 0x{pe_offset:X}")

    if pe_offset + 4 + IMAGE_FILE_HEADER_SIZE > len(data):
        raise ValueError("PE-Header liegt außerhalb der Datei.")

    if data[pe_offset:pe_offset + 4] != PE_SIGNATURE:
        raise ValueError(
            f"PE-Signatur fehlt bei e_lfanew=0x{pe_offset:X}."
        )

    coff_offset = pe_offset + 4
    number_of_sections = u16(data, coff_offset + 2)
    pointer_to_symbol_table = u32(data, coff_offset + 8)
    optional_size = u16(data, coff_offset + 16)
    optional_offset = coff_offset + IMAGE_FILE_HEADER_SIZE

    if optional_offset + optional_size > len(data):
        raise ValueError("Optional Header liegt außerhalb der Datei.")

    optional_magic = u16(data, optional_offset)

    if optional_magic == 0x10B:       # PE32
        directory_base_relative = 96
        number_of_directories_offset_relative = 92
    elif optional_magic == 0x20B:     # PE32+
        directory_base_relative = 112
        number_of_directories_offset_relative = 108
    else:
        raise ValueError(
            f"Nicht unterstützte Optional-Header-Magic: 0x{optional_magic:04X}"
        )

    if optional_size < directory_base_relative:
        raise ValueError("Optional Header ist bereits ungültig verkürzt.")

    file_alignment = u32(data, optional_offset + 36)
    size_of_headers = u32(data, optional_offset + 60)
    checksum_offset = optional_offset + 64
    number_of_directories = u32(
        data,
        optional_offset + number_of_directories_offset_relative
    )

    maximum_directories = (
        optional_size - directory_base_relative
    ) // 8

    if number_of_directories > maximum_directories:
        raise ValueError(
            "NumberOfRvaAndSizes überschreitet die Größe des Optional Headers."
        )

    section_table_offset = optional_offset + optional_size
    section_table_end = (
        section_table_offset
        + number_of_sections * IMAGE_SECTION_HEADER_SIZE
    )

    if section_table_end > len(data):
        raise ValueError("Section-Tabelle liegt außerhalb der Datei.")

    sections: list[Section] = []

    for index in range(number_of_sections):
        offset = (
            section_table_offset
            + index * IMAGE_SECTION_HEADER_SIZE
        )

        raw_name = bytes(data[offset:offset + 8]).split(b"\0", 1)[0]
        name = raw_name.decode("ascii", errors="replace")

        sections.append(
            Section(
                index=index,
                header_offset=offset,
                name=name,
                virtual_size=u32(data, offset + 8),
                virtual_address=u32(data, offset + 12),
                raw_size=u32(data, offset + 16),
                raw_pointer=u32(data, offset + 20),
                reloc_pointer=u32(data, offset + 24),
                line_pointer=u32(data, offset + 28),
            )
        )

    return PEInfo(
        data=data,
        pe_offset=pe_offset,
        coff_offset=coff_offset,
        optional_offset=optional_offset,
        optional_size=optional_size,
        optional_magic=optional_magic,
        directory_base_relative=directory_base_relative,
        number_of_directories_offset_relative=(
            number_of_directories_offset_relative
        ),
        number_of_directories=number_of_directories,
        file_alignment=file_alignment,
        size_of_headers=size_of_headers,
        checksum_offset=checksum_offset,
        section_table_offset=section_table_offset,
        sections=sections,
        pointer_to_symbol_table=pointer_to_symbol_table,
    )

def minimal_directory_count(info: PEInfo) -> int:
    last_used = -1

    for index in range(info.number_of_directories):
        address, size = info.directory(index)
        if address or size:
            last_used = index

    return last_used + 1

def shifted_file_offset(value: int, old_first_raw: int, delta: int) -> int:
    if value and value >= old_first_raw:
        return value - delta
    return value

def pe_checksum(data: bytes | bytearray, checksum_offset: int) -> int:
    checksum = 0
    length = len(data)

    for offset in range(0, length, 2):
        if checksum_offset <= offset < checksum_offset + 4:
            word = 0
        elif offset + 1 < length:
            word = data[offset] | (data[offset + 1] << 8)
        else:
            word = data[offset]

        checksum = (checksum + word) & 0xFFFFFFFF
        checksum = (checksum & 0xFFFF) + (checksum >> 16)

    checksum = (checksum & 0xFFFF) + (checksum >> 16)
    checksum = (checksum & 0xFFFF) + (checksum >> 16)
    return (checksum + length) & 0xFFFFFFFF

def collect_debug_pointer_locations(info: PEInfo) -> list[tuple[int, int]]:
    debug_rva, debug_size = info.directory(IMAGE_DIRECTORY_ENTRY_DEBUG)

    if not debug_rva or not debug_size:
        return []

    if debug_size % IMAGE_DEBUG_DIRECTORY_SIZE:
        raise ValueError(
            "Debug Directory besitzt keine ganzzahlige Anzahl "
            "IMAGE_DEBUG_DIRECTORY-Einträge."
        )

    directory_file_offset = info.rva_to_file_offset(debug_rva)
    result: list[tuple[int, int]] = []

    for relative in range(0, debug_size, IMAGE_DEBUG_DIRECTORY_SIZE):
        entry_offset = directory_file_offset + relative
        pointer_field = entry_offset + 24

        if pointer_field + 4 > len(info.data):
            raise ValueError("Debug Directory liegt außerhalb der Datei.")

        result.append(
            (pointer_field, u32(info.data, pointer_field))
        )

    return result

def build_compatible(info: PEInfo) -> bytearray:
    new_pe_offset = IMAGE_DOS_HEADER_SIZE
    new_coff_offset = new_pe_offset + 4
    new_optional_offset = new_coff_offset + IMAGE_FILE_HEADER_SIZE
    new_section_table_offset = new_optional_offset + info.optional_size
    new_section_table_end = (
        new_section_table_offset
        + len(info.sections) * IMAGE_SECTION_HEADER_SIZE
    )
    required_headers = align_up(
        new_section_table_end,
        info.file_alignment
    )

    if required_headers > info.first_raw_offset:
        raise ValueError(
            "Die Header passen nach dem Entfernen des DOS-Stubs nicht "
            "vor die erste Section. Verwende --mode compact."
        )

    output = bytearray(info.data)

    # Headerbereich neu aufbauen und den alten DOS-Stub überschreiben.
    output[IMAGE_DOS_HEADER_SIZE:info.first_raw_offset] = (
        b"\0" * (info.first_raw_offset - IMAGE_DOS_HEADER_SIZE)
    )

    output[new_pe_offset:new_pe_offset + 4] = PE_SIGNATURE

    output[
        new_coff_offset:
        new_coff_offset + IMAGE_FILE_HEADER_SIZE
    ] = info.data[
        info.coff_offset:
        info.coff_offset + IMAGE_FILE_HEADER_SIZE
    ]

    output[
        new_optional_offset:
        new_optional_offset + info.optional_size
    ] = info.data[
        info.optional_offset:
        info.optional_offset + info.optional_size
    ]

    section_bytes = (
        len(info.sections) * IMAGE_SECTION_HEADER_SIZE
    )

    output[
        new_section_table_offset:
        new_section_table_offset + section_bytes
    ] = info.data[
        info.section_table_offset:
        info.section_table_offset + section_bytes
    ]

    p32(output, 0x3C, new_pe_offset)

    new_checksum_offset = new_optional_offset + 64
    p32(output, new_checksum_offset, 0)
    p32(
        output,
        new_checksum_offset,
        pe_checksum(output, new_checksum_offset)
    )

    return output


def build_compact(info: PEInfo) -> bytearray:
    new_pe_offset = IMAGE_DOS_HEADER_SIZE
    directory_count = minimal_directory_count(info)
    new_optional_size = (
        info.directory_base_relative
        + directory_count * 8
    )

    new_coff_offset = new_pe_offset + 4
    new_optional_offset = new_coff_offset + IMAGE_FILE_HEADER_SIZE
    new_section_table_offset = new_optional_offset + new_optional_size
    new_section_table_end = (
        new_section_table_offset
        + len(info.sections) * IMAGE_SECTION_HEADER_SIZE
    )
    new_size_of_headers = align_up(
        new_section_table_end,
        info.file_alignment
    )

    old_first_raw = info.first_raw_offset

    if new_size_of_headers > old_first_raw:
        raise ValueError(
            "Der minimierte Header wäre größer als der bestehende "
            "Rohdatenbeginn. Diese Datei kann nicht nach vorne kompaktiert werden."
        )

    delta = old_first_raw - new_size_of_headers
    debug_pointers = collect_debug_pointer_locations(info)

    output = bytearray(new_size_of_headers)
    output[0:IMAGE_DOS_HEADER_SIZE] = info.data[0:IMAGE_DOS_HEADER_SIZE]
    p32(output, 0x3C, new_pe_offset)

    output[new_pe_offset:new_pe_offset + 4] = PE_SIGNATURE

    output[
        new_coff_offset:
        new_coff_offset + IMAGE_FILE_HEADER_SIZE
    ] = info.data[
        info.coff_offset:
        info.coff_offset + IMAGE_FILE_HEADER_SIZE
    ]

    # SizeOfOptionalHeader im IMAGE_FILE_HEADER.
    p16(output, new_coff_offset + 16, new_optional_size)

    output[
        new_optional_offset:
        new_optional_offset + new_optional_size
    ] = info.data[
        info.optional_offset:
        info.optional_offset + new_optional_size
    ]

    # NumberOfRvaAndSizes und SizeOfHeaders aktualisieren.
    p32(
        output,
        new_optional_offset
        + info.number_of_directories_offset_relative,
        directory_count
    )
    p32(output, new_optional_offset + 60, new_size_of_headers)

    # COFF PointerToSymbolTable ist ein Dateioffset.
    new_symbol_table_pointer = shifted_file_offset(
        info.pointer_to_symbol_table,
        old_first_raw,
        delta
    )
    p32(output, new_coff_offset + 8, new_symbol_table_pointer)

    # Security Directory.VirtualAddress ist ausnahmsweise ein Dateioffset.
    if directory_count > IMAGE_DIRECTORY_ENTRY_SECURITY:
        security_entry = (
            new_optional_offset
            + info.directory_base_relative
            + IMAGE_DIRECTORY_ENTRY_SECURITY * 8
        )
        certificate_offset = u32(output, security_entry)

        p32(
            output,
            security_entry,
            shifted_file_offset(
                certificate_offset,
                old_first_raw,
                delta
            )
        )

    # Section-Tabelle kopieren und alle darin enthaltenen Dateioffsets ändern.
    for section in info.sections:
        source = section.header_offset
        target = (
            new_section_table_offset
            + section.index * IMAGE_SECTION_HEADER_SIZE
        )

        output[
            target:
            target + IMAGE_SECTION_HEADER_SIZE
        ] = info.data[
            source:
            source + IMAGE_SECTION_HEADER_SIZE
        ]

        p32(
            output,
            target + 20,
            shifted_file_offset(
                section.raw_pointer,
                old_first_raw,
                delta
            )
        )
        p32(
            output,
            target + 24,
            shifted_file_offset(
                section.reloc_pointer,
                old_first_raw,
                delta
            )
        )
        p32(
            output,
            target + 28,
            shifted_file_offset(
                section.line_pointer,
                old_first_raw,
                delta
            )
        )

    # Sämtliche Section-Daten, Zertifikate und ein mögliches Overlay als
    # zusammenhängenden Block verschieben.
    output.extend(info.data[old_first_raw:])

    # Dateioffsets innerhalb von IMAGE_DEBUG_DIRECTORY korrigieren.
    for old_pointer_field, old_pointer_value in debug_pointers:
        new_pointer_field = shifted_file_offset(
            old_pointer_field,
            old_first_raw,
            delta
        )

        if new_pointer_field + 4 > len(output):
            raise ValueError(
                "Verschobenes Debug-Directory liegt außerhalb der Ausgabedatei."
            )

        p32(
            output,
            new_pointer_field,
            shifted_file_offset(
                old_pointer_value,
                old_first_raw,
                delta
            )
        )

    new_checksum_offset = new_optional_offset + 64
    p32(output, new_checksum_offset, 0)
    p32(
        output,
        new_checksum_offset,
        pe_checksum(output, new_checksum_offset)
    )

    return output

def verify_output(
    output_path: Path,
    expected_sections: list[Section],
    expected_section_payloads: list[bytes],
) -> PEInfo:
    result = parse_pe(output_path)

    if result.pe_offset != IMAGE_DOS_HEADER_SIZE:
        raise ValueError("Ausgabe besitzt e_lfanew != 0x40.")

    if len(result.sections) != len(expected_sections):
        raise ValueError("Anzahl der Sections hat sich verändert.")

    for new_section, old_section, expected_payload in zip(
        result.sections,
        expected_sections,
        expected_section_payloads,
    ):
        if (
            new_section.name != old_section.name
            or new_section.virtual_address != old_section.virtual_address
            or new_section.virtual_size != old_section.virtual_size
            or new_section.raw_size != old_section.raw_size
        ):
            raise ValueError(
                f"Section-Metadaten von {old_section.name} wurden verändert."
            )

        if new_section.raw_size:
            start = new_section.raw_pointer
            end = start + new_section.raw_size
            payload = bytes(result.data[start:end])

            if payload != expected_payload:
                raise ValueError(
                    f"Section-Inhalt von {old_section.name} stimmt nicht überein."
                )

    return result

def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Entfernt den DOS-Stub einer PE-Datei und setzt "
            "den PE-Header direkt hinter den MZ-Header."
        )
    )
    parser.add_argument(
        "input",
        type=Path,
        help="Eingabe-DLL oder -EXE",
    )
    parser.add_argument(
        "output",
        type=Path,
        help="Ausgabedatei",
    )
    parser.add_argument(
        "--mode",
        choices=("compact", "compatible"),
        default="compact",
        help=(
            "compact: Header und Datei verkleinern; "
            "compatible: nur DOS-Stub entfernen (Standard: compact)"
        ),
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Vorhandene Ausgabedatei überschreiben.",
    )
    parser.add_argument(
        "--backup",
        action="store_true",
        help=(
            "Falls Ein- und Ausgabepfad identisch sind, vorher eine "
            ".bak-Kopie anlegen."
        ),
    )

    args = parser.parse_args()

    input_path = args.input.resolve()
    output_path = args.output.resolve()

    if not input_path.is_file():
        parser.error(f"Eingabedatei nicht gefunden: {input_path}")

    if output_path.exists() and not args.overwrite:
        parser.error(
            f"Ausgabedatei existiert bereits: {output_path}; "
            "--overwrite verwenden."
        )

    same_file = input_path == output_path

    if same_file and not args.overwrite:
        parser.error(
            "Für Bearbeitung in derselben Datei sind "
            "--overwrite und möglichst --backup erforderlich."
        )

    try:
        info = parse_pe(input_path)

        expected_payloads = []
        for section in info.sections:
            if section.raw_size:
                start = section.raw_pointer
                end = start + section.raw_size
                expected_payloads.append(bytes(info.data[start:end]))
            else:
                expected_payloads.append(b"")

        if args.mode == "compact":
            output = build_compact(info)
        else:
            output = build_compatible(info)

        if same_file and args.backup:
            backup_path = input_path.with_suffix(
                input_path.suffix + ".bak"
            )
            shutil.copy2(input_path, backup_path)
            print(f"Sicherung: {backup_path}")

        output_path.parent.mkdir(parents=True, exist_ok=True)

        temporary_path = output_path.with_suffix(
            output_path.suffix + ".tmp"
        )
        temporary_path.write_bytes(output)
        temporary_path.replace(output_path)

        verified = verify_output(
            output_path,
            info.sections,
            expected_payloads,
        )

        print(f"Modus               : {args.mode}")
        print(f"Eingabe             : {input_path}")
        print(f"Ausgabe             : {output_path}")
        print(f"e_lfanew            : 0x{verified.pe_offset:X}")
        print(f"SizeOfOptionalHeader: 0x{verified.optional_size:X}")
        print(f"SizeOfHeaders       : 0x{verified.size_of_headers:X}")
        print(f"Data Directories    : {verified.number_of_directories}")
        print(f"Dateigröße vorher   : {len(info.data)} Byte")
        print(f"Dateigröße nachher  : {len(verified.data)} Byte")
        print("Section-Prüfung      : erfolgreich")

        return 0

    except (OSError, ValueError, struct.error) as exc:
        print(f"Fehler: {exc}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
