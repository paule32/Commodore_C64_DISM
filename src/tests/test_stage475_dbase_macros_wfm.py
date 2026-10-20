# -*- coding: utf-8 -*-
"""Stage 475: a single dBASE macro preprocessor for .prg and .wfm."""
from pathlib import Path
import pytest
from d64dbase.compiler import (
    DBaseCompilerError, preprocess_dbase_source, compile_dbase_to_assembly,
)
from test_stage460_wfm_typed_slot_optimization import compile_slot_optimized
from test_stage446_real_pe_link import linkers


@pytest.mark.parametrize('expr', [
    '2 + 3 * 4 == 14',
    '(2 + 3) * 4 == 20',
    '21.2 + 0.1 == 21.3',
    '"String1" + "String2" == "String1String2"',
    '2 => 2',
    '2 <= 3',
    '2 != 3',
    '2 < 3',
    '3 > 2',
])
def test_typed_macro_conditions(expr):
    r = preprocess_dbase_source(f'#if {expr}\n? "yes"\n#else\n? "no"\n#endif\n')
    assert '? "yes"' in r.preprocessed_source
    assert '? "no"' not in r.preprocessed_source


@pytest.mark.parametrize('expr', [
    '"String1" + 21', '"String1" + 21.2', '21 + "String"',
])
def test_reject_mixed_strings_numbers(expr):
    with pytest.raises(DBaseCompilerError, match='Inkompatible Datentypen'):
        preprocess_dbase_source('#if ' + expr + '\n? "wrong"\n#endif', filename='Form1.wfm')


@pytest.mark.parametrize('expr', ['1 >< 2', '1 =< 2', '1 === 2'])
def test_unsupported_comparators_give_explanatory_diagnostic(expr):
    with pytest.raises(DBaseCompilerError, match='Nicht unterstuetzter Vergleichsoperator'):
        preprocess_dbase_source('#if ' + expr + '\n#endif')


def test_nested_includes_project_input_paths_and_file_macros(tmp_path):
    project = tmp_path / 'project'
    directory = tmp_path / 'project-include'
    project.mkdir(); directory.mkdir()
    (directory / 'lib.h').write_text('#define LEVEL 2\n#include "nested.h"\n', encoding='utf8')
    (directory / 'nested.h').write_text('#define NAME "Hallo"\n', encoding='utf8')
    root = project / 'Form1.wfm'
    source = '''#include "lib.h"
#ifdef LEVEL
#if LEVEL => 2
#if NAME + " Welt" == "Hallo Welt"
? NAME
#endif
#else
#error Ungueltiger Zweig
#endif
#endif
#info Dies ist Infotext  aus der Datei: #__FILE__
#warn Das ist eine Warnung aus __FILE__
? #__LINE__
'''
    r = preprocess_dbase_source(source, filename=str(root), include_paths=[directory])
    assert '? "Hallo"' in r.preprocessed_source
    assert r.preprocessor_infos[0].endswith('Dies ist Infotext aus der Datei: Form1.wfm')
    assert r.preprocessor_warnings[0].endswith('Das ist eine Warnung aus Form1.wfm')
    assert '__LINE__' not in r.preprocessed_source
    # Include errors show where the preprocessor searched.
    with pytest.raises(DBaseCompilerError, match='Gepruefte Pfade'):
        preprocess_dbase_source('#include "missing.h"', filename=str(root), include_paths=[directory])


def test_error_stops_build_and_warning_does_not():
    source = '#info info __FILE__\n#warn warning\n? 1\n'
    r = compile_dbase_to_assembly(source, filename='foo.prg', target='pe32')
    assert r.frontend.preprocessor_infos and r.frontend.preprocessor_warnings
    with pytest.raises(DBaseCompilerError, match='Abbruch wegen Fehler'):
        compile_dbase_to_assembly('#error Abbruch wegen Fehler\n? 1\n', filename='foo.prg')


@pytest.mark.parametrize('target', ['pe32', 'pe64'])
def test_wfm_compiler_conditional_preamble_and_event_macros_link(target):
    source = '''#define FLAG 2
#if FLAG >= 2
STORE 21 TO z
#else
#error falscher Zweig
#endif
#info bereit __FILE__
#warn Testwarnung
CLASS Form1 OF FORM
    PROCEDURE Button1_onClick()
        #if FLAG == 2
        ? z
        #else
        #error nicht vorhanden
        #endif
        RETURN
ENDCLASS
'''
    asm = compile_slot_optimized(target, False, True, source)
    assert '__dbase_wfm_proc___dbase_top_level__' in asm
    assert '; STORE 21 TO z' in asm
    assert '; ? z' in asm
    lk = linkers()
    obj = lk[f'assemble_{target}_object_source'](asm)
    coff = lk[f'write_coff{64 if target == "pe64" else 32}_object'](obj)
    exe = lk[f'link_coff{64 if target == "pe64" else 32}_objects'](
        (coff,), entry_symbol='__d64_wfm_entry', gui=True)
    assert exe.executable.startswith(b'MZ')

@pytest.mark.parametrize('target', ['pe32', 'pe64'])
def test_wfm_include_expands_in_source_and_supports_defined_guard(tmp_path, target):
    header = tmp_path / 'common.h'
    header.write_text('''#ifndef LIB_WFM_COMMON_H
#define LIB_WFM_COMMON_H 1
#define CUSTOM_TEXT "Einbezogen"
#endif
''', encoding='utf-8')
    source = f'''#include "{header.as_posix()}"
#if defined(LIB_WFM_COMMON_H)
? CUSTOM_TEXT
#else
#error Include wurde nicht verarbeitet
#endif
CLASS Form1 OF FORM
ENDCLASS
'''
    asm = compile_slot_optimized(target, False, True, source)
    assert 'Einbezogen' in asm
    assert '__dbase_wfm_proc___dbase_top_level__' in asm
