# -*- coding: utf-8 -*-
"""Stage 673: O1 runtime output dispatcher moved from ASM to Qt5 DLL."""
from __future__ import annotations
from pathlib import Path
import re
import shutil
import subprocess
import ctypes
import hashlib

import pytest
from d64dbase import compile_dbase_to_assembly
from dbase_size_optimizer import optimize_dbase_size_assembly

ROOT = Path(__file__).parent
SOURCE = '? "one"\n? "two"\n? "three"\n'

@pytest.mark.parametrize('target',('pe32','pe64'))
def test_o0_remains_byte_identical_and_o1_imports_shared_export(target):
    asm=compile_dbase_to_assembly(SOURCE, target=target).assembly
    assert optimize_dbase_size_assembly(asm, level='O0').assembly == asm
    out=optimize_dbase_size_assembly(asm, level='O1').assembly
    assert 'call __dbase_o1_output_write' not in out
    assert '__dbase_o1_output_write:' not in out
    assert 'call DBaseQtRuntimeWrite' in out
    assert out.count('import DBaseQtRuntimeWrite, "libd64_qt5.dll", "DBaseQtRuntimeWrite"') == 1
    assert out.count('\n') == asm.count('\n') + 2
    assert optimize_dbase_size_assembly(out, level='O1').assembly == out
    if target=='pe32':
        assert 'push __dbase_output_debug_visible' in out
        assert 'add esp, 20' in out
    else:
        assert 'mov r8d, dword ptr [__dbase_output_debug_override]' in out
        assert 'mov r9d, dword ptr [__dbase_output_format_screen]' in out
        assert 'mov qword ptr [rsp+32], rax' in out


def test_new_export_does_not_change_original_runtime_abi_hash():
    header=(ROOT/'d64qt5/d64qt5_bridge.h').read_text()
    src=(ROOT/'d64qt5/d64qt5_bridge.cpp').read_text()
    entries=re.findall(r'^\s*(\w+)\s+@(\d+)',(ROOT/'d64qt5/d64qt5_bridge.def').read_text(),re.M)
    assert ('DBaseQtRuntimeWrite','1019') in entries
    assert all(sum(int(x==ordinal) for _,x in entries)==1 for _,ordinal in entries)
    assert 'DBaseQtRuntimeWrite(const char *text, int length' in header
    assert 'DBaseConsoleWrite(text, length);' in src
    core=sorted((int(o),n) for n,o in entries if 1 <= int(o) <= 64)
    digest=hashlib.sha256(''.join(f'{o}:{n}\n' for o,n in core).encode()).digest()
    orig=__import__('zipfile').ZipFile('/mnt/data/d64_dism_stage672.zip').read('d64qt5/d64_runtime_abi.inc').decode()
    current=(ROOT/'d64qt5/d64_runtime_abi.inc').read_text()
    assert current == orig
    assert digest.hex() == '02c94324ebc9e8373c08011d0f8c5ba5aec95b158087092ed4e741877b1a7cd7'


def test_actual_native_dispatch_order_and_console_contract(tmp_path):
    if not shutil.which('g++'):
        pytest.skip('C++ compiler is unavailable')
    src=(ROOT/'d64qt5/d64qt5_bridge.cpp').read_text()
    begin=src.index('extern "C" D64QT5_API void DBaseQtRuntimeWrite(')
    end=src.index('extern "C" D64QT5_API int DBaseQtSetColorNormal',begin)
    function=src[begin:end]
    # The real function body is compiled with a minimal fake Windows API,
    # making the Win32 DLL delegation observable without Qt or Windows.
    harness=r'''
#include <cstring>
#include <cstdint>
#define _WIN32
#define __cdecl
#define D64QT5_API
using HMODULE=void*;
static int num_console=0, num_qtconsole=0, num_debug=0, num_visible=0;
static int show_order=0, debug_order=0, state_at_show=0;
static int *state_ptr=nullptr;
extern "C" void DBaseConsoleWrite(const char*,int) { ++num_console; }
extern "C" void DBaseQtSetDebugVisible(int on) {
  ++num_visible; show_order=1;
  if(on && state_ptr) state_at_show=*state_ptr;
}
extern "C" void DBaseQtAppendDebug(const char*,int) { ++num_debug; debug_order=show_order==1 ? 2 : -1; }
extern "C" void DBaseQtAppendConsole(const char*,int) { ++num_qtconsole; }
'''
    harness += '\nextern "C" void DBaseConsoleWrite(const char*,int);\n'
    harness += function
    harness += r'''
extern "C" void init_state(int *ptr) { state_ptr=ptr; }
extern "C" int get_counter(int which) {
 switch(which){case 0:return num_console;case 1:return num_qtconsole;
 case 2:return num_debug;case 3:return num_visible;
 case 4:return state_at_show;case 5:return debug_order;default:return -1;}
}
'''
    cpp=tmp_path/'dispatch.cpp';cpp.write_text(harness)
    dll=tmp_path/'libdispatch.so'
    subprocess.run(['g++','-std=c++20','-fPIC','-shared',str(cpp),'-o',str(dll)],check=True,capture_output=True,text=True)
    lib=ctypes.CDLL(str(dll))
    lib.init_state.argtypes=[ctypes.POINTER(ctypes.c_int)]
    lib.DBaseQtRuntimeWrite.argtypes=[ctypes.c_char_p,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.POINTER(ctypes.c_int)]
    lib.get_counter.argtypes=[ctypes.c_int];lib.get_counter.restype=ctypes.c_int
    flag=ctypes.c_int(0);lib.init_state(ctypes.byref(flag))
    write=lambda override,fmt,length=3:lib.DBaseQtRuntimeWrite(b'abc',length,override,fmt,ctypes.byref(flag))
    write(-1,0,0)  # even an empty console output must initialize lazy console
    assert lib.get_counter(0)==1 and lib.get_counter(1)==0 and flag.value==0
    write(-1,1)
    assert (lib.get_counter(2),lib.get_counter(3),lib.get_counter(4),lib.get_counter(5))==(1,1,1,2)
    write(-1,1)
    assert lib.get_counter(2)==2 and lib.get_counter(3)==1
    write(0,1)
    assert lib.get_counter(0)==2
    write(1,0)
    assert lib.get_counter(2)==3

@pytest.mark.parametrize('target',('pe32','pe64'))
def test_generated_objects_link_with_new_import(target):
    from test_stage605_link import _load_pe_linker
    n=_load_pe_linker()
    asm=compile_dbase_to_assembly(SOURCE,target=target).assembly
    opt=optimize_dbase_size_assembly(asm,level='O1').assembly
    assemble=n['assemble_pe32_object_source' if target=='pe32' else 'assemble_pe64_object_source']
    coff=n['write_coff32_object' if target=='pe32' else 'write_coff64_object']
    link=n['link_coff32_objects' if target=='pe32' else 'link_coff64_objects']
    first=assemble(asm); second=assemble(opt)
    assert len(second.code) < len(first.code)
    assert second.imports['dbaseqtruntimewrite'] == ('libd64_qt5.dll', 'DBaseQtRuntimeWrite')
    output=link((coff(second),), entry_symbol='_start',gui=True)
    assert output.executable[:2]==b'MZ'
