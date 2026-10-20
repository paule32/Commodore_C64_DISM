# -*- coding: utf-8 -*-
"""Stage 448: real PE/COFF builds of unified console+character runtime."""
from __future__ import annotations

from pathlib import Path

import pytest
from d64dbase import compile_dbase_to_assembly
from d64dbase.char_case import is_char_case, emit_char_case_check
from d64dbase.char_case_runtime import CASE_EXPORTS
from d64dbase.console_runtime import DLL_NAME, EXPORTS, assembly_source, deploy_runtime
from d64dbase.runtime_builder import create_runtime_dll
from test_stage443_wfm_len_event import _compile_wfm_for_test
from test_stage446_console_dll import get_exports, pe_info
from test_stage446_real_pe_link import linkers

ROOT = Path(__file__).parent
WFM = '''Form1 = NEW Form1()
CLASS Form1 OF FORM
    PROCEDURE PushButton1_onClick()
        STORE "ä" TO Text
        ? ISLOWER(Text)
        ? ISUPPER(Text)
        RETURN
ENDCLASS
'''
PRG = '''STORE "ä" TO Text
? ISLOWER(Text)
? ISUPPER(Text)
FUNCTION CheckLower(value)
    RETURN ISLOWER(value)
FUNCTION CheckUpper(value)
    RETURN ISUPPER(value)
? CheckLower(Text)
? CheckUpper(Text)
'''


def test_one_dll_name_and_existing_console_case_exports():
    assert DLL_NAME == 'c64_dbase_runtime.dll'
    # Stage 449 adds three format/string helpers; the Stage 448 exports remain.
    assert len(EXPORTS) == 11
    assert len(CASE_EXPORTS) == 4
    for target in ('pe32', 'pe64'):
        src = assembly_source(target)
        assert 'DBaseConsoleWrite' in src
        for item in EXPORTS:
            assert 'export ' + item + ',' in src
        assert 'call DBaseCharIs' not in src  # implementations, not self-imports


@pytest.mark.parametrize('target,machine', [('pe32',0x14c),('pe64',0x8664)])
def test_packaged_new_dll_has_right_machine_and_complete_exports(target,machine):
    p = ROOT/'d64dbase'/'bin'/target/DLL_NAME
    assert p.is_file()
    actual_machine, names = pe_info(p)
    assert actual_machine == machine
    assert set(EXPORTS).issubset(names)
    assert not (p.parent/'d64_dbase_console.dll').exists()


@pytest.mark.parametrize('upper,encoding,export',[
    (True,'cp1252','DBaseCharIsUpperCP1252'),
    (False,'cp1252','DBaseCharIsLowerCP1252'),
    (True,'utf8','DBaseCharIsUpperUtf8'),
    (False,'utf8','DBaseCharIsLowerUtf8'),
])
def test_frontend_generates_short_calls_not_inline_tables(upper,encoding,export):
    ops = emit_char_case_check('__slot', is64=False, label_prefix='unused', upper=upper, encoding=encoding)
    assert f'    call {export}' in ops
    assert '    add esp, 8' in ops
    assert '    fild dword ptr [__dbase_temp_number]' in ops
    assert not any('_next_' in op for op in ops)
    ops64 = emit_char_case_check('__slot', is64=True, label_prefix='unused', upper=upper, encoding=encoding)
    assert f'    call {export}' in ops64
    assert '    sub rsp, 40' in ops64
    assert '    add rsp, 40' in ops64
    reserved = emit_char_case_check('__slot', is64=True, label_prefix='unused',
                                    upper=upper, encoding=encoding, has_shadow_space=True)
    assert f'    call {export}' in reserved
    assert '    sub rsp, 40' not in reserved
    assert '    add rsp, 40' not in reserved


def test_cp1252_semantics_preserved_for_cased_and_uncased_chars():
    assert is_char_case('ä',upper=False)
    assert is_char_case('Ä',upper=True)
    assert not is_char_case('7',upper=False)
    assert not is_char_case('ab',upper=False)


@pytest.mark.parametrize('target', ['pe32','pe64'])
def test_real_prg_and_wfm_exes_link_against_same_dll(target):
    ns=linkers()
    assembler=ns['assemble_pe32_object_source'] if target=='pe32' else ns['assemble_pe64_object_source']
    coff=ns['write_coff32_object'] if target=='pe32' else ns['write_coff64_object']
    linker=ns['link_coff32_objects'] if target=='pe32' else ns['link_coff64_objects']
    prg=compile_dbase_to_assembly(PRG,target=target).assembly
    assert 'call DBaseCharIsLowerCP1252' in prg
    assert 'call DBaseCharIsUpperCP1252' in prg
    wfm=_compile_wfm_for_test(WFM,target=target).assembly
    if target == 'pe64':
        assert '    sub rsp, 40\n    call DBaseCharIsLowerUtf8' not in wfm
        assert '    sub rsp, 40\n    call DBaseCharIsUpperUtf8' not in wfm
    assert 'call DBaseCharIsLowerUtf8' in wfm
    assert 'call DBaseCharIsUpperUtf8' in wfm
    for asm,entry in ((prg,'_start'),(wfm,'__d64_wfm_entry')):
        exe=linker((coff(assembler(asm)),),entry_symbol=entry,gui=True).executable
        assert exe[:2]==b'MZ'
        assert DLL_NAME.encode() in exe
        assert b'DBaseConsoleWrite' in exe
    assert b'DBaseCharIsLowerCP1252' in prg.encode()


@pytest.mark.parametrize('target', ['pe32','pe64'])
def test_existing_manual_build_ui_rebuilds_new_runtime(tmp_path,target):
    ns=linkers()
    out=create_runtime_dll(target,tmp_path/target,get_exports=get_exports,
        assemble32=ns['assemble_pe32_object_source'],coff32=ns['write_coff32_object'],link32=ns['link_coff32_objects'],
        assemble64=ns['assemble_pe64_object_source'],coff64=ns['write_coff64_object'],link64=ns['link_coff64_objects'])
    assert out.name == DLL_NAME
    assert set(EXPORTS).issubset(pe_info(out)[1])
    assert out.read_bytes()==(ROOT/'d64dbase'/'bin'/target/DLL_NAME).read_bytes()


@pytest.mark.parametrize('target', ['pe32','pe64'])
def test_deploy_replaces_old_or_incomplete_runtime(tmp_path,target):
    output=tmp_path/target/'application.exe'
    output.parent.mkdir()
    dest=output.parent/DLL_NAME
    dest.write_bytes(b'MZ invalid / old runtime')
    result=deploy_runtime(output,target,get_exports=get_exports)
    assert result==dest
    assert set(EXPORTS).issubset(pe_info(result)[1])


def test_stage447_menu_and_environment_controls_are_unchanged():
    src=(ROOT/'d64_dism.py').read_text(encoding='utf-8')
    for label in ('dBASE Runtime PE32 DLL erstellen','dBASE Runtime PE32+ DLL erstellen'):
        assert label in src
    assert 'self.console_runtime_build_button = QPushButton("dBASE Runtime DLL erstellen"' in src
    assert 'self.console_runtime_directory_edit = QLineEdit(runtime_group)' in src
    assert 'self.console_runtime_browse_button = QPushButton("...", runtime_group)' in src
    assert 'from d64dbase.runtime_builder import create_runtime_dll' in src
    assert 'b"c64_dbase_runtime.dll" in output_path.read_bytes().lower()' in src


def test_wfm_checklower_function_uses_one_shared_runtime_call():
    source = '''Form1 = NEW Form1()
CLASS Form1 OF FORM
    FUNCTION CheckLower(c)
        RETURN ISLOWER(c)
    PROCEDURE PushButton1_onClick()
        ? ISLOWER("ä")
        RETURN
ENDCLASS
'''
    for target in ('pe32', 'pe64'):
        asm = _compile_wfm_for_test(source, target=target).assembly
        body = asm.split('__dbase_wfm_proc_CheckLower:',1)[1].split('; END WFM PROCEDURE',1)[0]
        assert body.count('call DBaseCharIsLowerUtf8') == 1
        assert 'movzx eax, byte ptr' not in body
        if target == 'pe64':
            assert body.count('sub rsp, 40') == 1  # WFM method prologue only
            assert body.count('add rsp, 40') == 1  # WFM method epilogue only
        else:
            assert 'add esp, 8' in body
        ns = linkers()
        assembler = ns['assemble_pe64_object_source'] if target == 'pe64' else ns['assemble_pe32_object_source']
        coff = ns['write_coff64_object'] if target == 'pe64' else ns['write_coff32_object']
        linker = ns['link_coff64_objects'] if target == 'pe64' else ns['link_coff32_objects']
        exe = linker((coff(assembler(asm)),),entry_symbol='__d64_wfm_entry',gui=True).executable
        assert exe.startswith(b'MZ') and b'DBaseCharIsLowerUtf8' in exe
