"""Stage 443: echte WFM-Event-Assembler-Regression gegen Stage 441 Builtins."""
from __future__ import annotations

import ast
from pathlib import Path
import re
import struct
import textwrap
from dataclasses import replace
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))


def _compile_wfm_for_test(source: str, *, target="pe32"):
    """Extrahiert ausschließlich die PyQt-unabhängige WFM-Compilerfunktion."""
    full = (ROOT / "d64_dism.py").read_text(encoding="utf-8")
    start = full.index("        def _compile_dbase_wfm_fallback(\n")
    stop = full.index("        def compile_dbase_form(self) -> bool:", start)
    definition = textwrap.dedent(full[start:stop])
    ast.parse(definition)
    context = {
        "re": re, "struct": struct, "replace": replace,
        "_normalize_project_windows_debug_theme": lambda value: value,
        "AssemblerError": type("AssemblerError", (Exception,), {}),
        "DBASE_WFM_PROPERTY_DEFAULTS_ABI": 1,
        "__name__": "stage443_wfm_test",
    }
    exec(compile(definition, '<extracted dBase WFM>', 'exec'), context)

    class Stub:
        _compile_dbase_wfm_fallback = context['_compile_dbase_wfm_fallback']
        project_windows_import_packer = {}

        @staticmethod
        def _dbase_wfm_int(props, name, default):
            return int(next((v for k,v in (props or {}).items() if k.casefold() == name.casefold()), default))

        @staticmethod
        def _dbase_wfm_prop(props, name, default=None):
            return next((v for k,v in (props or {}).items() if k.casefold() == name.casefold()), default)

        @staticmethod
        def _dbase_wfm_asm_bytes(value):
            return ", ".join(str(b) for b in str(value).encode("utf-8"))

    return Stub()._compile_dbase_wfm_fallback(
        source, filename='form_test.wfm', target=target,
        workstation_mode=False, debug_theme='default',
    )


WFM = '''Form1 = NEW Form1()
CLASS Form1 OF FORM
    PROCEDURE PushButton1_onClick()
        STORE " Grüß dich  " TO Text
        ? LEN(Text)
        ?? LEN("Hallo")
        ? "länge: " + LEN(Text)
        STORE LEN(Text) TO Zahl
        IF LEN(Text) > 0
            ? Zahl
        ENDIF
        ? TRIM(Text)
        ? LEN(TRIM(Text))
        ? RTRIM(" xyz  ")
        RETURN
ENDCLASS
'''


def test_wfm_len_in_print_and_store_pe32_pe64():
    for target in ('pe32', 'pe64'):
        assembly = _compile_wfm_for_test(WFM, target=target).assembly
        assert 'WFM Event-Assembler Stage 203' not in assembly
        assert '__dbase_wfm_flow_len_loop_' in assembly
        assert 'cmp eax, 128' in assembly
        assert 'fild dword ptr [__dbase_temp_number]' in assembly
        assert '__dbase_wfm_mem_Zahl' in assembly
        assert 'DBaseQtConsoleWrite' in assembly


def test_wfm_len_follows_dynamic_memory_value_not_compile_time_constant():
    assembly = _compile_wfm_for_test(WFM, target='pe32').assembly
    assert 'dword ptr [__dbase_wfm_mem_Text_len]' in assembly
    assert 'dword ptr [__dbase_wfm_mem_Text_type]' in assembly
    assert 'mov esi, dword ptr [__dbase_wfm_mem_Text_ptr]' in assembly


def test_wfm_len_rejects_numeric_string_operand():
    source = WFM.replace('STORE " Grüß dich  " TO Text', 'STORE 42 TO Text')
    try:
        _compile_wfm_for_test(source)
    except Exception as exc:
        assert 'erwartet Text' in str(exc)
    else:
        raise AssertionError('LEN(42-Variable) wurde akzeptiert')


def test_wfm_trim_uses_reserved_shadow_space_in_pe64():
    assembly = _compile_wfm_for_test(WFM, target='pe64').assembly
    # WFM-Callback hat seinen eigenen 32-Byte-Shadow-Space und darf fuer
    # __dbase_malloc nicht nochmals 40 Bytes reservieren.
    assert '    call __dbase_malloc' in assembly
    assert '    sub rsp, 40\n    call __dbase_malloc' not in assembly
    assert '    mov ecx, eax\n    call __dbase_malloc' in assembly


def test_wfm_quoted_len_text_remains_ordinary_literal():
    wfm = WFM.replace('? LEN(Text)', '? "LEN(Text)"')
    assembly = _compile_wfm_for_test(wfm, target='pe32').assembly
    assert 'DBaseQtConsoleWrite' in assembly
