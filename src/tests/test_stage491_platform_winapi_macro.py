"""Stage 491: target-selected Windows/Linux #defines and limited Qt shell shim."""
import json
from pathlib import Path
import pytest
from d64dbase.compiler import _preprocess_dbase_macros, DBaseCompilerError
from d64dbase.ffi import extract_ffi_prototypes
from d64dbase.ffi_types import ffi_type_info
from d64dbase.linux_frontend import compile_linux_prg, compile_linux_wfm, LinuxDBaseError
from test_stage490_linux_qt_terminal import decode_embedded_json

HEADER = '''#ifdef WINDOWS
#define shell32 "shell32.dll"
#else
#ifdef LINUX
#define shell32 "shell32.so"
#endif
#endif
extern HINSTANCE ShellExecute(HWND, LPCSTR, LPCSTR, LPCSTR, LPCSTR, CINT) shell32 from "ShellExecuteA"
'''
CALL = 'ShellExecute(0, "open", "https://example.com", 0, 0, 1)'

@pytest.mark.parametrize('target,dll,defined,missing', [
    ('pe32','shell32.dll','WINDOWS','LINUX'),
    ('pe64','shell32.dll','WINDOWS','LINUX'),
    ('linux32','shell32.so','LINUX','WINDOWS'),
    ('linux64','shell32.so','LINUX','WINDOWS'),
])
def test_platform_macros_follow_compiler_target(target,dll,defined,missing):
    output,macros,*_= _preprocess_dbase_macros(HEADER,filename='test.h',target=target)
    assert '"'+dll+'"' in output
    names={macro.name for macro in macros}
    assert defined in names and missing not in names


def test_platform_predefines_shared_across_includes(tmp_path):
    (tmp_path/'platform.h').write_text(HEADER,encoding='utf-8')
    source='#include "platform.h"\n? "Hallo"\n'
    code,*_= _preprocess_dbase_macros(source,filename=str(tmp_path/'main.wfm'),target='linux64')
    assert '"shell32.so"' in code and '"shell32.dll"' not in code


def test_explicit_undef_and_define_still_available():
    code,macros,*_= _preprocess_dbase_macros('#undef WINDOWS\n#define LINUX 1\n#ifdef LINUX\n? "OK"\n#endif',filename='p.prg',target='pe32')
    assert '? "OK"' in code
    assert 'WINDOWS' not in {macro.name for macro in macros}


def test_linux_so_is_accepted_but_windows_ffi_remains_dll_only():
    decl='extern HINSTANCE ShellExecute(HWND, LPCSTR, LPCSTR, LPCSTR, LPCSTR, CINT) "shell32.so" from "ShellExecuteA"\n'
    _,linux=extract_ffi_prototypes(decl,filename='foo.prg',allow_so=True)
    assert linux[0].dll=='shell32.so'
    with pytest.raises(ValueError,match='DLL erwartet'):
        extract_ffi_prototypes(decl,filename='foo.prg')


@pytest.mark.parametrize('bits',[32,64])
def test_linux_prg_shell32_compatibility_and_type_sizes(bits):
    result=compile_linux_prg(HEADER+'\n? '+CALL+'\n',bits=bits,filename='main.prg',qt_terminal=True)
    data=decode_embedded_json(result.assembly,'__linux_console_json')
    assert data['actions'][0][:2]==['ffi_print','ShellExecuteA']
    assert data['actions'][0][2][1]=='open'
    assert ffi_type_info('HWND').bits('linux64' if bits==64 else 'linux32')==bits
    assert ffi_type_info('CINT').bits('linux64' if bits==64 else 'linux32')==32
    assert ffi_type_info('LPCSTR').bits('linux64' if bits==64 else 'linux32')==bits


def test_linux_wfm_shell32_call_in_preamble_and_method():
    src=HEADER+'\n? '+CALL+'\nCLASS Form1 OF FORM\nTHIS.Button1=NEW BUTTON()\nTHIS.Button1.OnClick=CLASS::click1\nPROCEDURE click1()\n? '+CALL+'\nRETURN\nENDCLASS\n'
    result=compile_linux_wfm(src,bits=64,filename='Form1.wfm')
    data=decode_embedded_json(result.assembly,'__linux_wfm_json')
    assert data['startup_actions'][0][0]=='ffi_print'
    assert data['methods']['click1'][0][0]=='ffi_print'


def test_unsupported_shared_library_call_stays_error():
    src='extern CINT NotImplemented() "other.so" from "NotImplemented"\n? NotImplemented()\n'
    with pytest.raises(LinuxDBaseError,match='nicht verfuegbar'):
        compile_linux_prg(src,bits=64,filename='bad.prg',qt_terminal=True)


def test_qt_bridge_exports_and_build_alias_are_present():
    root=Path(__file__).parent
    cpp=(root/'d64qt5/d64qt5_linux_form.cpp').read_text()
    script=(root/'d64qt5/build_linux.sh').read_text()
    for token in ['ShellExecuteA(', 'ShellExecuteW(', 'DBaseQtGetX11WindowId(', 'nativeX11Id(', 'runDBaseActions(']:
        assert token in cpp
    assert 'ln -sfn libd64_qt5.so release/shell32.so' in script
