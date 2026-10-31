# -*- coding: utf-8 -*-
"""Stage 508: codepage combo changes the STRINGTABLE hex preview, not PE bytes.

Reproduces the user's 346-byte sample verbatim, particularly native 0x150.
Qt-independent GUI callback tests also verify live change/source-sync.
"""
import struct
from pathlib import Path

import pytest

from test_stage504_resource_hex_codepage import SCOPE
from test_stage505_resource_codepage_live_refresh import Gui
from test_stage506_resource_source_codepage_hex_sync import Gui as SourceGui


STRINGS = [
    '', 'Deutsch Form', 'Drück mich', 'Schließen', 'Name', 'Vorname',
    'Auswahl 1', 'Auswahl 2', 'Blau', 'Rot', 'Rot', 'Gelb', 'Grün',
    'Kreis', 'Quadrat',
    'Dies ist kein Fehler. Ich wette, das Sie den Button gedrückt haben.',
]


def original_sample():
    return b''.join(struct.pack('<H', len(s.encode('utf-16le')) // 2) +
                    s.encode('utf-16le') for s in STRINGS)


def rc_source(page):
    definitions = '\n'.join(f'  {ident} "{text}"'
                            for ident, text in enumerate(STRINGS) if ident > 0)
    return f'#pragma code_page({page})\nSTRINGTABLE\nBEGIN\n{definitions}\nEND\n'


def test_input_matches_original_346_byte_resource_and_last_offset():
    raw = original_sample()
    assert len(raw) == 346
    assert raw[0x140:0x150] == bytes.fromhex('64 00 72 00 FC 00 63 00 6B 00 74 00 20 00 68 00')
    assert raw[0x150:] == bytes.fromhex('61 00 62 00 65 00 6E 00 2E 00')


def test_native_unicode_view_remains_byte_exact():
    raw = original_sample()
    view = SCOPE['format_resource_hex'](raw, 1200, resource_type=SCOPE['RT_STRING'])
    assert '00000150  61 00 62 00 65 00 6E 00 | 2E 00' in view
    assert 'a.b.e.n...' in view
    assert view.splitlines()[-1].endswith('aben.')


@pytest.mark.parametrize('codepage,codepage_label', [(20127, 'ASCII'), (65001, 'UTF-8')])
def test_stringtable_virtual_hex_matches_exact_user_example(codepage, codepage_label):
    raw = original_sample()
    before = bytes(raw)
    view = SCOPE['format_resource_hex'](raw, codepage, resource_type=SCOPE['RT_STRING'])
    last = next(line for line in view.splitlines() if line.startswith('00000150'))
    assert last.startswith('00000150  61 62 65 6E 2E')
    assert last.endswith('aben.')
    assert '61 00 62 00' not in last
    assert f'Text ({codepage_label})' in view
    assert 'Offsets der originalen Windows-UTF-16LE-Ressource' in view
    assert raw == before  # Windows RES/COFF must be byte-exact
    if codepage == 20127:
        assert '00000140  64 72 3F 63 6B 74 20 68' in view
        assert 'nicht darstellbare Zeichen als ?' in view
    else:
        assert '00000140  64 72 C3 BC 63 6B 74 20 | 68' in view
        assert 'drückt h' in view


def test_real_rc_compiler_generates_same_binary_for_all_codepages(tmp_path):
    raw = original_sample()
    for page in (1200, 65001, 20127):
        p = tmp_path / f'test_{page}.rc'
        p.write_text(rc_source(page), encoding='utf8')
        entry = SCOPE['compile_rc'](p).entries[0]
        assert entry.type_id == SCOPE['RT_STRING']
        assert entry.data == raw
        assert entry.codepage == page
        view = SCOPE['format_resource_hex'](entry.data, page, resource_type=entry.type_id)
        assert ('61 00 62 00' if page == 1200 else '61 62 65 6E 2E') in view


def test_combo_live_repaints_view_without_resaving_native_windows_data(tmp_path):
    p = tmp_path / 'sample.rc'
    original = rc_source(1200)
    p.write_text(original, encoding='utf8')
    gui = Gui(p)
    entry_data = bytes(gui.entries[0].data)
    assert len(entry_data) == 346
    assert '00000150  61 00 62 00' in gui.hex_edit.value
    for page, marker in [(20127, '61 62 65 6E 2E'), (65001, '61 62 65 6E 2E'),
                         (1200, '61 00 62 00')]:
        gui.properties.combo.setCurrentIndex(gui.properties.combo.findData(page))
        gui._codepage_changed(0, page)
        assert marker in gui.hex_edit.value
        assert gui.entries[0].data == entry_data
        assert gui.entries[0].codepage == page
        assert gui.properties.size.value == '346'
    assert p.read_text(encoding='utf8') == original


def test_manual_rc_pragma_change_resynchronizes_combo_and_virtual_hex(tmp_path):
    p = tmp_path / 'sample.rc'
    p.write_text(rc_source(1200), encoding='utf8')
    gui = SourceGui(p)
    original_bytes = bytes(gui.entries[0].data)
    gui.set_source(gui.text.replace('(1200)', '(20127)'))
    gui._resource_tab_changed(2)
    assert gui.properties.combo.current == 2
    assert '00000150  61 62 65 6E 2E' in gui.hex_edit.value
    assert gui.entries[0].data == original_bytes
    gui.set_source(gui.text.replace('(20127)', '(65001)'))
    gui._resource_tab_changed(2)
    assert gui.properties.combo.current == 1
    assert '00000140  64 72 C3 BC 63 6B 74 20 | 68' in gui.hex_edit.value


def test_malformed_stringtable_falls_back_to_exact_native_bytes():
    bad = b'\x02\x00H\x00'
    view = SCOPE['format_resource_hex'](bad, 20127, resource_type=SCOPE['RT_STRING'])
    assert '02 00 48 00' in view
    assert 'Windows-UTF-16LE' in view
