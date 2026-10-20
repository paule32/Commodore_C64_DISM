# -*- coding: utf-8 -*-
"""Stage 440: drei C64-Zellbytes, Legacy-Lesen, Farbmodus und weiße GroupBox-Titel."""
import ast
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import *

SOURCE_PATH = Path(__file__).with_name('d64_dism.py')
SOURCE = SOURCE_PATH.read_text(encoding='utf-8')
TREE = ast.parse(SOURCE)

PURE_NAMES = {
    'normalize_c64_text_screen_data', 'normalize_c64_text_screen_layers',
    'encode_c64_text_screen_data', 'decode_c64_text_screen_data',
    'encode_c64_text_screen_json', 'decode_c64_text_screen_json',
    'load_c64_text_screen_file', 'save_c64_text_screen_file',
    '_format_asm_byte_rows', 'format_c64_text_screen_asm',
    'format_c64_text_screen_c', 'format_c64_text_screen_pascal',
    'format_c64_text_screen_basic', 'format_c64_text_screen_output',
}


def _functions():
    ns = dict(
        __name__='__test__', __file__=str(SOURCE_PATH), Path=Path, json=json,
        Any=Any, Dict=Dict, List=List, Optional=Optional, Sequence=Sequence,
        Tuple=Tuple, Union=Union,
        C64_TEXT_SCREEN_COLUMNS=40, C64_TEXT_SCREEN_ROWS=25,
        C64_TEXT_SCREEN_CELL_COUNT=1000, C64_TEXT_SCREEN_FILE_SIZE=2000,
        C64_TEXT_SCREEN_RGB_FILE_SIZE=3000,
        C64_TEXT_SCREEN_JSON_VERSION=1,
        C64_TEXT_SCREEN_JSON_FORMAT='d64-c64-text-screen',
        normalize_c64_output_format=lambda s: s,
    )
    nodes = [node for node in TREE.body if isinstance(node, ast.FunctionDef) and node.name in PURE_NAMES]
    module = ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[]))
    exec(compile(module, '<stage440_subset>', 'exec'), ns)
    return ns


def _data():
    chars = bytearray([32] * 1000)
    fg = bytearray([1] * 1000)
    bg = bytearray([0] * 1000)
    chars[5] = 65
    fg[5] = 7
    bg[5] = 9
    return chars, fg, bg


def test_new_3000_byte_file_contains_three_independent_layers():
    ns = _functions()
    chars, fg, bg = _data()
    raw = ns['encode_c64_text_screen_data'](chars, fg, bg)
    assert len(raw) == 3000
    assert (raw[5], raw[1005], raw[2005]) == (65, 9, 7)
    out_chars, out_bg, out_fg = ns['decode_c64_text_screen_data'](raw, include_background=True)
    assert (out_chars, out_bg, out_fg) == (chars, bg, fg)


def test_legacy_1000_and_2000_bytes_load_with_black_background():
    ns = _functions()
    chars, fg, _ = _data()
    raw1000 = bytes(chars)
    raw2000 = ns['encode_c64_text_screen_data'](chars, fg)
    assert len(raw2000) == 2000
    assert ns['decode_c64_text_screen_data'](raw1000, include_background=True)[1] == bytes(1000)
    assert ns['decode_c64_text_screen_data'](raw2000, include_background=True) == (chars, bytearray(1000), fg)
    assert ns['decode_c64_text_screen_data'](raw2000) == (chars, fg)


def test_json_3_byte_roundtrip_and_legacy_json_compatibility():
    ns = _functions()
    chars, fg, bg = _data()
    raw = ns['encode_c64_text_screen_json'](chars, fg, bg)
    payload = json.loads(raw)
    assert payload['version'] == 2
    assert payload['cells'][0][5] == {'character': 65, 'color': 7, 'background': 9}
    assert ns['decode_c64_text_screen_json'](raw, include_background=True) == (chars, bg, fg)
    legacy = ns['encode_c64_text_screen_json'](chars, fg)
    assert ns['decode_c64_text_screen_json'](legacy, include_background=True) == (chars, bytearray(1000), fg)


def test_files_save_and_load_3000_bytes_or_json():
    ns = _functions()
    chars, fg, bg = _data()
    with TemporaryDirectory() as temp:
        for suffix in ('.scr', '.json'):
            path = Path(temp) / ('screen' + suffix)
            nbytes = ns['save_c64_text_screen_file'](path, chars, fg, bg)
            assert nbytes == path.stat().st_size
            assert ns['load_c64_text_screen_file'](path, include_background=True) == (chars, bg, fg)
            if suffix == '.scr': assert nbytes == 3000


def test_invalid_layer_lengths_rejected():
    ns = _functions()
    chars, fg, bg = _data()
    try:
        ns['encode_c64_text_screen_data'](chars, fg, [1, 2])
    except ValueError as exc:
        assert '1000' in str(exc)
    else:
        raise AssertionError('Must reject incorrect background layer length')


def test_color_only_changes_background_and_retains_character_and_foreground():
    # Use actual method AST, replacing signals with little local stand-ins.
    outer = next(n for n in ast.walk(TREE) if isinstance(n, ast.ClassDef) and n.name == 'C64TextScreenCanvas')
    method = next(n for n in outer.body if isinstance(n, ast.FunctionDef) and n.name == '_paint_cell')
    ns = {}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[method], type_ignores=[])), '<paint_cell>', 'exec'), ns)

    class Signal:
        def __init__(self): self.emits = 0
        def emit(self): self.emits += 1

    class Canvas:
        def __init__(self):
            self._characters, self._colors, self._backgrounds = _data()
            self._color_only = True
            self._brush_color = 12
            self._brush_character = 88
            self.screenChanged = Signal()
            self._offset = lambda x,y: y*40+x
            self._emit_cursor = lambda: None
            self.update = lambda: None
    c=Canvas()
    ns['_paint_cell'](c, 5, 0)
    assert (c._characters[5], c._backgrounds[5], c._colors[5]) == (65, 12, 7)
    assert c.screenChanged.emits == 1
    ns['_paint_cell'](c, 5, 0, True)
    assert (c._characters[5], c._backgrounds[5], c._colors[5]) == (65, 0, 7)
    c._color_only = False
    ns['_paint_cell'](c, 5, 0)
    assert (c._characters[5], c._backgrounds[5], c._colors[5]) == (88, 0, 12)


def test_exporters_include_backgrounds_without_breaking_legacy():
    ns = _functions()
    chars, fg, bg = _data()
    for lang, token in [('Assembler','C64TextScreenBackgrounds:'),('Pascal','C64TextScreenBackgrounds:'),('C','C64TextScreenBackgrounds['),('BASIC','HINTERGRUNDFARBEN')]:
        output = ns['format_c64_text_screen_output'](chars, fg, lang, bg)
        assert token in output, lang
        legacy = ns['format_c64_text_screen_output'](chars, fg, lang)
        assert token not in legacy, lang


def test_six_tool_dialogs_get_initial_and_dynamic_theme():
    names = ('C64TextScreenEditorDialog', 'C64PixelScreenEditorDialog',
             'C64PaletteEditorDialog', 'C64CharacterEditorDialog',
             'LocalizeToolWindow', 'DoxyGenToolWindow')
    for name in names:
        cls = next(n for n in ast.walk(TREE) if isinstance(n, ast.ClassDef) and n.name == name)
        init = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == '__init__')
        fragment = ast.get_source_segment(SOURCE, init)
        assert 'apply_c64_tool_groupbox_theme(self' in fragment, name
    theme_method = next(n for n in ast.walk(TREE) if isinstance(n, ast.FunctionDef) and n.name == '_apply_application_theme')
    theme_source = ast.get_source_segment(SOURCE, theme_method)
    assert 'apply_c64_tool_groupbox_theme(widget, enabled)' in theme_source
    helper = next(n for n in TREE.body if isinstance(n, ast.FunctionDef) and n.name == 'apply_c64_tool_groupbox_theme')
    helper_source = ast.get_source_segment(SOURCE, helper)
    assert '#ffffff' in helper_source
    assert 'group.setStyleSheet(str(base or ""))' in helper_source


def test_text_screen_draw_uses_cell_background_and_foreground_palette():
    cls = next(n for n in ast.walk(TREE) if isinstance(n, ast.ClassDef) and n.name == 'C64TextScreenCanvas')
    paint = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == 'paintEvent')
    fragment = ast.get_source_segment(SOURCE, paint)
    assert 'self._backgrounds[offset]' in fragment
    assert 'self._colors[offset]' in fragment
    editor = next(n for n in ast.walk(TREE) if isinstance(n, ast.ClassDef) and n.name == 'C64TextScreenEditorDialog')
    fragment = ast.get_source_segment(SOURCE, editor)
    assert 'self.canvas.backgrounds()' in fragment
    assert 'include_background=True' in fragment


def test_theme_helper_preserves_existing_groupbox_stylesheet_and_toggles():
    node = next(n for n in TREE.body if isinstance(n, ast.FunctionDef) and n.name == 'apply_c64_tool_groupbox_theme')
    ns = {'QWidget': object, 'QGroupBox': object}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[])), '<groupbox_theme>', 'exec'), ns)

    class Group:
        def __init__(self):
            self._properties = {}
            self.style = 'QGroupBox { border: 1px solid #444444; }'
        def property(self, key): return self._properties.get(key)
        def setProperty(self, key, value): self._properties[key] = value
        def styleSheet(self): return self.style
        def setStyleSheet(self, value): self.style = value

    class Widget:
        def __init__(self, groups): self.groups = groups
        def findChildren(self, cls): return self.groups

    group = Group()
    widget = Widget([group])
    base = group.styleSheet()
    ns['apply_c64_tool_groupbox_theme'](widget, True)
    assert '#ffffff' in group.styleSheet()
    assert '#444444' in group.styleSheet()
    ns['apply_c64_tool_groupbox_theme'](widget, False)
    assert group.styleSheet() == base
    ns['apply_c64_tool_groupbox_theme'](widget, True)
    assert group.styleSheet().count('QGroupBox::title') == 1
