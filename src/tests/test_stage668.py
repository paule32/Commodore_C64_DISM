# -*- coding: utf-8 -*-
"""Stage 668: Module owns EXE/DLL entry, Programme are assigned COFF objects."""
from pathlib import Path
from types import SimpleNamespace, ModuleType
from textwrap import dedent
import re
import sys
import struct

import pytest

from dbase_module_coff import (
    module_link_inputs, namespace_module_object, module_namespace,
    strip_program_entry_assembly, strip_dbase_library_entry_assembly,
)
from test_stage667 import body
from test_stage605_link import _load_pe_linker, OBJECTS
from d64dbase import compile_dbase_to_assembly
from pascal_console_dependencies import inspect_pe
from project_named_targets import normalize_names


@pytest.mark.parametrize('target,machine', [('pe32', 0x14c), ('pe64', 0x8664)])
def test_real_compiler_module_as_entry_programmes_as_objects(tmp_path, target, machine):
    native = _load_pe_linker()
    asm = native['assemble_pe64_object_source' if target == 'pe64' else 'assemble_pe32_object_source']
    write = native['write_coff64_object' if target == 'pe64' else 'write_coff32_object']
    link = native['link_coff64_inputs' if target == 'pe64' else 'link_coff32_inputs']
    src_mod = tmp_path/'App001.prg'
    src_programme1 = tmp_path/'functions.prg'
    src_programme2 = tmp_path/'utils.prg'
    src_mod.write_text('? "Application"\n', encoding='utf-8')
    src_programme1.write_text('? "Object one"\n', encoding='utf-8')
    src_programme2.write_text('? "Object two"\n', encoding='utf-8')
    module = asm(compile_dbase_to_assembly(src_mod.read_text(), target=target).assembly)
    assert '_start' in module.symbols
    mod_obj = src_mod.with_suffix('.o'); mod_obj.write_bytes(write(module))
    programme_sources = [src_programme1,src_programme2]
    for src in programme_sources:
        original = compile_dbase_to_assembly(src.read_text(), target=target).assembly
        transformed = strip_program_entry_assembly(original)
        assert not re.search(r'(?m)^\s*(?:entry|global)\s+_start\b|^\s*_start:', transformed)
        obj = namespace_module_object(asm(transformed), src)
        assert '_start' not in obj.symbols
        assert not any(x.endswith('_start') for x in obj.symbols)
        src.with_suffix('.o').write_bytes(write(obj))
    result = module_link_inputs(mod_obj, programme_sources, lambda path:path.with_suffix('.o'))
    assert result[0] == mod_obj and len(result)==3
    exe = tmp_path/'App001.exe'
    exe.write_bytes(link(result,entry_symbol='_start',gui=True).executable)
    assert inspect_pe(exe)[0] == machine
    assert exe.read_bytes()[:2] == b'MZ'


@pytest.mark.parametrize('target,machine', [('pe32', 0x14c), ('pe64', 0x8664)])
def test_real_class_dll_module_plus_library_programme(tmp_path, target, machine):
    native = _load_pe_linker()
    asm = native['assemble_pe64_object_source' if target == 'pe64' else 'assemble_pe32_object_source']
    write = native['write_coff64_object' if target == 'pe64' else 'write_coff32_object']
    link = native['link_coff64_inputs' if target == 'pe64' else 'link_coff32_inputs']
    src = OBJECTS.read_text(encoding='utf-8')
    original = compile_dbase_to_assembly(src,filename=str(OBJECTS),target=target,source_kind='library').assembly
    mod = asm(original)
    assert '__d64_dll_entry' in mod.symbols
    mod_obj = tmp_path/'App001.o';mod_obj.write_bytes(write(mod))
    programme_code = strip_dbase_library_entry_assembly(original)
    programme = namespace_module_object(asm(programme_code),tmp_path/'helpers.prg',
                                         hide_tobject_exports=True)
    assert '__d64_dll_entry' not in programme.symbols
    assert '__dbase_cls_tobject_create' not in programme.exports
    programme_obj=tmp_path/'helpers.o';programme_obj.write_bytes(write(programme))
    dest=tmp_path/'App001.dll'
    dest.write_bytes(link((mod_obj,programme_obj),entry_symbol='__d64_dll_entry',
                          dll=True,dll_name=dest.name,gui=True,pack_dll=False).executable)
    machine_actual,_,exports=inspect_pe(dest)
    assert machine_actual==machine
    assert '__dbase_cls_tobject_create' in exports


def test_only_module_needed_and_missing_objects_rejected(tmp_path):
    m=tmp_path/'App001.o';m.write_bytes(b'test')
    assert module_link_inputs(m,[],lambda _:None)==(m,)
    p=tmp_path/'one.prg'
    with pytest.raises(ValueError,match='fehlt'):
        module_link_inputs(m,[p],lambda src:src.with_suffix('.o'))
    p.with_suffix('.o').write_bytes(b'other')
    assert len(module_link_inputs(m,[p],lambda src:src.with_suffix('.o')))==2
    with pytest.raises(ValueError,match='doppelte'):
        module_link_inputs(m,[p,p],lambda src:src.with_suffix('.o'))


def test_switches_to_object_only_in_all_build_handlers():
    source=body('_compile_dbase_document')
    assert 'strip_program_entry_assembly(generated.assembly)' in source
    assert 'strip_dbase_library_entry_assembly(generated.assembly)' in source
    for name in ('assemble_generated_document','build_and_run_source_document',
                 'build_and_run_generated_assembly_document'):
        source=body(name)
        assert 'self._is_selected_dbase_program_document(document)' in source
        assert 'self.assemble_project_dbase_program_object(document)' in source
    button=body('refresh_project_module_link_buttons','DocumentEditor')
    assert 'object_only' in button and 'not (active or object_only) or executable_ready' in button


def test_bulk_group_choice_and_individual_override():
    env={'PROJECT_NODE_DBASE_GROUP':'group','PROJECT_NODE_DBASE_FILE':'file','Qt':SimpleNamespace(UserRole=1000),'QTreeWidgetItem':object}
    exec(dedent(body('_project_named_file_changed')),env)
    fn=env['_project_named_file_changed']
    class Fake:
        def __init__(self, key, kind='file'):
            self.key=key;self.kind=kind;self.children=[]
        def childCount(self):return len(self.children)
        def child(self,i):return self.children[i]
        def data(self,col,role):return 'programs' if role==1306 else None
    group=Fake('group','group'); group.children=[Fake('a'),Fake('b')]
    current={'group':'dbase|program','a':'dbase|library','b':''}
    owner=SimpleNamespace(
        _named_project_loading=False,
        _named_project_assignments={'a':'dbase|library'},
        project_tree=SimpleNamespace(itemWidget=lambda item,col:SimpleNamespace(currentData=lambda:current[item.key])),
        _project_named_leaf_key=lambda item:item.key,
        _project_item_kind=lambda item:item.kind,
        set_project_modified=lambda *args:None,
        _project_named_schedule_refresh=lambda:None,
    )
    fn(owner,group)
    assert owner._named_project_assignments=={
        'group':'dbase|program','a':'dbase|program','b':'dbase|program'}
    current['a']='dbase|library'
    fn(owner,group.children[0])
    assert owner._named_project_assignments['a']=='dbase|library'
    assert owner._named_project_assignments['b']=='dbase|program'


@pytest.mark.parametrize('target,machine', [('pe32',0x14c),('pe64',0x8664)])
@pytest.mark.parametrize('kind', ['program','library'])
@pytest.mark.parametrize('include_programme', [False,True])
def test_actual_gui_link_handler_profile_assignments(
        tmp_path,target,machine,kind,include_programme,monkeypatch):
    native=_load_pe_linker()
    asm=native['assemble_pe64_object_source' if target=='pe64' else 'assemble_pe32_object_source']
    write=native['write_coff64_object' if target=='pe64' else 'write_coff32_object']
    src_mod=tmp_path/'App001.prg'
    src_programme=tmp_path/'utility.prg'
    if kind=='program':
        source='? "EXE module"\n'
        module_asm=compile_dbase_to_assembly(source,target=target).assembly
        programme_asm=strip_program_entry_assembly(
            compile_dbase_to_assembly('? "Code"\n',target=target).assembly)
    else:
        source=OBJECTS.read_text(encoding='utf-8')
        module_asm=compile_dbase_to_assembly(source,target=target,source_kind='library').assembly
        programme_asm=strip_dbase_library_entry_assembly(module_asm)
    src_mod.write_text(source)
    src_programme.write_text(source)
    mod_o=src_mod.with_suffix('.o');mod_o.write_bytes(write(asm(module_asm)))
    prog_o=src_programme.with_suffix('.o')
    prog_o.write_bytes(write(namespace_module_object(
        asm(programme_asm),src_programme,hide_tobject_exports=True)))
    env={
        'Path':Path,'Qt':SimpleNamespace(UserRole=1000), 're':re,
        'DocumentEditor':object,
        'link_coff32_inputs':native['link_coff32_inputs'],
        'link_coff64_inputs':native['link_coff64_inputs'],
        'parse_coff32_object':native['parse_coff32_object'],
        'parse_coff64_object':native['parse_coff64_object'],
        '_coff_target_header_matches':native['_coff_target_header_matches'],
        'normalize_windows_application_mode':lambda mode:mode,
        'PE32AssemblerError':native['PE32AssemblerError'],
        'PE64AssemblerError':native['PE64AssemblerError'],
        'ResourceCompilerError':type('ResourceCompilerError',(Exception,),{}),
        'embed_project_manifest_resource':lambda *args,**kw:None,
    }
    exec(dedent(body('link_project_dbase_module_document')),env)
    fn=env['link_project_dbase_module_document']
    class Leaf:
        def data(self,c,r):return str(src_programme) if r==1302 else None
    group=SimpleNamespace(childCount=lambda:1,child=lambda i:Leaf())
    logs=[]
    out=tmp_path/'dest';out.mkdir()
    fake=ModuleType('turbo_help_settings')
    fake.write_application_help_manifest=lambda *a,**kw:None
    monkeypatch.setitem(sys.modules,'turbo_help_settings',fake)
    doc=SimpleNamespace(
        path=src_mod,build_target=target,windows_application_mode='GUI',
        generated_source_kind='library' if kind=='library' else 'program',
        _dbase_module_coff_path=mod_o,
        _dbase_module_coff_target=target,
        _dbase_module_coff_digest='digest',
        _dbase_module_link_digest='',
        generated_assembly_digest=lambda:'digest',
        refresh_project_module_link_buttons=lambda:None,
        generated_assembly_status_label=SimpleNamespace(setText=lambda s:None),
        hints_editor=SimpleNamespace(setPlainText=lambda s:None),
    )
    owner=SimpleNamespace(
        _is_selected_dbase_module_document=lambda doc:True,
        _document_windows_output_path=lambda doc:out,
        _document_windows_pascal_unit_output_path=lambda doc:tmp_path,
        _project_generated_object_path=lambda path,t,output_directory=None:Path(path).with_suffix('.o'),
        _project_named_current_scope=lambda:('dbase',kind),
        _project_named_effective_assignment=lambda leaf:f'dbase|{kind}' if include_programme else 'dbase|'+('library' if kind=='program' else 'program'),
        _named_project_names=normalize_names({'dbase_program':'App001','dbase_library':'MyLib'}),
        project_dbase_group_nodes={'programs':group},
        _stage549_sync_debug_options_for_build=lambda t:False,
        _dbase_console_runtime_pack_enabled=lambda t:False,
        project_windows_manifests={'pe32':None,'pe64':None},
        project_windows_compact_enabled={'pe32':False,'pe64':False},
        _sign_windows_output_if_enabled=lambda *a:True,
        _write_assembled_program=lambda path,bytes_:Path(path).write_bytes(bytes_),
        _prepare_dbase_console_runtime=lambda *a:True,
        project_turbo_help_root=None,project_help_settings=None,
        current_directory=tmp_path,current_project_path=None,
        show_error=lambda title,message:pytest.fail(f'{title}: {message}'),
        log=lambda text:logs.append(text),
        statusBar=lambda:SimpleNamespace(showMessage=lambda _:None),
        populate_file_list=lambda:None,
    )
    assert fn(owner,doc) is True
    dest=out/('MyLib.dll' if kind=='library' else 'App001.exe')
    assert inspect_pe(dest)[0]==machine
    assert len(doc._dbase_module_link_inputs)==(2 if include_programme else 1)
    assert doc._dbase_module_link_path==dest
    assert doc._dbase_module_link_is_dll == (kind == 'library')
    assert doc._dbase_module_link_profile_kind == kind


def test_obj_assembler_for_programme_produces_only_coff(tmp_path):
    native=_load_pe_linker();target='pe32'
    src=tmp_path/'functions.prg';src.write_text('? "hi"')
    source=strip_program_entry_assembly(
        compile_dbase_to_assembly(src.read_text(),target=target).assembly)
    env={
        'Path':Path, 'DocumentEditor':object,
        'assemble_pe64_object_source':native['assemble_pe64_object_source'],
        'assemble_pe32_object_source':native['assemble_pe32_object_source'],
        'write_coff64_object':native['write_coff64_object'],
        'write_coff32_object':native['write_coff32_object'],
        'PE32AssemblerError':native['PE32AssemblerError'],
        'PE64AssemblerError':native['PE64AssemblerError'],
    }
    exec(dedent(body('assemble_project_dbase_program_object')),env)
    fn=env['assemble_project_dbase_program_object']
    doc=SimpleNamespace(path=src,build_target=target,
        generated_assembly_editor=SimpleNamespace(toPlainText=lambda:source),
        generated_assembly_path=tmp_path/'functions.generated.asm',
        generated_assembly_status_label=SimpleNamespace(setText=lambda _:None),
        hints_editor=SimpleNamespace(setPlainText=lambda _:None),
        show_generated_assembly_error=lambda *a:pytest.fail(str(a)),
    )
    obj_path=tmp_path/'functions.o'
    owner=SimpleNamespace(
        _is_selected_dbase_program_document=lambda doc:True,
        _project_generated_object_path=lambda *a,**kw:obj_path,
        _document_windows_pascal_unit_output_path=lambda doc:tmp_path,
        _project_windows_asm_include_paths=lambda *a:(),
        _write_assembled_program=lambda path,bytes_:Path(path).write_bytes(bytes_),
        show_error=lambda *a:pytest.fail(str(a)),
        log=lambda *a:None,
        statusBar=lambda:SimpleNamespace(showMessage=lambda _:None),
        populate_file_list=lambda:None,current_directory=tmp_path,
    )
    assert fn(owner,doc) is True
    assert obj_path.read_bytes()[:2]==struct.pack('<H',0x14c)
    parsed=native['parse_coff32_object'](obj_path.read_bytes())
    assert '_start' not in parsed.symbols


def test_start_never_appears_for_dll_or_changed_profile(tmp_path):
    from types import SimpleNamespace
    fn_env={'Path':Path}
    exec(dedent(body('refresh_project_module_link_buttons','DocumentEditor')),fn_env)
    refresh=fn_env['refresh_project_module_link_buttons']
    class Button:
        def __init__(self): self.visible=None;self.enabled=None
        def setVisible(self,value):self.visible=value
        def setEnabled(self,value):self.enabled=value
        def setText(self,_):pass
        def setToolTip(self,_):pass
    obj=tmp_path/'x.o';obj.write_bytes(b'one')
    binary=tmp_path/'x.dll';binary.write_bytes(b'MZ')
    doc=SimpleNamespace(
        _dbase_module_selected=True,_dbase_program_selected=False,
        is_dbase_document=True,is_assembler_document=False,
        build_target='pe32',
        _dbase_module_coff_path=obj,_dbase_module_coff_target='pe32',
        _dbase_module_coff_digest='x',
        _dbase_module_link_path=binary,_dbase_module_link_target='pe32',
        _dbase_module_link_digest='x',_dbase_module_link_is_dll=True,
        _dbase_module_link_profile_kind='library',
        _dbase_module_active_profile_kind='library',
        _dbase_module_link_inputs=((str(obj),obj.stat().st_mtime_ns,obj.stat().st_size),),
        generated_assembly_digest=lambda:'x',
        link_assembled_button=Button(),link_generated_button=Button(),
        start_generated_button=Button(),start_assembled_button=Button(),
        assemble_generated_button=Button(),
    )
    refresh(doc)
    assert doc.link_generated_button.visible is True
    assert doc.start_generated_button.visible is False
    assert doc.start_generated_button.enabled is False
    doc._dbase_module_link_is_dll=False
    refresh(doc)
    assert doc.start_generated_button.visible is True
    doc._dbase_module_active_profile_kind='program'
    refresh(doc)
    assert doc.start_generated_button.visible is False
