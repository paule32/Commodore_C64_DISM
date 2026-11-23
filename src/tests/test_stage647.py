"""Stage 647 regression: SUPER(). inherited fields and numeric class concat."""
from pathlib import Path
import re
import pytest
from d64dbase.compiler import (compile_dbase_to_assembly, DBaseCompilerError,
    DBaseClassDefinition, parse_dbase_statements)

ROOT = Path(__file__).resolve().parent
SAMPLE = ROOT / 'examples/dbase/stage647_user_sysutils.prg'


def compile_sample(src, target, source_kind="library"):
    return compile_dbase_to_assembly(
        src, target=target, filename=str(SAMPLE.parent / 'stage647_driver.prg'),
        source_kind=source_kind, include_paths=[str(ROOT / 'runtime/dbase/src')]).assembly


@pytest.mark.parametrize('target', ['pe32', 'pe64'])
def test_original_class_definition_and_multiline_expression_compiles(target):
    src = SAMPLE.read_text(encoding='utf-8')
    classes = [x for x in parse_dbase_statements(src, filename=str(SAMPLE))
               if isinstance(x, DBaseClassDefinition)]
    ctor = next(m for cls in classes if cls.name == 'Win32Exception'
                for m in cls.methods if m.name == '__ini__')
    assert any('super().Code' in text and 'Text: ' in text for _, text in ctor.body)
    asm = compile_sample(src, target)
    assert 'call __dbase_cls_u32toa' in asm
    assert '__dbase_cls_u32toa:' in asm
    assert 'call __dbase_cls_api_LocalFree' in asm
    assert 'call __dbase_cls_concat3' in asm
    assert ('mov rax, qword ptr [rax+24]' if target == 'pe64'
            else 'mov eax, dword ptr [eax+12]') in asm


@pytest.mark.parametrize('target', ['pe32', 'pe64'])
def test_self_code_and_unqualified_code_compile(target):
    src = SAMPLE.read_text(encoding='utf-8')
    for spelling in ('self.Code', 'Code'):
        asm = compile_sample(src.replace('super().Code', spelling), target)
        assert 'call __dbase_cls_u32toa' in asm


@pytest.mark.parametrize('target', ['pe32','pe64'])
def test_parent_member_resolution_and_error(target):
    src = SAMPLE.read_text(encoding='utf-8').replace('super().Code', 'super().NoSuchField')
    with pytest.raises(DBaseCompilerError, match='kein geerbtes PROPERTY'):
        compile_sample(src, target)
    src = SAMPLE.read_text(encoding='utf-8').replace('super().Code', 'super().Own')
    src = src.replace('CLASS Win32Exception OF Exception',
                      'CLASS Win32Exception OF Exception\n    PUBLIC Own = 1')
    with pytest.raises(DBaseCompilerError, match='kein geerbtes PROPERTY'):
        compile_sample(src, target)


@pytest.mark.parametrize('target', ['pe32','pe64'])
def test_original_source_assembles_to_coff(target):
    from test_stage605_link import _load_pe_linker
    asm = compile_sample(SAMPLE.read_text(encoding='utf-8'), target)
    obj = _load_pe_linker()['assemble_' + target + '_object_source'](asm)
    assert obj.code


def test_user_sysutils_is_the_active_runtime_source():
    src = (ROOT / 'runtime/dbase/src/System.SysUtils.prg').read_text('utf-8')
    assert 'super().Code' in src and 'Text: ' in src

@pytest.mark.parametrize('target,offset', [('pe32',12), ('pe64',24)])
def test_win32raise_sets_code_before_constructor_which_formats_message(target,offset):
    src = '''#include "stage647_user_sysutils"
TRY
 Win32FileRaise(5)
CATCH (Win32Exception e)
 ? e.Code
 ? e.Message
ENDTRY'''
    asm = compile_sample(src, target, 'program')
    coded_factory = '__dbase_cls_win32fileexception_create_with_code'
    assert 'call ' + coded_factory in asm
    body = asm.split(coded_factory + ':',1)[1].split(coded_factory + '_done:',1)[0]
    store = (f'    mov dword ptr [rax+{offset}], edx' if target == 'pe64'
             else f'    mov dword ptr [ebx+{offset}], edx')
    assert body.index(store) < body.index('call __dbase_cls_win32exception___ini__')
    assert 'call __dbase_cls_exception_set_code' in asm  # Stage 646 ABI retained
    # Full PE32/PE64 integrated COFF smoke tested separately.
