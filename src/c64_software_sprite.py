"""Stage 417: 1541 independent multicolour bitmap software-sprite planner.

VIC-II MC bitmap: 160x200 logical pixels (2 physical X pixels each), four
colours per 4x8 logical-pixel cell: global background plus three selectable
colours (screen high, low, colour RAM).  No silent quantisation.

All draw positions are literal constants; compiler emits delta writes for a
straight-line BASIC scene, guaranteeing correct overlapping ERASE semantics.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import struct

from c64_bitmap_sprite import decode_bitmap_sprites, EXTENSIONS, TRANSPARENT

WIDTH, HEIGHT = 160, 200
BITMAP_ADDR, SCREEN_ADDR, COLOR_ADDR = 0x6000, 0x4400, 0xD800


@dataclass(frozen=True)
class SoftwareSpriteSheet:
    sprites: tuple[bytes, ...]
    width: int
    height: int
    path: Path


def load_software_sprite_sheet(path: Path) -> SoftwareSpriteSheet:
    """Read .bmsprite colour pixels or VIC-II .spr monochrome bitmap."""
    path = Path(path)
    raw = path.read_bytes()
    if path.suffix.lower() in EXTENSIONS:
        sprites, width, height = decode_bitmap_sprites(raw)
        return SoftwareSpriteSheet(tuple(bytes(s) for s in sprites), width, height, path)
    if len(raw) >= 66 and (len(raw) - 2) % 64 == 0:
        raw = raw[2:]
    if raw and len(raw) % 64 == 0:
        sprite_bytes = [raw[i:i + 64][:63] for i in range(0, len(raw), 64)]
    elif raw and len(raw) % 63 == 0:
        sprite_bytes = [raw[i:i + 63] for i in range(0, len(raw), 63)]
    else:
        raise ValueError('Erwartet .bmsprite oder .spr mit 63/64 Bytes pro Hardware-Sprite')
    if len(sprite_bytes) > 256:
        raise ValueError('Maximal 256 Software-Sprites pro Datei')
    sprites = []
    for bitmap in sprite_bytes:
        pixels = bytearray()
        for value in bitmap:
            for shift in range(7, -1, -1):
                pixels.append(1 if value & (1 << shift) else TRANSPARENT)
        sprites.append(bytes(pixels))
    return SoftwareSpriteSheet(tuple(sprites), 24, 21, path)


class SoftwareSpriteScene:
    """Computes the three VIC memory planes for the current logical scene."""
    def __init__(self):
        self.sheet: SoftwareSpriteSheet | None = None
        self.visible: dict[int, tuple[int, int]] = {}
        self.reset()

    def reset(self):
        self.visible = {}
        self.bitmap = bytes(8000)
        self.screen = bytes(1000)
        self.colour = bytes(1000)

    def compose(self):
        if not self.sheet:
            raise ValueError('Vor SPRITE DRAW muss LOAD SPRITE ausgeführt werden')
        pix = bytearray(WIDTH * HEIGHT)
        width, height = self.sheet.width, self.sheet.height
        for number, (x, y) in self.visible.items():
            data = self.sheet.sprites[number]
            # X is given in physical C64 pixels (0..319): X/2 is the MC pixel.
            x //= 2
            for sy in range(height):
                dy = y + sy
                if dy >= HEIGHT:
                    break
                for sx in range(width):
                    dx = x + sx
                    if dx >= WIDTH:
                        break
                    color = data[sy * width + sx]
                    if color != TRANSPARENT:
                        pix[dy * WIDTH + dx] = color
        bitmap = bytearray(8000)
        screen = bytearray(1000)
        colour = bytearray(1000)
        for cell_y in range(25):
            for cell_x in range(40):
                cell = cell_y * 40 + cell_x
                colors = []
                codes = [[0] * 4 for _ in range(8)]
                for py in range(8):
                    for px in range(4):
                        color = pix[(cell_y * 8 + py) * WIDTH + cell_x * 4 + px]
                        if not color:
                            continue
                        if color not in colors:
                            colors.append(color)
                            if len(colors) > 3:
                                raise ValueError(
                                    f'Multicolor-Farbgrenze: 8x8-Zelle X={cell_x*8}, Y={cell_y*8} '
                                    'enthaelt mehr als 3 sichtbare Farben zusaetzlich zu Hintergrundfarbe 0'
                                )
                        codes[py][px] = colors.index(color) + 1
                if colors:
                    screen[cell] = ((colors[0] & 15) << 4) | (colors[1] if len(colors) > 1 else 0)
                    colour[cell] = colors[2] if len(colors) > 2 else 0
                for py in range(8):
                    bitmap[cell * 8 + py] = (codes[py][0] << 6) | (codes[py][1] << 4) | (codes[py][2] << 2) | codes[py][3]
        return bytes(bitmap), bytes(screen), bytes(colour)

    def move(self, number: int, x: int, y: int):
        if self.sheet is None or not 0 <= number < len(self.sheet.sprites):
            raise ValueError(f'Software-Sprite {number} ist nicht in LOAD SPRITE enthalten')
        if not 0 <= x < 320 or x & 1 or not 0 <= y < HEIGHT:
            raise ValueError('SPRITE DRAW: X muss gerade und 0..318, Y muss 0..199 sein')
        old = self.visible.get(number)
        self.visible[number] = (x, y)
        try:
            return self.compose()
        except ValueError:
            if old is None:
                del self.visible[number]
            else:
                self.visible[number] = old
            raise

    def erase(self, number: int):
        if self.sheet is None or not 0 <= number < len(self.sheet.sprites):
            raise ValueError(f'Software-Sprite {number} ist nicht in LOAD SPRITE enthalten')
        self.visible.pop(number, None)
        return self.compose()

    def commit(self, planes):
        old = (self.bitmap, self.screen, self.colour)
        modifications = []
        for base, previous, current in zip((BITMAP_ADDR, SCREEN_ADDR, COLOR_ADDR), old, planes):
            modifications.extend((base + i, value) for i, (prev, value) in enumerate(zip(previous, current)) if prev != value)
        self.bitmap, self.screen, self.colour = planes
        return modifications
