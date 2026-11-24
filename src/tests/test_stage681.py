# -*- coding: utf-8 -*-
"""Stage 681: O3 must also recognize shipped System.Objects.prg methods."""
from __future__ import annotations

from pathlib import Path
import re

import pytest

from d64dbase import compile_dbase_to_assembly
from dbase_size_optimizer import optimize_dbase_size_assembly

ROOT = Path(__file__).resolve().parent
SYSTEM_OBJECTS = ROOT / 'runtime/dbase/src/System.Objects.prg'


def compiled(source, target):
    return compile_dbase_to_assembly(
        source, target=target, filename='<stage681-test>',
        include_paths=(str(SYSTEM_OBJECTS.parent),),
    ).assembly


@pytest.mark.parametrize('target,ptr', [('pe32', 'dd'), ('pe64', 'dq')])
def test_shipped_system_objects_library_can_use_o3_runtime_table(target, ptr):
    source = ('#include "System.Objects.prg"\n'
              'CLASS TChild OF TObject ENDCLASS\n'
              'obj = new TChild()\nobj.Free()\n? "O3"\n')
    raw = compiled(source, target)
    assert '; Stage 679: TObject builtin virtual methods; DLL fallback safe' in raw
    for level in ('O0', 'O1', 'O2'):
        assert '__dbase_class_object:' in optimize_dbase_size_assembly(raw, level=level).assembly
    result = optimize_dbase_size_assembly(raw, level='O3').assembly
    assert '__dbase_class_object:' not in result
    assert re.search(rf'__dbase_vmt_tobject:\n(?:\s*{ptr}\s+[^\n]+\n){{5}}\s*{ptr}\s+0\b', result)
    assert re.search(rf'__dbase_vmt_tchild:\n(?:\s*{ptr}\s+[^\n]+\n){{5}}\s*{ptr}\s+0\b', result)
    assert '__dbase_o3_abi_guard:' in result
    assert 'call __dbase_o3_default_vmt_abi' in result
    assert optimize_dbase_size_assembly(result, level='O3').assembly == result
    # Also check a real COFF object and linked executable for both targets.
    from test_stage605_link import _load_pe_linker
    backend = _load_pe_linker()
    assembler = backend['assemble_pe32_object_source' if target == 'pe32' else 'assemble_pe64_object_source']
    writer = backend['write_coff32_object' if target == 'pe32' else 'write_coff64_object']
    linker = backend['link_coff32_objects' if target == 'pe32' else 'link_coff64_objects']
    object_file = assembler(result)
    assert '__dbase_class_object' not in {name.casefold() for name in object_file.symbols}
    assert object_file.imports['__dbase_o3_default_vmt_abi'] == ('libd64_qt5.dll', 'jit_default_tobject_vmt_abi')
    assert linker((writer(object_file),), entry_symbol='_start', gui=True).executable[:2] == b'MZ'


@pytest.mark.parametrize('target', ('pe32', 'pe64'))
def test_real_tobject_free_override_still_requires_local_table(target):
    baseline = SYSTEM_OBJECTS.read_text(encoding='utf-8')
    assert 'jit_object_free(Self)' in baseline
    # A method whose body changes at all must never silently use the DLL body.
    override = baseline.replace('jit_object_free(Self)', 'jit_object_instance_free(Self)', 1)
    raw = compiled(override + '\nCLASS TChild OF TObject ENDCLASS\n', target)
    assert '; Stage 679: TObject custom virtual methods; no DLL fallback' in raw
    opt = optimize_dbase_size_assembly(raw, level='O3').assembly
    assert '__dbase_class_object:' in opt
    assert '__dbase_o3_abi_guard:' not in opt


def test_one_canonical_method_does_not_hide_another_custom_method():
    baseline = SYSTEM_OBJECTS.read_text(encoding='utf-8')
    source = baseline.replace(
        'return ClassNameAddress()',
        'return jit_class_name(jit_object_class_type(Self))',
        1,
    )
    raw = compiled(source, 'pe32')
    assert '; Stage 679: TObject custom virtual methods; no DLL fallback' in raw
    assert '__dbase_class_object:' in optimize_dbase_size_assembly(raw, level='O3').assembly


def test_without_tobject_override_no_change_in_o0():
    src = 'CLASS TChild OF TObject ENDCLASS\no = new TChild()\n'
    raw = compiled(src, 'pe32')
    assert optimize_dbase_size_assembly(raw, level='O0').assembly == raw
    assert '__dbase_class_object:' not in optimize_dbase_size_assembly(raw, level='O3').assembly
