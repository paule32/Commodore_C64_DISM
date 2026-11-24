"""Stage 683: versioned, backward-compatible d64 COFF linker metadata.

The private .drectve representation is consumed by dBase2Many's own COFF
linker, not by Microsoft's/GNU's general-purpose .drectve parser.
"""

from __future__ import annotations

import struct
import zlib

_MAGIC = b"D64JZ\x01"
_HEADER = struct.Struct("<II")  # original byte length, CRC32 of JSON bytes
_MAX_JSON_BYTES = 16 * 1024 * 1024


def encode_coff_link_metadata(json_data: bytes, *, compress: bool = False) -> bytes:
    """Encode JSON bytes; by default keep the Stage-682 legacy representation."""
    payload = bytes(json_data)
    if not compress or not payload:
        return payload
    if len(payload) > _MAX_JSON_BYTES:
        raise ValueError("COFF-Metadaten überschreiten die Größenbegrenzung (16 MiB).")
    return (_MAGIC + _HEADER.pack(len(payload), zlib.crc32(payload))
            + zlib.compress(payload, level=9))


def decode_coff_link_metadata(payload: bytes) -> bytes:
    """Return original JSON; reject corrupt/unreasonably large compressed data."""
    data = bytes(payload)
    if not data.startswith(_MAGIC):
        if data.startswith(b"D64JZ"):
            raise ValueError("Komprimierte COFF-Metadaten: unbekannte Formatversion.")
        return data   # existing Stage-682 / external COFF objects
    if len(data) < len(_MAGIC) + _HEADER.size:
        raise ValueError("Komprimierte COFF-Metadaten: Header unvollständig.")
    length, checksum = _HEADER.unpack_from(data, len(_MAGIC))
    if length > _MAX_JSON_BYTES:
        raise ValueError("Komprimierte COFF-Metadaten: Originallänge zu groß.")
    encoded = data[len(_MAGIC) + _HEADER.size:]
    try:
        decompressor = zlib.decompressobj()
        decoded = decompressor.decompress(encoded, length + 1)
        if len(decoded) > length or decompressor.unconsumed_tail:
            raise ValueError("Komprimierte COFF-Metadaten: Länge überschritten.")
        decoded += decompressor.flush(length + 1 - len(decoded))
    except zlib.error as exc:
        raise ValueError("Komprimierte COFF-Metadaten sind beschädigt.") from exc
    if not decompressor.eof or decompressor.unused_data:
        raise ValueError("Komprimierte COFF-Metadaten: unvollständiger oder zusätzlicher Datenstrom.")
    if len(decoded) != length or zlib.crc32(decoded) != checksum:
        raise ValueError("Komprimierte COFF-Metadaten: Länge oder CRC32-Prüfsumme ungültig.")
    return decoded
