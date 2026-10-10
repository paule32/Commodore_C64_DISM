#!/usr/bin/env python3
# remove_gcc_ident.py
# Entfernt ausschliesslich GCC-Versionskennungen aus PE-.rdata/.comment.
# Erzeugt eine neue Datei, behaelt das PE-Layout bei und aktualisiert CheckSum.
import argparse
import re
import struct
from pathlib import Path

IDENT_RE = re.compile(
    rb"GCC: \([ -~]{1,128}\) [0-9][A-Za-z0-9.+_-]{0,48}\x00"
)


def word(data, offset):
    return struct.unpack_from("<H", data, offset)[0]


def dword(data, offset):
    return struct.unpack_from("<I", data, offset)[0]


def read_pe_sections(data):
    if len(data) < 128 or data[:2] != b"MZ":
        raise ValueError("Keine gueltige PE-Datei (MZ fehlt)")

    pe = dword(data, 0x3C)
    if pe + 24 > len(data) or data[pe:pe + 4] != b"PE\0\0":
        raise ValueError("PE-Signatur fehlt")

    section_count = word(data, pe + 6)
    opt_size = word(data, pe + 20)
    opt = pe + 24
    if opt + opt_size > len(data):
        raise ValueError("Ungueltiger PE Optional Header")

    magic = word(data, opt)
    if magic not in (0x10B, 0x20B):
        raise ValueError("Unbekanntes PE-Format")

    checksum_offset = opt + 64
    if checksum_offset + 4 > opt + opt_size:
        raise ValueError("PE-Checksum-Feld fehlt")

    sec_dir = opt + (96 if magic == 0x10B else 112) + 4 * 8
    signed = (
        sec_dir + 8 <= opt + opt_size
        and dword(data, sec_dir) != 0
        and dword(data, sec_dir + 4) != 0
    )

    sections = []
    sec_table = opt + opt_size
    if section_count > 96 or sec_table + section_count * 40 > len(data):
        raise ValueError("Ungueltige PE-Sektionstabelle")

    for i in range(section_count):
        header = sec_table + i * 40
        name = data[header:header + 8].split(b"\0", 1)[0].decode(
            "ascii", errors="replace"
        )
        raw_size = dword(data, header + 16)
        raw_offset = dword(data, header + 20)
        if raw_size and raw_offset + raw_size > len(data):
            raise ValueError(f"PE-Sektion {name} ausserhalb der Datei")
        sections.append((name, raw_offset, raw_size))

    return sections, checksum_offset, signed


def pe_checksum(data, checksum_offset):
    """IMAGE_OPTIONAL_HEADER.CheckSum nach PE-Checksum-Algorithmus."""
    padded = data + b"\0" * (-len(data) % 4)
    checksum = 0

    for i in range(0, len(padded), 4):
        if i == checksum_offset:
            continue
        value = struct.unpack_from("<I", padded, i)[0]
        checksum = (checksum & 0xFFFFFFFF) + value + (checksum >> 32)

    checksum = (checksum & 0xFFFF) + (checksum >> 16)
    checksum += checksum >> 16
    checksum &= 0xFFFF
    return (checksum + len(data)) & 0xFFFFFFFF


def clean_file(source, destination):
    raw = source.read_bytes()
    sections, checksum_offset, signed = read_pe_sections(raw)

    if signed:
        raise ValueError(
            "Die Datei besitzt eine Authenticode-Signatur. "
            "Bitte zuerst die Signatur-/Neusignierungsstrategie klaeren."
        )

    result = bytearray(raw)
    findings = []
    for name, offset, size in sections:
        if not (name.startswith(".rdata") or name == ".comment"):
            continue
        chunk = raw[offset:offset + size]

        for match in IDENT_RE.finditer(chunk):
            absolute = offset + match.start()
            # Nur eigenstaendige NUL-terminierte Metadatenstrings bearbeiten.
            if absolute != offset and raw[absolute - 1] != 0:
                continue
            result[absolute:absolute + len(match.group())] = (
                b"\0" * len(match.group())
            )
            findings.append((name, absolute, match.group()[:-1].decode("ascii")))

    if not findings:
        return []

    checksum = pe_checksum(bytes(result), checksum_offset)
    struct.pack_into("<I", result, checksum_offset, checksum)

    # Original unangetastet lassen.
    if destination.resolve() == source.resolve():
        raise ValueError("Originaldatei wird nicht ueberschrieben")

    destination.write_bytes(result)
    verified = destination.read_bytes()
    if len(verified) != len(raw):
        raise AssertionError("Dateigroesse hat sich geaendert")
    if IDENT_RE.search(verified):
        raise AssertionError("Mindestens ein GCC-Ident-String ist verblieben")

    print(f"PE CheckSum neu berechnet: 0x{checksum:08X}")
    return findings


def main():
    parser = argparse.ArgumentParser(
        description="GCC-Ident-Strings aus Windows-EXE/DLL entfernen"
    )
    parser.add_argument("input", type=Path, help="Original EXE/DLL")
    parser.add_argument(
        "output", nargs="?", type=Path,
        help="Ausgabedatei (Standard: *_noident.exe/.dll)"
    )
    args = parser.parse_args()

    if not args.input.is_file():
        parser.error(f"Nicht gefunden: {args.input}")

    output = args.output or args.input.with_name(
        args.input.stem + "_noident" + args.input.suffix
    )

    try:
        found = clean_file(args.input, output)
    except (ValueError, OSError, AssertionError) as exc:
        parser.error(str(exc))

    if found:
        print(f"{len(found)} GCC-Ident-Strings entfernt:")
        for section, offset, ident in found[:5]:
            print(f"  {section} @ 0x{offset:X} : {ident}")
        if len(found) > 5:
            print(f"  ... und {len(found) - 5} weitere")
        print(f"Ausgabe: {output}")
    else:
        print("Keine passenden GCC-Ident-Strings gefunden; keine Datei geschrieben.")


if __name__ == "__main__":
    main()
