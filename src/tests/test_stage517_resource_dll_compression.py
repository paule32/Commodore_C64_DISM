# -*- coding: utf-8 -*-
"""Stage 517: two resource-DLL compression strategies, compatibility and persistence."""
import ast
import configparser
import os
import struct
from pathlib import Path
from types import SimpleNamespace
import pytest

from test_stage504_resource_hex_codepage import SCOPE
from test_stage512_resource_dll import _pe_headers, _leaf_values
from test_stage516_resource_mapping import _method, _execute, SOURCE

RC = '''#pragma code_page(1200)
STRINGTABLE
BEGIN
 1 "Drück mich"
END
100 MENU
BEGIN
 POPUP "Datei"
 BEGIN
 MENUITEM "Öffnen", 3011
 END
END
200 RCDATA
BEGIN
 "'''+ ('ABCD'*130) + '''"
END
'''

@pytest.mark.parametrize('arch', ['x86', 'x64'])
@pytest.mark.parametrize('page', [20127, 65001, 1200])
def test_custom_keeps_native_windows_resources_and_packs_rcdata(tmp_path, arch, page):
    src=tmp_path/'Resources.rc';src.write_text(RC, encoding='utf8')
    base=SCOPE['compile_rc'](src).entries
    raw_res,raw_o,raw_dll=SCOPE['build_resource_dll_files'](
        src,base,machine=arch,codepage=page,include_native_utf16=True,
        compress_enabled=False)
    plain_bytes=raw_dll.read_bytes(); plain_o=raw_o.read_bytes()
    _,_,compressed=SCOPE['build_resource_dll_files'](
        src,base,machine=arch,codepage=page,include_native_utf16=True,
        compress_enabled=True,compress_mode='custom')
    packed_bytes=compressed.read_bytes()
    assert len(packed_bytes) < len(plain_bytes)
    assert b'D64PK001' in packed_bytes
    assert b'D64PK001' not in raw_res.read_bytes()
    assert raw_o.read_bytes()==plain_o # .o stays linkable
    entries=SCOPE['pack_resource_dll_entries'](
        SCOPE['_resource_dll_codepage_entries'](src,base,page,include_native_utf16=True)[0])
    p=[e for e in entries if e.type_id==0xF117]
    assert p
    for rec in p:
        t,n,language,cp,data=SCOPE['unpack_resource_dll_record'](rec.data)
        matches=[e for e in SCOPE['_resource_dll_codepage_entries'](
            src,base,page,include_native_utf16=True)[0]
            if e.type_id==t and e.name_id==n and e.language==language]
        assert matches and data==matches[0].data
        assert cp==page
    pe=_pe_headers(packed_bytes)
    assert pe['machine']==(0x14c if arch=='x86' else 0x8664)
    assert len(_leaf_values(pe['data']))==len(entries)
    assert {e.type_id for e in entries}.issuperset({4,6,0xF117})


def test_custom_small_payload_is_left_untouched():
    Entry=SCOPE['ResourceEntry']
    e=Entry(10, 1, b'no useful savings', 0x409, codepage=65001)
    assert SCOPE['pack_resource_dll_entries']([e])==[e]


def test_custom_rejects_tampering():
    Entry=SCOPE['ResourceEntry']
    e=Entry(10,7,b'a'*1200,0x409,codepage=65001)
    data=SCOPE['pack_resource_dll_entries']([e])[0].data
    assert SCOPE['unpack_resource_dll_record'](data)[4]==e.data
    damaged=bytearray(data)
    damaged[8+6+4:8+6+4+4] = struct.pack('<I', 1201)
    with pytest.raises(SCOPE['ResourceCompilerError']):
        SCOPE['unpack_resource_dll_record'](damaged)
    damaged=bytearray(data)
    damaged[8+6+4+4:8+6+4+4+4] = b'\0'*4
    with pytest.raises(SCOPE['ResourceCompilerError']):
        SCOPE['unpack_resource_dll_record'](damaged)


def test_transparent_rejects_non_ntfs_platform_without_writing(tmp_path):
    if os.name=='nt': pytest.skip('Test für non-Windows')
    src=tmp_path/'Resources.rc';src.write_text(RC, encoding='utf8')
    entries=SCOPE['compile_rc'](src).entries
    with pytest.raises(SCOPE['ResourceCompilerError'], match='Windows/NTFS'):
        SCOPE['build_resource_dll_files'](src,entries,compress_enabled=True,compress_mode='transparent')
    assert not (tmp_path/'win32').exists()


def test_disabled_compression_matches_original_dll(tmp_path):
    src=tmp_path/'Resources.rc';src.write_text(RC, encoding='utf8')
    entries=SCOPE['compile_rc'](src).entries
    first=SCOPE['build_resource_dll_files'](src,entries,compress_enabled=False)
    dll=first[2].read_bytes()
    second=SCOPE['build_resource_dll_files'](src,entries,compress_enabled=False,compress_mode='custom')
    assert second[2].read_bytes()==dll


def test_project_state_setter_and_autosave():
    ns={};_execute(_method('set_project_windows_resource_compression'),ns)
    calls=[]
    class Host:
        _project_windows_target_key=lambda self,k:k
        project_windows_resource_compression={'pe32':{'enabled':False,'mode':'transparent'},
                                               'pe64':{'enabled':False,'mode':'transparent'}}
        project_settings_panel=None
        current_project_path=Path('test.pro')
        set_project_modified=lambda self,value:calls.append('dirty')
        save_project=lambda self:calls.append('save')
    h=Host(); fn=ns['set_project_windows_resource_compression']
    fn(h,'pe32',True,'custom')
    assert h.project_windows_resource_compression['pe32']=={'enabled':True,'mode':'custom'}
    assert h.project_windows_resource_compression['pe64']=={'enabled':False,'mode':'transparent'}
    assert calls==['dirty','save']
    fn(h,'pe32',True,'custom');assert calls==['dirty','save']
    fn(h,'pe64',True,'transparent',mark_modified=False);assert calls==['dirty','save']
    with pytest.raises(ValueError):fn(h,'pe32',True,'nonsense')


def test_project_ini_includes_both_options_with_defaults():
    assert '"ResourceDLLCompressEnabled"' in SOURCE
    assert '"ResourceDLLCompressMode"' in SOURCE
    assert '"resource_compress_enabled_key"' in SOURCE
    assert '"resource_compress_mode_key"' in SOURCE
    assert 'ResourceDLLCompressEnabled' in SOURCE
    assert 'self.set_project_windows_resource_compression(' in SOURCE
    assert '"enabled": False, "mode": "transparent"' in SOURCE
    for name in ['pe32','pe64']:
        assert f'__windows_{name}_resource_compress_enabled__' in SOURCE
        assert f'__windows_{name}_resource_compress_mode__' in SOURCE


def test_ui_page_signals_compiler_hook():
    assert 'QGroupBox("Compress DLL:"' in SOURCE
    assert 'QCheckBox("enable", compress_group)' in SOURCE
    assert 'QRadioButton("transparent", compress_group)' in SOURCE
    assert 'QRadioButton("custom", compress_group)' in SOURCE
    assert 'self.resource_compression_provider = None' in SOURCE
    assert 'editor.resource_compression_provider = lambda target:' in SOURCE
    assert 'compress_enabled=options["compress_enabled"]' in SOURCE
    assert 'compress_mode=options["compress_mode"]' in SOURCE
    assert 'self.project_windows_resource_compression.get(_target, {})' in SOURCE


def test_transparent_invokes_compact_lzx_and_handles_errors(tmp_path, monkeypatch):
    """Windows subprocess invocation is stubbed; actual NTFS requires Windows."""
    import subprocess
    dll=tmp_path/'Resource.dll';dll.write_bytes(b'MZ'+b'X'*1024)
    calls=[]
    def fake_run(command, **opts):
        calls.append((command,opts))
        return SimpleNamespace(returncode=0, stderr='', stdout='compressed')
    monkeypatch.setattr(subprocess, 'run', fake_run)
    ns={'os':SimpleNamespace(name='nt'),'Path':Path,
        'ResourceCompilerError':SCOPE['ResourceCompilerError']}
    _execute(_method('compress_resource_dll_transparent'), ns)
    ns['compress_resource_dll_transparent'](dll)
    assert calls[0][0][:5]==['compact.exe','/C','/EXE:LZX','/F','/I']
    assert calls[0][0][-1]==str(dll)
    monkeypatch.setattr(subprocess,'run',lambda *a,**kw:SimpleNamespace(
        returncode=1,stderr='not NTFS',stdout=''))
    with pytest.raises(SCOPE['ResourceCompilerError'],match='not NTFS'):
        ns['compress_resource_dll_transparent'](dll)


def test_custom_skips_existing_packed_id_collision():
    Entry=SCOPE['ResourceEntry']
    existing=Entry(0xF117,1,b'existing record',0x0409,codepage=65001)
    raw=Entry(10,100,b'a'*1000,0x0409,codepage=65001)
    output=SCOPE['pack_resource_dll_entries']([existing,raw])
    assert output[0]==existing
    assert output[1].type_id==0xF117 and output[1].name_id==2
