# -*- coding: utf-8 -*-
"""Stage 516: dual-format resource mapping, persistence and editor wiring."""
from __future__ import annotations
import ast
import configparser
import struct
from pathlib import Path
from types import SimpleNamespace
import pytest
from test_stage504_resource_hex_codepage import SCOPE
from test_stage512_resource_dll import _pe_headers, _leaf_values

SOURCE = Path(__file__).with_name('d64_dism.py').read_text('utf8')
TREE = ast.parse(SOURCE)
RC = '''#pragma code_page(1200)
STRINGTABLE
BEGIN
 1 "Deutsch Form"
 2 "Drück mich"
END
100 MENU
BEGIN
 POPUP "Datei"
 BEGIN
 MENUITEM "Öffnen", 3011
 END
END
'''

@pytest.mark.parametrize('machine,folder', [('x86','win32'),('x64','win64')])
@pytest.mark.parametrize('page,cpfolder', [(20127,'ascii'),(65001,'utf8')])
@pytest.mark.parametrize('with_copy', [False,True])
def test_output_with_and_without_windows_native_copies(tmp_path,machine,folder,page,cpfolder,with_copy):
    rc = tmp_path/'Test.rc';rc.write_text(RC,encoding='utf8')
    entries=SCOPE['compile_rc'](rc).entries
    res,obj,dll=SCOPE['build_resource_dll_files'](
        rc,entries,machine=machine,codepage=page,include_native_utf16=with_copy)
    assert all(p.parent==tmp_path/folder/cpfolder for p in (res,obj,dll))
    seen=SCOPE['read_res'](res)
    ids={e.type_id for e in seen}
    assert {0xF004,0xF006}.issubset(ids)
    if with_copy:
        assert ids=={0xF004,0xF006,4,6}
        assert 'Drück mich'.encode('utf-16le') in dll.read_bytes()
        assert b'D\x00a\x00t\x00e\x00i\x00' in dll.read_bytes()
    else:
        assert ids=={0xF004,0xF006}
        assert 'Drück mich'.encode('utf-16le') not in dll.read_bytes()
        assert b'D\x00a\x00t\x00e\x00i\x00' not in dll.read_bytes()
    for artifact in (res,obj,dll):
        data=artifact.read_bytes()
        assert ('Drück mich'.encode('utf-8') if page==65001 else b'Dr?ck mich') in data
    pe=_pe_headers(dll.read_bytes())
    assert pe['machine']==(0x14c if machine=='x86' else 0x8664)
    assert len(_leaf_values(pe['data']))==len(seen)

@pytest.mark.parametrize('include', [False,True])
def test_unicode_remains_windows_native_regardless_of_copy_flag(tmp_path,include):
    rc=tmp_path/'Test.rc';rc.write_text(RC,encoding='utf8')
    entries=SCOPE['compile_rc'](rc).entries
    res,_,dll=SCOPE['build_resource_dll_files'](
        rc,entries,codepage=1200,include_native_utf16=include)
    assert {e.type_id for e in SCOPE['read_res'](res)}=={4,6}
    assert 'Drück mich'.encode('utf-16le') in dll.read_bytes()


def _method(name):
    candidates=[n for n in ast.walk(TREE) if isinstance(n,ast.FunctionDef) and n.name==name]
    assert len(candidates)==1,(name,len(candidates))
    return candidates[0]


def _execute(node,ctx):
    node=ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[]))
    exec(compile(node,'d64_dism.py','exec'),ctx)


def test_project_ini_environment_mapping_round_trip_from_source():
    cfg={
        'resource_ascii_copy_key':'_ascii',
        'resource_utf8_copy_key':'_utf8',
        'environment_section':'Settings.Windows.32Bit.Environment',
        'title':'32-Bit',
        'console_dll_directory_key':'_dll',
        'console_dll_pack_key':'_pack',
        'console_const_pool_key':'_const',
        'workstation_mode_key':'_work',
        'debug_theme_normal_key':'_normal',
        'debug_theme_workstation_key':'_workstation',
    }
    fmt=_method('format_project_ini')
    assignments=[n for n in ast.walk(fmt) if isinstance(n,ast.Assign)
                 and any('environment_section' in ast.unparse(t) and 'parser' in ast.unparse(t)
                         for t in n.targets)]
    assert len(assignments)==1
    parser=configparser.ConfigParser(interpolation=None)
    parser.optionxform=str
    context={
        'parser':parser,'_settings':cfg,'_workstation_mode':False,
        '_debug_theme_normal':'default','_debug_theme_workstation':'default',
        '_dll_directory':'','_project_bool_entry':lambda entries,k,default: entries.get(k,[{'value':'false'}])[0]['value']=='true',
        '_project_storage_path_mode':lambda *a,**kw:'', 'project_path':Path('dummy.pro'),
        'entries':{'_ascii':[{'value':'true'}], '_utf8':[{'value':'false'}]},
    }
    _execute(assignments[0],context)
    assert parser[cfg['environment_section']]['ResourceASCIINativeUTF16Copy']=='true'
    assert parser[cfg['environment_section']]['ResourceUTF8NativeUTF16Copy']=='false'
    parse=_method('parse_project_ini')
    copies=[n for n in ast.walk(parse) if isinstance(n,ast.For)
            and 'ResourceASCIINativeUTF16Copy' in ast.unparse(n)
            and '_ini_key' in ast.unparse(n.target)]
    assert len(copies)==1
    restore={'parser':parser, '_environment_section':cfg['environment_section'],
             '_settings':cfg,'entries':{},'_parse_project_bool':lambda v,d:v.casefold()=='true'}
    _execute(copies[0],restore)
    assert restore['entries']['_ascii']==[{'value':'true'}]
    assert restore['entries']['_utf8']==[{'value':'false'}]
    del parser[cfg['environment_section']]['ResourceASCIINativeUTF16Copy']
    restore['entries']={}
    _execute(copies[0],restore)
    assert restore['entries']['_ascii']==[{'value':'false'}] # backward-compatible defaults


def test_project_setter_marks_and_saves_changes():
    ns={}
    _execute(_method('set_project_windows_resource_mapping'),ns)
    calls=[]
    class Host:
        _project_windows_target_key=lambda self,key:key
        project_windows_resource_mapping={'pe32':{'ascii':False,'utf8':False},
                                          'pe64':{'ascii':False,'utf8':False}}
        project_settings_panel=None
        current_project_path=Path('example.pro')
        set_project_modified=lambda self,value:calls.append(('modified',value))
        save_project=lambda self:calls.append(('save',))
    host=Host()
    ns['set_project_windows_resource_mapping'](host,'pe32','ascii',True)
    assert host.project_windows_resource_mapping['pe32']=={'ascii':True,'utf8':False}
    assert host.project_windows_resource_mapping['pe64']=={'ascii':False,'utf8':False}
    assert calls==[('modified',True),('save',)]
    ns['set_project_windows_resource_mapping'](host,'pe32','ascii',True)
    assert len(calls)==2 # no rewrite when value unchanged
    ns['set_project_windows_resource_mapping'](host,'pe64','utf8',True,mark_modified=False)
    assert host.project_windows_resource_mapping['pe64']['utf8'] is True
    assert len(calls)==2


def test_project_settings_page_and_editor_are_connected():
    assert '"environment.resources"' in SOURCE
    assert 'QGroupBox("Mapping:"' in SOURCE
    for caption in ('ASCII, without UTF - 16 LE Copy','ASCII with UTF - 16 LE Copy',
                    'UTF - 8, without UTF - 16 LE Copy','UTF - 8, with UTF - 16 LE Copy',
                    'UTF-16 LE Windows Standard'):
        assert caption in SOURCE
    assert 'self.project_windows_resource_mapping.get(target, {})' in SOURCE
    assert 'editor.resource_mapping_provider = lambda target:' in SOURCE
    assert 'self._resource_with_native_copy(machine, effective_page)' in SOURCE or 'self, "_resource_with_native_copy"' in SOURCE
    assert '_resource_dll_codepage_entries(' in SOURCE.split('def compile_to_res(self):',1)[1]
    assert '_resource_dll_codepage_entries(' in SOURCE.split('def compile_to_coff(self, machine: str):',1)[1]


@pytest.mark.parametrize('with_copy', [False,True])
def test_resource_editor_res_and_coff_write_use_active_project_mapping(tmp_path,with_copy):
    scope = {
        'ResourceCompilerError': SCOPE['ResourceCompilerError'],
        '_resource_dll_codepage_entries': SCOPE['_resource_dll_codepage_entries'],
        'save_res': SCOPE['save_res'],
        'save_resource_coff': SCOPE['save_resource_coff'],
    }
    for name in ('_resource_with_native_copy','compile_to_res','compile_to_coff'):
        _execute(_method(name),scope)
    rc = tmp_path/'Resource.rc';rc.write_text(RC,encoding='utf8')
    class Editor:
        current_path=rc
        current_target='pe32'
        resource_mapping_provider=staticmethod(lambda target: {
            'ascii':False,
            'utf8':with_copy if target == 'pe64' else False,
        })
        _resource_with_native_copy=scope['_resource_with_native_copy']
        _selected_dll_codepage=lambda self:65001
        _critical=lambda self,*args: (_ for _ in ()).throw(AssertionError(args))
        _set_status=lambda self,*args:None
        def _file_dialog(self,*args,**kwargs):
            if args[0]=='RES schreiben':return tmp_path/'Manual.res'
            return tmp_path/'Manual.o'
        def _compile_current_rc(self):
            self.entries=SCOPE['compile_rc'](rc).entries
    editor=Editor()
    scope['compile_to_res'](editor)
    res_entries=SCOPE['read_res'](tmp_path/'Manual.res')
    assert {e.type_id for e in res_entries}=={0xF004,0xF006}
    scope['compile_to_coff'](editor,'x64')
    blob=(tmp_path/'Manual.o').read_bytes()
    # A plain COFF .o contains the Windows UTF-16LE payload only with mapping enabled.
    assert ('Drück mich'.encode('utf-16le') in blob) == with_copy
    assert 'Drück mich'.encode('utf-8') in blob
