"""Stage 503: generated SESSION::<method>(param) compiles to native WFM code."""
from pathlib import Path
import pytest

from d64dbase.session_designer import SESSION_METHODS, parse_session_return_call
from test_stage460_wfm_typed_slot_optimization import compile_slot_optimized
from test_stage446_real_pe_link import linkers

ROOT = Path(__file__).resolve().parent


def form(method='deleteAlias', *, argument='param', object_name='SESSION1'):
    return f'''CLASS Form1 OF FORM
    THIS.{object_name} = NEW SESSION(THIS)
    WITH (THIS.{object_name})
        {method} = CLASS::{object_name}_{method.upper()}
        left = 80
        top = 80
    ENDWITH
    function {object_name}_{method}(param)
        return SESSION::{method}({argument})
ENDCLASS
'''


@pytest.mark.parametrize('method', SESSION_METHODS)
def test_grammar_accepts_all_method_wrappers(method):
    assert parse_session_return_call(f'SESSION::{method}(param)') == (method, 'param')
    assert parse_session_return_call(f'session :: {method.upper()} ( param )') == (method, 'param')


def test_grammar_rejects_unsupported_calls_instead_of_generic_colon_error():
    assert parse_session_return_call('5+3') is None
    with pytest.raises(ValueError, match='Unbekannte SESSION-Methode'):
        parse_session_return_call('SESSION::notExisting(param)')
    with pytest.raises(ValueError, match='SESSION:: erwartet'):
        parse_session_return_call('SESSION::deleteAlias(')


@pytest.mark.parametrize('target', ['pe32', 'pe64'])
@pytest.mark.parametrize('method', SESSION_METHODS)
def test_compiles_all_generated_methods_once_and_links_native_export(target, method):
    asm = compile_slot_optimized(target, False, False, source=form(method))
    assert asm.count('call DBaseQtWfmSessionInvoke') == 1
    assert asm.count(f'__dbase_wfm_proc_SESSION1_{method}:') == 1
    assert 'import DBaseQtWfmSessionInvoke, "libd64_qt5.dll", "DBaseQtWfmSessionInvoke"' in asm
    assert 'SESSION::' not in asm.split('call DBaseQtWfmSessionInvoke')[1][:100]
    if target == 'pe32':
        assert 'add esp, 20' in asm
    else:
        assert 'mov dword ptr [rsp+32], eax' in asm
        assert 'add rsp, 48' in asm


@pytest.mark.parametrize('target', ['pe32', 'pe64'])
def test_actual_windows_coff_linker_accepts_method_binding(target):
    asm = compile_slot_optimized(target, False, False, source=form())
    ns = linkers()
    if target == 'pe32':
        obj = ns['write_coff32_object'](ns['assemble_pe32_object_source'](asm))
        exe = ns['link_coff32_objects']((obj,), entry_symbol='__d64_wfm_entry', gui=True).executable
    else:
        obj = ns['write_coff64_object'](ns['assemble_pe64_object_source'](asm))
        exe = ns['link_coff64_objects']((obj,), entry_symbol='__d64_wfm_entry', gui=True).executable
    assert exe[:2] == b'MZ'
    assert b'DBaseQtWfmSessionInvoke' in exe


@pytest.mark.parametrize('bad_source,diagnostic', [
    (form(argument='wrong'), 'genau einem gleichnamigen Parameter'),
    (form(object_name='OTHER').replace('CLASS::OTHER_DELETEALIAS', 'CLASS::SESSION1_DELETEALIAS').replace('function OTHER_', 'function SESSION1_'), 'SESSION-Objekt SESSION1'),
    (form(method='deleteAlias').replace('SESSION::deleteAlias(param)', 'SESSION::notExisting(param)'), 'Unbekannte SESSION-Methode'),
])
def test_invalid_forwarders_raise_compiler_errors(bad_source, diagnostic):
    with pytest.raises(Exception, match=diagnostic):
        compile_slot_optimized('pe32', False, False, source=bad_source)


def test_existing_ordinary_wfm_return_and_old_session_methods_unchanged():
    src = '''CLASS Form1 OF FORM
FUNCTION normal(x)
    RETURN 7
ENDCLASS
'''
    asm = compile_slot_optimized('pe32', False, False, source=src)
    assert 'call DBaseQtWfmSessionInvoke' not in asm
    assert 'import DBaseQtWfmSessionInvoke' not in asm


def test_qt5_runtime_export_is_name_linked_optional_and_checked():
    deftext = (ROOT / 'd64qt5/d64qt5_bridge.def').read_text('utf-8')
    gen = (ROOT / 'd64qt5/generate_runtime_abi.py').read_text('utf-8')
    cpp = (ROOT / 'd64qt5/d64qt5_bridge.cpp').read_text('utf-8')
    header = (ROOT / 'd64qt5/d64qt5_bridge.h').read_text('utf-8')
    assert 'DBaseQtWfmSessionInvoke @1015' in deftext
    assert '"DBaseQtWfmSessionInvoke"' in gen
    assert 'DBaseQtWfmSessionInvoke(' in header
    assert 'extern "C" D64QT5_API int DBaseQtWfmSessionInvoke(' in cpp
    assert 'dbaseNonVisualClass' in cpp
    assert 'dbaseSessionLocalAliases' in cpp
