# -*- coding: utf-8 -*-
"""Stage 505: Codepage switch must immediately update raw resource bytes AND hex viewer.

Headless tests drive exactly the methods called by the properties ComboBox.  They
model a populated tree and property table, so replacing data without refreshing
the UI (the Stage 504 regression) is detected.
"""
import os
import re
import struct
import sys
import ast
import textwrap
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Mapping, MutableMapping, Optional, Sequence, Iterable, Tuple, Union

import pytest

from test_stage504_resource_hex_codepage import SCOPE, SOURCE


def method(name):
    widget = WIDGET_AST
    node = next(n for n in widget.body if isinstance(n, ast.FunctionDef) and n.name == name)
    lines = SOURCE.splitlines(keepends=True)
    return textwrap.dedent(''.join(lines[node.lineno - 1:node.end_lineno]))


WIDGET_AST = next(n for n in ast.parse(SOURCE).body
                  if isinstance(n, ast.ClassDef) and n.name == "WindowsResourceEditorWidget")

METHOD_NAMES = (
    '_codepage_changed', '_update_resource_tree_in_place',
    '_update_resource_hex_and_size', '_reset_codepage_combo',
)
SLOTS = {'compile_rc': SCOPE['compile_rc'],
         'format_resource_hex': SCOPE['format_resource_hex'],
         'ResourceCompilerError': SCOPE['ResourceCompilerError']}
for name in METHOD_NAMES:
    exec(method(name), SLOTS)


class DummyItem:
    def __init__(self, idx):
        self.idx = idx
        self.texts = {}
    def data(self, col, role): return self.idx
    def setText(self, col, text): self.texts[col] = text

class DummyParent:
    def __init__(self, child): self._child = child
    def childCount(self): return 1
    def child(self, number): return self._child

class DummyTree:
    def __init__(self): self.child = DummyItem(0)
    def topLevelItemCount(self): return 1
    def topLevelItem(self, i): return DummyParent(self.child)

class DummyHex:
    def __init__(self): self.value = ''
    def setPlainText(self, text): self.value = text
    def clear(self): self.value = ''

class DummyCell:
    def __init__(self): self.value = ''
    def setText(self, text): self.value = text

class DummyCombo:
    def __init__(self):
        self.pages = [1200, 65001, 20127]
        self.current = 0
        self._blocked = False
    def findData(self, page): return self.pages.index(page)
    def blockSignals(self, flag):
        old = self._blocked
        self._blocked = flag
        return old
    def setCurrentIndex(self, idx): self.current = idx

class DummyProperties:
    def __init__(self): self.size = DummyCell(); self.combo = DummyCombo()
    def item(self, row, col): return self.size if (row, col) == (3, 1) else None
    def cellWidget(self, row, col): return self.combo if (row, col) == (8, 1) else None

class DummyQt:
    UserRole = 0x100

SLOTS['Qt'] = DummyQt
# Re-exec where global Qt is now available.


class Gui:
    _codepage_changed = SLOTS['_codepage_changed']
    _update_resource_tree_in_place = SLOTS['_update_resource_tree_in_place']
    _update_resource_hex_and_size = SLOTS['_update_resource_hex_and_size']
    _reset_codepage_combo = SLOTS['_reset_codepage_combo']

    def __init__(self, path):
        self.current_path = path
        self.text = path.read_text(encoding='utf8')
        self.source_edit = self
        self.entries = SCOPE['compile_rc'](path).entries
        self._dirty = False
        self.hex_edit = DummyHex()
        self.properties = DummyProperties()
        self.resource_tree = DummyTree()
        self.messages = []
        self._update_resource_hex_and_size(0)
    def toPlainText(self): return self.text
    def _write_rc_codepage(self, page):
        self.text = re.sub(r'#pragma code_page\(\d+\)', f'#pragma code_page({page})', self.text)
        self._dirty = True
    def _set_source_text_preserve_cursor(self, text):
        self.text = text
        self._dirty = True
    def _set_status(self, message): self.messages.append(message)


@pytest.mark.parametrize('start,next_page,final_page,value', [
    (1200,65001,20127,'Hello'),
    (1200,20127,65001,'Hello'),
    (65001,1200,20127,'Hello'),
])
def test_combo_transcodes_raw_bytes_repaints_hex_without_tree_recreate(tmp_path, start, next_page, final_page, value):
    p = tmp_path / 'test.rc'
    original = f'#pragma code_page({start})\n100 RCDATA\nBEGIN\n  "{value}"\nEND\n'
    p.write_text(original, encoding='utf8')
    gui = Gui(p)
    old_hex = gui.hex_edit.value
    prev_tree_item = gui.resource_tree.child
    prev_combo = gui.properties.combo

    for page in [next_page, final_page]:
        gui._codepage_changed(0, page)
        expected = SCOPE['_resource_encode_string'](value, page)
        assert gui.entries[0].data == expected
        assert gui.entries[0].codepage == page
        assert gui.hex_edit.value == SCOPE['format_resource_hex'](expected, page, resource_type=gui.entries[0].type_id)
        assert f'Text ({"Unicode" if page == 1200 else "UTF-8" if page == 65001 else "ASCII"})' in gui.hex_edit.value
        assert gui.properties.size.value == str(len(expected))
        assert gui.resource_tree.child.texts[2] == str(len(expected))
        assert gui.resource_tree.child is prev_tree_item
        assert gui.properties.combo is prev_combo
    assert gui.hex_edit.value != old_hex
    assert gui._dirty
    assert p.read_text(encoding='utf8') == original


def test_ascii_failure_keeps_old_bytes_view_and_codepage_selection(tmp_path):
    p = tmp_path / 'source.rc'
    original = '#pragma code_page(65001)\n100 RCDATA\nBEGIN\n "Grüße"\nEND\n'
    p.write_text(original, encoding='utf8')
    gui = Gui(p)
    old_data = gui.entries[0].data
    old_hex = gui.hex_edit.value
    gui.properties.combo.setCurrentIndex(2)
    gui._codepage_changed(0, 20127)
    assert gui.text == original
    assert gui.entries[0].data == old_data
    assert gui.hex_edit.value == old_hex
    assert gui.properties.combo.current == 1   # UTF-8 restored
    assert gui.messages[-1].startswith('Codepage nicht geändert:')
    assert gui._dirty is False


def test_utf8_and_utf16_non_ascii_live_bytes_and_hex(tmp_path):
    p = tmp_path / 'source.rc'
    p.write_text('#pragma code_page(1200)\n100 RCDATA\nBEGIN\n "Grüße"\nEND\n', encoding='utf8')
    gui = Gui(p)
    assert gui.entries[0].data == 'Grüße'.encode('utf-16le')+b'\0\0'
    gui._codepage_changed(0, 65001)
    assert gui.entries[0].data == 'Grüße'.encode('utf8')+b'\0'
    assert 'Grüße' in gui.hex_edit.value
    assert 'C3 BC' in gui.hex_edit.value
    gui._codepage_changed(0, 1200)
    assert 'Grüße' in gui.hex_edit.value
    assert 'FC 00' in gui.hex_edit.value


def test_predefined_windows_format_remains_structurally_valid(tmp_path):
    p = tmp_path / 'source.rc'
    p.write_text('#pragma code_page(1200)\nSTRINGTABLE\nBEGIN\n 16 "Grüße"\nEND\n', encoding='utf8')
    gui = Gui(p)
    original_data = gui.entries[0].data
    gui._codepage_changed(0, 65001)
    assert gui.entries[0].data == original_data
    assert gui.entries[0].codepage == 65001
    assert 'Windows-UTF-16LE' in gui.hex_edit.value
