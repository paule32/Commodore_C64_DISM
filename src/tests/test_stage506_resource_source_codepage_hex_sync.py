# -*- coding: utf-8 -*-
"""Stage 506: direct #pragma changes update hex AND the properties combo.

These GUI-method tests deliberately use small Qt stubs because PyQt5 is not
installed in the CI environment. They exercise the real widget method source.
"""
import ast
import textwrap
from pathlib import Path

import pytest

import test_stage505_resource_codepage_live_refresh as prev


NAMES = ("_source_changed", "_resource_tab_changed", "_sync_codepage_combo", "_refresh_source_preview")
SLOTS = dict(prev.SLOTS)
SLOTS["Path"] = Path
for name in NAMES:
    exec(prev.method(name), SLOTS)


class Timer:
    def __init__(self): self.running = False
    def start(self): self.running = True
    def stop(self): self.running = False


class Tree(prev.DummyTree):
    def currentItem(self): return self.child


class Gui(prev.Gui):
    _source_changed = SLOTS['_source_changed']
    _resource_tab_changed = SLOTS['_resource_tab_changed']
    _sync_codepage_combo = SLOTS['_sync_codepage_combo']
    _refresh_source_preview = SLOTS['_refresh_source_preview']

    def __init__(self, path):
        super().__init__(path)
        self.resource_tree = Tree()
        self._loading = False
        self._preview_source_text = self.text
        self._source_preview_timer = Timer()
        self.properties.combo.current = self.properties.combo.findData(self.entries[0].codepage)

    def set_source(self, text):
        self.text = text
        self._source_changed()

    def _populate_tree(self, selected_index=None):
        self._update_resource_hex_and_size(selected_index or 0)
        self._sync_codepage_combo(selected_index or 0)


@pytest.mark.parametrize('initial,next_page,last_page', [
    (1200, 65001, 20127),
    (65001, 1200, 20127),
    (20127, 65001, 1200),
])
def test_direct_pragma_edit_resyncs_bytes_hex_and_combo(tmp_path, initial, next_page, last_page):
    path = tmp_path / 'example.rc'
    original = f'#pragma code_page({initial})\n101 RCDATA\nBEGIN\n  "Hello"\nEND\n'
    path.write_text(original, encoding='utf-8')
    widget = Gui(path)

    for page in (next_page, last_page):
        widget.set_source(widget.text.replace(f'#pragma code_page({widget.entries[0].codepage})',
                                                  f'#pragma code_page({page})'))
        assert widget._dirty
        assert widget._source_preview_timer.running
        widget._resource_tab_changed(2)  # user opens the Hex tab
        assert not widget._source_preview_timer.running
        assert widget.entries[0].codepage == page
        assert widget.entries[0].data == prev.SCOPE['_resource_encode_string']('Hello', page)
        assert widget.hex_edit.value == prev.SCOPE['format_resource_hex'](
            widget.entries[0].data, page, resource_type=widget.entries[0].type_id)
        assert widget.properties.combo.pages[widget.properties.combo.current] == page
        assert widget.properties.size.value == str(len(widget.entries[0].data))
        assert widget.resource_tree.child.texts[2] == str(len(widget.entries[0].data))
        assert widget._refresh_source_preview() is True  # no redundant changes

    assert path.read_text(encoding='utf-8') == original  # not saved automatically


def test_direct_pragma_change_updates_utf8_multibyte_text(tmp_path):
    path = tmp_path / 'german.rc'
    path.write_text('#pragma code_page(1200)\n123 RCDATA\nBEGIN\n "Grüße"\nEND\n', encoding='utf8')
    gui = Gui(path)
    gui.set_source(gui.text.replace('(1200)', '(65001)'))
    assert gui._refresh_source_preview()
    assert gui.entries[0].data == 'Grüße'.encode('utf8') + b'\0'
    assert 'Grüße' in gui.hex_edit.value
    assert 'C3 BC' in gui.hex_edit.value
    assert gui.properties.combo.current == 1


def test_invalid_ascii_codepage_keeps_last_valid_preview(tmp_path):
    path = tmp_path / 'german.rc'
    path.write_text('#pragma code_page(65001)\n123 RCDATA\nBEGIN\n "Grüße"\nEND\n', encoding='utf8')
    gui = Gui(path)
    old_bytes = gui.entries[0].data
    old_hex = gui.hex_edit.value
    gui.set_source(gui.text.replace('(65001)', '(20127)'))
    gui._resource_tab_changed(1)
    assert gui.entries[0].data == old_bytes
    assert gui.entries[0].codepage == 65001
    assert gui.properties.combo.current == 1
    assert gui.hex_edit.value == old_hex
    assert 'nicht aktualisiert' in gui.messages[-1]
    assert gui.text.startswith('#pragma code_page(20127)')  # user changes kept


def test_native_stringtable_keeps_required_utf16_bytes(tmp_path):
    path = tmp_path / 'text.rc'
    path.write_text('#pragma code_page(1200)\nSTRINGTABLE\nBEGIN\n 16 "Hallo"\nEND\n', encoding='utf8')
    gui = Gui(path)
    original_bytes = gui.entries[0].data
    gui.set_source(gui.text.replace('(1200)', '(65001)'))
    assert gui._refresh_source_preview()
    assert gui.entries[0].data == original_bytes
    assert gui.entries[0].codepage == 65001
    assert gui.properties.combo.current == 1
    assert 'Windows-UTF-16LE' in gui.hex_edit.value


def test_unsaved_rc_preview_works_without_file_path(tmp_path, monkeypatch):
    path = tmp_path / 'unsaved.rc'
    path.write_text('#pragma code_page(65001)\n1 RCDATA\nBEGIN\n"Test"\nEND\n', encoding='utf8')
    gui = Gui(path)
    gui.current_path = None
    monkeypatch.chdir(tmp_path)
    gui.set_source(gui.text.replace('(65001)', '(1200)'))
    assert gui._refresh_source_preview()
    assert gui.entries[0].data == b'T\0e\0s\0t\0\0\0'
    assert gui.properties.combo.current == 0
    assert not (tmp_path / 'untitled.rc').exists()
