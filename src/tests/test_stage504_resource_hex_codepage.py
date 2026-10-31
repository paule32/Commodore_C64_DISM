# -*- coding: utf-8 -*-
"""Stage 504: RES hex view honors chosen codec and RC raw strings use its bytes.

The pure compiler is extracted so these tests don't need PyQt5 installed.
"""
from __future__ import annotations

import ast
import os
import re
import struct
import sys
import textwrap
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional, Sequence, Tuple, Union

import pytest

SOURCE = Path(__file__).with_name("d64_dism.py").read_text(encoding="utf-8")


def _pure_scope():
    scope = {
        "os": os, "re": re, "struct": struct, "ast": ast, "sys": sys,
        "Path": Path, "dataclass": dataclass, "field": field,
        "Union": Union, "Optional": Optional,
        "MutableMapping": MutableMapping, "Mapping": Mapping,
        "Sequence": Sequence, "Iterable": Iterable, "Any": Any,
        "Dict": Dict, "List": List, "Tuple": Tuple,
    }
    begin = SOURCE.index("RT_CURSOR       = 1")
    end = SOURCE.index("\n# ---------------------------------------------------------------------------\n# Projektdateien", begin)
    exec(SOURCE[begin:end], scope)
    begin = SOURCE.index("class ResourceCompilerError(Exception):")
    end = SOURCE.index("def resource_dialog_stylesheet", begin)
    exec(SOURCE[begin:end], scope)
    for name, value in re.findall(r"^(IMAGE_(?:FILE_MACHINE_|REL_|SCN_)[A-Z0-9_]+)\s*=\s*(0x[0-9A-Fa-f]+|\d+)", SOURCE, re.M):
        scope[name] = int(value, 0)
    return scope


SCOPE = _pure_scope()


def _resource_data(tmp_path, page: int, text: str = "Grüße"):
    rc = tmp_path / "page.rc"
    rc.write_text(f'#pragma code_page({page})\n100 RCDATA\nBEGIN\n    "{text}"\nEND\n', encoding="utf8")
    result = SCOPE["compile_rc"](rc)
    assert len(result.entries) == 1
    entry = result.entries[0]
    assert entry.codepage == page
    return entry


@pytest.mark.parametrize("page, expected", [
    (20127, b"Hallo\x00"),
    (65001, b"Hallo\x00"),
    (1200, "Hallo".encode("utf-16le") + b"\0\0"),
])
def test_rc_compiler_writes_selected_byte_encoding(tmp_path, page, expected):
    assert _resource_data(tmp_path, page, "Hallo").data == expected


@pytest.mark.parametrize("page, expected", [
    (65001, "Grüße".encode("utf8") + b"\0"),
    (1200, "Grüße".encode("utf-16le") + b"\0\0"),
    (0, "Grüße".encode("cp1252") + b"\0"),
])
def test_nonascii_raw_string_byte_output(tmp_path, page, expected):
    assert _resource_data(tmp_path, page).data == expected


def test_ascii_nonrepresentable_fails_without_data_loss(tmp_path):
    with pytest.raises(SCOPE["ResourceCompilerError"], match="Codepage 20127"):
        _resource_data(tmp_path, 20127)


def test_explicit_wide_string_stays_wide_even_for_ascii(tmp_path):
    rc = tmp_path / "wide.rc"
    rc.write_text('#pragma code_page(20127)\n101 RCDATA\nBEGIN\n L"Grüße"\nEND\n', encoding='utf8')
    entry = SCOPE["compile_rc"](rc).entries[0]
    assert entry.data == "Grüße".encode("utf-16le") + b"\0\0"


@pytest.mark.parametrize("page", [1200, 65001, 20127])
def test_windows_stringtable_is_mandatory_utf16le(tmp_path, page):
    rc = tmp_path / "strings.rc"
    rc.write_text(f'#pragma code_page({page})\nSTRINGTABLE\nBEGIN\n  16 "Grüße"\nEND\n', encoding='utf8')
    entry = SCOPE["compile_rc"](rc).entries[0]
    assert "Grüße".encode('utf-16le') in entry.data
    assert entry.codepage == page


def test_preview_uses_unsaved_source_and_does_not_modify_file(tmp_path):
    rc = tmp_path / "preview.rc"
    saved = '#pragma code_page(1200)\n10 RCDATA\nBEGIN\n "Ä"\nEND\n'
    rc.write_text(saved, encoding='utf8')
    unsaved = saved.replace('1200', '65001')
    preview = SCOPE["compile_rc"](rc, source_text=unsaved)
    assert preview.entries[0].data == 'Ä'.encode('utf8') + b'\0'
    assert rc.read_text(encoding='utf8') == saved


def test_res_binary_preserves_exact_raw_data(tmp_path):
    entry = _resource_data(tmp_path, 65001)
    blob = SCOPE["write_res"]([entry])
    assert SCOPE["read_res"](blob)[0].data == 'Grüße'.encode('utf8') + b'\0'


@pytest.mark.parametrize('page,text', [
    (20127, 'Hallo'),
    (65001, 'Grüße'),
    (1200, 'Grüße'),
])
def test_hex_column_decodes_using_selected_codepage(page, text):
    raw = SCOPE['_resource_encode_string'](text, page)
    hex_view = SCOPE['format_resource_hex'](raw, page)
    assert text in hex_view
    for byte in raw:
        assert f'{byte:02X}' in hex_view


def test_utf8_character_across_16_byte_boundary():
    raw = b'X' * 15 + '€'.encode('utf8') + b'\0'
    view = SCOPE['format_resource_hex'](raw, 65001)
    assert '€' in view
    assert '�' not in view
    assert '00000010' in view


def test_hex_ascii_invalid_bytes_not_falsely_decoded_as_latin1():
    view = SCOPE['format_resource_hex'](b'ABC\xff', 20127)
    assert 'ABC�' in view


def test_hex_utf16_shows_nul_dots_and_decoded_unicode():
    raw = 'Hallo'.encode('utf-16le') + b'\0\0'
    view = SCOPE['format_resource_hex'](raw, 1200)
    assert 'Hallo.' in view
    assert 'H.a.l.l.o.' in view  # each 00 byte is visible as a dot


def test_codepage_change_recompiles_current_rc_memory_and_preserves_dirty(tmp_path):
    rc = tmp_path / 'changed.rc'
    rc.write_text('#pragma code_page(1200)\n10 RCDATA\nBEGIN\n  "Hü"\nEND\n', encoding='utf8')
    gui_class = SOURCE[SOURCE.index('class WindowsResourceEditorWidget(QWidget):'):]
    start = gui_class.index('    def _codepage_changed(')
    end = gui_class.index('\n\ndef install_doxygen_messagebox_theme(', start)
    definition = textwrap.dedent(gui_class[start:end])
    ns = {'compile_rc': SCOPE['compile_rc'], 'format_resource_hex': SCOPE['format_resource_hex']}
    exec(definition, ns)

    class Gui:
        _codepage_changed = ns['_codepage_changed']
        def __init__(self):
            self.current_path = rc
            self.source_edit = self
            self.text = rc.read_text(encoding='utf8')
            self.entries = SCOPE['compile_rc'](rc).entries
            self._dirty = False
            self.selected_index = None
            self.messages = []
        def _write_rc_codepage(self, page):
            self.text = self.text.replace('#pragma code_page(1200)', f'#pragma code_page({page})')
            self._dirty = True
        def toPlainText(self): return self.text
        def _populate_tree(self, selected_index=None): self.selected_index = selected_index
        def _set_status(self, message): self.messages.append(message)

    gui = Gui()
    gui._codepage_changed(0, 65001)
    assert gui.entries[0].data == 'Hü'.encode('utf8') + b'\0'
    assert gui.selected_index == 0 and gui._dirty
    assert rc.read_text(encoding='utf8').startswith('#pragma code_page(1200)')


@pytest.mark.parametrize("machine", ["x86", "x64"])
def test_coff_output_contains_utf8_payload_and_codepage(tmp_path, machine):
    entry = _resource_data(tmp_path, 65001)
    blob = SCOPE["write_resource_coff"]([entry], machine=machine)
    assert entry.data in blob  # .rsrc$02 contains untranscoded UTF-8 bytes
    directory, data, reloc = SCOPE["_build_resource_sections"]([entry])
    assert data.startswith(entry.data)
    assert reloc and struct.unpack_from("<I", directory, reloc[0] + 8)[0] == 65001


def test_native_windows_string_table_does_not_misinterpret_selected_utf8():
    string_bytes = struct.pack("<H", 5) + "Grüße".encode("utf-16le")
    text = SCOPE["format_resource_hex"](
        string_bytes, 65001, resource_type=SCOPE["RT_STRING"]
    )
    assert "Grüße" in text
    assert "Windows-UTF-16LE" in text and "UTF-8" in text
