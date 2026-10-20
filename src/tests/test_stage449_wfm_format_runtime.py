# -*- coding: utf-8 -*-
"""Stage 449: native DLL binary/ABI and WFM formatter COFF regression tests."""
from pathlib import Path
import pytest

from d64dbase.console_runtime import DLL_NAME, EXPORTS, assembly_source, build_dll
from d64dbase.runtime_builder import create_runtime_dll
from d64dbase.wfm_format_runtime import classify_type, string_length_n, EXPORTS as FORMAT_EXPORTS
from d64dbase import compile_dbase_to_assembly
from test_stage443_wfm_len_event import _compile_wfm_for_test
from test_stage446_console_dll import pe_info, get_exports
from test_stage446_real_pe_link import linkers

ROOT = Path(__file__).parent

WFM = '''Form1 = NEW Form1()
CLASS Form1 OF FORM
    PROCEDURE PushButton1_onClick()
        STORE "Grüße" TO Text
        ? Text
        ?? Text
        STORE 321 TO Zahl
        ? Zahl
        STORE 1.234 TO Pi
        ? Pi
        STORE 0 TO Nullwert
        ? Nullwert
        RETURN
ENDCLASS
'''


def test_export_set_keeps_console_case_and_adds_three_helpers():
    assert DLL_NAME == 'c64_dbase_runtime.dll'
    assert len(EXPORTS) == 11
    assert set(FORMAT_EXPORTS) == {'DBaseStringLengthN','DBaseWfmClassifyType','DBaseWfmFormatValue'}
    assert all(name in EXPORTS for name in FORMAT_EXPORTS)
    for target in ('pe32', 'pe64'):
        asm = assembly_source(target)
        for name in FORMAT_EXPORTS:
            assert f'export {name}, {name}' in asm
        assert 'import __dbase_runtime_gcvt, "msvcrt.dll", "_gcvt"' in asm
        assert 'DBaseQtConsoleWrite' not in asm  # independent of Qt5
        assert '.dll", "DBaseQt' not in asm
        assert 'section .bss' in asm


@pytest.mark.parametrize('tag,group',[(0,0),(1,3),(2,3),(3,1),(4,2),(5,3),(6,1),(-1,0)])
def test_type_classifier_retains_value_semantics(tag,group):
    assert classify_type(tag) == group


def test_bounded_strlen_counts_bytes_not_utf8_characters():
    assert string_length_n(b'Hallo\0ignored',100)==5
    assert string_length_n('Grüße'.encode('utf8'),100)==7
    assert string_length_n(b'abcdef',3)==3
    assert string_length_n(b'abcdef',0)==0
    assert string_length_n(None,96)==0
    assert string_length_n(b'\0',96)==0


@pytest.mark.parametrize('target', ['pe32','pe64'])
def test_dll_assembler_and_machine_export_set(target,tmp_path):
    ns=linkers()
    new=tmp_path/target/DLL_NAME
    build_dll(target,new,assemble32=ns['assemble_pe32_object_source'],
              coff32=ns['write_coff32_object'],link32=ns['link_coff32_objects'],
              assemble64=ns['assemble_pe64_object_source'],
              coff64=ns['write_coff64_object'],link64=ns['link_coff64_objects'])
    expected_machine=0x14c if target=='pe32' else 0x8664
    machine,exports=pe_info(new)
    assert machine==expected_machine
    assert set(EXPORTS).issubset(exports)
    assert new.read_bytes()==(ROOT/'d64dbase'/'bin'/target/DLL_NAME).read_bytes()
    # The production DLL itself imports _gcvt from msvcrt.dll.
    assert b'msvcrt.dll' in new.read_bytes()
    assert b'_gcvt' in new.read_bytes()


@pytest.mark.parametrize('target', ['pe32','pe64'])
def test_wfm_prints_use_one_formatter_call_and_keep_qt_output(target):
    asm=_compile_wfm_for_test(WFM,target=target).assembly
    assert asm.count('call DBaseWfmFormatValue')==5
    assert asm.count('call DBaseQtConsoleWrite')>=5
    # The old type dispatch, strlen loops, and _gcvt conversions were
    # duplicated per print operation; they now exist once in the DLL.
    assert '__dbase_wfm_strlen_' not in asm
    assert '__dbase_wfm_print_string_' not in asm
    assert '__dbase_wfm_print_number_' not in asm
    assert '    call __dbase_gcvt' not in asm.split('; Stage 133: WFM Event-/Methoden-Code',1)[-1]
    assert '__dbase_wfm_format_result_len:' in asm
    assert f'import DBaseWfmFormatValue, "{DLL_NAME}", "DBaseWfmFormatValue"' in asm
    assembler=linkers()
    program = assembler['assemble_pe32_object_source'](asm) if target=='pe32' else assembler['assemble_pe64_object_source'](asm)
    offsets=program.symbols
    slot=next(k for k in offsets if k.startswith('__dbase_wfm_mem_text_type'))
    prefix=slot[:-4]
    assert offsets[prefix+'num']-offsets[prefix+'type']==4
    assert offsets[prefix+'ptr']-offsets[prefix+'type']==12
    assert offsets[prefix+'len']-offsets[prefix+'type']==(20 if target=='pe64' else 16)
    obj=assembler['write_coff32_object'](program) if target=='pe32' else assembler['write_coff64_object'](program)
    binary=(assembler['link_coff32_objects']((obj,),entry_symbol='__d64_wfm_entry',gui=True).executable
            if target=='pe32' else assembler['link_coff64_objects']((obj,),entry_symbol='__d64_wfm_entry',gui=True).executable)
    assert binary.startswith(b'MZ')
    assert b'DBaseWfmFormatValue' in binary
    assert b'DBaseQtConsoleWrite' in binary


@pytest.mark.parametrize('target', ['pe32','pe64'])
def test_menu_build_uses_same_unified_runtime_exports(target,tmp_path):
    ns=linkers()
    dst=create_runtime_dll(target, tmp_path/target,get_exports=get_exports,
                           assemble32=ns['assemble_pe32_object_source'],
                           coff32=ns['write_coff32_object'],link32=ns['link_coff32_objects'],
                           assemble64=ns['assemble_pe64_object_source'],
                           coff64=ns['write_coff64_object'],link64=ns['link_coff64_objects'])
    assert set(EXPORTS).issubset(pe_info(dst)[1])


def test_stage447_menu_actions_and_settings_still_present():
    text=(ROOT/'d64_dism.py').read_text('utf-8')
    assert 'dBASE Runtime PE32 DLL erstellen' in text
    assert 'dBASE Runtime PE32+ DLL erstellen' in text
    assert 'self.console_runtime_build_button = QPushButton("dBASE Runtime DLL erstellen"' in text
    assert 'self.console_runtime_directory_edit = QLineEdit(runtime_group)' in text
    assert 'self.console_runtime_browse_button = QPushButton("...", runtime_group)' in text
