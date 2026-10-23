"""Stage 487: tests for the bounded Linux dBASE and Qt5/WFM ELF bridge."""
from __future__ import annotations

import os
import platform
from pathlib import Path
import struct
import subprocess
import sys

import pytest

from d64dbase.linux_frontend import LinuxDBaseError, compile_linux_prg, compile_linux_wfm
from linux_elf import assemble_linux_elf
from test_stage446_real_pe_link import linkers


WFM = '''CLASS Form1 OF FORM
THIS.Caption = "Hallo Linux"
THIS.Width = 500
THIS.Height = 240
THIS.Button1 = NEW BUTTON()
THIS.Button1.Text = "Klicken"
THIS.Button1.OnClick = CLASS::OnClick1
PROCEDURE OnClick1()
    ? "Klick aus dBASE!"
    RETURN
ENDCLASS
'''

@pytest.fixture(scope='module')
def asm():
    return linkers()


def build(source, bits, asm, file):
    return assemble_linux_elf(source, bits=bits, filename=file,
                              assembler32=asm['assemble_pe32_object_source'],
                              assembler64=asm['assemble_pe64_object_source'])


@pytest.mark.parametrize('bits', [32, 64])
def test_prg_generates_real_elf_and_relocatable_object(asm, bits):
    gen = compile_linux_prg('#define TEXT "Hallo"\n? TEXT\n?? " Linux"\n', bits=bits, filename='demo.prg')
    obj, exe = build(gen.assembly, bits, asm, 'demo.asm')
    assert obj[:4] == exe[:4] == b'\x7fELF'
    assert struct.unpack_from('<H', obj, 16)[0] == 1
    assert struct.unpack_from('<H', exe, 16)[0] == 2
    assert b'Hallo\n Linux' in exe


def test_prg_elf64_real_execution(asm, tmp_path):
    if platform.machine().lower() not in ('x86_64','amd64') or sys.platform != 'linux':
        pytest.skip('native Linux x86-64 only')
    gen = compile_linux_prg('LOCAL A = 2 + 3*4\n? A\n? "Ende"\n', bits=64, filename='demo.prg')
    obj, exe = build(gen.assembly, 64, asm, 'demo.asm')
    binary = tmp_path/'demo.elf64'; binary.write_bytes(exe); binary.chmod(0o755)
    result = subprocess.run([str(binary)], capture_output=True, timeout=4)
    assert result.returncode == 0
    assert result.stdout == b'14\nEnde\n'


@pytest.mark.parametrize('bits', [32,64])
def test_wfm_elf_imports_native_qt5_runtime(asm,bits):
    result=compile_linux_wfm(WFM,bits=bits,filename='Form1.wfm')
    assert result.source_kind=='form'
    assert 'DBaseQtRunFormJson' in result.assembly
    assert 'PyQt5.QtWidgets' not in result.assembly
    obj,exe=assemble_linux_elf(result.assembly,bits=bits,filename='Form1.generated.asm',
        assembler32=asm['assemble_pe32_object_source'],
        assembler64=asm['assemble_pe64_object_source'],
        shared_library='libd64_qt5.so',imported_symbols=('DBaseQtRunFormJson',))
    assert b'libd64_qt5.so' in exe
    assert b'DBaseQtRunFormJson' in exe
    assert b'Klick aus dBASE!' in exe
    assert b'.rel' in obj


def test_qt_wfm_elf64_calls_real_dynamic_shared_library(asm,tmp_path):
    if platform.machine().lower() not in ('x86_64','amd64') or sys.platform!='linux':
        pytest.skip('native Linux x86-64 only')
    import shutil
    if shutil.which('gcc') is None:
        pytest.skip('GCC required for a temporary ABI test library')
    shared=tmp_path/'libd64_qt5.so'
    mock=tmp_path/'abi_test.c'
    mock.write_text("""#include <stdio.h>
int DBaseQtRunFormJson(const char *text) {
    puts("Native-Qt5-ABI-Test"); fflush(stdout); return text ? 42 : 1;
}
""",encoding='utf8')
    subprocess.run(['gcc','-fPIC','-shared','-o',str(shared),str(mock)],check=True)
    gen=compile_linux_wfm(WFM,bits=64,filename='Form1.wfm')
    _,exe=assemble_linux_elf(gen.assembly,bits=64,filename='Form1.asm',
        assembler32=asm['assemble_pe32_object_source'],
        assembler64=asm['assemble_pe64_object_source'],
        shared_library='libd64_qt5.so',imported_symbols=('DBaseQtRunFormJson',))
    binary=tmp_path/'form.elf64'; binary.write_bytes(exe); binary.chmod(0o755)
    run=subprocess.run([str(binary)],capture_output=True,timeout=6)
    assert run.returncode==42,run.stderr.decode(errors='replace')
    assert b'Native-Qt5-ABI-Test' in run.stdout


def test_unsupported_prg_fails_explicitly():
    with pytest.raises(LinuxDBaseError,match='nicht unterstuetzt'):
        compile_linux_prg('DO WHILE .T.\n? "Text"\nENDDO\n',bits=64,filename='bad.prg')


def test_unknown_control_is_rejected():
    source='CLASS Form1 OF FORM\nTHIS.Map1 = NEW WEBVIEW()\nENDCLASS\n'
    with pytest.raises(LinuxDBaseError,match='Steuerelement'):
        compile_linux_wfm(source,bits=64,filename='bad.wfm')


def test_unimplemented_event_is_rejected():
    source=WFM.replace('    ? "Klick aus dBASE!"','    IF 1 == 1')
    with pytest.raises(LinuxDBaseError,match='noch nicht implementiert'):
        compile_linux_wfm(source,bits=64,filename='bad.wfm')


def test_linux_wfm_does_not_silently_import_windows_dll():
    source='extern CINT Foo() user32 from "Foo"\nCLASS Form1 OF FORM\nENDCLASS\n'
    with pytest.raises(LinuxDBaseError,match='Windows-DLL'):
        compile_linux_wfm(source,bits=64,filename='bad.wfm')


def test_gui_integration_and_start_mode_present():
    source=Path(__file__).with_name('d64_dism.py').read_text(encoding='utf8')
    assert 'target_combo.addItem("Linux Ubuntu 22.04 32-Bit", "linux32")' in source
    assert 'target_combo.addItem("Linux Ubuntu 22.04 64-Bit", "linux64")' in source
    assert 'from d64dbase.linux_frontend import compile_linux_wfm' in source
    assert 'from d64dbase.linux_frontend import LinuxDBaseError, compile_linux_prg' in source
    assert 'document.build_target in {"pe32", "pe64", "linux32", "linux64"}' in source
    assert 'if document.build_target in {"pe32", "pe64"}:\n                if not self._prepare_dbase_form_runtime' in source
