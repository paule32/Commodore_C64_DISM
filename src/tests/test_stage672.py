# -*- coding: utf-8 -*-
"""Stage 672: O1 dispatch de-duplication for repeated static outputs."""
from __future__ import annotations

from pathlib import Path
import pytest
from dbase_size_optimizer import optimize_dbase_size_assembly
from dbase_output_compactor import compact_dbase_static_outputs
from d64dbase import compile_dbase_to_assembly

ROOT = Path(__file__).resolve().parent
SOURCE = '? "Hallo"\n? "Welt"\n? "Nummer"\n? "vier"\n'


@pytest.mark.parametrize('target', ['pe32', 'pe64'])
def test_real_generator_shared_dispatch_and_o0(target):
    asm = compile_dbase_to_assembly(SOURCE, target=target).assembly
    off = optimize_dbase_size_assembly(asm, level='O0')
    on = optimize_dbase_size_assembly(asm, level='O1')
    assert off.assembly == asm
    assert '__dbase_o1_output_write:' not in off.assembly
    assert '__dbase_o1_output_write:' not in on.assembly
    assert on.assembly.count('call DBaseQtRuntimeWrite') >= 4
    assert on.assembly.count('import DBaseQtRuntimeWrite') == 1
    assert 'call DBaseQtAppendDebug' in on.assembly
    assert 'call DBaseConsoleWrite' in on.assembly
    assert on.replacements > 0
    assert on.assembly.startswith('bits '+ ('64' if target == 'pe64' else '32')) or 'section .text' in on.assembly
    assert optimize_dbase_size_assembly(on.assembly, level='O1').assembly == on.assembly
    # All old source lines stay on their original numbers (helper only appended).
    initial_lines = len(asm.splitlines())
    assert on.assembly.splitlines()[initial_lines].startswith('; Stage 673 / O1:')


@pytest.mark.parametrize('target', ['pe32', 'pe64'])
def test_dynamic_output_is_not_hoisted_before_debug_visibility(target):
    # Both dynamic arms read their pointer/length *after* the visibility call;
    # a correct optimizer must not hoist those reads into an early wrapper.
    asm = compile_dbase_to_assembly('? "one"\n? "two"\n? "three"\n', target=target).assembly
    # Replace one static writer pair with dynamic memory operands: only this
    # block must remain unchanged, while the other blocks can be compacted.
    first = asm.index('call DBaseQtAppendDebug')
    # Replace the literal+length in both arms of that matching output block.
    beginning = asm.rfind('cmp dword ptr [__dbase_output_debug_override], -1', 0, first)
    ending = asm.index('__dbase_output_done_', first)
    end_label_end = asm.index('\n', asm.index(':', ending))
    block = asm[beginning:end_label_end]
    import re
    if target == 'pe32':
        block_new = re.sub(r'push \d+\n\s+push __dbase_text_\d+',
                           'push dword ptr [runtime_length]\n    push dword ptr [runtime_pointer]',block)
    else:
        block_new = re.sub(r'mov rcx, __dbase_text_\d+\n\s+mov edx, \d+',
                           'mov rcx, qword ptr [runtime_pointer]\n    mov edx, dword ptr [runtime_length]',block)
    changed = asm[:beginning] + block_new + asm[end_label_end:]
    optimized = compact_dbase_static_outputs(changed)
    assert block_new in optimized.assembly
    assert optimized.blocks >= 3  # other static output blocks remain


def test_uploaded_app001_static_output_and_source_map():
    sample = Path('/mnt/data/App001.generated.pe32.asm')
    asm = sample.read_text('utf8') if sample.exists() else (ROOT/'tests/fixtures/App001.generated.pe32.asm').read_text('utf8')
    result = compact_dbase_static_outputs(asm)
    assert result.blocks >= 8
    assert result.instructions_saved > 0
    assert result.assembly.count('call DBaseQtRuntimeWrite') == result.blocks
    assert '__dbase_vmt_exception:' in result.assembly
    assert 'dd __dbase_class_object' in result.assembly
    assert result.assembly.splitlines()[:len(asm.splitlines())] != asm.splitlines()  # call replacements
    assert result.assembly.splitlines()[len(asm.splitlines())].startswith('; Stage 673 / O1:')


def test_unrelated_jumps_and_custom_assembler_remain_untouched():
    src = ('bits 32\nsection .text\nstart:\n'
           '    jmp done\ndone:\n    ret\nsection .data\nvalue:\n    dd 1\n')
    result = compact_dbase_static_outputs(src)
    assert result.assembly == src
    assert result.blocks == 0


def test_no_external_entry_to_rewritten_internal_labels():
    base = compile_dbase_to_assembly(SOURCE, target='pe32').assembly
    import re
    # An external use of a local selector label prevents its transformation.
    label = re.search(r'(__dbase_output_console_\d+):', base).group(1)
    altered = base + '\nsection .text\n; artificially referenced selector\n    jmp ' + label + '\n'
    result = compact_dbase_static_outputs(altered)
    assert result.blocks >= 3
    # It must preserve the first block because an external jump reaches it.
    assert '    je ' + label in result.assembly
    assert '    jmp ' + label in result.assembly


@pytest.mark.parametrize('target', ['pe32', 'pe64'])
def test_assembled_machine_code_is_shorter_and_links(target):
    from test_stage605_link import _load_pe_linker
    native = _load_pe_linker()
    source = compile_dbase_to_assembly(SOURCE,target=target).assembly
    optimized = optimize_dbase_size_assembly(source,level='O1').assembly
    assemble = native['assemble_pe32_object_source' if target=='pe32' else 'assemble_pe64_object_source']
    original_obj = assemble(source)
    smaller_obj = assemble(optimized)
    assert len(smaller_obj.code) < len(original_obj.code)
    assert {key for key in original_obj.symbols if not key.startswith("__dbase_output_")} <= set(smaller_obj.symbols)
    assert len(smaller_obj.code) < len(original_obj.code) * 0.95


def test_uploaded_app001_real_pe32_link_with_external_import_sidecar(tmp_path):
    """Real user upload: O0/O1 should both produce a linkable PE32 executable."""
    from test_stage605_link import _load_pe_linker
    import shutil
    root = Path('/mnt/data')
    asm_path = root/'App001.generated.pe32.asm'
    include_path = root/'App001.generated.pe32.extern.inc'
    if not asm_path.exists():
        asm_path = ROOT/'tests/fixtures/App001.generated.pe32.asm'
    if not include_path.exists():
        include_path = ROOT/'tests/fixtures/App001.generated.pe32.extern.inc'
    if not asm_path.exists() or not include_path.exists():
        pytest.skip('App001 ASM + import sidecar fixture not installed')
    source = asm_path.read_text('utf8')
    shutil.copyfile(include_path, tmp_path/include_path.name)
    native = _load_pe_linker()
    old_obj = native['assemble_pe32_object_source'](source,
        filename=str(tmp_path/asm_path.name),include_dirs=(str(tmp_path),))
    compact_source = optimize_dbase_size_assembly(source, level='O1').assembly
    new_obj = native['assemble_pe32_object_source'](compact_source,
        filename=str(tmp_path/asm_path.name),include_dirs=(str(tmp_path),))
    assert len(new_obj.code) < len(old_obj.code)
    assert set(old_obj.imports.items()).issubset(set(new_obj.imports.items()))
    assert new_obj.imports["dbaseqtruntimewrite"] == ("libd64_qt5.dll", "DBaseQtRuntimeWrite")
    assert new_obj.data == old_obj.data
    old_coff = native['write_coff32_object'](old_obj)
    new_coff = native['write_coff32_object'](new_obj)
    old_exe = native['link_coff32_objects']((old_coff,),entry_symbol='_start',gui=True)
    new_exe = native['link_coff32_objects']((new_coff,),entry_symbol='_start',gui=True)
    assert len(new_exe.executable) < len(old_exe.executable)
    assert new_exe.executable.startswith(b'MZ')
    assert old_exe.executable.startswith(b'MZ')


@pytest.mark.parametrize('target', ['pe32', 'pe64'])
def test_multi_coff_objects_with_compacted_output_link(tmp_path, target):
    from test_stage605_link import _load_pe_linker
    from dbase_module_coff import strip_program_entry_assembly, namespace_module_object
    from pascal_console_dependencies import inspect_pe
    native = _load_pe_linker()
    assemble = native['assemble_pe32_object_source' if target=='pe32' else 'assemble_pe64_object_source']
    write = native['write_coff32_object' if target=='pe32' else 'write_coff64_object']
    link = native['link_coff32_inputs' if target=='pe32' else 'link_coff64_inputs']
    docs = []
    for name in ('App001', 'Utility'):
        src = tmp_path/f'{name}.prg'
        src.write_text(SOURCE, encoding='utf8')
        asm = optimize_dbase_size_assembly(
            compile_dbase_to_assembly(SOURCE, target=target).assembly,
            level='O1').assembly
        if name == 'Utility':
            asm = strip_program_entry_assembly(asm)
            obj = namespace_module_object(assemble(asm), src)
        else:
            obj = assemble(asm)
        outfile = src.with_suffix('.o')
        outfile.write_bytes(write(obj))
        docs.append(outfile)
    image = link(docs,entry_symbol='_start',gui=True).executable
    exe = tmp_path/'App001.exe'
    exe.write_bytes(image)
    assert image[:2] == b'MZ'
    assert inspect_pe(exe)[0] == (0x14c if target=='pe32' else 0x8664)
