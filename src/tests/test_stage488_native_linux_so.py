"""Stage 488 ELF DT_NEEDED native Qt5 loader regression tests."""
from __future__ import annotations
import os
import platform
import shutil
import subprocess
import struct
from pathlib import Path

import pytest
from test_stage446_real_pe_link import linkers
from d64dbase.linux_frontend import compile_linux_wfm
from linux_elf import assemble_linux_elf, LinuxELFError

SRC='''CLASS Form1 OF FORM
THIS.Caption = "Native WFM"
THIS.Button1 = NEW BUTTON()
THIS.Button1.Text = "OK"
THIS.Button1.OnClick = CLASS::OnClick1
PROCEDURE OnClick1()
    ? "OnClick"
    RETURN
ENDCLASS
'''

@pytest.fixture(scope='module')
def asm(): return linkers()

@pytest.mark.parametrize('bits', (32,64))
def test_native_elf_import_table_and_json(asm,bits,tmp_path):
    generated=compile_linux_wfm(SRC,bits=bits,filename='Form1.wfm')
    assert 'DBaseQtRunFormJson' in generated.assembly
    assert 'python3' not in generated.assembly
    obj,exe=assemble_linux_elf(generated.assembly,bits=bits,filename='Form1.asm',
        assembler32=asm['assemble_pe32_object_source'],
        assembler64=asm['assemble_pe64_object_source'],
        shared_library='libd64_qt5.so',imported_symbols=('DBaseQtRunFormJson',))
    assert obj.startswith(b'\x7fELF') and exe.startswith(b'\x7fELF')
    assert b'libd64_qt5.so\0' in exe
    assert b'DBaseQtRunFormJson\0' in exe
    assert b'$ORIGIN\0' in exe
    assert b'Native WFM' in exe
    if shutil.which('readelf'):
        sample=tmp_path/f'dynamic{bits}.elf'
        sample.write_bytes(exe)
        info=subprocess.check_output(['readelf','-d',str(sample)])
        assert b'NEEDED' in info and b'RUNPATH' in info

@pytest.mark.parametrize('bits', (32,64))
def test_att_mode_wfm_linux(asm,bits):
    from windows_asm_att import intel_to_att
    gen=compile_linux_wfm(SRC,bits=bits,filename='Form1.wfm')
    att=intel_to_att(gen.assembly,target='pe32' if bits==32 else 'pe64')
    _,binary=assemble_linux_elf(att,bits=bits,filename='Form1.asm',
        assembler32=asm['assemble_pe32_object_source'],
        assembler64=asm['assemble_pe64_object_source'],
        shared_library='libd64_qt5.so',imported_symbols=('DBaseQtRunFormJson',))
    assert binary.startswith(b'\x7fELF')

@pytest.mark.parametrize('bits', (32,64))
def test_missing_shared_import_refuses_silent_link(asm,bits):
    gen=compile_linux_wfm(SRC,bits=bits,filename='Form1.wfm')
    with pytest.raises(LinuxELFError, match='Ungeloestes'):
        assemble_linux_elf(gen.assembly,bits=bits,filename='Form1.asm',
            assembler32=asm['assemble_pe32_object_source'],
            assembler64=asm['assemble_pe64_object_source'])

def test_full_elf64_native_dynamic_invocation(asm,tmp_path):
    if platform.system()!='Linux' or platform.machine() not in ('x86_64','amd64'):
        pytest.skip('Linux x86-64 only')
    if shutil.which('gcc') is None:
        pytest.skip('gcc not installed')
    c=tmp_path/'runtime_abi.c'
    c.write_text('''#include <stdio.h>
int DBaseQtRunFormJson(const char *s) {
    puts("Loaded native d64_qt5.so"); fflush(stdout);
    return s && s[0] == '{' ? 42 : 2;
}''',encoding='utf-8')
    subprocess.run(['gcc','-shared','-fPIC','-o',str(tmp_path/'libd64_qt5.so'),str(c)],check=True)
    gen=compile_linux_wfm(SRC,bits=64,filename='Form1.wfm')
    _,exe=assemble_linux_elf(gen.assembly,bits=64,filename='Form1.asm',
        assembler32=asm['assemble_pe32_object_source'],
        assembler64=asm['assemble_pe64_object_source'],
        shared_library='libd64_qt5.so',imported_symbols=('DBaseQtRunFormJson',))
    f=tmp_path/'Form1.elf64';f.write_bytes(exe);f.chmod(0o755)
    outcome=subprocess.run([str(f)],capture_output=True,timeout=8)
    assert outcome.returncode==42, outcome.stderr.decode(errors='replace')
    assert b'Loaded native d64_qt5.so' in outcome.stdout


def test_qt5_native_project_bridge_source():
    root=Path(__file__).parent
    project=(root/'d64qt5'/'d64qt5_bridge.pro').read_text(encoding='utf-8')
    header=(root/'d64qt5'/'d64qt5_bridge.h').read_text(encoding='utf-8')
    implementation=(root/'d64qt5'/'d64qt5_linux_form.cpp').read_text(encoding='utf-8')
    gui=(root/'d64_dism.py').read_text(encoding='utf-8')
    assert 'd64qt5_linux_form.cpp' in project
    assert 'DBaseQtRunFormJson(const char *utf8Json)' in header
    assert 'extern "C" D64QT5_API int DBaseQtRunFormJson' in implementation
    assert '_prepare_linux_form_runtime' in gui
    assert 'shared_library=("libd64_qt5.so" if' in gui
    assert 'return False\n' in gui
