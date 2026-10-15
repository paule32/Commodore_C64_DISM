"""C64 sprite builder: portable storage, 6510/VIC-II pixel packing.

A hardware sprite uses 63 bytes for 24x21 single-colour pixels or 12x21
multicolour pixels (each multicolour pixel spans two hardware X pixels).
The 64th alignment byte in 64-byte records is preserved verbatim.
"""
from __future__ import annotations

import json
from pathlib import Path

SPRITE_HEIGHT = 21
SPRITE_WIDTH = 24
SPRITE_BYTES = 63
DEFAULT_META = {
    "mode": "hires", "width": 24, "height": 21,
    "sprite_color": 1, "multicolor_1": 2, "multicolor_2": 3,
    "background": 0, "expand_x": False, "expand_y": False,
}


def sprite_pixel(data, x: int, y: int, mode: str = "hires") -> int:
    if not (0 <= y < 21):
        raise ValueError("Zeile außerhalb des Sprite-Rasters")
    if mode == "multicolor":
        if not 0 <= x < 12:
            raise ValueError("Multicolor-Spalte außerhalb des Rasters")
        index = y * 3 + x // 4
        shift = 6 - 2 * (x % 4)
        return (data[index] >> shift) & 3
    if not 0 <= x < 24:
        raise ValueError("HiRes-Spalte außerhalb des Rasters")
    index = y * 3 + x // 8
    return (data[index] >> (7 - x % 8)) & 1


def set_sprite_pixel(data, x: int, y: int, value: int, mode: str = "hires") -> bool:
    before = sprite_pixel(data, x, y, mode)
    if mode == "multicolor":
        if not 0 <= value <= 3:
            raise ValueError("Multicolor-Wert muss 0..3 sein")
        index, shift = y * 3 + x // 4, 6 - 2 * (x % 4)
        data[index] = (data[index] & ~(3 << shift)) | (value << shift)
    else:
        if value not in (0, 1):
            raise ValueError("HiRes-Wert muss 0 oder 1 sein")
        index, shift = y * 3 + x // 8, 7 - x % 8
        data[index] = (data[index] & ~(1 << shift)) | (value << shift)
    return before != value


def default_sprite_meta():
    return DEFAULT_META.copy()


def normalize_meta(value):
    if not isinstance(value, dict):
        raise ValueError("Sprite-Einstellungen müssen ein Objekt sein")
    meta = default_sprite_meta()
    meta.update(value)
    if meta['mode'] not in ('hires', 'multicolor'):
        raise ValueError("Sprite-Modus muss hires oder multicolor sein")
    max_width = 12 if meta['mode'] == 'multicolor' else 24
    for name, maximum in (('width', max_width), ('height', 21)):
        if type(meta[name]) is not int or not 1 <= meta[name] <= maximum:
            raise ValueError(f"{name}: nur Werte von 1 bis {maximum} erlaubt")
    for name in ('sprite_color', 'multicolor_1', 'multicolor_2', 'background'):
        if type(meta[name]) is not int or not 0 <= meta[name] <= 15:
            raise ValueError(f"{name}: nur Farbnummern von 0 bis 15 erlaubt")
    for name in ('expand_x', 'expand_y'):
        if type(meta[name]) is not bool:
            raise ValueError(f"{name} muss true oder false sein")
    return {key: meta[key] for key in DEFAULT_META}


def decode_raw_sprites(data):
    data = bytes(data)
    if not data:
        raise ValueError('Sprite-Datei ist leer')
    # Prefer 64-byte VIC-II-aligned records for ambiguous lengths.
    if len(data) % 64 == 0:
        size = 64
    elif len(data) % 63 == 0:
        size = 63
    else:
        raise ValueError('Dateigröße muss durch 63 oder 64 teilbar sein')
    return [bytearray(data[n:n+size]) for n in range(0, len(data), size)], size


def encode_raw_sprites(sprites, record_size=64):
    if record_size not in (63, 64):
        raise ValueError('Recordgröße nur 63 oder 64 Bytes')
    if not sprites:
        raise ValueError('Mindestens ein Sprite erforderlich')
    result = bytearray()
    for sprite in sprites:
        if len(sprite) not in (63, 64):
            raise ValueError('Sprite muss 63 oder 64 Bytes lang sein')
        result.extend(bytes(sprite)[:record_size].ljust(record_size, b'\0'))
    return bytes(result)


def palette_from_bytes(data, default_names):
    data = bytes(data)
    if len(data) != 48:
        raise ValueError('C64-Palette muss genau 48 RGB-Bytes haben')
    return [(str(default_names[i]), '#'+data[i*3:i*3+3].hex().upper()) for i in range(16)]


def normalize_palette(palette):
    if not isinstance(palette, (tuple, list)) or len(palette) != 16:
        raise ValueError('Genau 16 Palettenfarben erforderlich')
    result = []
    for i, entry in enumerate(palette):
        if not isinstance(entry, (list, tuple)) or len(entry) != 2:
            raise ValueError(f'Palette[{i}]: Name und RGB-Farbe erwartet')
        name, rgb = entry
        if not isinstance(rgb, str) or len(rgb) != 7 or rgb[0] != '#':
            raise ValueError('RGB-Format muss #RRGGBB sein')
        try:
            int(rgb[1:], 16)
        except ValueError as exc:
            raise ValueError('Ungültige RGB-Farbe') from exc
        result.append([str(name), rgb.upper()])
    return result



# VIC-II: $D025 and $D026 are shared by ALL eight hardware sprites.
# Only $D027 ... $D02E (individual sprite colour) differs per sprite.
VICII_COLOR_REGISTERS = {
    'multicolor_1': 0xD025,
    'multicolor_2': 0xD026,
    'sprite_color': 0xD027,
}


def synchronize_shared_sprite_colors(metas, multicolor_1=None, multicolor_2=None):
    """Apply VIC-II global multicolor registers to every sprite's metadata.

    In-place; return True if an entry changed. In a loaded legacy file the
    first sprite determines the global colour values.
    """
    if not metas:
        return False
    first = normalize_meta(metas[0])
    values = {
        'multicolor_1': first['multicolor_1'] if multicolor_1 is None else multicolor_1,
        'multicolor_2': first['multicolor_2'] if multicolor_2 is None else multicolor_2,
    }
    for key, value in values.items():
        if type(value) is not int or not 0 <= value <= 15:
            raise ValueError(f'{key}: nur VIC-II-Farben 0 bis 15 erlaubt')
    changed = False
    for meta in metas:
        for key, value in values.items():
            if meta[key] != value:
                meta[key] = value
                changed = True
    return changed


def vicii_sprite_color_registers(meta, sprite_number=0):
    """Return the REAL VIC-II colour register values for sprite 0..7.

    Bitmap bytes in .spr/.bin do not contain colour-register information.
    """
    meta = normalize_meta(meta)
    if type(sprite_number) is not int or not 0 <= sprite_number <= 7:
        raise ValueError('Hardware-Sprite-Nummer muss 0 bis 7 sein')
    registers = {0xD027 + sprite_number: meta['sprite_color']}
    if meta['mode'] == 'multicolor':
        registers[0xD025] = meta['multicolor_1']
        registers[0xD026] = meta['multicolor_2']
    return registers


def save_document(path, sprites, metas, palette, record_size=64):
    if len(sprites) != len(metas):
        raise ValueError('Sprite- und Metadaten-Anzahl ungleich')
    # Multiple sprites cannot have differing values for shared VIC-II registers.
    metas = [normalize_meta(meta) for meta in metas]
    synchronize_shared_sprite_colors(metas)
    document = {
        'format': 'd64-c64-sprites', 'version': 1,
        'palette': normalize_palette(palette),
        'record_size': int(record_size),
        'sprites': [
            {'data_hex': bytes(sprite).hex().upper(), 'settings': normalize_meta(meta)}
            for sprite, meta in zip(sprites, metas)
        ],
    }
    # Validate all sprites before writing; no partial success.
    encode_raw_sprites(sprites, record_size)
    Path(path).write_text(json.dumps(document, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def load_document(path):
    obj = json.loads(Path(path).read_text(encoding='utf-8'))
    if not isinstance(obj, dict) or obj.get('format') != 'd64-c64-sprites' or obj.get('version') != 1:
        raise ValueError('Unbekanntes C64-Sprite-Projektformat')
    size = obj.get('record_size', 64)
    if type(size) is not int or size not in (63, 64):
        raise ValueError('record_size muss 63 oder 64 sein')
    entries = obj.get('sprites')
    if not isinstance(entries, list) or not entries:
        raise ValueError('Mindestens ein Sprite erforderlich')
    sprites, metas = [], []
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError('Ungültiger Sprite-Eintrag')
        raw = bytes.fromhex(entry['data_hex'])
        if len(raw) != size:
            raise ValueError('Falsche Sprite-Datenlänge')
        sprites.append(bytearray(raw))
        metas.append(normalize_meta(entry['settings']))
    synchronize_shared_sprite_colors(metas)
    return sprites, metas, normalize_palette(obj['palette']), size
