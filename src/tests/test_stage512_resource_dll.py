# -*- coding: utf-8 -*-
"""Stage 512: native PE32/PE32+ resource-only DLL builds + GUI wiring."""
from __future__ import annotations

import shutil
import struct
import subprocess
from pathlib import Path

import pytest
from test_stage504_resource_hex_codepage import SCOPE

SOURCE = Path(__file__).with_name('d64_dism.py').read_text('utf-8')
RC = '''#pragma code_page(1200)
LANGUAGE 0x0007, 0x01
STRINGTABLE
BEGIN
 1 "Hallo"
 16 "Grüße"
END
100 MENU
BEGIN
 POPUP "Datei"
 BEGIN
  MENUITEM "Öffnen", 3011
  MENUITEM "Beenden", 3012
 END
END
'''


def _entries(tmp_path):
    rc = tmp_path / 'Resource32.rc'
    rc.write_text(RC, encoding='utf8')
    return rc, SCOPE['compile_rc'](rc).entries


def _pe_headers(blob):
    assert blob[:2] == b'MZ'
    offset, = struct.unpack_from('<I', blob, 0x3C)
    assert blob[offset:offset+4] == b'PE\0\0'
    machine, sections, _, _, _, optional_size, characteristics = struct.unpack_from('<HHIIIHH', blob, offset+4)
    optional = offset+24
    magic, = struct.unpack_from('<H', blob, optional)
    pe64 = magic == 0x20B
    assert magic in (0x10B, 0x20B)
    directory = optional + (0x70 if pe64 else 0x60)
    rsrc_rva, rsrc_len = struct.unpack_from('<II', blob, directory+16)
    section = optional+optional_size
    name, vsize, section_rva, raw_len, raw_offset = struct.unpack_from('<8sIIII', blob, section)
    return {'machine':machine, 'sections':sections, 'characteristics':characteristics,
            'magic':magic, 'entrypoint':struct.unpack_from('<I', blob, optional+16)[0],
            'rsrc_rva':rsrc_rva, 'rsrc_len':rsrc_len, 'section_name':name.rstrip(b'\0'),
            'section_rva':section_rva, 'vsize':vsize, 'raw_len':raw_len, 'raw_offset':raw_offset,
            'data':blob[raw_offset:raw_offset+vsize]}


def _leaf_values(resource_data):
    """Walk three-level IMAGE_RESOURCE_DIRECTORY, read every RVA/data leaf."""
    result = []
    def follow(offset, path):
        _, _, _, _, nnames, nids = struct.unpack_from('<IIHHHH', resource_data, offset)
        for i in range(nnames + nids):
            name, value = struct.unpack_from('<II', resource_data, offset+16+i*8)
            name = name if not name & 0x80000000 else 'named'
            if value & 0x80000000:
                follow(value & 0x7fffffff, path + [name])
            else:
                data_rva, size, cp, _ = struct.unpack_from('<IIII', resource_data, value)
                result.append((path+[name], data_rva, size, cp))
    follow(0, [])
    return result


@pytest.mark.parametrize('machine,identifier,magic,folder', [
    ('x86',0x14c,0x10b,'win32'), ('x64',0x8664,0x20b,'win64'),
])
def test_native_resource_only_pe_dll_and_coff(tmp_path, machine, identifier, magic, folder):
    source, entries = _entries(tmp_path)
    paths = SCOPE['build_resource_dll_files'](source, entries, machine=machine)
    assert [p.name for p in paths] == ['Resource32.res','Resource32.o','Resource32.dll']
    assert all(p.parent.name == folder for p in paths)
    assert all(p.is_file() for p in paths)
    assert [(e.type_id,e.name_id,e.data) for e in SCOPE['read_res'](paths[0])] == [
        (e.type_id,e.name_id,e.data) for e in entries]
    assert struct.unpack_from('<H', paths[1].read_bytes())[0] == identifier
    blob = paths[2].read_bytes()
    pe = _pe_headers(blob)
    assert pe['machine'] == identifier
    assert pe['magic'] == magic
    assert pe['sections'] == 1
    assert pe['characteristics'] & 0x2000  # IMAGE_FILE_DLL
    assert pe['entrypoint'] == 0  # Resource-only DLL, no DllMain
    assert pe['section_name'] == b'.rsrc'
    assert pe['rsrc_rva'] == pe['section_rva'] == 0x1000
    assert pe['rsrc_len'] == pe['vsize']
    found = _leaf_values(pe['data'])
    assert len(found) == len(entries)
    for (path, rva, size, cp), original in zip(sorted(found),
                                              sorted(entries, key=lambda e:(e.type_id,e.name_id))):
        assert tuple(path) == (original.type_id,original.name_id,original.language)
        assert size == len(original.data)
        assert cp == original.codepage
        start = rva - pe['section_rva'] + pe['raw_offset']
        assert blob[start:start+size] == original.data
    if shutil.which('objdump'):
        completed = subprocess.run(['objdump','-x',str(paths[2])], capture_output=True, text=True, check=True)
        assert 'The .rsrc Resource Directory section:' in completed.stdout
        assert 'Entry: ID: 0x000064' in completed.stdout


def test_both_architecture_builds_coexist(tmp_path):
    source, entries = _entries(tmp_path)
    x86 = SCOPE['build_resource_dll_files'](source,entries,machine='win32')
    x64 = SCOPE['build_resource_dll_files'](source,entries,machine='win64')
    assert set(x86).isdisjoint(x64)
    assert [p.name for p in x86] == [p.name for p in x64]
    assert x86[2].read_bytes() != x64[2].read_bytes()
    assert source.read_text('utf8') == RC


def test_no_partial_files_for_invalid_input(tmp_path):
    source,_ = _entries(tmp_path)
    with pytest.raises(SCOPE['ResourceCompilerError']):
        SCOPE['build_resource_dll_files'](source,[],machine='x86')
    assert not (tmp_path/'win32').exists()
    with pytest.raises(SCOPE['ResourceCompilerError']):
        SCOPE['write_resource_dll']([],machine='x64')
    with pytest.raises(SCOPE['ResourceCompilerError']):
        SCOPE['build_resource_dll_files'](source,[],machine='arm64')


def test_gui_actions_exact_spacing_and_dark_light_titlebar():
    assert 'self.act_win32_dll = add_action("win32 DLL"' in SOURCE
    assert 'self.act_win64_dll = add_action("win64 DLL"' in SOURCE
    assert 'dll_button_layout.setSpacing(0)' in SOURCE
    assert SOURCE.count('setToolButtonStyle(Qt.ToolButtonTextOnly)') >= 3
    assert 'dll_button_layout.addSpacing(14)' in SOURCE
    assert 'self.refresh_toolbutton.setDefaultAction(self.act_refresh)' in SOURCE
    assert 'self.win32_dll_button.setDefaultAction(self.act_win32_dll)' in SOURCE
    assert 'self.win64_dll_button.setDefaultAction(self.act_win64_dll)' in SOURCE
    assert 'dock.setTitleBarWidget(DockTitleBar(dock))' in SOURCE
    assert 'dock.titleBarWidget().set_dark_mode(self.dark_mode_enabled)' in SOURCE
    assert 'icon_color = "#ffffff" if self._dark_mode else "#000000"' in SOURCE


def test_gui_build_compiles_current_rc_and_uses_selected_architecture():
    region = SOURCE[SOURCE.index('    def compile_to_resource_dll(self, machine: str) -> bool:'):
                    SOURCE.index('    def compile_to_coff(self, machine: str):')]
    assert 'self._compile_current_rc()' in region
    assert 'read_res(self.current_path)' in region
    assert 'build_resource_dll_files(self.current_path, self.entries, machine=machine)' in region
    assert 'self.set_target("pe64" if machine == "x64" else "pe32")' in region


def test_existing_resource_dll_output_matches_independent_lld_coff(tmp_path):
    lld = shutil.which('lld-link')
    if not lld:
        pytest.skip('LLD not installed')
    source, entries = _entries(tmp_path)
    for arch in ('x86','x64'):
        paths = SCOPE['build_resource_dll_files'](source,entries,machine=arch)
        independent = paths[2].with_name('reference_lld.dll')
        cmd = [lld,'/dll','/noentry',f'/machine:{arch}','/out:'+str(independent)]
        if arch == 'x86': cmd.append('/safeseh:no')
        cmd.append(str(paths[1]))
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        ours, reference = _pe_headers(paths[2].read_bytes()),_pe_headers(independent.read_bytes())
        assert _leaf_values(ours['data']) == _leaf_values(reference['data'])
