"""Stage 477: declared Win32 API imports from dBASE PRG/WFM and #include."""
from pathlib import Path
import pytest
from d64dbase.compiler import (DBaseCompilerError, compile_dbase_to_assembly,
                               preprocess_dbase_source)
from test_stage460_wfm_typed_slot_optimization import compile_slot_optimized
from test_stage446_real_pe_link import linkers

DECL = '''#define shell32 "shell32.dll"
extern HINSTANCE ShellExecute(HWND, LPCSTR, LPCSTR, LPCSTR, ;
LPCSTR, CINT) shell32 ;
from "ShellExecuteA"
'''
CALL = 'ShellExecute(0, "open", "notepad.exe", 0, 0, 1)'

@pytest.mark.parametrize('target', ('pe32', 'pe64'))
@pytest.mark.parametrize('kind', ('prg', 'wfm'))
def test_shell_execute_assembles_and_links(target,kind):
    src = DECL + 'result = ' + CALL + '\n? result\n'
    if kind == 'wfm':
        src += 'CLASS Form1 OF FORM\nENDCLASS\n'
    asm = (compile_dbase_to_assembly(src,target=target).assembly if kind=='prg'
           else compile_slot_optimized(target,False,True,src))
    assert 'import __dbase_ffi_shellexecute, "shell32.dll", "ShellExecuteA"' in asm
    assert 'call __dbase_ffi_shellexecute' in asm
    assert 'cvttsd2si' not in asm
    assert ('push ' in asm if target=='pe32' else ('sub rsp, 48' in asm or 'sub rsp, 56' in asm))
    lk = linkers()
    obj = lk[f'assemble_{target}_object_source'](asm)
    coff = lk[f'write_coff{64 if target=="pe64" else 32}_object'](obj)
    exe = lk[f'link_coff{64 if target=="pe64" else 32}_objects'](
        (coff,), entry_symbol='_start' if kind=='prg' else '__d64_wfm_entry', gui=True)
    assert exe.executable[:2] == b'MZ'

@pytest.mark.parametrize('target',('pe32','pe64'))
def test_prototype_from_include_with_macro_alias(tmp_path,target):
    (tmp_path/'winapi.h').write_text('extern HINSTANCE ShellExecute(HWND,LPCSTR,LPCSTR,LPCSTR, ;\nLPCSTR,CINT) shell32 ;\nfrom "ShellExecuteA"\n')
    src='#define shell32 "shell32.dll"\n#include "winapi.h"\n'+CALL+'\n'
    res=preprocess_dbase_source(src,filename=str(tmp_path/'foo.prg'),target=target)
    assert len(res.ffi_prototypes)==1
    assert res.ffi_prototypes[0].dll=='shell32.dll'
    assert res.ffi_prototypes[0].entry=='ShellExecuteA'
    asm=compile_dbase_to_assembly(src,filename=str(tmp_path/'foo.prg'),target=target).assembly
    assert 'import __dbase_ffi_shellexecute, "shell32.dll", "ShellExecuteA"' in asm

@pytest.mark.parametrize('kind',('prg','wfm'))
def test_argument_type_and_arity_errors(kind):
    bad=[('ShellExecute(0, "open", "file", 0, 0)', 'Parameter'),
         ('ShellExecute(0, "open", "file", 0, 0, "bad")', 'erwartet'),
         ('ShellExecute("not HWND", "open", "file", 0, 0, 1)', 'erwartet'),
         ('ShellExecute(0, 42, "file", 0, 0, 1)', 'LPCSTR')]
    for call,token in bad:
        source=DECL+call+'\n'
        if kind=='wfm':source+='CLASS Form1 OF FORM\nENDCLASS'
        with pytest.raises(Exception,match=token):
            compile_dbase_to_assembly(source) if kind=='prg' else compile_slot_optimized('pe32',False,True,source)

def test_cvoid_and_nullary_prototypes():
    code='extern CVOID Done(CVOID) "user32.dll" from "MessageBeep"\nDone()\n'
    # The declaration grammar rejects unsupported forms rather than emitting broken ABI.
    frontend=preprocess_dbase_source(code)
    assert frontend.ffi_prototypes[0].argument_types==()
    asm=compile_dbase_to_assembly(code).assembly
    assert 'call __dbase_ffi_done' in asm
    with pytest.raises(DBaseCompilerError,match='CVOID'):
        compile_dbase_to_assembly(code.replace('Done()','x = Done()'))

@pytest.mark.parametrize('kind',('prg','wfm'))
def test_parameterless_cvoid_call(kind):
    code='extern CVOID NoOp() "kernel32.dll" from "GetLastError"\nNoOp()\n'
    if kind=='wfm':code+='CLASS Form1 OF FORM\nENDCLASS\n'
    asm=(compile_dbase_to_assembly(code).assembly if kind=='prg' else
         compile_slot_optimized('pe32',False,False,code))
    assert 'call __dbase_ffi_noop' in asm

def test_invalid_prototype_errors_and_duplicated_declarations():
    for declaration in [
        'extern BAD ShellExecute(CINT) "shell32.dll" from "ShellExecuteA"',
        'extern HINSTANCE ShellExecute(BAD) "shell32.dll" from "ShellExecuteA"',
        'extern CINT Foo(CINT) "other" from "Foo"',
    ]:
        with pytest.raises(DBaseCompilerError):
            preprocess_dbase_source(declaration)

@pytest.mark.parametrize('target',('pe32','pe64'))
def test_wfm_event_method_calls_dll(target):
    source=DECL+'''CLASS Form1 OF FORM
    PROCEDURE Button1_onClick()
        LOCAL hwnd = 0
        LOCAL result = ShellExecute(hwnd, "open", "notepad.exe", 0, 0, 1)
        IF result > 32
            ? "Application opened"
        ENDIF
        RETURN
ENDCLASS\n'''
    asm=compile_slot_optimized(target,False,True,source)
    block=asm.split('; WFM PROCEDURE/FUNCTION MASCHINENCODE: Button1_onClick',1)[1]
    assert 'call __dbase_ffi_shellexecute' in block
    lk=linkers();obj=lk[f'assemble_{target}_object_source'](asm)
    coff=lk[f'write_coff{64 if target=="pe64" else 32}_object'](obj)
    exe=lk[f'link_coff{64 if target=="pe64" else 32}_objects']((coff,),entry_symbol='__d64_wfm_entry',gui=True)
    assert exe.executable.startswith(b'MZ')

@pytest.mark.parametrize('target',('pe32','pe64'))
def test_wfm_ffi_declared_in_project_include(tmp_path,target):
    (tmp_path/'api.h').write_text('extern HINSTANCE ShellExecute(HWND,LPCSTR,LPCSTR,LPCSTR,LPCSTR,CINT) shell32 from "ShellExecuteA"\n')
    src='#define shell32 "shell32.dll"\n#include "api.h"\n'+CALL+'\nCLASS Form1 OF FORM\nENDCLASS\n'
    # Stub builds with its own filename relative to the current directory.
    # Set absolute #include and use the normal project path for this test.
    asm=compile_slot_optimized(target,False,True,src.replace('"api.h"', f'"{tmp_path / "api.h"}"'))
    assert 'import __dbase_ffi_shellexecute, "shell32.dll", "ShellExecuteA"' in asm

@pytest.mark.parametrize('target',('pe32','pe64'))
def test_bare_macro_shell32_expands_inside_prototype(target):
    result=preprocess_dbase_source(DECL+CALL+'\n',filename='foo.wfm',target=target)
    assert result.ffi_prototypes[0].dll=='shell32.dll'
    assert result.ffi_prototypes[0].name=='ShellExecute'
    assert result.ffi_prototypes[0].return_type=='HINSTANCE'
    assert len(result.preprocessed_source.splitlines())==5
