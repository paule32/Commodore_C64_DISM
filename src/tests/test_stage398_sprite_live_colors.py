"""Regression Stage 398: Farbregister -> Zeichenfläche -> Pinselvorschau.

Die echten C64-Sprite-Editor/Canvas-Methoden werden aus dem AST isoliert,
so dass alle Farbpipeline-Tests auch ohne installiertes PyQt5 laufen.
"""
import ast
import unittest
from pathlib import Path
from types import SimpleNamespace
from c64_sprite_codec import (default_sprite_meta, normalize_meta,
                               normalize_palette, sprite_pixel, set_sprite_pixel,
                               synchronize_shared_sprite_colors)

SOURCE = (Path(__file__).parent / 'd64_dism.py').read_text('utf-8')
TREE = ast.parse(SOURCE)

class Color:
    def __init__(self, raw):
        self.raw = raw.raw if isinstance(raw, Color) else raw
    def lightness(self):
        val = str(self.raw).lstrip('#')
        return sum(int(val[n:n+2], 16) for n in (0, 2, 4)) // 3
    def __repr__(self):
        return repr(self.raw)

class Widget:
    def __init__(self, parent=None):
        self.redraws = 0
    def setMouseTracking(self, state): pass
    def setCursor(self, value): pass
    def setFixedSize(self, x, y): self.canvas_size = (x, y)
    def update(self): self.redraws += 1
    def rect(self): return 'WHOLE'
    def setWindowTitle(self, s): self.window_title = s

class Signal:
    def emit(self): pass

def pyqtSignal(*args): return Signal()

class Painter:
    paints = []
    def __init__(self, widget):
        self.paints = []
        Painter.paints.append(self.paints)
    def fillRect(self, *args):
        self.paints.append(args)
    def end(self): pass

class Dummy:
    def __init__(self, value=0):
        self.index = value
        self.items = []
        self.roles = {}
        self.enabled = True
        self.signals_blocked = False
    def value(self): return self.index
    def currentIndex(self): return self.index
    def count(self): return len(self.items)
    def setCurrentIndex(self, value): self.index = value
    def setText(self, value): self.text = value
    def setToolTip(self, value): self.tooltip = value
    def setStyleSheet(self, value): self.stylesheet = value
    def blockSignals(self, state): self.signals_blocked = state
    def clear(self): self.items.clear(); self.index = -1
    def addItem(self, value): self.items.append(value)
    def setItemData(self, i, value, role): self.roles[(i, role)] = value
    def setEnabled(self, enabled): self.enabled = enabled

PALETTE = [(f'Farbe {i}', f'#{i:02X}{i:02X}{i:02X}') for i in range(16)]
PALETTE[7] = ('Gelb', '#FFFF00')
PALETTE[6] = ('Blau', '#0000FF')
PALETTE[11] = ('Grau', '#808080')

NAMESPACE = {
    'QWidget': Widget, 'QColor': Color, 'QPainter': Painter,
    'pyqtSignal': pyqtSignal, 'default_sprite_meta': default_sprite_meta,
    'normalize_meta': normalize_meta, 'normalize_palette': normalize_palette,
    'sprite_pixel': sprite_pixel, 'set_sprite_pixel': set_sprite_pixel,
    'synchronize_shared_sprite_colors': synchronize_shared_sprite_colors,
    'C64_CHARACTER_PALETTE': PALETTE,
    'Qt': SimpleNamespace(CrossCursor=0, DecorationRole=1, ToolTipRole=2),
}

for name in ('C64SpriteCanvas', 'C64SpriteEditorDialog'):
    original = next(n for n in ast.walk(TREE)
                    if isinstance(n, ast.ClassDef) and n.name == name)
    methods = (original.body if name == 'C64SpriteCanvas' else
               [n for n in original.body if isinstance(n, ast.FunctionDef) and n.name in
                ('_current_index', '_current_meta', '_mark_modified', '_set_vicii_color',
                 '_update_palette_buttons', '_register_color_changed',
                 '_palette_clicked', '_brush_changed')])
    fresh = ast.ClassDef(name=name, bases=[ast.Name(id='QWidget',ctx=ast.Load())],
                         keywords=[], body=methods, decorator_list=[])
    exec(compile(ast.fix_missing_locations(ast.Module(body=[fresh], type_ignores=[])),
                 '<stage398_live_colors>', 'exec'), NAMESPACE)

Canvas = NAMESPACE['C64SpriteCanvas']
Editor = NAMESPACE['C64SpriteEditorDialog']


def new_editor(mode='multicolor'):
    obj = Editor()
    obj.metas = [default_sprite_meta(), default_sprite_meta()]
    for meta in obj.metas:
        meta.update(mode=mode, width=3, height=1)
    obj.palette_entries = [list(entry) for entry in PALETTE]
    obj.sprite_number = Dummy(1)
    obj.brush_combo = Dummy(2 if mode == 'multicolor' else 1)
    for text in (['Transparent', 'Multicolor 1', 'Spritefarbe', 'Multicolor 2']
                 if mode == 'multicolor' else ['Transparent', 'Spritefarbe']):
        obj.brush_combo.addItem(text)
    obj.color_register_combos = {
        key: Dummy() for key in ('multicolor_1','sprite_color','multicolor_2')
    }
    obj.palette_buttons = [Dummy() for _ in range(16)]
    obj.canvas = Canvas()
    obj.canvas.set_data(bytearray(63), obj.metas[0])
    obj.modified = False
    obj._updating_controls = False
    return obj


def draw_pixel_colors(canvas):
    Painter.paints.clear()
    canvas.paintEvent(SimpleNamespace())
    drawn = [args[4].raw for args in Painter.paints[-1]
             if len(args) == 5]
    return drawn


class LiveSpriteColorsTests(unittest.TestCase):
    def test_hires_color_selection_repaints_existing_pixel(self):
        editor = new_editor('hires')
        set_sprite_pixel(editor.canvas.sprite_data, 0, 0, 1, 'hires')
        editor._update_palette_buttons()
        editor._register_color_changed('sprite_color', 7)
        self.assertEqual(draw_pixel_colors(editor.canvas)[0], '#FFFF00')
        self.assertEqual(editor.canvas.meta['sprite_color'], 7)
        self.assertEqual(editor.brush_combo.roles[(1, 1)].raw, '#FFFF00')
        editor._register_color_changed('sprite_color', 6)
        self.assertEqual(draw_pixel_colors(editor.canvas)[0], '#0000FF')
        self.assertTrue(editor.modified)

    def test_multicolor_yellow_blue_grey_all_three_pixel_codes(self):
        editor = new_editor()
        for x, code in enumerate((1, 2, 3)):
            set_sprite_pixel(editor.canvas.sprite_data, x, 0, code, 'multicolor')
        editor._update_palette_buttons()
        editor._register_color_changed('multicolor_1', 7)
        editor._register_color_changed('sprite_color', 6)
        editor._register_color_changed('multicolor_2', 11)
        self.assertEqual(draw_pixel_colors(editor.canvas),
                         ['#FFFF00', '#0000FF', '#808080'])
        self.assertEqual([editor.brush_combo.roles[(i, 1)].raw for i in (1,2,3)],
                         ['#FFFF00', '#0000FF', '#808080'])
        self.assertEqual([m['multicolor_1'] for m in editor.metas], [7, 7])
        self.assertEqual([m['multicolor_2'] for m in editor.metas], [11, 11])

    def test_brush_combo_selects_actual_two_bit_pixel_codes(self):
        editor = new_editor()
        for role in (0, 1, 2, 3):
            editor.brush_combo.setCurrentIndex(role)
            editor._brush_changed()
            self.assertEqual(editor.canvas.brush, role)
        editor = new_editor('hires')
        for role in (0, 1):
            editor.brush_combo.setCurrentIndex(role)
            editor._brush_changed()
            self.assertEqual(editor.canvas.brush, 1)

    def test_transparent_brush_switched_to_color_when_palette_click(self):
        for mode, expected in (('hires', 1), ('multicolor', 2)):
            editor = new_editor(mode)
            editor.brush_combo.setCurrentIndex(0)
            editor._palette_clicked(7)
            self.assertEqual(editor.brush_combo.currentIndex(), expected)
            self.assertEqual(editor.metas[0]['sprite_color'], 7)
            self.assertEqual(editor.canvas.meta['sprite_color'], 7)

    def test_palette_replace_does_not_mutate_hardware_byte_data(self):
        editor = new_editor()
        set_sprite_pixel(editor.canvas.sprite_data, 0, 0, 1, 'multicolor')
        original = bytes(editor.canvas.sprite_data)
        editor._register_color_changed('multicolor_1', 7)
        editor._register_color_changed('multicolor_2', 6)
        self.assertEqual(bytes(editor.canvas.sprite_data), original)
        other_palette = [list(e) for e in PALETTE]
        other_palette[7][1] = '#AA5500'
        editor.palette_entries = other_palette
        editor._update_palette_buttons()
        self.assertEqual(draw_pixel_colors(editor.canvas)[0], '#AA5500')

    def test_selected_palette_button_marks_same_register_as_brush(self):
        editor = new_editor()
        for role, key in ((1,'multicolor_1'), (2,'sprite_color'), (3,'multicolor_2')):
            editor.brush_combo.setCurrentIndex(role)
            editor._brush_changed()
            editor._palette_clicked(7)
            self.assertEqual(editor.metas[0][key], 7)
            self.assertEqual(editor.canvas.meta[key], 7)

if __name__ == '__main__':
    unittest.main(verbosity=2)
