"""Stage 460: independent WFM slot optimizations, PE32/PE32+ actual assembler/linker."""
from __future__ import annotations

import ast
import re
import struct
import textwrap
from dataclasses import replace
from pathlib import Path

import pytest
from test_stage446_real_pe_link import linkers

ROOT = Path(__file__).parent
SOURCE = (ROOT / 'd64_dism.py').read_text(encoding='utf8')
FORM = '''Form1 = NEW Form1()
CLASS Form1 OF FORM
    PROCEDURE PushButton1_onClick()
        STORE "Hallo Äpfel" TO Text
        STORE 2 TO Wert
        STORE Wert TO Kopie
        STORE "Text" TO Wert
        STORE 5 TO Wert
        ? ISKEYBOARD()
        ? ISKEYBOARD()
        ? ISMOUSE()
        ? LEN(Text)
        ? LEN(Text)
        ? ISUPPER("Ä")
        RETURN
ENDCLASS
'''


def compile_slot_optimized(target, static_numeric, dynamic_typed, source=FORM):
    start = SOURCE.index('        def _compile_dbase_wfm_fallback(\n')
    stop = SOURCE.index('        def compile_dbase_form(self) -> bool:', start)
    code = textwrap.dedent(SOURCE[start:stop])
    namespace = {
        're': re, 'struct': struct, 'replace': replace,
        '_normalize_project_windows_debug_theme': lambda x: x,
        'AssemblerError': type('AssemblerError', (Exception,), {}),
        'DBASE_WFM_PROPERTY_DEFAULTS_ABI': 1,
        '__name__': 'stage460',
    }
    ast.parse(code)
    exec(compile(code, '<stage460 compiler>', 'exec'), namespace)

    class Stub:
        _compile_dbase_wfm_fallback = namespace['_compile_dbase_wfm_fallback']
        project_windows_import_packer = {}
        project_windows_dbase_slots = {
            target: {'static_numeric_internal_slots': static_numeric,
                     'dynamic_typed_variables': dynamic_typed}
        }

        @staticmethod
        def _dbase_wfm_int(props, name, default):
            return int(next((v for k, v in (props or {}).items()
                            if k.casefold() == name.casefold()), default))

        @staticmethod
        def _dbase_wfm_prop(props, name, default=None):
            return next((v for k, v in (props or {}).items()
                         if k.casefold() == name.casefold()), default)

        @staticmethod
        def _dbase_wfm_asm_bytes(value):
            return ', '.join(map(str, str(value).encode('utf8')))

    return Stub()._compile_dbase_wfm_fallback(
        source, filename='stage460.wfm', target=target,
    ).assembly


def test_independent_gui_and_ini_settings_are_persistent():
    for target in ('pe32', 'pe64'):
        for field in ('static_numeric_slots', 'dynamic_typed_variables'):
            assert f'__windows_{target}_dbase_{field}__' in SOURCE
    for token in (
        '"static numeric internal slots"', '"dynamic typed variables"',
        '"Variablen und Speicher"',
        'StaticNumericInternalSlots', 'DynamicTypedVariables',
        'set_project_windows_dbase_slot_settings',
        'set_dbase_slot_settings',
        'project_windows_dbase_slots',
        'compiler.dbase.optimization',
        'entries[_settings["dbase_dynamic_typed_variables_key"]]',
    ):
        assert token in SOURCE


@pytest.mark.parametrize('target', ['pe32', 'pe64'])
@pytest.mark.parametrize('static_numeric,dynamic_typed', [
    (False, False), (True, False), (False, True), (True, True),
])
def test_four_independent_switch_modes_assemble_and_link(
    target, static_numeric, dynamic_typed
):
    asm = compile_slot_optimized(target, static_numeric, dynamic_typed)
    assert '__dbase_wfm_mem_Wert_type:' in asm
    assert '__dbase_wfm_mem_Wert_num:' in asm
    assert '__dbase_wfm_mem_Wert_ptr:' in asm
    assert '__dbase_wfm_mem_Wert_len:' in asm
    assert '    call DBaseQtConsoleWrite' in asm

    if static_numeric:
        # These internal slots stay numeric even across repeated events.
        assert re.search(r'__dbase_wfm_mem___wfm_iskeyboard_print_type:\s+dd 1\b', asm)
        assert re.search(r'__dbase_wfm_mem___wfm_ismouse_print_type:\s+dd 1\b', asm)
        # 'Wert' is a STORE variable which changes from number to string.
        assert re.search(r'__dbase_wfm_mem_Wert_type:\s+resd 1\b', asm)
        assert re.search(r'__dbase_wfm_mem___wfm_len_\d+_type:\s+dd 1\b', asm)
        assert asm.count('mov dword ptr [__dbase_wfm_mem___wfm_iskeyboard_print_type], 1') == 0
    else:
        assert re.search(r'__dbase_wfm_mem___wfm_iskeyboard_print_type:\s+resd 1\b', asm)
        assert not re.search(r'__dbase_wfm_mem___wfm_len_\d+_type:\s+dd 1\b', asm)

    if dynamic_typed:
        assert '    call __dbase_wfm_assign_numeric_header' in asm
        assert '    call __dbase_wfm_copy_variant' in asm
        assert '__dbase_wfm_assign_numeric_header:' in asm
        assert '__dbase_wfm_copy_variant:' in asm
        assert asm.count('__dbase_wfm_assign_numeric_header:') == 1
    else:
        assert '__dbase_wfm_assign_numeric_header:' not in asm
        assert '__dbase_wfm_copy_variant:' not in asm
        assert 'mov dword ptr [__dbase_wfm_mem_Wert_type], 1' in asm

    funcs = linkers()
    coff_obj = funcs[f'assemble_{target}_object_source'](asm)
    bits = 64 if target == 'pe64' else 32
    coff = funcs[f'write_coff{bits}_object'](coff_obj)
    result = funcs[f'link_coff{bits}_objects'](
        (coff,), entry_symbol='__d64_wfm_entry', gui=True
    )
    assert result.executable.startswith(b'MZ')


def test_dynamic_header_keeps_exact_pe32_pe64_field_offsets():
    a32 = compile_slot_optimized('pe32', False, True)
    a64 = compile_slot_optimized('pe64', False, True)
    assert '    mov dword ptr [eax], edx' in a32
    assert '    mov dword ptr [eax+12], 0' in a32
    assert '    mov dword ptr [eax+16], 0' in a32
    assert '    mov dword ptr [rcx], edx' in a64
    assert '    mov qword ptr [rcx+12], 0' in a64
    assert '    mov dword ptr [rcx+20], 0' in a64
    assert '    mov r8, qword ptr [rcx+12]' in a64
    assert '    mov qword ptr [rdx+12], r8' in a64


def test_static_numeric_never_claims_explicit_user_memory_alias():
    # A reserved-looking name can still be used by a legacy WFM STORE.
    # Such a slot MUST remain dynamically typed, regardless of checkbox.
    source = FORM.replace(
        '        STORE 2 TO Wert',
        '        STORE "WFM Text" TO __wfm_iskeyboard_print\n'
        '        STORE 2 TO Wert',
    )
    asm = compile_slot_optimized('pe32', True, False, source)
    assert '__dbase_wfm_mem___wfm_iskeyboard_print_type:\n    resd 1' in asm
    assert '    mov dword ptr [__dbase_wfm_mem___wfm_iskeyboard_print_type], 1' in asm
