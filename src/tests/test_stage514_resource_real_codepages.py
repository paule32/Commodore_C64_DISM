# -*- coding: utf-8 -*-
"""Stage 515: codepage-specific output supersedes Stage 514 native mirrors."""
from pathlib import Path
import struct
import pytest
from test_stage504_resource_hex_codepage import SCOPE
from test_stage512_resource_dll import _pe_headers, _leaf_values

SAMPLE = '''#pragma code_page(1200)
LANGUAGE 0x0007, 0x01
STRINGTABLE
BEGIN
  1 "Deutsch Form"
  2 "Drück mich"
  3 "Schließen"
END
100 MENU
BEGIN
  POPUP "Datei"
  BEGIN
    MENUITEM "Öffnen", 3011
    MENUITEM SEPARATOR
    MENUITEM "Beenden", 3012
  END
END
1000 RCDATA
BEGIN
 "Test"
END
'''


def test_original_rc_codepage_is_overridden_for_actual_build(tmp_path):
    path = tmp_path / 'Resource32.rc'
    path.write_text(SAMPLE, encoding='utf8')
    original = SCOPE['compile_rc'](path).entries
    assert all(e.codepage == 1200 for e in original)
    for page, folder in ((20127, 'ascii'), (65001, 'utf8'), (1200, 'unicode')):
        for machine, arch in (('x86', 'win32'), ('x64', 'win64')):
            paths = SCOPE['build_resource_dll_files'](path, original, machine=machine, codepage=page)
            assert all(p.parent == tmp_path / arch / folder for p in paths)
            built = SCOPE['read_res'](paths[0])
            raw = next(e.data for e in built if e.type_id == 10)
            expected = 'Test'.encode({1200:'utf-16le',65001:'utf8',20127:'ascii'}[page])
            assert raw == expected + (b'\0\0' if page == 1200 else b'\0')
            data = paths[2].read_bytes()
            assert raw in data
            assert _pe_headers(data)['machine'] == (0x14c if machine == 'x86' else 0x8664)
            leaves = _leaf_values(_pe_headers(data)['data'])
            assert len(leaves) == len(built)
            assert all(leaf[3] == page for leaf in leaves)
            if page == 1200:
                assert any(e.type_id == 6 for e in built)
                assert any(e.type_id == 4 for e in built)
                assert not any(e.type_id in (0xF006, 0xF004) for e in built)
            else:
                assert not any(e.type_id in (6, 4) for e in built)
                assert all(isinstance(e.type_id, int) and isinstance(e.name_id, int) for e in built)
                mirror = next(e for e in built if e.type_id == 0xF006 and e.name_id == 1)
                assert mirror.data[:8] == b'D64STR01'
                assert struct.unpack_from('<I',mirror.data,8)[0] == page
                assert ('Drück mich'.encode('utf8') if page == 65001 else b'Dr?ck mich') in mirror.data
                menu_mirror = next(e for e in built if e.type_id == 0xF004)
                assert menu_mirror.data[:8] == b'D64MENU1'
                assert (b'\xc3\x96ffnen' if page == 65001 else b'?ffnen') in menu_mirror.data
    # No change to source file, and all six result directories coexist.
    assert path.read_text('utf8') == SAMPLE


def test_bad_ascii_raw_text_is_refused_without_partial_output(tmp_path):
    path = tmp_path / 'Resource32.rc'
    path.write_text('#pragma code_page(1200)\n101 RCDATA\nBEGIN\n "Grüße"\nEND\n', encoding='utf8')
    entries = SCOPE['compile_rc'](path).entries
    with pytest.raises(SCOPE['ResourceCompilerError'], match='Codepage 20127'):
        SCOPE['build_resource_dll_files'](path, entries, machine='x86', codepage=20127)
    assert not (tmp_path / 'win32').exists()


def test_native_res_cannot_be_reinterpreted_as_another_codepage(tmp_path):
    path = tmp_path / 'test.res'
    path.write_bytes(SCOPE['write_res']([SCOPE['ResourceEntry'](10, 123, b'Hello\0')]))
    entries = SCOPE['read_res'](path)
    with pytest.raises(SCOPE['ResourceCompilerError'], match=r'\.rc-Datei'):
        SCOPE['build_resource_dll_files'](path, entries, machine='x64', codepage=65001)
    assert not (tmp_path / 'win64').exists()


def test_unicode_in_nonunicode_stringtable_is_excluded_from_artifacts(tmp_path):
    path = tmp_path/'Resource32.rc'
    path.write_text(SAMPLE, encoding='utf8')
    entries = SCOPE['compile_rc'](path).entries
    for page in (65001,20127):
        res = SCOPE['build_resource_dll_files'](path,entries,machine='x86',codepage=page)[0]
        built = SCOPE['read_res'](res)
        assert not any(e.type_id == 6 for e in built)
        assert not any(e.type_id == 4 for e in built)
        for artifact in res, res.with_suffix('.o'), res.with_suffix('.dll'):
            assert 'Drück mich'.encode('utf-16le') not in artifact.read_bytes()
            assert 'Öffnen'.encode('utf-16le') not in artifact.read_bytes()
