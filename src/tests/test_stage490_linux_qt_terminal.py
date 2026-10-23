"""Stage 490: Linux dBASE console and WFM native Qt5 terminal contracts."""
import json
import os
import platform
import shutil
import subprocess
from pathlib import Path

import pytest
from d64dbase.linux_frontend import compile_linux_prg, compile_linux_wfm, LinuxDBaseError
from linux_elf import assemble_linux_elf
from test_stage446_real_pe_link import linkers

ROOT = Path(__file__).parent


def decode_embedded_json(source: str, label: str):
    fragment = source.split(label + ':\n',1)[1]
    parts=[]
    for line in fragment.splitlines():
        stripped=line.strip()
        if not stripped.startswith('db '): break
        parts.extend(int(number) for number in stripped[3:].split(', '))
    return json.loads(bytes(parts).rstrip(b'\0').decode('utf-8'))


def test_console_output_type_vartype_and_print_semantics():
    src='''? "Hallo"\n?? " dBASE"\nLOCAL xyz=42\n? TYPE("xyz") && N\n? VARTYPE("xyz") && C\n'''
    result=compile_linux_prg(src,bits=64,filename='Beispiel.prg',qt_terminal=True)
    assert 'DBaseQtRunConsoleJson' in result.assembly
    output=decode_embedded_json(result.assembly,'__linux_console_json')
    assert output['output']==['Hallo\n',' dBASE','N\n','C\n']
    assert output['title'].endswith('Beispiel.prg')


def test_wfm_preamble_and_event_both_use_qt_terminal():
    src='''#define user32 "user32.dll"\nextern CINT MessageBoxA(HWND,LPCSTR,LPCSTR,UINT) user32 from "MessageBoxA"\n? "Hallo"\n? TYPE("xyz") && U\nCLASS Form1 OF FORM\nTHIS.Caption="Form"\nTHIS.Button1=NEW BUTTON()\nTHIS.Button1.Text="OK"\nTHIS.Button1.OnClick=CLASS::click1\nPROCEDURE click1()\n? "Event"\nRETURN\nENDCLASS\n'''
    result=compile_linux_wfm(src,bits=64,filename='Form1.wfm')
    output=decode_embedded_json(result.assembly,'__linux_wfm_json')
    assert output['startup_output']==['Hallo\n','U\n']
    assert output['methods']['click1']==[['print','Event',True]]
    assert 'DBaseQtRunFormJson' in result.assembly
    assert any('ungenutzte Windows-DLL' in item for item in result.warnings)


def test_windows_ffi_call_still_rejected():
    src='''#define shell32 "shell32.dll"\nextern CINT Foo() shell32 from "Foo"\n? Foo()\nCLASS Form1 OF FORM\nENDCLASS\n'''
    with pytest.raises(LinuxDBaseError,match='Windows-DLL-Aufruf'):
        compile_linux_wfm(src,bits=64,filename='Form1.wfm')


@pytest.mark.parametrize('bits', [32,64])
def test_elf_imports_native_qt_console(bits):
    asm=linkers()
    result=compile_linux_prg('? "Hallo Qt"',bits=bits,filename='main.prg',qt_terminal=True)
    obj, elf=assemble_linux_elf(result.assembly,bits=bits,filename='main.asm',
        assembler32=asm['assemble_pe32_object_source'],
        assembler64=asm['assemble_pe64_object_source'],
        shared_library='libd64_qt5.so', imported_symbols=('DBaseQtRunConsoleJson',))
    assert obj.startswith(b'\x7fELF') and elf.startswith(b'\x7fELF')
    assert b'DBaseQtRunConsoleJson\x00' in elf
    assert b'libd64_qt5.so\x00' in elf


def test_linux_build_only_native_qt_source():
    pro=(ROOT/'d64qt5/d64qt5_bridge.pro').read_text(encoding='utf-8')
    cpp=(ROOT/'d64qt5/d64qt5_linux_form.cpp').read_text(encoding='utf-8')
    gui=(ROOT/'d64_dism.py').read_text(encoding='utf-8')
    assert 'SOURCES = d64qt5_linux_form.cpp' in pro
    assert 'class DBaseTerminalDialog final : public QDialog' in cpp
    assert 'QPlainTextEdit' in cpp
    assert 'DBaseQtRunConsoleJson' in cpp
    assert 'startup_output' in cpp
    assert 'DBaseQtRunConsoleJson' in gui


def test_elf64_runs_real_dynamic_shared_library(tmp_path):
    if platform.system()!='Linux' or platform.machine().lower() not in ('x86_64','amd64'):
        pytest.skip('Linux x86-64 required')
    if not shutil.which('gcc'):
        pytest.skip('gcc required for a C-ABI shim')
    c=tmp_path/'abi.c'
    c.write_text('''#include <stdio.h>
#include <string.h>
int DBaseQtRunConsoleJson(const char *p) {
   puts(p && strstr(p, "Hallo Qt5") ? "Qt5-Terminal-ABI-OK" : "ERROR");
   fflush(stdout); return p && strstr(p,"Hallo Qt5") ? 29 : 2;
}''')
    subprocess.run(['gcc','-shared','-fPIC','-o',str(tmp_path/'libd64_qt5.so'),str(c)],check=True)
    asm=linkers()
    generated=compile_linux_prg('? "Hallo Qt5"',bits=64,filename='Main.prg',qt_terminal=True)
    _obj, exe=assemble_linux_elf(generated.assembly,bits=64,filename='Main.asm',
        assembler32=asm['assemble_pe32_object_source'],
        assembler64=asm['assemble_pe64_object_source'],
        shared_library='libd64_qt5.so', imported_symbols=('DBaseQtRunConsoleJson',))
    output=tmp_path/'Main.elf64';output.write_bytes(exe);output.chmod(0o755)
    result=subprocess.run([str(output)],capture_output=True,timeout=8)
    assert result.returncode==29, result.stderr.decode(errors='replace')
    assert b'Qt5-Terminal-ABI-OK' in result.stdout

def test_windows_runtime_qt_terminal_preserves_debug_and_existing_console():
    cpp=(ROOT/'d64qt5/d64qt5_bridge.cpp').read_text(encoding='utf-8')
    assert 'append_dbase_qt_terminal(const QString &text, bool newline)' in cpp
    assert 'new QDialog(nullptr)' in cpp
    assert 'new QPlainTextEdit(g_dbase_qt_terminal_dialog)' in cpp
    assert 'if (g_debug_visible) append_wfm_output' in cpp
    assert 'append_dbase_qt_terminal(value, newline != 0);' in cpp
    assert 'delete g_dbase_qt_terminal_dialog;' in cpp
