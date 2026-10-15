"""Stage 416: binäres Bitmap-Sprite-Format für 16 C64-Farbwerte/Pixel.

Dies ist KEIN VIC-II-Hardware-Sprite und kein direktes 320x200-Bitmapimage.
8-Byte-Signatur, uint16-le Breite, Höhe, Anzahl, dann Byte/Pix.
0..15 = C64-Farbe; 255 = transparenter Pixel.
"""
from __future__ import annotations

import struct
from pathlib import Path

MAGIC = b"C64BMSP1"
TRANSPARENT = 255
EXTENSIONS = (".bmsprite", ".bmspr")
HEADER = struct.Struct("<8sHHH")
MAX_DIMENSION = 128
MAX_SPRITES = 256
MAX_TOTAL_PIXELS = 4_194_304


def empty_sprite(width: int = 24, height: int = 21) -> bytearray:
    width, height, _ = _validate_dimensions(width, height, 1)
    return bytearray([TRANSPARENT]) * (width * height)


def _validate_dimensions(width: int, height: int, count: int):
    width, height, count = int(width), int(height), int(count)
    if not 1 <= width <= MAX_DIMENSION or not 1 <= height <= MAX_DIMENSION:
        raise ValueError("Bitmap-Sprite-Größe muss zwischen 1 und 128 Pixeln liegen")
    if not 1 <= count <= MAX_SPRITES:
        raise ValueError("Anzahl Bitmap-Sprites muss zwischen 1 und 256 liegen")
    if width * height * count > MAX_TOTAL_PIXELS:
        raise ValueError("Bitmap-Sprite-Datei überschreitet das Größenlimit")
    return width, height, count


def encode_bitmap_sprites(sprites, width: int, height: int) -> bytes:
    width, height, count = _validate_dimensions(width, height, len(sprites))
    result = bytearray(HEADER.pack(MAGIC, width, height, count))
    expected = width * height
    for index, data in enumerate(sprites, 1):
        source = bytes(data)
        if len(source) != expected:
            raise ValueError(f"Sprite {index} hat {len(source)} statt {expected} Pixel")
        if any(value != TRANSPARENT and value > 15 for value in source):
            raise ValueError(f"Sprite {index} enthält ungültige Farbwerte")
        result.extend(source)
    return bytes(result)


def decode_bitmap_sprites(data: bytes):
    data = bytes(data)
    if len(data) < HEADER.size:
        raise ValueError("Bitmap-Sprite-Datei hat keinen vollständigen Header")
    signature, width, height, count = HEADER.unpack_from(data)
    if signature != MAGIC:
        raise ValueError("Keine C64 Bitmap-Sprite-Datei (Signatur C64BMSP1 fehlt)")
    width, height, count = _validate_dimensions(width, height, count)
    span = width * height
    if len(data) != HEADER.size + span * count:
        raise ValueError("Bitmap-Sprite-Datei ist abgeschnitten oder enthält zusätzliche Daten")
    sprites = [bytearray(data[HEADER.size + i * span:HEADER.size + (i + 1) * span])
               for i in range(count)]
    if any(v != TRANSPARENT and v > 15 for sprite in sprites for v in sprite):
        raise ValueError("Bitmap-Sprite-Datei enthält ungültige Farbwerte")
    return sprites, width, height


def resized_sprite(data, old_width: int, old_height: int, width: int, height: int):
    width, height, _ = _validate_dimensions(width, height, 1)
    if len(data) != old_width * old_height:
        raise ValueError("Quell-Bitmap hat eine falsche Größe")
    pixels = empty_sprite(width, height)
    for y in range(min(old_height, height)):
        pixels[y * width:y * width + min(width, old_width)] = data[
            y * old_width:y * old_width + min(width, old_width)]
    return pixels


def load_bitmap_sprites(path: Path):
    return decode_bitmap_sprites(Path(path).read_bytes())


def save_bitmap_sprites(path: Path, sprites, width: int, height: int):
    Path(path).write_bytes(encode_bitmap_sprites(sprites, width, height))
