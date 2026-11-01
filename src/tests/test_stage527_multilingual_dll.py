# -*- coding: utf-8 -*-
"""Stage 527: RC language variants survive RES/COFF and PE32/PE32+ DLL builds."""
from __future__ import annotations

import ast
from pathlib import Path
import struct
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import windows_resource as wr
from resource_multilang import edit_resource_language, language_statement

SOURCE = '''#pragma code_page(1200)
LANGUAGE 0x0007, 0x01
STRINGTABLE
BEGIN
  100 "Hallo"
END
100 MENU
BEGIN
 POPUP "Datei"
 BEGIN
  MENUITEM "Öffnen", 3011
 END
END
101 RCDATA
BEGIN
 "Test"
END
'''


def compile_source(path, source):
    return wr.compile_rc(path, source_text=source).entries


def _native_dll_writer():
    # The IDE's DLL writer is pure Python but lives in the large GUI module.
    # Extract it without importing PyQt or starting the application.
    module = ast.parse((ROOT / 'd64_dism.py').read_text(encoding='utf-8'))
    node = next(x for x in module.body
                if isinstance(x, ast.FunctionDef) and x.name == 'write_resource_dll')
    scope = vars(wr).copy()
    exec(compile(ast.fix_missing_locations(ast.Module(
        body=[node], type_ignores=[])), '<resource-dll-writer>', 'exec'), scope)
    return scope['write_resource_dll']


def _resource_paths(blob):
    pe = struct.unpack_from('<I', blob, 0x3c)[0]
    assert blob[pe:pe + 4] == b'PE\0\0'
    opt_size = struct.unpack_from('<H', blob, pe + 20)[0]
    section = pe + 24 + opt_size
    offset = struct.unpack_from('<I', blob, section + 20)[0]
    paths = []

    def walk(directory, path):
        named, ids = struct.unpack_from('<HH', blob, offset + directory + 12)
        for i in range(named + ids):
            name, entry = struct.unpack_from('<II', blob, offset + directory + 16 + 8*i)
            if entry & 0x80000000:
                walk(entry & 0x7fffffff, path + [name])
            else:
                paths.append(path + [name])
    walk(0, [])
    return paths


def test_language_statements():
    assert language_statement(0x0409) == 'LANGUAGE 0x0009, 0x01'
    assert language_statement(0x0407) == 'LANGUAGE 0x0007, 0x01'


def test_add_language_and_preserve_other_resources(tmp_path):
    path = tmp_path / 'demo.rc'
    path.write_text(SOURCE, encoding='utf-8')
    initial = compile_source(path, SOURCE)
    menu = next(e for e in initial if e.type_id == wr.RT_MENU)
    text, entries, selected = edit_resource_language(
        SOURCE, menu, 0x0409, lambda s: compile_source(path, s), duplicate=True)
    assert len(entries) == len(initial) + 1
    assert entries[selected].key() == (wr.RT_MENU, 100, 0x0409)
    assert {e.key() for e in initial} <= {e.key() for e in entries}
    # Replacing only the second language's text keeps the original German bytes.
    at = text.rfind('100 MENU')
    english = text[:at] + text[at:].replace('"Datei"', '"File"', 1)
    translated = compile_source(path, english)
    de = next(e.data for e in translated if e.key() == (wr.RT_MENU, 100, 0x0407))
    en = next(e.data for e in translated if e.key() == (wr.RT_MENU, 100, 0x0409))
    assert de != en
    assert de == menu.data


@pytest.mark.parametrize('arch,magic', [('x86', 0x10b), ('x64', 0x20b)])
def test_multilingual_real_pe_and_coff(tmp_path, arch, magic):
    path = tmp_path / 'demo.rc'
    path.write_text(SOURCE, encoding='utf-8')
    initial = compile_source(path, SOURCE)
    menu = next(e for e in initial if e.type_id == wr.RT_MENU)
    updated, entries, _ = edit_resource_language(
        SOURCE, menu, 0x0409, lambda s: compile_source(path, s), duplicate=True)
    dll = _native_dll_writer()(entries, machine=arch)
    assert struct.unpack_from('<H', dll, struct.unpack_from('<I', dll, 0x3c)[0] + 24)[0] == magic
    paths = _resource_paths(dll)
    assert [wr.RT_MENU, 100, 0x0407] in paths
    assert [wr.RT_MENU, 100, 0x0409] in paths
    assert wr.write_resource_coff(entries, machine=arch)
    decoded = wr.read_res(wr.write_res(entries))
    assert {e.key() for e in decoded} == {e.key() for e in entries}


def test_change_only_one_resource_language(tmp_path):
    path = tmp_path / 'demo.rc'
    path.write_text(SOURCE, encoding='utf-8')
    initial = compile_source(path, SOURCE)
    selected = next(e for e in initial if e.type_id == wr.RT_RCDATA)
    text, updated, index = edit_resource_language(
        SOURCE, selected, 0x040c, lambda s: compile_source(path, s))
    assert updated[index].language == 0x040c
    assert len(updated) == len(initial)
    assert all(e.language == 0x0407 for e in updated if e.type_id != wr.RT_RCDATA)


def test_duplicate_language_rejected(tmp_path):
    path = tmp_path / 'demo.rc'
    path.write_text(SOURCE, encoding='utf-8')
    menu = next(e for e in compile_source(path, SOURCE) if e.type_id == wr.RT_MENU)
    updated, _, _ = edit_resource_language(
        SOURCE, menu, 0x0409, lambda s: compile_source(path, s), duplicate=True)
    with pytest.raises(ValueError, match='existiert'):
        edit_resource_language(updated, menu, 0x0409,
                               lambda s: compile_source(path, s), duplicate=True)
