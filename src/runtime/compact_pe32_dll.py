#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# File: compact_pe32_dll_safe.py
#
# Konservative PE32-DLL-Kompaktierung:
#   - entfernt ausschließlich den vollständig unbenutzten Null-Nachlauf
#     der .edata-Rohdaten;
#   - verkleinert VirtualSize und Export-Directory-Größe von .edata
#     auf die tatsächlich referenzierten Exportdaten;
#   - lässt RVA und virtuelle Section-Struktur unverändert;
#   - kann optional eine vollständig leere .idata physisch entfernen,
#     ohne ihre VirtualSize oder RVA zu löschen;
#   - verschiebt nur nachfolgende Rohdaten und korrigiert PointerToRawData;
#   - berechnet die PE-Prüfsumme neu.
#
# Das Skript ist absichtlich strenger als ein allgemeiner PE-Rewriter.
# Es verweigert Dateien mit Zertifikat-, Debug- oder COFF-Symboltabellen,
# weil dort zusätzliche absolute Dateioffsets angepasst werden müssten.
# ---------------------------------------------------------------------------
from __future__ import annotations

import argparse
import shutil
import struct
import sys
from dataclasses import dataclass
from pathlib import Path


IMAGE_DIRECTORY_ENTRY_EXPORT = 0
IMAGE_DIRECTORY_ENTRY_IMPORT = 1
IMAGE_DIRECTORY_ENTRY_SECURITY = 4
IMAGE_DIRECTORY_ENTRY_DEBUG = 6
IMAGE_DIRECTORY_ENTRY_BOUND_IMPORT = 11
IMAGE_DIRECTORY_ENTRY_IAT = 12
IMAGE_DIRECTORY_ENTRY_DELAY_IMPORT = 13

IMAGE_SCN_CNT_CODE = 0x00000020
IMAGE_SCN_CNT_INITIALIZED_DATA = 0x00000040
IMAGE_SCN_CNT_UNINITIALIZED_DATA = 0x00000080


@dataclass
class Section:
    index: int
    header_offset: int
    name: str
    virtual_size: int
    virtual_address: int
    raw_size: int
    raw_pointer: int
    reloc_pointer: int
    line_pointer: int
    characteristics: int


def read_u16(data: bytes | bytearray, offset: int) -> int:
    return struct.unpack_from("<H", data, offset)[0]


def read_u32(data: bytes | bytearray, offset: int) -> int:
    return struct.unpack_from("<I", data, offset)[0]


def write_u32(data: bytearray, offset: int, value: int) -> None:
    struct.pack_into("<I", data, offset, value & 0xFFFFFFFF)


def align_up(value: int, alignment: int) -> int:
    if alignment <= 0:
        raise ValueError("Alignment muss größer als null sein")

    return (
        value + alignment - 1
    ) // alignment * alignment


def parse_sections(
    data: bytes | bytearray,
    table_offset: int,
    count: int
) -> list[Section]:
    sections: list[Section] = []

    for index in range(count):
        offset = table_offset + index * 40

        raw_name = bytes(
            data[offset:offset + 8]
        )

        name = (
            raw_name
            .split(b"\0", 1)[0]
            .decode("ascii", errors="replace")
        )

        sections.append(
            Section(
                index=index,
                header_offset=offset,
                name=name,
                virtual_size=read_u32(data, offset + 8),
                virtual_address=read_u32(data, offset + 12),
                raw_size=read_u32(data, offset + 16),
                raw_pointer=read_u32(data, offset + 20),
                reloc_pointer=read_u32(data, offset + 24),
                line_pointer=read_u32(data, offset + 28),
                characteristics=read_u32(data, offset + 36)
            )
        )

    return sections


def section_bytes(
    data: bytes | bytearray,
    section: Section
) -> bytes:
    if section.raw_size == 0:
        return b""

    if section.raw_pointer == 0:
        raise ValueError(
            f"Section {section.name} besitzt Rohdaten ohne Dateioffset"
        )

    end = section.raw_pointer + section.raw_size

    if end > len(data):
        raise ValueError(
            f"Section {section.name} liegt außerhalb der Datei"
        )

    return bytes(
        data[
            section.raw_pointer:
            end
        ]
    )


def rva_to_file_offset(
    rva: int,
    sections: list[Section],
    size_of_headers: int
) -> int:
    if rva < size_of_headers:
        return rva

    for section in sections:
        mapped_size = max(
            section.virtual_size,
            section.raw_size
        )

        start = section.virtual_address
        end = start + mapped_size

        if start <= rva < end:
            delta = rva - start

            if delta >= section.raw_size:
                raise ValueError(
                    f"RVA 0x{rva:X} liegt nur im nullgefüllten "
                    f"virtuellen Teil von {section.name}"
                )

            return section.raw_pointer + delta

    raise ValueError(
        f"RVA 0x{rva:X} gehört zu keiner Section"
    )


def read_c_string_end(
    data: bytes | bytearray,
    file_offset: int
) -> int:
    if not 0 <= file_offset < len(data):
        raise ValueError(
            f"Ungültiger String-Dateioffset 0x{file_offset:X}"
        )

    end = bytes(data).find(
        b"\0",
        file_offset
    )

    if end < 0:
        raise ValueError(
            f"Nicht terminierter PE-String bei 0x{file_offset:X}"
        )

    return end + 1


def export_required_end(
    data: bytes | bytearray,
    sections: list[Section],
    edata: Section,
    size_of_headers: int,
    export_rva: int,
    export_size: int
) -> int:
    """
    Liefert das Ende aller tatsächlich referenzierten Exportdaten relativ
    zum Beginn der .edata-Rohdaten.
    """

    if export_rva == 0 or export_size == 0:
        raise ValueError(
            "Die DLL besitzt kein Export Directory"
        )

    if not (
        edata.virtual_address
        <= export_rva
        < edata.virtual_address + edata.virtual_size
    ):
        raise ValueError(
            "Das Export Directory liegt nicht in .edata"
        )

    directory_offset = rva_to_file_offset(
        export_rva,
        sections,
        size_of_headers
    )

    if directory_offset + 40 > len(data):
        raise ValueError(
            "IMAGE_EXPORT_DIRECTORY ist abgeschnitten"
        )

    name_rva = read_u32(data, directory_offset + 12)
    number_of_functions = read_u32(data, directory_offset + 20)
    number_of_names = read_u32(data, directory_offset + 24)
    functions_rva = read_u32(data, directory_offset + 28)
    names_rva = read_u32(data, directory_offset + 32)
    ordinals_rva = read_u32(data, directory_offset + 36)

    required_file_end = directory_offset + 40

    def include_rva_range(rva: int, size: int) -> None:
        nonlocal required_file_end

        if size == 0:
            return

        start = rva_to_file_offset(
            rva,
            sections,
            size_of_headers
        )

        required_file_end = max(
            required_file_end,
            start + size
        )

    include_rva_range(
        functions_rva,
        number_of_functions * 4
    )

    include_rva_range(
        names_rva,
        number_of_names * 4
    )

    include_rva_range(
        ordinals_rva,
        number_of_names * 2
    )

    dll_name_offset = rva_to_file_offset(
        name_rva,
        sections,
        size_of_headers
    )

    required_file_end = max(
        required_file_end,
        read_c_string_end(
            data,
            dll_name_offset
        )
    )

    if number_of_names:
        name_table_offset = rva_to_file_offset(
            names_rva,
            sections,
            size_of_headers
        )

        for index in range(number_of_names):
            symbol_name_rva = read_u32(
                data,
                name_table_offset + index * 4
            )

            symbol_name_offset = rva_to_file_offset(
                symbol_name_rva,
                sections,
                size_of_headers
            )

            required_file_end = max(
                required_file_end,
                read_c_string_end(
                    data,
                    symbol_name_offset
                )
            )

    relative_end = (
        required_file_end
        - edata.raw_pointer
    )

    if relative_end <= 0:
        raise ValueError(
            "Ungültiges Ende der Exportdaten"
        )

    return relative_end


def pe_checksum(
    data: bytes | bytearray,
    checksum_offset: int
) -> int:
    """
    Berechnet die PE-Prüfsumme gemäß CheckSumMappedFile-Logik.
    Das Checksum-Feld selbst wird als null behandelt.
    """

    total = 0
    length = len(data)
    index = 0

    while index + 1 < length:
        if checksum_offset <= index < checksum_offset + 4:
            word = 0
        else:
            word = data[index] | (data[index + 1] << 8)

        total = (total + word) & 0xFFFFFFFF
        total = (
            (total & 0xFFFF)
            + (total >> 16)
        )

        index += 2

    if index < length:
        if checksum_offset <= index < checksum_offset + 4:
            word = 0
        else:
            word = data[index]

        total = (total + word) & 0xFFFFFFFF
        total = (
            (total & 0xFFFF)
            + (total >> 16)
        )

    total = (
        (total & 0xFFFF)
        + (total >> 16)
    )

    total = (
        total
        + length
    ) & 0xFFFFFFFF

    return total


def compact_edata_tail(
    source: Path,
    destination: Path,
    drop_empty_idata: bool = False
) -> tuple[int, int, int, int, int, int]:
    original = bytearray(
        source.read_bytes()
    )

    if len(original) < 0x40 or original[:2] != b"MZ":
        raise ValueError(
            "Keine gültige MZ/PE-Datei"
        )

    pe_offset = read_u32(
        original,
        0x3C
    )

    if (
        pe_offset + 24 > len(original)
        or original[pe_offset:pe_offset + 4] != b"PE\0\0"
    ):
        raise ValueError(
            "Ungültige PE-Signatur"
        )

    file_header = pe_offset + 4
    machine = read_u16(original, file_header)
    section_count = read_u16(original, file_header + 2)
    symbol_table_pointer = read_u32(original, file_header + 8)
    symbol_count = read_u32(original, file_header + 12)
    optional_size = read_u16(original, file_header + 16)

    if machine != 0x014C:
        raise ValueError(
            "Nur PE32/i386 wird unterstützt"
        )

    if symbol_table_pointer or symbol_count:
        raise ValueError(
            "COFF-Symboltabelle vorhanden; sichere Verschiebung "
            "wird nicht unterstützt"
        )

    optional = file_header + 20

    if read_u16(original, optional) != 0x010B:
        raise ValueError(
            "Nur PE32 wird unterstützt"
        )

    file_alignment = read_u32(
        original,
        optional + 36
    )

    size_of_headers = read_u32(
        original,
        optional + 60
    )

    checksum_offset = optional + 64
    directory_offset = optional + 96

    export_rva = read_u32(
        original,
        directory_offset
        + IMAGE_DIRECTORY_ENTRY_EXPORT * 8
    )

    export_size = read_u32(
        original,
        directory_offset
        + IMAGE_DIRECTORY_ENTRY_EXPORT * 8
        + 4
    )

    import_rva = read_u32(
        original,
        directory_offset
        + IMAGE_DIRECTORY_ENTRY_IMPORT * 8
    )

    import_size = read_u32(
        original,
        directory_offset
        + IMAGE_DIRECTORY_ENTRY_IMPORT * 8
        + 4
    )

    bound_import_rva = read_u32(
        original,
        directory_offset
        + IMAGE_DIRECTORY_ENTRY_BOUND_IMPORT * 8
    )

    bound_import_size = read_u32(
        original,
        directory_offset
        + IMAGE_DIRECTORY_ENTRY_BOUND_IMPORT * 8
        + 4
    )

    iat_rva = read_u32(
        original,
        directory_offset
        + IMAGE_DIRECTORY_ENTRY_IAT * 8
    )

    iat_size = read_u32(
        original,
        directory_offset
        + IMAGE_DIRECTORY_ENTRY_IAT * 8
        + 4
    )

    delay_import_rva = read_u32(
        original,
        directory_offset
        + IMAGE_DIRECTORY_ENTRY_DELAY_IMPORT * 8
    )

    delay_import_size = read_u32(
        original,
        directory_offset
        + IMAGE_DIRECTORY_ENTRY_DELAY_IMPORT * 8
        + 4
    )

    security_offset = read_u32(
        original,
        directory_offset
        + IMAGE_DIRECTORY_ENTRY_SECURITY * 8
    )

    security_size = read_u32(
        original,
        directory_offset
        + IMAGE_DIRECTORY_ENTRY_SECURITY * 8
        + 4
    )

    debug_rva = read_u32(
        original,
        directory_offset
        + IMAGE_DIRECTORY_ENTRY_DEBUG * 8
    )

    debug_size = read_u32(
        original,
        directory_offset
        + IMAGE_DIRECTORY_ENTRY_DEBUG * 8
        + 4
    )

    if security_offset or security_size:
        raise ValueError(
            "Authenticode-Zertifikat vorhanden; Datei wird nicht verändert"
        )

    if debug_rva or debug_size:
        raise ValueError(
            "Debug Directory vorhanden; Datei wird nicht verändert"
        )

    section_table = optional + optional_size

    sections = parse_sections(
        original,
        section_table,
        section_count
    )

    edata = next(
        (
            section
            for section in sections
            if section.name == ".edata"
        ),
        None
    )

    if edata is None:
        raise ValueError(
            ".edata-Section nicht gefunden"
        )

    if (
        edata.raw_size == 0
        or edata.raw_pointer == 0
    ):
        raise ValueError(
            ".edata besitzt keine Rohdaten"
        )

    idata = next(
        (
            section
            for section in sections
            if section.name == ".idata"
        ),
        None
    )

    remove_idata_raw = False
    old_idata_raw_size = (
        idata.raw_size
        if idata is not None
        else 0
    )

    if drop_empty_idata:
        if idata is None:
            raise ValueError(
                "--drop-empty-idata wurde angegeben, "
                "aber .idata fehlt"
            )

        if (
            idata.raw_size == 0
            or idata.raw_pointer == 0
        ):
            raise ValueError(
                ".idata besitzt bereits keine physischen Rohdaten"
            )

        idata_blob = section_bytes(
            original,
            idata
        )

        if any(idata_blob):
            raise ValueError(
                ".idata enthält Nicht-Null-Daten und wird "
                "nicht entfernt"
            )

        if not (
            idata.virtual_address
            <= import_rva
            < idata.virtual_address
            + max(idata.virtual_size, 1)
        ):
            raise ValueError(
                "Das Import Directory liegt nicht in .idata"
            )

        if import_size > idata.virtual_size:
            raise ValueError(
                "Import Directory ist größer als .idata"
            )

        descriptor_offset = rva_to_file_offset(
            import_rva,
            sections,
            size_of_headers
        )

        if any(
            original[
                descriptor_offset:
                descriptor_offset + import_size
            ]
        ):
            raise ValueError(
                "Import Directory ist nicht leer"
            )

        if (
            bound_import_rva
            or bound_import_size
            or iat_rva
            or iat_size
            or delay_import_rva
            or delay_import_size
        ):
            raise ValueError(
                "Bound-, IAT- oder Delay-Importdaten vorhanden; "
                ".idata wird nicht entfernt"
            )

        remove_idata_raw = True

    required_end = export_required_end(
        original,
        sections,
        edata,
        size_of_headers,
        export_rva,
        export_size
    )

    blob = section_bytes(
        original,
        edata
    )

    last_nonzero = -1

    for index in range(
        len(blob) - 1,
        -1,
        -1
    ):
        if blob[index] != 0:
            last_nonzero = index
            break

    if last_nonzero < 0:
        raise ValueError(
            ".edata besteht vollständig aus Nullen"
        )

    used_end = max(
        required_end,
        last_nonzero + 1
    )

    new_edata_raw_size = align_up(
        used_end,
        file_alignment
    )

    if new_edata_raw_size >= edata.raw_size:
        raise ValueError(
            ".edata besitzt keinen entfernbaren, "
            "alignmentgerechten Null-Nachlauf"
        )

    removed_tail = blob[
        new_edata_raw_size:
    ]

    if any(removed_tail):
        raise ValueError(
            "Der zu entfernende .edata-Nachlauf enthält Nutzdaten"
        )

    old_raw_end = size_of_headers

    for section in sections:
        if section.raw_size:
            old_raw_end = max(
                old_raw_end,
                section.raw_pointer + section.raw_size
            )

        if section.reloc_pointer or section.line_pointer:
            raise ValueError(
                f"Section {section.name} besitzt COFF-Relocation- "
                f"oder Zeilennummer-Dateioffsets"
            )

    overlay = bytes(
        original[old_raw_end:]
    )

    output = bytearray(
        original[:size_of_headers]
    )

    cursor = size_of_headers

    for section in sections:
        if section.index == edata.index:
            new_raw_size = new_edata_raw_size
        elif (
            remove_idata_raw
            and idata is not None
            and section.index == idata.index
        ):
            new_raw_size = 0
        else:
            new_raw_size = section.raw_size

        if new_raw_size == 0:
            new_raw_pointer = 0
        else:
            cursor = align_up(
                cursor,
                file_alignment
            )

            if len(output) < cursor:
                output.extend(
                    b"\0" * (
                        cursor - len(output)
                    )
                )

            new_raw_pointer = cursor
            old_blob = section_bytes(
                original,
                section
            )

            output.extend(
                old_blob[:new_raw_size]
            )

            cursor += new_raw_size

        write_u32(
            output,
            section.header_offset + 16,
            new_raw_size
        )

        write_u32(
            output,
            section.header_offset + 20,
            new_raw_pointer
        )

        if (
            remove_idata_raw
            and idata is not None
            and section.index == idata.index
        ):
            new_characteristics = (
                section.characteristics
                & ~IMAGE_SCN_CNT_INITIALIZED_DATA
            ) | IMAGE_SCN_CNT_UNINITIALIZED_DATA

            write_u32(
                output,
                section.header_offset + 36,
                new_characteristics
            )

    output.extend(
        overlay
    )

    size_of_initialized_data = 0
    size_of_uninitialized_data = 0

    for section in sections:
        if section.index == edata.index:
            raw_size = new_edata_raw_size
        elif (
            remove_idata_raw
            and idata is not None
            and section.index == idata.index
        ):
            raw_size = 0
        else:
            raw_size = section.raw_size

        characteristics = section.characteristics

        if (
            remove_idata_raw
            and idata is not None
            and section.index == idata.index
        ):
            characteristics = (
                characteristics
                & ~IMAGE_SCN_CNT_INITIALIZED_DATA
            ) | IMAGE_SCN_CNT_UNINITIALIZED_DATA

        if (
            characteristics
            & IMAGE_SCN_CNT_INITIALIZED_DATA
        ):
            size_of_initialized_data += raw_size

        if (
            characteristics
            & IMAGE_SCN_CNT_UNINITIALIZED_DATA
        ):
            size_of_uninitialized_data += align_up(
                section.virtual_size,
                file_alignment
            )

    write_u32(
        output,
        optional + 8,
        size_of_initialized_data
    )

    write_u32(
        output,
        optional + 12,
        size_of_uninitialized_data
    )

    # Die .edata-RVA bleibt unverändert. Nur ihre tatsächliche virtuelle
    # Nutzgröße und die Export-Directory-Größe werden auf das ermittelte Ende
    # der referenzierten Exportdaten reduziert.
    write_u32(
        output,
        edata.header_offset + 8,
        required_end
    )

    write_u32(
        output,
        directory_offset
        + IMAGE_DIRECTORY_ENTRY_EXPORT * 8
        + 4,
        required_end
    )

    if remove_idata_raw:
        # Die virtuelle .idata-Section bleibt mit ihrer RVA und VirtualSize
        # erhalten, wird aber wie eine kleine BSS-Section nullgefüllt.
        # Da die DLL keine Imports besitzt, wird das leere Import Directory
        # vollständig deaktiviert.
        write_u32(
            output,
            directory_offset
            + IMAGE_DIRECTORY_ENTRY_IMPORT * 8,
            0
        )

        write_u32(
            output,
            directory_offset
            + IMAGE_DIRECTORY_ENTRY_IMPORT * 8
            + 4,
            0
        )

    write_u32(
        output,
        checksum_offset,
        0
    )

    checksum = pe_checksum(
        output,
        checksum_offset
    )

    write_u32(
        output,
        checksum_offset,
        checksum
    )

    destination.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    destination.write_bytes(
        output
    )

    return (
        len(original),
        len(output),
        edata.raw_size,
        new_edata_raw_size,
        old_idata_raw_size,
        0 if remove_idata_raw else old_idata_raw_size
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Entfernt konservativ den unbenutzten .edata-Nachlauf "
            "und optional die physischen Nullbytes einer leeren .idata."
        )
    )

    parser.add_argument(
        "input",
        type=Path,
        help="Eingabe-DLL"
    )

    parser.add_argument(
        "output",
        type=Path,
        nargs="?",
        help=(
            "Ausgabe-DLL. Ohne Angabe wird die Eingabedatei "
            "mit automatischer Sicherung ersetzt."
        )
    )

    parser.add_argument(
        "--drop-empty-idata",
        action="store_true",
        help=(
            "Entfernt zusätzlich die physischen 512 Nullbytes einer "
            "vollständig leeren .idata-Section. VirtualSize und RVA "
            "bleiben erhalten; das Import Directory wird deaktiviert."
        )
    )

    args = parser.parse_args()

    source = args.input.resolve()

    if not source.is_file():
        print(
            f"Fehler: Datei nicht gefunden: {source}",
            file=sys.stderr
        )
        return 1

    in_place = args.output is None

    if in_place:
        destination = source.with_name(
            source.name + ".compact.tmp"
        )
    else:
        destination = args.output.resolve()

    try:
        (
            old_file_size,
            new_file_size,
            old_edata_size,
            new_edata_size,
            old_idata_size,
            new_idata_size
        ) = compact_edata_tail(
            source,
            destination,
            drop_empty_idata=args.drop_empty_idata
        )

        if in_place:
            backup = source.with_name(
                source.name + ".before-safe-compact"
            )

            shutil.copy2(
                source,
                backup
            )

            destination.replace(
                source
            )

            final_path = source

            print(
                f"Sicherung : {backup}"
            )
        else:
            final_path = destination

        print(
            f"Ausgabe   : {final_path}"
        )
        print(
            f".edata raw: 0x{old_edata_size:X} -> "
            f"0x{new_edata_size:X}"
        )
        print(
            f"Dateigröße: {old_file_size} -> "
            f"{new_file_size} Bytes"
        )
        print(
            f"Ersparnis : "
            f"{old_file_size - new_file_size} Bytes"
        )
        if args.drop_empty_idata:
            print(
                f".idata raw: 0x{old_idata_size:X} -> "
                f"0x{new_idata_size:X}"
            )
            print(
                "Die virtuelle .idata-Section blieb erhalten; "
                "das leere Import Directory wurde deaktiviert."
            )
        else:
            print(
                ".idata und das Import Directory blieben unverändert; "
                ".edata VirtualSize und Exportgröße wurden sicher angepasst."
            )

        return 0

    except Exception as exc:
        try:
            if destination.exists():
                destination.unlink()
        except OSError:
            pass

        print(
            f"Fehler: {exc}",
            file=sys.stderr
        )

        return 2


if __name__ == "__main__":
    raise SystemExit(main())
