"""Stage 646: Windows GetLastError -> managed TObject Code/Message.

Native Windows Qt5 runtime is not available in this test environment;
assembly, C++ VFS source contracts and an assembler/COFF pass are tested.
"""
import re
from pathlib import Path
from decimal import Decimal
import pytest
from d64dbase.compiler import (
    DBaseCompilerError, compile_dbase_to_assembly, parse_dbase_statements,
    evaluate_dbase_statements,
)
from d64dbase.win32_errors import win32_message

ROOT=Path(__file__).resolve().parent


def compile_src(src, target):
    return compile_dbase_to_assembly(
        src, target=target, filename='runtime/dbase/src/stage646.prg',
        include_paths=['runtime/dbase/src']).assembly


def test_windows_error_fallback_messages():
    for code, word in ((2,'Datei'),(3,'Pfad'),(5,'Zugriff'),(32,'Prozess'),(183,'vorhanden')):
        assert word in win32_message(code)
    assert win32_message(123456) == 'Windows-Systemfehler 123456.'
    assert win32_message(0x100000002) == win32_message(2)


def test_preview_code_class_and_message():
    src='''TRY
 Win32FileRaise(2)
CATCH (Win32FileException e)
 ? e.ClassName
 ? e.Code
 ? e.Message
FINALLY
 ? "ENDE"
ENDTRY'''
    output=evaluate_dbase_statements(parse_dbase_statements(src))
    assert output.splitlines() == [
        'Win32FileException', '2',
        'Das System kann die angegebene Datei nicht finden.', 'ENDE']


def test_preview_inheritance_and_rethrow_code():
    src='''TRY
 TRY
  Win32FileRaise(32)
 CATCH (Win32Exception e)
  THROW e
 ENDTRY
CATCH (Exception e)
 ? e.Code
 ? e.ClassName
ENDTRY'''
    assert evaluate_dbase_statements(parse_dbase_statements(src)).splitlines() == [
        '32', 'Win32FileException']


def test_zero_error_is_not_an_exception():
    src='''TRY
 Win32Raise(0)
 ? "OK"
CATCH (Win32Exception e)
 ? "NOT OK"
ENDTRY'''
    assert evaluate_dbase_statements(parse_dbase_statements(src)).strip() == 'OK'


def test_normal_exception_code_defaults_to_zero():
    src='''TRY
 THROW NEW Exception("test")
CATCH (Exception e)
 ? e.Code
ENDTRY'''
    assert evaluate_dbase_statements(parse_dbase_statements(src)).strip() == '0'


@pytest.mark.parametrize('code', ['"abc"', '1,2', ''])
def test_invalid_win32_raise_arguments_are_rejected(code):
    src=f'Win32FileRaise({code})'
    with pytest.raises(DBaseCompilerError):
        compile_src(src,'pe32')


def test_win32_raise_imports_formatmessage_and_native_code_setter_both_targets():
    src='''#include "System.SysUtils"
TRY
 Win32FileRaise(5)
CATCH (Win32Exception e)
 ? e.Message
 ? e.Code
ENDTRY'''
    for target in ('pe32','pe64'):
        a=compile_src(src,target)
        assert 'import FormatMessageA, "kernel32.dll", "FormatMessageA"' in a
        assert 'call FormatMessageA' in a
        assert 'call __dbase_cls_exception_set_code' in a
        assert '__dbase_win32_message_buffer:' in a
        assert '__dbase_vmt_win32fileexception:' in a
        assert '    fild dword ptr [__dbase_exception_code]' in a
        assert '    fstp qword ptr [__dbase_caught_' in a
        assert '    fistp dword ptr [__dbase_exception_code]' in a
        labels=set(re.findall(r'^([A-Za-z_]\w*):',a,re.M))
        imports=set(re.findall(r'^import\s+([A-Za-z_]\w*)\s*,',a,re.M))
        calls=set(re.findall(r'\bcall\s+([A-Za-z_]\w*)\b',a))
        assert not calls-labels-imports, calls-labels-imports


def test_native_code_property_is_inherited():
    src='''#include "System.SysUtils"
CLASS EPath OF Win32FileException
ENDCLASS
TRY
 Win32FileRaise(3)
CATCH (Win32Exception e)
 ? e.Code
ENDTRY'''
    for target, word, size in (('pe32','dd',20),('pe64','dq',40)):
        a=compile_src(src,target)
        label='__dbase_vmt_epath:\n'
        assert f'    {word} 0x{(size | 0x80000000):08X}' in a.split(label,1)[1][:200]


def test_vfs_file_probe_compiles_and_is_confined_to_dbase_qt_bridge():
    src='''#include "System.SysUtils"
TRY
 Win32CheckFile("Dokumente/fehlt.prg")
CATCH (Win32FileException e)
 ? e.Code
 ? e.Message
ENDTRY'''
    for target in ('pe32','pe64'):
        a=compile_src(src,target)
        assert 'import DBaseQtVfsCheckOpenRead, "libd64_qt5.dll", "DBaseQtVfsCheckOpenRead"' in a
        assert '    call DBaseQtVfsCheckOpenRead' in a
        assert '    mov dword ptr [__dbase_exception_code], eax' in a
        assert '    call FormatMessageA' in a
    with pytest.raises(DBaseCompilerError,match='nur in der Windows-EXE'):
        evaluate_dbase_statements(parse_dbase_statements('Win32CheckFile("Dokumente/f.txt")'))


def test_vfs_probe_enforces_two_virtual_mounts_and_captures_last_error_atomically():
    bridge=(ROOT/'d64qt5/d64qt5_bridge.cpp').read_text(encoding='utf-8')
    header=(ROOT/'d64qt5/d64qt5_bridge.h').read_text(encoding='utf-8')
    chunk=bridge.split('unsigned int DBaseQtVfsCheckOpenRead(',1)[1].split('extern "C" D64QT5_API void DBaseQtEnsureDefaultMenu',1)[0]
    assert 'g_editor_vfs.hostPath(virtualName)' in chunk
    assert 'const QFileInfo candidate(hostPath)' in chunk
    assert 'FILE_FLAG_OPEN_REPARSE_POINT' in chunk
    assert 'FILE_ATTRIBUTE_REPARSE_POINT' in chunk
    assert '::CreateFileW' in chunk
    assert 'static_cast<unsigned int>(::GetLastError())' in chunk
    assert 'DBaseQtVfsCheckOpenRead' in header


def test_internal_coff_assembler_accepts_win32_file_errors_both_targets():
    from test_stage605_link import _load_pe_linker
    link=_load_pe_linker()
    src='''TRY
 Win32CheckFile("Dokumente/fehlt.txt")
CATCH (Win32FileException e)
 ? e.Code
 ? e.Message
ENDTRY'''
    for target in ('pe32','pe64'):
        assembly=compile_src(src,target)
        obj=link['assemble_'+target+'_object_source'](assembly)
        assert obj.code
        assert link['write_coff32_object'](obj) if target=='pe32' else link['write_coff64_object'](obj)
