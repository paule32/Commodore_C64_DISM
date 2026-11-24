# -*- coding: utf-8 -*-
"""Stage 679: O3 inherited optimizations and native default TObject VMT."""
from __future__ import annotations

import ctypes
from pathlib import Path
from types import SimpleNamespace
import re
import shutil
import subprocess
import sys

import pytest

from dbase_size_optimizer import normalize_dbase_optimization_level, optimize_dbase_size_assembly
from d64dbase import compile_dbase_to_assembly
from d64dbase.object_abi import NativeClassMethod, emit_classes

ROOT = Path(__file__).resolve().parent


def _asm(text, target):
    return compile_dbase_to_assembly(text, target=target).assembly


def _o(text, level, target):
    return optimize_dbase_size_assembly(_asm(text, target), level=level).assembly


def test_ui_level_and_project_storage():
    assert normalize_dbase_optimization_level('o3') == 'O3'
    assert normalize_dbase_optimization_level('O2') == 'O2'
    assert normalize_dbase_optimization_level('bad') == 'O0'
    gui = (ROOT / 'd64_dism.py').read_text(encoding='utf8')
    assert '"O3  -  Reduce redundant method tables"' in gui
    assert 'self.dbase_size_o3_radio.setChecked(selected == "O3")' in gui
    assert '"O3" if self.dbase_size_o3_radio.isChecked()' in gui
    assert '"OptimizationLevel": normalize_dbase_optimization_level' in gui
    assert 'if _dbase_level in {"O1", "O2", "O3"}' in gui
    assert 'in {"O1", "O2", "O3"} else {}' in gui


@pytest.mark.parametrize('target,ptr,bytes_saved', [('pe32', 'dd', 36), ('pe64', 'dq', 72)])
def test_no_redundant_table_and_o1_o2_inheritance(target, ptr, bytes_saved):
    source = ('CLASS TChild OF TObject ENDCLASS\n'
              'obj = new TChild()\n'
              'obj.Free()\n'
              '? "erste"\n? "zweite"\n')
    raw = _asm(source, target)
    opt2 = optimize_dbase_size_assembly(raw, level='O2').assembly
    opt3 = optimize_dbase_size_assembly(raw, level='O3').assembly
    assert '__dbase_class_object:' in opt2
    assert '__dbase_class_object:' not in opt3
    assert re.search(rf'__dbase_vmt_tobject:\n(?:\s*{ptr}\s+[^\n]+\n){{5}}\s*{ptr}\s+0\b', opt3)
    assert re.search(rf'__dbase_vmt_tchild:\n(?:\s*{ptr}\s+[^\n]+\n){{5}}\s*{ptr}\s+0\b', opt3)
    assert opt3.count('call DBaseQtRuntimeWriteText') == opt2.count('call DBaseQtRuntimeWriteText')
    assert opt3.count('call DBaseQtBindOutputState') == opt2.count('call DBaseQtBindOutputState')
    assert 'call __dbase_obj_jit_get_virtual_object' in opt3
    assert 'call __dbase_obj_jit_object_free' not in opt3
    assert opt3.count('; O3: TObject Standardtabelle') == 10
    assert optimize_dbase_size_assembly(opt3, level='O3').assembly == opt3
    assert len(opt3.splitlines()) >= len(opt2.splitlines())
    assert 'call __dbase_o3_default_vmt_abi' in opt3
    # O0 and O1 remain unaffected by Stage-679 post-pass.
    assert optimize_dbase_size_assembly(raw, level='O0').assembly == raw
    assert '__dbase_class_object:' in optimize_dbase_size_assembly(raw, level='O1').assembly


@pytest.mark.parametrize('target,ptr', [('pe32','dd'), ('pe64','dq')])
def test_custom_override_keeps_derived_method_table(target,ptr):
    source = '''CLASS TChild OF TObject
procedure Free
if Self == 0
return
endif
return
ENDCLASS
obj = new TChild()
'''
    output = _o(source,'O3',target)
    assert '__dbase_class_object:' not in output
    assert '__dbase_class_methods_1:' in output
    assert f'{ptr} __dbase_cls_tchild_free' in output
    assert f'{ptr} __dbase_cls_tobject_freeinstance' in output
    assert '__dbase_cls_tobject_freeinstance:' in output
    assert re.search(rf'__dbase_vmt_tchild:\n(?:\s*{ptr}\s+[^\n]+\n){{5}}\s*{ptr}\s+__dbase_class_methods_1',output)


@pytest.mark.parametrize('target', ['pe32', 'pe64'])
def test_custom_tobject_disables_default_fallback(target):
    original=_asm('CLASS TObject OF CUSTOM\nprocedure Free\nif Self == 0\nreturn\nendif\nreturn\nENDCLASS\n',target)
    assert '; Stage 679: TObject custom virtual methods; no DLL fallback' in original
    optimized=optimize_dbase_size_assembly(original,level='O3').assembly
    assert '__dbase_class_object:' in optimized
    assert 'dd __dbase_class_object' in optimized if target=='pe32' else 'dq __dbase_class_object' in optimized
    assert '__dbase_cls_tobject_free:' in optimized


@pytest.mark.parametrize('target', ('pe32', 'pe64'))
def test_multiple_classes_keep_one_shared_default_sentinel(target):
    classes=[SimpleNamespace(name=f'TClass{i}', parent='TObject', methods=(),properties=())
             for i in range(20)]
    _imports, code, data = emit_classes(classes,target=target)
    # Compilation without O3 still produces the original table exactly once.
    assert '\n'.join(data).count('__dbase_class_object:') == 1
    # O3 is a guarded post-assembly pass, preserving baseline O0.
    asm=_asm('CLASS TOne OF TObject ENDCLASS\n',target)
    a=optimize_dbase_size_assembly(asm, level='O3').assembly
    assert '__dbase_class_object:' not in a


@pytest.mark.parametrize('target', ['pe32', 'pe64'])
def test_real_coff_and_pe_link_with_o3(target):
    from test_stage605_link import _load_pe_linker
    n=_load_pe_linker()
    source='CLASS TChild OF TObject ENDCLASS\nobj = new TChild()\nobj.Free()\n? "OK"\n'
    asm=_o(source,'O3',target)
    assembler=n['assemble_pe32_object_source' if target=='pe32' else 'assemble_pe64_object_source']
    writer=n['write_coff32_object' if target=='pe32' else 'write_coff64_object']
    link=n['link_coff32_objects' if target=='pe32' else 'link_coff64_objects']
    obj=assembler(asm)
    assert '__dbase_class_object' not in {name.lower() for name in obj.symbols}
    assert '__dbase_o3_default_vmt_abi' in obj.imports
    assert obj.imports['__dbase_o3_default_vmt_abi'] == ('libd64_qt5.dll', 'jit_default_tobject_vmt_abi')
    exe=link((writer(obj),), entry_symbol='_start', gui=True).executable
    assert exe[:2] == b'MZ'


@pytest.mark.skipif(not shutil.which('clang++'), reason='clang++ missing')
def test_native_win32_cpp_syntax_no_fallback_imports():
    result=subprocess.run(['clang++','-target','i686-w64-windows-gnu',
                           '-std=c++20','-fsyntax-only','-fno-exceptions','-fno-rtti',
                           '-nostdinc','-DDLL_BUILD','-DD64_QT5_EMBEDDED',
                           '-I'+str(ROOT/'runtime'),str(ROOT/'runtime/jitObject.cc')],
                          capture_output=True,text=True)
    assert result.returncode==0,result.stderr


@pytest.mark.skipif(not sys.platform.startswith('linux') or not shutil.which('g++'),
                    reason='Linux native C++ smoke test')
def test_real_native_o3_default_and_legacy_dispatch(tmp_path):
    stub=tmp_path/'stub.cpp'
    stub.write_text('#include <cstdlib>\n'
                    'extern "C" void* _jit_calloc(unsigned n,unsigned s){return std::calloc(n,s);}\n'
                    'extern "C" void _jit_free(void *p){std::free(p);}\n'
                    'extern "C" int _jit_printf(const char*,...){return 0;}\n')
    so=tmp_path/'jit.so'
    a=tmp_path/'jit.o'; b=tmp_path/'stub.o'
    cmds=[['g++','-std=c++20','-fPIC','-fpermissive','-DDLL_BUILD',
           '-D__declspec(x)=','-I'+str(ROOT/'runtime'),'-c',
           str(ROOT/'runtime/jitObject.cc'),'-o',str(a)],
          ['g++','-std=c++20','-fPIC','-c',str(stub),'-o',str(b)],
          ['g++','-shared',str(a),str(b),'-o',str(so)]]
    for command in cmds:
        r=subprocess.run(command,capture_output=True,text=True)
        assert r.returncode==0,r.stderr
    lib=ctypes.CDLL(str(so)); vp=ctypes.c_void_p
    class Header(ctypes.Structure):
        _fields_=[('parent',vp),('class_name',vp),('size',ctypes.c_uint32),
                  ('init',vp),('done',vp),('destroy',vp)]
    instance_size=ctypes.sizeof(vp)
    h=Header(size=0x80000000|instance_size)
    lib.jit_get_virtual_vmt.argtypes=[vp,ctypes.c_uint32]
    lib.jit_get_virtual_vmt.restype=vp
    lib.jit_object_instance_new.argtypes=[vp]
    lib.jit_object_instance_new.restype=vp
    lib.jit_object_class_type.argtypes=[vp]
    lib.jit_object_class_type.restype=vp
    lib.jit_class_instance_size.argtypes=[vp]
    lib.jit_class_instance_size.restype=ctypes.c_uint32
    lib.jit_object_free.argtypes=[vp]
    lib.jit_object_error_last.restype=ctypes.c_int
    lib.jit_default_tobject_vmt_abi.restype=ctypes.c_uint32
    assert lib.jit_default_tobject_vmt_abi()==1
    assert lib.jit_class_instance_size(ctypes.byref(h)) == instance_size
    defaults=[lib.jit_get_virtual_vmt(ctypes.byref(h),i) for i in range(8)]
    assert all(defaults)
    assert defaults[4] == defaults[5]  # ClassNameAddress and ClassName
    inst=lib.jit_object_instance_new(ctypes.byref(h))
    assert inst
    assert lib.jit_object_class_type(inst)==ctypes.addressof(h)
    obj_class_type=ctypes.CFUNCTYPE(vp,vp)(defaults[2])
    assert obj_class_type(inst)==ctypes.addressof(h)
    obj_instance_size=ctypes.CFUNCTYPE(ctypes.c_uint32,vp)(defaults[6])
    assert obj_instance_size(inst)==instance_size
    obj_free=ctypes.CFUNCTYPE(None,vp)(defaults[0])
    obj_free(inst)
    # User override compact method table is preserved and does not fall back.
    cb=ctypes.CFUNCTYPE(None,vp)
    calls=[]
    @cb
    def custom(ptr): calls.append(ptr)
    tab=(vp*9)();tab[1]=ctypes.cast(custom,vp).value
    h2=Header(size=0x80000000|instance_size,destroy=ctypes.addressof(tab))
    assert lib.jit_get_virtual_vmt(ctypes.byref(h2),0)==ctypes.cast(custom,vp).value
    # An unflagged legacy VMT must continue using the original inline slots.
    class Legacy(ctypes.Structure):
        _fields_=[('header',Header),('slots',vp*8)]
    old=Legacy();old.header.size=instance_size
    old.slots[0]=ctypes.cast(custom,vp).value
    assert lib.jit_get_virtual_vmt(ctypes.byref(old),0)==ctypes.cast(custom,vp).value

@pytest.mark.parametrize('target', ['pe32', 'pe64'])
def test_o3_two_programme_objects_link_and_preserve_runtime_guard(tmp_path, target):
    from test_stage605_link import _load_pe_linker
    from dbase_module_coff import strip_program_entry_assembly, namespace_module_object
    n=_load_pe_linker()
    assemble=n['assemble_pe32_object_source' if target=='pe32' else 'assemble_pe64_object_source']
    write=n['write_coff32_object' if target=='pe32' else 'write_coff64_object']
    link=n['link_coff32_inputs' if target=='pe32' else 'link_coff64_inputs']
    a=_o('CLASS TA OF TObject ENDCLASS\na = new TA()\n','O3',target)
    b=strip_program_entry_assembly(_o('CLASS TB OF TObject ENDCLASS\n? "Test"\n','O3',target))
    assert 'call __dbase_o3_default_vmt_abi' in b
    obj1=tmp_path/'Module.o';obj2=tmp_path/'Programme.o'
    obj1.write_bytes(write(assemble(a)))
    obj2.write_bytes(write(namespace_module_object(assemble(b),tmp_path/'Programme.prg')))
    result=link((obj1,obj2),entry_symbol='_start',gui=True)
    assert result.executable[:2]==b'MZ'
    from pascal_console_dependencies import inspect_pe
    exe=tmp_path/'result.exe';exe.write_bytes(result.executable)
    _machine,imports,_=inspect_pe(exe)
    assert 'jit_default_tobject_vmt_abi' in imports['libd64_qt5.dll']


def test_o3_runtime_export_and_deployment_guard():
    from d64dbase.native_runtime_deploy import REQUIRED_EXPORTS
    header=(ROOT/'runtime/jitObject.h').read_text()
    exports=(ROOT/'d64qt5/d64qt5_bridge.def').read_text()
    assert re.search(r'^\s*jit_default_tobject_vmt_abi\s+@2085\s*$',exports,re.M)
    assert 'jit_default_tobject_vmt_abi' in REQUIRED_EXPORTS
    assert 'jit_default_tobject_vmt_abi(void)' in header
    assert 'jit_default_tobject_vmt_abi(void) { return 1u; }' in (ROOT/'runtime/jitObject.cc').read_text()


def test_o3_project_config_roundtrip():
    import configparser
    src=(ROOT/'d64_dism.py').read_text(encoding='utf8')
    begin=src.index('        parser[_settings["dbase_optimization_section"]] = {')
    end=src.index('        parser[_settings["prolog_optimization_section"]] = {',begin)
    writer=src[begin:end]
    begin=src.index('        _dbase_optimization_section = _settings["dbase_optimization_section"]')
    end=src.index('        _prolog_optimization_section = _settings["prolog_optimization_section"]',begin)
    reader=src[begin:end]
    settings={a:{'title':b,'dbase_optimization_section':f'Settings.Windows.{b}.Compiler.dBASE.Optimierung',
                 'dbase_size_level_key':f'size_{a}',**{key:f'opt_{a}_{key}' for key in (
                    'dbase_external_ui_key','dbase_compress_json_key','dbase_store_binary_key',
                    'dbase_static_numeric_slots_key','dbase_dynamic_typed_variables_key',
                    'dbase_peephole_register_width_key','dbase_peephole_processor_flags_key',
                    'dbase_peephole_stack_state_key')}} for a,b in (('pe32','32Bit'),('pe64','64Bit'))}
    env={'PROJECT_WINDOWS_TARGET_SETTINGS':settings,
         '_project_bool_entry':lambda entries,key,default=False:False,
         '_parse_project_bool':lambda value,default=False:value.casefold()=='true',
         'normalize_dbase_optimization_level':normalize_dbase_optimization_level}
    exec('def write(parser,entries):\n    for _target,_settings in PROJECT_WINDOWS_TARGET_SETTINGS.items():\n'+writer,env)
    exec('def load(parser,entries):\n    for _target,_settings in PROJECT_WINDOWS_TARGET_SETTINGS.items():\n'+reader,env)
    parser=configparser.ConfigParser(interpolation=None);parser.optionxform=str
    env['write'](parser,{'size_pe32':[{'value':'O3'}], 'size_pe64':[{'value':'O2'}]})
    assert parser['Settings.Windows.32Bit.Compiler.dBASE.Optimierung']['OptimizationLevel']=='O3'
    assert parser['Settings.Windows.64Bit.Compiler.dBASE.Optimierung']['OptimizationLevel']=='O2'
    loaded={}
    env['load'](parser,loaded)
    assert loaded['size_pe32']==[{'value':'O3'}]
    assert loaded['size_pe64']==[{'value':'O2'}]
