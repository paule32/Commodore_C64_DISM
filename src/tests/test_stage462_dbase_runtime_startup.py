"""Stage 462: shared Qt runtime init, format buffer and shutdown for PE32/PE32+."""
from __future__ import annotations

import hashlib
import shutil
import subprocess
from pathlib import Path

import pytest

from d64dbase import compile_dbase_to_assembly
from test_stage446_real_pe_link import linkers
from test_stage460_wfm_typed_slot_optimization import compile_slot_optimized

ROOT = Path(__file__).parent
BRIDGE = (ROOT / 'd64qt5' / 'd64qt5_bridge.cpp').read_text('utf8')
HEADER = (ROOT / 'd64qt5' / 'd64qt5_bridge.h').read_text('utf8')
EXPORTS = (ROOT / 'd64qt5' / 'd64qt5_bridge.def').read_text('utf8')


@pytest.mark.parametrize('target',['pe32','pe64'])
def test_console_real_pe_startup_shutdown(target):
    asm = compile_dbase_to_assembly(
        'SET FORMAT TO CONSOLE\n? "Hallo"\n',target=target
    ).assembly
    assert 'import DBaseQtRuntimeStartup, "libd64_qt5.dll"' in asm
    assert 'import DBaseQtRuntimeShutdown, "libd64_qt5.dll"' in asm
    assert '    call DBaseQtRuntimeStartup' in asm
    assert '    call DBaseQtRuntimeShutdown' in asm
    assert '    call DBaseQtInitialize\n' not in asm
    assert '    call DBaseQtShutdown\n' not in asm
    assert '    call VirtualAlloc\n' not in asm
    assert '    call VirtualFree\n' not in asm
    assert asm.index('call DBaseConsoleShutdown') < asm.index('call DBaseQtRuntimeShutdown')
    assert asm.index('call DBaseQtRuntimeShutdown') < asm.rindex('call ExitProcess')
    if target=='pe64':
        assert '    mov qword ptr [rsp+32], rax\n    call DBaseQtRuntimeStartup' in asm
        assert '    mov rcx, __dbase_format_buffer\n' in asm
    else:
        assert '    push __dbase_format_buffer\n    push 0\n' in asm
        assert '    add esp, 20\n    test eax, eax' in asm
    funcs=linkers()
    obj=funcs[f'assemble_{target}_object_source'](asm)
    bits=32 if target=='pe32' else 64
    coff=funcs[f'write_coff{bits}_object'](obj)
    image=funcs[f'link_coff{bits}_objects']((coff,),entry_symbol='_start',gui=True).executable
    assert image[:2]==b'MZ'
    assert b'DBaseQtRuntimeStartup' in image
    assert b'DBaseQtRuntimeShutdown' in image


@pytest.mark.parametrize('target',['pe32','pe64'])
def test_wfm_real_pe_startup_shutdown(target):
    asm=compile_slot_optimized(target,True,True)
    assert '    call DBaseQtRuntimeStartup' in asm
    assert '    call DBaseQtRuntimeShutdown' in asm
    assert '    call DBaseQtInitializeGui\n' not in asm
    # The explicit WFM entry no longer uses inline allocations. ISKEYBOARD
    # still has its own temporary device-list allocation.
    section=asm.split('__d64_wfm_entry:',1)[1].split('; Stage 133: WFM Event-',1)[0]
    assert '    call VirtualAlloc\n' not in section
    assert '    call VirtualFree\n' not in section
    assert '    mov r9d, 1\n' in section if target=='pe64' else '    push 1\n' in section
    assert '    test eax, eax\n' in section
    funcs=linkers()
    obj=funcs[f'assemble_{target}_object_source'](asm)
    bits=32 if target=='pe32' else 64
    coff=funcs[f'write_coff{bits}_object'](obj)
    image=funcs[f'link_coff{bits}_objects']((coff,),entry_symbol='__d64_wfm_entry',gui=True).executable
    assert image[:2]==b'MZ'
    assert b'DBaseQtRuntimeStartup' in image
    assert b'DBaseQtRuntimeShutdown' in image


@pytest.mark.parametrize('target',['pe32','pe64'])
def test_iskeyboard_keeps_temporary_device_list_allocation(target):
    asm=compile_dbase_to_assembly('? ISKEYBOARD()\n',target=target).assembly
    assert '    call DBaseQtRuntimeStartup' in asm
    assert '    call VirtualAlloc' in asm
    assert '    call VirtualFree' in asm
    assert 'import VirtualAlloc, "kernel32.dll", "VirtualAlloc"' in asm
    assert 'import VirtualFree, "kernel32.dll", "VirtualFree"' in asm
    funcs=linkers()
    obj=funcs[f'assemble_{target}_object_source'](asm)
    bits=32 if target=='pe32' else 64
    coff=funcs[f'write_coff{bits}_object'](obj)
    result=funcs[f'link_coff{bits}_objects']((coff,),entry_symbol='_start',gui=True)
    assert result.executable[:2]==b'MZ'

def test_runtime_header_exports_and_fixed_ordinal_hash():
    from d64qt5 import generate_runtime_abi
    assert 'void **formatBuffer' in HEADER
    assert 'DBaseQtRuntimeStartup @1011' in EXPORTS
    assert 'DBaseQtRuntimeShutdown @1012' in EXPORTS
    rows=generate_runtime_abi.read_exports()
    assert len(rows)==78
    optional={
        'DBaseQtFormApplyExternalUi','DBaseUtf8Substring',
        'DBaseUtf8SubstringUpper','DBaseUtf8SubstringLower',
        'DBaseUtf8Upper','DBaseUtf8Lower',
        'DBaseQtRuntimeStartup','DBaseQtRuntimeShutdown',
        'DBaseQtWfmModalParameter','DBaseQtFormRun'
    }
    core=[(o,n) for o,n in rows if not n.startswith('DBaseQtProlog') and n not in optional]
    assert len(core)==64
    digest=hashlib.sha256(''.join(f'{o}:{n}\n' for o,n in core).encode()).hexdigest()
    assert digest=='02c94324ebc9e8373c08011d0f8c5ba5aec95b158087092ed4e741877b1a7cd7'


def test_bridge_native_startup_shutdown_failure_and_order(tmp_path):
    """Compile unchanged C++ implementation bodies with mocked Qt API."""
    compiler=shutil.which('g++')
    if not compiler:
        pytest.skip('g++ not installed')
    start=BRIDGE.index('extern "C" D64QT5_API int DBaseQtRuntimeStartup(')
    end=BRIDGE.index('extern "C" D64QT5_API void DBaseQtShowWindow(',start)
    startup=BRIDGE[start:end]
    shutdown=BRIDGE[BRIDGE.rindex('extern "C" D64QT5_API void DBaseQtRuntimeShutdown('):]
    preamble=r'''
#include <cassert>
#include <cstdlib>
#define D64QT5_API
static int mode = -1, theme = -1, kind = -1;
static int shutdown_count = 0;
static bool fail_init = false;
extern "C" void DBaseQtSetWorkstationMode(int x) {mode = x;}
extern "C" void DBaseQtSetDebugTheme(int x) {theme = x;}
extern "C" int DBaseQtInitialize(const char *) {kind = 0; return fail_init ? 0 : 1;}
extern "C" int DBaseQtInitializeGui(const char *) {kind = 1; return fail_init ? 0 : 1;}
extern "C" void DBaseQtShutdown() {assert(!shutdown_count || kind >= 0); ++shutdown_count;}
'''
    main=r'''
int main() {
  assert(!DBaseQtRuntimeStartup("x",0,0,0,nullptr));
  void* ptr=reinterpret_cast<void*>(1);
  fail_init=true;
  assert(!DBaseQtRuntimeStartup("x",0,2,1,&ptr));
  assert(ptr==nullptr);
  assert(kind==1 && theme==2);
  fail_init=false;
  assert(DBaseQtRuntimeStartup("console",0,1,0,&ptr));
  assert(ptr!=nullptr && kind==0 && theme==1 && mode==0);
  auto* bytes=reinterpret_cast<unsigned char*>(ptr);
  for(int i=0;i<96;++i) assert(bytes[i]==0);
  bytes[95]=37;
  DBaseQtRuntimeShutdown(&ptr);
  assert(ptr==nullptr && shutdown_count==1);
  assert(DBaseQtRuntimeStartup("gui",1,2,1,&ptr));
  assert(ptr!=nullptr && mode==1 && theme==2 && kind==1);
  DBaseQtRuntimeShutdown(&ptr);
  assert(ptr==nullptr && shutdown_count==2);
  return 0;
}
'''
    source=tmp_path/'runtime462.cpp'
    source.write_text(preamble+startup+shutdown+main)
    exe=tmp_path/'runtime462'
    compile_result=subprocess.run([compiler,'-std=c++17','-Wall','-Wextra','-Werror',str(source),'-o',str(exe)],capture_output=True,text=True)
    assert compile_result.returncode==0, compile_result.stderr
    run=subprocess.run([str(exe)],capture_output=True,text=True)
    assert run.returncode==0,run.stderr
