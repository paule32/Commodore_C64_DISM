# -*- coding: utf-8 -*-
"""Stage 466: executable statements preceding the WFM END HEADER/CLASS."""
import re
import pytest
from d64dbase.wfm import wfm_executable_preamble
from test_stage460_wfm_typed_slot_optimization import compile_slot_optimized
from test_stage446_real_pe_link import linkers

USER_SOURCE = '''STORE 123.45 TO xyz

? TYPE("xyz")       && N
? VARTYPE(xyz)      && N

IF TYPE("xyz") == "N"
    ? "xyz ist numerisch"
ENDIF

STORE "Hallo" TO xyz

? TYPE("xyz")       && C
? VARTYPE(xyz)      && C

? TYPE("unbekannt") && U

** END HEADER -- do not remove this line
// Generated on 19.10.2026
//
PARAMETER bmodal
LOCAL B
B = NEW Form1(51,4)
if bmodal = .T.
   B.ReadModal()
else
   B.Open()
endif

CLASS Form1 OF FORM
    PROCEDURE Button1_onClick()
        ? VARTYPE(xyz)
        RETURN
ENDCLASS
'''


def test_top_level_parser_keeps_all_real_code_and_original_line_positions():
    lines = wfm_executable_preamble(USER_SOURCE, class_name='Form1')
    assert len(lines) == USER_SOURCE.splitlines().index('CLASS Form1 OF FORM')
    assert lines[0] == 'STORE 123.45 TO xyz'
    assert lines[2].strip() == '? TYPE("xyz")'
    assert lines[5] == 'IF TYPE("xyz") == "N"'
    assert lines[6].strip() == '? "xyz ist numerisch"'
    assert lines[14].strip() == '? TYPE("unbekannt")'
    assert not any('bmodal' in x.lower() or 'NEW Form1' in x for x in lines)


@pytest.mark.parametrize('target', ('pe32', 'pe64'))
@pytest.mark.parametrize('dynamic', (False, True))
def test_native_top_level_runs_before_form_creation_assembles_and_links(target, dynamic):
    asm = compile_slot_optimized(target, False, dynamic, USER_SOURCE)
    entry = asm.split('__d64_wfm_entry:', 1)[1].split('; Stage 133: WFM Event-', 1)[0]
    assert entry.index('call DBaseQtRuntimeStartup') < entry.index('call __dbase_wfm_proc___dbase_top_level__')
    assert entry.index('call __dbase_wfm_proc___dbase_top_level__') < entry.index('call DBaseQtFormCreate')
    assert entry.count('call __dbase_wfm_proc___dbase_top_level__') == 1
    assert 'call DBaseQtWfmModalParameter' in asm
    proc = asm.split('__dbase_wfm_proc___dbase_top_level__:', 1)[1].split('; END WFM PROCEDURE/FUNCTION: __dbase_top_level__', 1)[0]
    assert '; STORE 123.45 TO xyz' in proc
    assert '; STORE "Hallo" TO xyz' in proc
    assert re.search(r'mov edx, dword ptr \[__dbase_wfm_mem_xyz_type\]', proc)
    assert proc.count('call DBaseQtConsoleWrite') >= 5
    assert 'xyz ist numerisch' in asm
    assert 'WFM PROCEDURE/FUNCTION MASCHINENCODE: Button1_onClick' in asm
    assert asm.count('__dbase_wfm_mem_xyz_type:') == 1
    lk = linkers()
    obj = lk[f'assemble_{target}_object_source'](asm)
    coff = lk[f'write_coff{64 if target == "pe64" else 32}_object'](obj)
    exe = lk[f'link_coff{64 if target == "pe64" else 32}_objects'](
        (coff,), entry_symbol='__d64_wfm_entry', gui=True)
    assert exe.executable.startswith(b'MZ')


def test_top_level_without_header_marker_is_executable():
    source = '''STORE 10 TO value
? value
CLASS Form1 OF FORM
ENDCLASS
'''
    asm = compile_slot_optimized('pe32', False, True, source)
    assert 'call __dbase_wfm_proc___dbase_top_level__' in asm
    assert '; STORE 10 TO value' in asm


def test_top_level_comment_quotes_and_debug_order():
    source = '''STORE "A&&B" TO text && suffix
SET DEBUG OFF
? text
SET DEBUG ON
** END HEADER -- do not remove this line
B = NEW Form1()
CLASS Form1 OF FORM
ENDCLASS'''
    asm = compile_slot_optimized('pe32', False, True, source)
    proc = asm.split('__dbase_wfm_proc___dbase_top_level__:', 1)[1]
    assert proc.index('; STORE "A&&B" TO text') < proc.index('; Stage 318: SET DEBUG OFF')
    assert proc.index('; Stage 318: SET DEBUG OFF') < proc.index('; Stage 318: SET DEBUG ON')
    assert proc.count('call DBaseQtSetDebugVisible') == 2
    assert not re.search(r'__dbase_wfm_runtime_ready:\n\s*; WFM preamble', asm)


def test_invalid_top_level_statement_is_not_silently_ignored():
    source = 'THIS COMMAND DOES NOT EXIST\nCLASS Form1 OF FORM\nENDCLASS'
    with pytest.raises(Exception, match=r'stage460\.wfm:1:.*Statement noch nicht.*THIS COMMAND'):
        compile_slot_optimized('pe32', False, True, source)



def test_legacy_constructor_variable_is_not_compiled_as_assignment():
    source = "Form1 = NEW Form1()\nCLASS Form1 OF FORM\nENDCLASS"
    assert not any(x.strip() for x in wfm_executable_preamble(source, class_name='Form1'))
    asm = compile_slot_optimized('pe32', False, False, source)
    assert 'call __dbase_wfm_proc___dbase_top_level__' not in asm

def test_plain_wfm_without_preamble_keeps_old_lifecycle():
    source = '''PARAMETER bmodal
LOCAL B
B = NEW Form1()
if bmodal = .T.
B.ReadModal()
else
B.Open()
endif
CLASS Form1 OF FORM
ENDCLASS'''
    asm = compile_slot_optimized('pe32', False, True, source)
    assert 'call __dbase_wfm_proc___dbase_top_level__' not in asm
    assert 'call DBaseQtWfmModalParameter' in asm
