# -*- coding: utf-8 -*-
"""Stage 515: no Windows-native UTF-16LE text in ASCII/UTF-8 export artifacts."""
from pathlib import Path
import struct
import pytest
from test_stage504_resource_hex_codepage import SCOPE
from test_stage512_resource_dll import _pe_headers, _leaf_values

RC = '''#pragma code_page(1200)
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
        MENUITEM "Beenden", 3012
    END
END
101 RCDATA
BEGIN
    "Hallo"
END
'''

@pytest.mark.parametrize('page,folder,nonwide', [(65001,'utf8','Drück mich'.encode('utf8')),
                                                 (20127,'ascii',b'Dr?ck mich')])
@pytest.mark.parametrize('machine,arch', [('x86','win32'),('x64','win64')])
def test_no_unicode_in_any_artifact(tmp_path,page,folder,nonwide,machine,arch):
    rc = tmp_path/'Sample.rc'; rc.write_text(RC,encoding='utf8')
    native = SCOPE['compile_rc'](rc).entries
    res,obj,dll=SCOPE['build_resource_dll_files'](rc,native,machine=machine,codepage=page)
    assert all(p.parent == tmp_path/arch/folder for p in (res,obj,dll))
    items = SCOPE['read_res'](res)
    assert {e.type_id for e in items} == {0xF004,0xF006,10}
    assert all(isinstance(e.name_id,int) for e in items)
    for file in (res,obj,dll):
        blob = file.read_bytes()
        assert nonwide in blob
        assert 'Drück mich'.encode('utf-16le') not in blob
        assert 'Deutsch Form'.encode('utf-16le') not in blob
        assert 'Öffnen'.encode('utf-16le') not in blob
        assert b'D\x00a\x00t\x00e\x00i\x00' not in blob
    pe = _pe_headers(dll.read_bytes())
    assert pe['machine'] == (0x14c if machine == 'x86' else 0x8664)
    leaves=_leaf_values(pe['data'])
    assert len(leaves)==3
    assert all(leaf[3] == page for leaf in leaves)
    assert all(all(isinstance(v,int) for v in leaf[0]) for leaf in leaves)


def test_unicode_build_still_windows_native(tmp_path):
    rc=tmp_path/'Sample.rc';rc.write_text(RC,encoding='utf8')
    paths=SCOPE['build_resource_dll_files'](rc,SCOPE['compile_rc'](rc).entries,codepage=1200)
    items=SCOPE['read_res'](paths[0])
    assert {e.type_id for e in items}=={4,6,10}
    assert 'Drück mich'.encode('utf-16le') in paths[2].read_bytes()


def test_nonunicode_dialog_version_preserve_rc_text_but_not_native_wide_payload(tmp_path):
    src='''#pragma code_page(1200)
100 DIALOG 0, 0, 120, 60
CAPTION "Grüße"
BEGIN
    LTEXT "Drück mich", 110, 4, 4, 50, 10
END
'''
    rc=tmp_path/'Dialog.rc';rc.write_text(src,encoding='utf8')
    native=SCOPE['compile_rc'](rc).entries
    assert native[0].type_id==5
    for page in (65001,20127):
        res,obj,dll=SCOPE['build_resource_dll_files'](rc,native,codepage=page)
        items=SCOPE['read_res'](res)
        assert [e.type_id for e in items]==[0xF005]
        assert items[0].data[:8]==b'D64SRC01'
        assert struct.unpack_from('<I',items[0].data,8)[0]==page
        for f in (res,obj,dll):
            assert 'Grüße'.encode('utf-16le') not in f.read_bytes()
        assert (b'Gr\xc3\xbc\xc3\x9fe' if page == 65001 else b'Gr??e') in dll.read_bytes()


def test_explicit_wstring_must_not_create_nonunicode_output(tmp_path):
    rc=tmp_path/'Wide.rc'
    rc.write_text('#pragma code_page(1200)\n1 RCDATA\nBEGIN\n L"Hello"\nEND\n',encoding='utf8')
    with pytest.raises(SCOPE['ResourceCompilerError'],match='Unicode-Literale'):
        SCOPE['build_resource_dll_files'](rc,SCOPE['compile_rc'](rc).entries,codepage=65001)
    assert not (tmp_path/'win32').exists()


def test_raw_utf16_payload_is_refused_before_files_are_created(tmp_path):
    rc=tmp_path/'Raw.rc'
    (tmp_path/'wide.bin').write_bytes('Hallo'.encode('utf-16le') + b'\x00\x00')
    rc.write_text('#pragma code_page(65001)\n101 RCDATA "wide.bin"\n',encoding='utf8')
    compiled=SCOPE['compile_rc'](rc).entries
    with pytest.raises(SCOPE['ResourceCompilerError'],match='UTF-16-/UTF-32-Text'):
        SCOPE['build_resource_dll_files'](rc,compiled,codepage=65001)
    assert not (tmp_path/'win32').exists()


def test_string_resource_identifier_must_be_numeric(tmp_path):
    rc=tmp_path/'Named.rc'
    rc.write_text('#pragma code_page(65001)\nMY_DATA RCDATA\nBEGIN\n "Hello"\nEND\n',encoding='utf8')
    entries=SCOPE['compile_rc'](rc).entries
    with pytest.raises(SCOPE['ResourceCompilerError'],match='numerische Ressourcen-IDs'):
        SCOPE['build_resource_dll_files'](rc,entries,codepage=65001)
    assert not (tmp_path/'win32').exists()


def test_raw_utf32_payload_is_refused_too(tmp_path):
    rc=tmp_path/'Raw32.rc'
    (tmp_path/'wide32.bin').write_bytes('Hallo'.encode('utf-32le'))
    rc.write_text('#pragma code_page(65001)\n102 RCDATA "wide32.bin"\n', encoding='utf8')
    with pytest.raises(SCOPE['ResourceCompilerError'], match='UTF-16-/UTF-32-Text'):
        SCOPE['build_resource_dll_files'](rc,SCOPE['compile_rc'](rc).entries,codepage=65001)
    assert not (tmp_path/'win32').exists()
