"""Stage 478: Win32 LLP64 FFI aliases and actual PE32/PE64 ABI lowering."""
import pytest

from d64dbase.ffi_types import FFI_TYPES, ffi_type_info, ffi_return_instructions
from d64dbase.compiler import DBaseCompilerError, compile_dbase_to_assembly, preprocess_dbase_source
from test_stage460_wfm_typed_slot_optimization import compile_slot_optimized
from test_stage446_real_pe_link import linkers


@pytest.mark.parametrize('type_name,b32,b64,signed,category', [
    ('BOOL',32,32,True,'integer'),
    ('BYTE',8,8,False,'integer'),
    ('WORD',16,16,False,'integer'),
    ('DWORD',32,32,False,'integer'),
    ('LONG',32,32,True,'integer'),
    ('HRESULT',32,32,True,'integer'),
    ('SIZE_T',32,64,False,'integer'),
    ('SSIZE_T',32,64,True,'integer'),
    ('WPARAM',32,64,False,'integer'),
    ('LPARAM',32,64,True,'integer'),
    ('LRESULT',32,64,True,'integer'),
    ('HWND',32,64,False,'pointer'),
    ('HINSTANCE',32,64,False,'pointer'),
    ('HANDLE',32,64,False,'pointer'),
    ('LPVOID',32,64,False,'pointer'),
    ('LPCSTR',32,64,False,'ansi_string'),
    ('LPCWSTR',32,64,False,'wide_string'),
    ('LPWSTR',32,64,False,'pointer'),
    ('CINT',32,32,True,'integer'),
])
def test_windows_llp64(type_name,b32,b64,signed,category):
    info=ffi_type_info(type_name.lower())
    assert info.bits('pe32')==b32
    assert info.bits('pe64')==b64
    assert info.signed==signed
    assert info.category==category


def test_unsupported_float_is_reported_not_silently_integer():
    with pytest.raises(DBaseCompilerError, match='Unbekannter DLL-Rueckgabetyp'):
        preprocess_dbase_source('extern FLOAT GetSomething() "user32.dll" from "Foo"')


def _compile(src,target,kind):
    if kind=='wfm':
        return compile_slot_optimized(target,False,True,src+'CLASS Form1 OF FORM\nENDCLASS\n')
    return compile_dbase_to_assembly(src,target=target).assembly


@pytest.mark.parametrize('target',('pe32','pe64'))
@pytest.mark.parametrize('kind',('prg','wfm'))
def test_dword_signedness_and_handle_abi_link(target,kind):
    src='''extern DWORD GetLastError() "kernel32.dll" from "GetLastError"
extern BOOL IsWindow(HWND) "user32.dll" from "IsWindow"
extern HANDLE GetCurrentProcess() "kernel32.dll" from "GetCurrentProcess"
err = GetLastError()
result = IsWindow(0)
handle = GetCurrentProcess()
'''
    asm=_compile(src,target,kind)
    assert 'call __dbase_ffi_getlasterror' in asm
    assert 'call __dbase_ffi_iswindow' in asm
    assert 'call __dbase_ffi_getcurrentprocess' in asm
    assert 'mov dword ptr [__dbase_ffi_return+4], 0' in asm
    lk=linkers()
    coff=lk[f'write_coff{64 if target=="pe64" else 32}_object'](
        lk[f'assemble_{target}_object_source'](asm))
    exe=lk[f'link_coff{64 if target=="pe64" else 32}_objects'](
        (coff,),entry_symbol='__d64_wfm_entry' if kind=='wfm' else '_start',gui=True)
    assert exe.executable.startswith(b'MZ')


@pytest.mark.parametrize('target',('pe32','pe64'))
@pytest.mark.parametrize('kind',('prg','wfm'))
def test_lpcwstr_literal_compiles_and_links(target,kind):
    src='''extern CINT MessageBoxW(HWND,LPCWSTR,LPCWSTR,UINT) "user32.dll" from "MessageBoxW"
x = MessageBoxW(0,"Grüße","Titel",0)
'''
    asm=_compile(src,target,kind)
    assert 'call __dbase_ffi_messageboxw' in asm
    # UTF-16LE: G r ü ß e NUL
    assert ('db 71, 0, 114, 0, 252, 0, 223, 0, 101, 0, 0, 0') in asm
    lk=linkers()
    coff=lk[f'write_coff{64 if target=="pe64" else 32}_object'](
        lk[f'assemble_{target}_object_source'](asm))
    exe=lk[f'link_coff{64 if target=="pe64" else 32}_objects'](
        (coff,),entry_symbol='__d64_wfm_entry' if kind=='wfm' else '_start',gui=True)
    assert exe.executable.startswith(b'MZ')


@pytest.mark.parametrize('kind',('prg','wfm'))
def test_writable_lpstr_requires_native_pointer_not_string(kind):
    src='extern UINT GetWindowsDirectoryA(LPSTR, UINT) "kernel32.dll" from "GetWindowsDirectoryA"\n'
    source=src+'x=GetWindowsDirectoryA("text",256)\n'
    with pytest.raises(Exception,match='native Speicheradresse|Zahl/Pointer|kein String'):
        _compile(source,'pe32',kind)


@pytest.mark.parametrize('kind',('wfm',))
def test_utf16_dynamic_text_fails_without_buffer(kind):
    src='extern CINT MessageBoxW(HWND,LPCWSTR,LPCWSTR,UINT) "user32.dll" from "MessageBoxW"\n'
    with pytest.raises(Exception,match='UTF-16'):
        _compile(src+'name="Hallo"\nx=MessageBoxW(0,name,"titel",0)\n','pe32',kind)


@pytest.mark.parametrize('target',('pe32','pe64'))
def test_return_signedness(target):
    instructions=ffi_return_instructions('DWORD',is64=target=='pe64')
    assert '    mov dword ptr [__dbase_ffi_return+4], 0' in instructions
    instructions=ffi_return_instructions('LONG',is64=target=='pe64')
    assert '    sar eax, 31' in instructions
    assert ffi_return_instructions('HANDLE',is64=target=='pe64')
    assert ffi_return_instructions('CVOID',is64=target=='pe64')==[]

@pytest.mark.parametrize('target',('pe32','pe64'))
@pytest.mark.parametrize('kind',('prg','wfm'))
def test_small_integer_return_width_and_sign_extension(target,kind):
    src='''extern WORD GetSystemDefaultLangID() "kernel32.dll" from "GetSystemDefaultLangID"
extern BYTE GetByte() "kernel32.dll" from "GetLastError"
x = GetSystemDefaultLangID()
y = GetByte()
'''
    asm=_compile(src,target,kind)
    assert 'and eax, 65535' in asm
    assert 'and eax, 255' in asm
    lk=linkers()
    coff=lk[f'write_coff{64 if target=="pe64" else 32}_object'](
        lk[f'assemble_{target}_object_source'](asm))
    exe=lk[f'link_coff{64 if target=="pe64" else 32}_objects'](
        (coff,),entry_symbol='__d64_wfm_entry' if kind=='wfm' else '_start',gui=True)
    assert exe.executable.startswith(b'MZ')


@pytest.mark.parametrize('target',('pe32','pe64'))
@pytest.mark.parametrize('kind',('prg','wfm'))
def test_unsigned_dword_argument_zero_extended_in_x64(target,kind):
    source='''extern DWORD Sum(DWORD,DWORD,DWORD,DWORD,DWORD) "kernel32.dll" from "GetLastError"
x = Sum(4294967295, 4294967295, 4294967295, 4294967295, 4294967295)
'''
    asm=_compile(source,target,kind)
    if target=='pe64':
        assert 'mov ecx, dword ptr [__dbase_ffi_return]' in asm
        assert 'mov r8d, dword ptr [__dbase_ffi_return]' in asm
    lk=linkers()
    coff=lk[f'write_coff{64 if target=="pe64" else 32}_object'](
        lk[f'assemble_{target}_object_source'](asm))
    exe=lk[f'link_coff{64 if target=="pe64" else 32}_objects'](
        (coff,),entry_symbol='__d64_wfm_entry' if kind=='wfm' else '_start',gui=True)
    assert exe.executable.startswith(b'MZ')


def test_void_keyword_as_zero_parameter_list():
    src='extern VOID NoOp(VOID) "kernel32.dll" from "GetLastError"\nNoOp()\n'
    frontend=preprocess_dbase_source(src)
    assert frontend.ffi_prototypes[0].argument_types==()
    assert 'call __dbase_ffi_noop' in compile_dbase_to_assembly(src).assembly

@pytest.mark.parametrize('kind',('prg','wfm'))
def test_pe32_int64_arguments_occupy_two_stack_slots(kind):
    # An int64 occupies 8 stack bytes in Win32 stdcall, unlike a HANDLE.
    code='extern CVOID SendQword(LONGLONG, DWORD64) "kernel32.dll" from "Sleep"\nSendQword(123456, 987654)\n'
    asm=_compile(code,'pe32',kind)
    assert 'push dword ptr [__dbase_ffi_return+4]' in asm
    assert 'push dword ptr [__dbase_ffi_return]' in asm
    lk=linkers()
    coff=lk['write_coff32_object'](lk['assemble_pe32_object_source'](asm))
    exe=lk['link_coff32_objects']((coff,),entry_symbol='__d64_wfm_entry' if kind=='wfm' else '_start',gui=True)
    assert exe.executable.startswith(b'MZ')
