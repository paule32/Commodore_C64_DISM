# -*- coding: utf-8 -*-
"""Stage 675: combine the former Pascal console DLL with libd64_qt5.dll."""
from __future__ import annotations
import ctypes
import hashlib
from pathlib import Path
import re
import shutil
import subprocess

import pytest
from pascal_console_dependencies import (
    CONSOLE_DLL, LEGACY_CONSOLE_DLL, manifest_dlls_and_console_symbols,
    obsolete_console_dependencies, console_library_candidates,
    required_console_exports,
)

ROOT = Path(__file__).resolve().parent
EXPORTS = ('d64_console_init','d64_console_restore','d64_console_write_text',
           'd64_console_write_int','d64_console_write_double',
           'd64_console_write_char','d64_console_newline','d64_console_clear',
           'd64_console_read_line','d64_console_read_int','d64_console_read_string')


def test_qt5_project_compiles_embedded_console_implementation():
    pro = (ROOT/'d64qt5/d64qt5_bridge.pro').read_text()
    src = (ROOT/'d64qt5/d64_pascal_console.cpp').read_text()
    header = (ROOT/'d64qt5/d64qt5_bridge.h').read_text()
    assert 'SOURCES += d64_pascal_console.cpp' in pro
    assert '#include "d64qt5_bridge.h"' in src
    for symbol in EXPORTS:
        assert re.search(r'\b'+symbol+r'\s*\(',src)
        assert re.search(r'\b'+symbol+r'\s*\(',header)
    assert 'd64_console_read_string' in src and '_jit_malloc(1024)' in src
    assert 'libd64_console.dll' not in (ROOT/'c64pascal/compiler.py').read_text()
    assert '"libd64_qt5.dll", "{export}"' in (ROOT/'c64pascal/compiler.py').read_text()
    # Historical build scripts must no longer create the obsolete DLL.
    for arch in ('win32','win64'):
        script=(ROOT/f'runtime/compiler/build.console.{arch}.sh').read_text()
        assert 'exec bash' in script and 'd64qt5/build.sh' in script
        assert '-o win' not in script


def test_new_exports_append_without_changing_original_abi_hash():
    items=re.findall(r'^\s*(\w+)\s+@(\d+)',
                     (ROOT/'d64qt5/d64qt5_bridge.def').read_text(), re.M)
    symbols=dict(items)
    values=[int(num) for _,num in items]
    assert len(values)==len(set(values))
    assert [symbols[s] for s in EXPORTS] == [str(1022+i) for i in range(11)]
    for label,ordinal in [('DBaseQtRuntimeWrite','1019'),
                          ('DBaseQtBindOutputState','1020'),
                          ('DBaseQtRuntimeWriteText','1021')]:
        assert symbols[label]==ordinal
    core=sorted((int(num),name) for name,num in items if int(num)<=64)
    digest=hashlib.sha256(''.join(f'{num}:{name}\n' for num,name in core).encode()).hexdigest()
    assert digest=='02c94324ebc9e8373c08011d0f8c5ba5aec95b158087092ed4e741877b1a7cd7'


def test_dependency_detection_is_qt_only_and_finds_old_objects(tmp_path):
    manifest={'imports':[
        {'dll':'libd64_qt5.dll','member':'d64_console_write_text'},
        {'dll':'libd64_qt5.dll','member':'DBaseQtRuntimeWriteText'},
        {'dll':'kernel32.dll','member':'ExitProcess'}]}
    assert CONSOLE_DLL=='libd64_qt5.dll'
    assert manifest_dlls_and_console_symbols(manifest)[1] == {'d64_console_write_text'}
    assert required_console_exports(tmp_path/'prog.exe',manifest) == {'d64_console_write_text'}
    assert obsolete_console_dependencies(tmp_path/'prog.exe',manifest) == set()
    old={'imports':[{'dll':LEGACY_CONSOLE_DLL,'member':'d64_console_write_int'}]}
    assert obsolete_console_dependencies(tmp_path/'prog.exe',old) == {LEGACY_CONSOLE_DLL}
    roots=console_library_candidates(tmp_path/'prog.exe','pe32',program_root=ROOT)
    assert any(str(p).endswith('d64qt5/release/libd64_qt5.dll') for p in roots)
    assert all(p.name==CONSOLE_DLL for p in roots)


def test_pascal_pe32_pe64_import_names_both_redirected():
    src=(ROOT/'c64pascal/compiler.py').read_text()
    assert src.count('f\'import {symbol}, "libd64_qt5.dll", "{export}"\'')==2
    assert '_d64_console_read_string' in src
    assert '_d64_console_read_int' in src
    assert 'import _jit_free' in src
    gui=(ROOT/'d64_dism.py').read_text()
    assert 'obsolete_console_dependencies(' in gui
    assert '"libd64_qt5.dll",' in gui
    assert 'Keine libd64_qt5.dll mit Pascal-Konsolenexports' in gui


@pytest.mark.parametrize('target',('pe32','pe64'))
def test_real_coff_and_pe_import_only_qt5(target,tmp_path):
    from test_stage605_link import _load_pe_linker
    from pascal_console_dependencies import inspect_pe
    native=_load_pe_linker()
    source=('bits 32\n' if target=='pe32' else 'bits 64\n')+'''import _d64_console_init, "libd64_qt5.dll", "d64_console_init"
import _d64_console_newline, "libd64_qt5.dll", "d64_console_newline"
section .text
global _start
entry _start
_start:
    call _d64_console_init
    call _d64_console_newline
    ret
'''
    assemble=native['assemble_pe32_object_source' if target=='pe32' else 'assemble_pe64_object_source']
    writer=native['write_coff32_object' if target=='pe32' else 'write_coff64_object']
    link=native['link_coff32_objects' if target=='pe32' else 'link_coff64_objects']
    obj=assemble(source)
    assert obj.imports['_d64_console_init']==('libd64_qt5.dll','d64_console_init')
    linked=link((writer(obj),),entry_symbol='_start',gui=True)
    pe=tmp_path/'test.exe';pe.write_bytes(linked.executable)
    machine,imports,_exports=inspect_pe(pe)
    assert machine==(0x14c if target=='pe32' else 0x8664)
    assert 'libd64_console.dll' not in imports
    assert {'d64_console_init','d64_console_newline'} <= imports['libd64_qt5.dll']


@pytest.mark.skipif(not shutil.which('g++'), reason='No C++ compiler')
def test_actual_merged_native_console_implementation(tmp_path):
    """Compile the actual new C++ file with minimal mocked Win32 calls."""
    stub=tmp_path/'windows.h'
    stub.write_text(r'''#pragma once
#include <cstdint>
#include <cstring>
#include <cstdio>
using HANDLE=void*;
using HWND=void*;
using HMODULE=void*;
using DWORD=unsigned long;
using LONG=long;
using BOOL=int;
#define INVALID_HANDLE_VALUE ((HANDLE)-1)
#define STD_OUTPUT_HANDLE ((DWORD)-11)
#define STD_INPUT_HANDLE ((DWORD)-10)
#define ENABLE_VIRTUAL_TERMINAL_PROCESSING 4
#define TRUE 1
struct CONSOLE_SCREEN_BUFFER_INFO { int dummy; };
struct SMALL_RECT {short left,top,right,bottom;};
struct COORD {short x,y;};
extern "C" {
void* GetStdHandle(DWORD);
void* GetConsoleWindow();
int AllocConsole();
int FreeConsole();
int GetConsoleScreenBufferInfo(HANDLE,CONSOLE_SCREEN_BUFFER_INFO*);
int GetConsoleMode(HANDLE,DWORD*);
int SetConsoleMode(HANDLE,DWORD);
int SetConsoleWindowInfo(HANDLE,int,const SMALL_RECT*);
int SetConsoleScreenBufferSize(HANDLE,COORD);
LONG InterlockedCompareExchange(volatile LONG*,LONG,LONG);
LONG InterlockedExchange(volatile LONG*,LONG);
void Sleep(DWORD);
int WriteFile(HANDLE,const void*,DWORD,DWORD*,void*);
int ReadFile(HANDLE,void*,DWORD,DWORD*,void*);
HMODULE GetModuleHandleA(const char*);
void* GetProcAddress(HMODULE,const char*);
}
''')
    support=tmp_path/'stub.cpp'
    support.write_text(r'''#include "windows.h"
#include <string>
#include <cstdlib>
static std::string printed;
static unsigned input_index=0;
static std::string input="123\n-42\n";
extern "C" {
void* GetStdHandle(DWORD) {return (void*)2;}
void* GetConsoleWindow(){return (void*)1;}
int AllocConsole(){return 1;}
int FreeConsole(){return 1;}
int GetConsoleScreenBufferInfo(HANDLE,CONSOLE_SCREEN_BUFFER_INFO*){return 1;}
int GetConsoleMode(HANDLE,DWORD*p){*p=0;return 1;}
int SetConsoleMode(HANDLE,DWORD){return 1;}
int SetConsoleWindowInfo(HANDLE,int,const SMALL_RECT*){return 1;}
int SetConsoleScreenBufferSize(HANDLE,COORD){return 1;}
LONG InterlockedCompareExchange(volatile LONG*p,LONG newv,LONG compare){return __sync_val_compare_and_swap(p,compare,newv);}
LONG InterlockedExchange(volatile LONG*p,LONG v){return __sync_lock_test_and_set(p,v);}
void Sleep(DWORD){}
int WriteFile(HANDLE,const void*p,DWORD size,DWORD*out,void*){printed.append((const char*)p,size);*out=size;return 1;}
int ReadFile(HANDLE,void*p,DWORD n,DWORD*out,void*){
  if(input_index>=input.size()){*out=0;return 0;}
  *(char*)p=input[input_index++];*out=1;return 1;
}
HMODULE GetModuleHandleA(const char*){return nullptr;}
void* GetProcAddress(HMODULE,const char*){return nullptr;}
void* _jit_malloc(unsigned size) { return std::malloc(size); }
const char* test_output(){return printed.c_str();}
}
''')
    library=tmp_path/'merged.so'
    cmd=['g++','-std=c++20','-shared','-fPIC','-D_WIN32','-DD64QT5_BRIDGE_EXPORTS',
         '-D__cdecl=', '-D__declspec(x)=', '-I'+str(tmp_path),
         '-I'+str(ROOT/'d64qt5'),str(ROOT/'d64qt5/d64_pascal_console.cpp'),
         str(support), '-o',str(library)]
    subprocess.run(cmd,check=True,capture_output=True,text=True)
    obj=ctypes.CDLL(str(library))
    obj.d64_console_init.restype=ctypes.c_int
    assert obj.d64_console_init()==1
    obj.d64_console_write_text.argtypes=[ctypes.c_char_p]
    obj.d64_console_write_text(b'Hallo ')
    obj.d64_console_write_int.argtypes=[ctypes.c_int]
    obj.d64_console_write_int(42)
    obj.d64_console_newline()
    obj.d64_console_write_double.argtypes=[ctypes.c_double]
    obj.d64_console_write_double(1.25)
    obj.d64_console_write_char.argtypes=[ctypes.c_int]
    obj.d64_console_write_char(ord('!'))
    obj.test_output.restype=ctypes.c_char_p
    assert obj.test_output() == b'Hallo 42\r\n1.25!'
    obj.d64_console_read_int.restype=ctypes.c_int
    assert obj.d64_console_read_int()==123
    assert obj.d64_console_read_int()==-42
    obj.d64_console_restore()
