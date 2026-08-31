#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# File: pack_dll.py
#
# Packs a DLL into a small zlib container suitable for embedding as RCDATA.
# ---------------------------------------------------------------------------
from __future__ import annotations

import argparse
import struct
import zlib
from pathlib import Path

MAGIC = b"DBDLLZ1\0"
VERSION = 1
HEADER = struct.Struct("<8sIIII")


def pack_dll(source: Path, destination: Path, level: int) -> None:
    raw = source.read_bytes()
    compressor = zlib.compressobj(
        level,
        zlib.DEFLATED,
        -15
    )
    compressed = (
        compressor.compress(raw)
        + compressor.flush()
    )

    header = HEADER.pack(
        MAGIC,
        VERSION,
        len(raw),
        len(compressed),
        zlib.crc32(raw) & 0xFFFFFFFF
    )

    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(header + compressed)

    print(f"Eingabe    : {source}")
    print(f"Ausgabe    : {destination}")
    print(f"Original   : {len(raw)} Bytes")
    print(f"Komprimiert: {len(compressed)} Bytes")
    print(f"Container  : {len(header) + len(compressed)} Bytes")
    print(f"Ersparnis  : {len(raw) - len(header) - len(compressed)} Bytes")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Komprimiert eine DLL in einen DBDLLZ1-Container."
    )
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument(
        "--level",
        type=int,
        default=9,
        choices=range(0, 10),
        metavar="0..9"
    )
    args = parser.parse_args()

    if not args.input.is_file():
        parser.error(f"DLL nicht gefunden: {args.input}")

    pack_dll(args.input, args.output, args.level)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
