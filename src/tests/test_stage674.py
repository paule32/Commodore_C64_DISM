# -*- coding: utf-8 -*-
"""Stage 674: O2 static text ABI, GUI persistence, COFF and native runtime."""
from __future__ import annotations
import ctypes
import hashlib
from pathlib import Path
import re
import shutil
import subprocess

import pytest

from d64dbase import compile_dbase_to_assembly
from dbase_size_optimizer import normalize_dbase_optimization_level, optimize_dbase_size_assembly

ROOT = Path(__file__).resolve().parent
SOURCE = '? "eins"\n? "zwei"\n? "drei"\n'


def test_level_normalization_and_project_ui():
    assert [normalize_dbase_optimization_level(i) for i in ('O0','O1','O2','o2','garbage')] == [
        'O0','O1','O2','O2','O0']
    gui = (ROOT/'d64_dism.py').read_text(encoding='utf8')
    assert '"O1  -  Länge Optimierung - JNE JE"' in gui
    assert '"O2  -  Static String Optimierung"' in gui
    assert 'self.dbase_size_o0_radio.setChecked(True)' in gui
    assert 'self.dbase_size_o2_radio.setChecked(selected == "O2")' in gui
    assert 'return ("O2" if self.dbase_size_o2_radio.isChecked() else' in gui
    assert '"OptimizationLevel": normalize_dbase_optimization_level' in gui
    assert 'parser.get(_dbase_optimization_section, "OptimizationLevel", fallback="O0")' in gui
    assert 'if _dbase_level in {"O1", "O2"}' in gui


@pytest.mark.parametrize('target', ['pe32', 'pe64'])
def test_o2_codegen_carries_o1_and_is_idempotent(target):
    asm = compile_dbase_to_assembly(SOURCE, target=target).assembly
    opt0 = optimize_dbase_size_assembly(asm, level='O0').assembly
    opt1 = optimize_dbase_size_assembly(asm, level='O1').assembly
    opt2 = optimize_dbase_size_assembly(asm, level='O2').assembly
    assert opt0 == asm
    assert 'call DBaseQtRuntimeWrite' in opt1
    assert 'call DBaseQtRuntimeWriteText' not in opt1
    assert opt2.count('call DBaseQtRuntimeWriteText') >= 3
    assert opt2.count('call DBaseQtBindOutputState') == 2
    assert 'import DBaseQtRuntimeWriteText, "libd64_qt5.dll", "DBaseQtRuntimeWriteText"' in opt2
    assert 'import DBaseQtBindOutputState, "libd64_qt5.dll", "DBaseQtBindOutputState"' in opt2
    assert re.search(r'^\s*call DBaseQtRuntimeWrite\s*$',opt2,re.M) is None
    assert '__dbase_o2_dbase_text_1:' in opt2
    assert '__dbase_text_1:' in opt2  # raw strings preserve legacy pointer ABI
    assert 'dd __dbase_output_debug_override' in opt2 if target == 'pe32' else 'dq __dbase_output_debug_override' in opt2
    assert optimize_dbase_size_assembly(opt2,level='O2').assembly == opt2
    assert opt2.index('call DBaseQtBindOutputState') < opt2.index('call DBaseQtRuntimeWriteText')
    jump = 'bits 32\nsection .text\nx:\n    jne yes\n    jmp no\nyes:\n    ret\nno:\n    ret\n'
    assert 'je no' in optimize_dbase_size_assembly(jump, level='O2').assembly


@pytest.mark.parametrize('target', ['pe32', 'pe64'])
def test_o2_real_coff_link_is_smaller_than_o1(target):
    from test_stage605_link import _load_pe_linker
    native = _load_pe_linker()
    assembler = native['assemble_pe32_object_source' if target=='pe32' else 'assemble_pe64_object_source']
    writer = native['write_coff32_object' if target=='pe32' else 'write_coff64_object']
    linker = native['link_coff32_objects' if target=='pe32' else 'link_coff64_objects']
    asm = compile_dbase_to_assembly(SOURCE, target=target).assembly
    a = assembler(optimize_dbase_size_assembly(asm, level='O1').assembly)
    b = assembler(optimize_dbase_size_assembly(asm, level='O2').assembly)
    assert len(b.code) < len(a.code)
    assert b.imports['dbaseqtruntimewritetext'] == ('libd64_qt5.dll','DBaseQtRuntimeWriteText')
    assert b.imports['dbaseqtbindoutputstate'] == ('libd64_qt5.dll','DBaseQtBindOutputState')
    assert linker((writer(b),),entry_symbol='_start',gui=True).executable.startswith(b'MZ')


def test_o2_rewrites_single_static_output_and_binds_empty_module():
    for source in ('? "einzel"\n', 'x = 1\n'):
        asm = compile_dbase_to_assembly(source,target='pe32').assembly
        out = optimize_dbase_size_assembly(asm,level='O2').assembly
        assert out.count('call DBaseQtBindOutputState') == 2
        assert 'import DBaseQtBindOutputState' in out
        if 'einzel' in source:
            assert 'call DBaseQtRuntimeWriteText' in out
        else:
            # The generated unhandled-exception path still contains static strings.
            assert '__dbase_o2_output_state:' in out


def test_dll_exports_preserve_abi_core():
    header=(ROOT/'d64qt5/d64qt5_bridge.h').read_text()
    exports=dict(re.findall(r'^\s*(\w+)\s+@(\d+)',(ROOT/'d64qt5/d64qt5_bridge.def').read_text(),re.M))
    assert exports['DBaseQtRuntimeWrite']=='1019'
    assert exports['DBaseQtBindOutputState']=='1020'
    assert exports['DBaseQtRuntimeWriteText']=='1021'
    for name in ('DBaseQtOutputBindings', 'DBaseQtStaticText'):
        assert name in header
    assert 'DBaseQtRuntimeWriteText(const DBaseQtStaticText *text)' in header
    core=sorted((int(number),name) for name,number in exports.items() if 1<=int(number)<=64)
    digest=hashlib.sha256(''.join(f'{number}:{name}\n' for number,name in core).encode()).hexdigest()
    assert digest=='02c94324ebc9e8373c08011d0f8c5ba5aec95b158087092ed4e741877b1a7cd7'


def test_native_o2_state_is_live_and_unbinds(tmp_path):
    if not shutil.which('g++'):
        pytest.skip('g++ unavailable')
    src=(ROOT/'d64qt5/d64qt5_bridge.cpp').read_text()
    begin=src.index('// Stage 674: O2 bind-once output state')
    end=src.index('extern "C" D64QT5_API int DBaseQtSetOutputColor',begin)
    cpp=r'''
#include <cstdint>
#define D64QT5_API
struct DBaseQtOutputBindings { const int *debugOverride; const int *formatScreen; int *debugVisible; };
struct DBaseQtStaticText { unsigned int length; const char *text; };
static int calls=0, last_debug=0, last_format=0, last_length=0;
extern "C" void DBaseQtRuntimeWrite(const char *,int length,int debug,int format,int *visible) {
    ++calls;last_length=length;last_debug=debug;last_format=format;
    if(visible) *visible=1;
}
'''
    cpp+=src[begin:end]
    cpp+=r'''
extern "C" int read_state(int idx) {
    switch(idx) {case 0:return calls;case 1:return last_debug;case 2:return last_format;
                 case 3:return last_length;default:return -999;}
}
'''
    source=tmp_path/'o2.cpp';source.write_text(cpp)
    lib_path=tmp_path/'o2.so'
    subprocess.run(['g++','-std=c++20','-fPIC','-shared',str(source),'-o',str(lib_path)],check=True,capture_output=True,text=True)
    lib=ctypes.CDLL(str(lib_path))
    class Binding(ctypes.Structure):
        _fields_=[('override',ctypes.POINTER(ctypes.c_int)),('format',ctypes.POINTER(ctypes.c_int)),('visible',ctypes.POINTER(ctypes.c_int))]
    class Text(ctypes.Structure):
        _fields_=[('length',ctypes.c_uint),('data',ctypes.c_char_p)]
    lib.DBaseQtBindOutputState.argtypes=[ctypes.POINTER(Binding)]
    lib.DBaseQtRuntimeWriteText.argtypes=[ctypes.POINTER(Text)]
    lib.read_state.argtypes=[ctypes.c_int]
    lib.read_state.restype=ctypes.c_int
    override=ctypes.c_int(-1);format_screen=ctypes.c_int(0);visible=ctypes.c_int(0)
    binding=Binding(ctypes.pointer(override),ctypes.pointer(format_screen),ctypes.pointer(visible))
    literal=Text(4,b'hihi')
    lib.DBaseQtBindOutputState(ctypes.byref(binding))
    lib.DBaseQtRuntimeWriteText(ctypes.byref(literal))
    assert [lib.read_state(i) for i in range(4)] == [1,-1,0,4]
    assert visible.value == 1
    visible.value=0;format_screen.value=1
    lib.DBaseQtRuntimeWriteText(ctypes.byref(literal))
    assert [lib.read_state(i) for i in range(4)] == [2,-1,1,4]
    override.value=0;format_screen.value=1
    lib.DBaseQtRuntimeWriteText(ctypes.byref(literal))
    assert [lib.read_state(i) for i in range(4)] == [3,0,1,4]
    lib.DBaseQtBindOutputState(None)
    lib.DBaseQtRuntimeWriteText(ctypes.byref(literal))
    assert [lib.read_state(i) for i in range(4)] == [4,-1,0,4]


def test_o2_uploaded_app001_links_with_sidecar(tmp_path):
    asm_path=Path('/mnt/data/App001.generated.pe32.asm')
    inc=Path('/mnt/data/App001.generated.pe32.extern.inc')
    if not asm_path.exists() or not inc.exists():
        pytest.skip('uploaded sample unavailable')
    from test_stage605_link import _load_pe_linker
    n=_load_pe_linker();asm=asm_path.read_text(encoding='utf8')
    shutil.copy(inc,tmp_path/inc.name)
    a=n['assemble_pe32_object_source'](optimize_dbase_size_assembly(asm,level='O1').assembly,
        filename=str(tmp_path/asm_path.name),include_dirs=(str(tmp_path),))
    b=n['assemble_pe32_object_source'](optimize_dbase_size_assembly(asm,level='O2').assembly,
        filename=str(tmp_path/asm_path.name),include_dirs=(str(tmp_path),))
    assert len(b.code)<len(a.code)
    link=n['link_coff32_objects'];write=n['write_coff32_object']
    image=link((write(b),),entry_symbol='_start',gui=True).executable
    assert image.startswith(b'MZ')
    assert b.imports['dbaseqtruntimewritetext'][1]=='DBaseQtRuntimeWriteText'

@pytest.mark.parametrize('target', ['pe32', 'pe64'])
def test_o2_linked_programme_object_does_not_rebind(tmp_path, target):
    from test_stage605_link import _load_pe_linker
    from dbase_module_coff import strip_program_entry_assembly, namespace_module_object
    n = _load_pe_linker()
    assemble = n['assemble_pe32_object_source' if target == 'pe32' else 'assemble_pe64_object_source']
    write = n['write_coff32_object' if target == 'pe32' else 'write_coff64_object']
    link = n['link_coff32_inputs' if target == 'pe32' else 'link_coff64_inputs']
    module = compile_dbase_to_assembly('x = 1\n', target=target).assembly
    programme = compile_dbase_to_assembly('? "aus Programm"\n', target=target).assembly
    main_asm = optimize_dbase_size_assembly(module, level='O2').assembly
    extra_asm = optimize_dbase_size_assembly(programme, level='O2').assembly
    assert main_asm.count('call DBaseQtBindOutputState') == 2
    extra_asm = strip_program_entry_assembly(extra_asm)
    assert 'call DBaseQtBindOutputState' not in extra_asm
    # In ordinary Programme objects, top-level execution is correctly stripped.
    assert 'call DBaseQtRuntimeWriteText' not in extra_asm
    sources = (tmp_path/'App001.o', tmp_path/'Utility.o')
    sources[0].write_bytes(write(assemble(main_asm)))
    sources[1].write_bytes(write(namespace_module_object(assemble(extra_asm), tmp_path/'Utility.prg')))
    result = link(sources, entry_symbol='_start', gui=True)
    assert result.executable[:2] == b'MZ'


def test_real_project_ini_o2_roundtrip_via_existing_writer_reader_fragments():
    import configparser
    from dbase_size_optimizer import normalize_dbase_optimization_level
    src=(ROOT/'d64_dism.py').read_text('utf8')
    start=src.index('        parser[_settings["dbase_optimization_section"]] = {')
    end=src.index('        parser[_settings["prolog_optimization_section"]] = {',start)
    writer=src[start:end]
    start=src.index('        _dbase_optimization_section = _settings["dbase_optimization_section"]')
    end=src.index('        _prolog_optimization_section = _settings["prolog_optimization_section"]',start)
    reader=src[start:end]
    settings={a:{'title':b,'dbase_optimization_section':f'Settings.Windows.{b}.Compiler.dBASE.Optimierung',
                 'dbase_size_level_key':f'size_{a}', **{key:f'opt_{a}_{key}' for key in (
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
    parser=configparser.ConfigParser(interpolation=None)
    parser.optionxform=str
    env['write'](parser,{'size_pe32':[{'value':'O2'}],'size_pe64':[{'value':'O1'}]})
    assert parser['Settings.Windows.32Bit.Compiler.dBASE.Optimierung']['OptimizationLevel']=='O2'
    assert parser['Settings.Windows.64Bit.Compiler.dBASE.Optimierung']['OptimizationLevel']=='O1'
    read_back={};env['load'](parser,read_back)
    assert read_back['size_pe32']==[{'value':'O2'}]
    assert read_back['size_pe64']==[{'value':'O1'}]
