#!/usr/bin/env python3
from __future__ import annotations

import argparse
import pathlib
import struct
import zlib


MAGIC = b"DBDLLZ1\0"
VERSION = 1
HEADER_FORMAT = "<8sIIII"
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)  # 24 bytes


def compress_fixed_raw(data: bytes, level: int = 9) -> bytes:
    compressor = zlib.compressobj(
        level=level,
        method=zlib.DEFLATED,
        wbits=-15,                 # Raw DEFLATE
        memLevel=9,
        strategy=zlib.Z_FIXED,     # Fixed Huffman / stored blocks
    )
    return compressor.compress(data) + compressor.flush(zlib.Z_FINISH)


def build_dbm_image(data: bytes, level: int = 9) -> bytes:
    packed = compress_fixed_raw(data, level)

    header = struct.pack(
        HEADER_FORMAT,
        MAGIC,
        VERSION,
        len(data),
        len(packed),
        zlib.crc32(data) & 0xFFFFFFFF,
    )

    return header + packed


def verify_dbm_image(image: bytes) -> bytes:
    if len(image) < HEADER_SIZE:
        raise ValueError("image is shorter than the DBDLLZ1 header")

    magic, version, original_size, packed_size, expected_crc = struct.unpack_from(
        HEADER_FORMAT,
        image,
        0,
    )

    if magic != MAGIC:
        raise ValueError(f"bad magic: {magic!r}")

    if version != VERSION:
        raise ValueError(f"unsupported version: {version}")

    if packed_size > len(image) - HEADER_SIZE:
        raise ValueError("packed size exceeds file size")

    packed = image[HEADER_SIZE:HEADER_SIZE + packed_size]
    restored = zlib.decompress(packed, wbits=-15)

    if len(restored) != original_size:
        raise ValueError(
            f"size mismatch: expected {original_size}, got {len(restored)}"
        )

    actual_crc = zlib.crc32(restored) & 0xFFFFFFFF
    if actual_crc != expected_crc:
        raise ValueError(
            f"CRC mismatch: expected {expected_crc:08X}, got {actual_crc:08X}"
        )

    return restored


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create a DBDLLZ1 image using Raw DEFLATE with fixed Huffman codes."
    )
    parser.add_argument("source", type=pathlib.Path)
    parser.add_argument("destination", type=pathlib.Path)
    parser.add_argument("--level", type=int, default=9)
    args = parser.parse_args()

    source_data = args.source.read_bytes()
    image = build_dbm_image(source_data, args.level)

    # Validate before writing.
    restored = verify_dbm_image(image)
    if restored != source_data:
        raise RuntimeError("internal verification failed")

    args.destination.write_bytes(image)

    _, _, original_size, packed_size, crc32 = struct.unpack_from(
        HEADER_FORMAT,
        image,
        0,
    )

    print(f"header     : {HEADER_SIZE} bytes")
    print(f"original   : {original_size} bytes")
    print(f"compressed : {packed_size} bytes")
    print(f"total      : {len(image)} bytes")
    print(f"crc32      : {crc32:08X}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
