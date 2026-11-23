"""Stage 649: dBASE CLASS DLL exports in a named PE32/PE64 include."""
from __future__ import annotations
from pathlib import Path
import re

import pytest

from d64dbase import compile_dbase_to_assembly
from windows_asm_macros import (
    externalize_windows_exports, externalize_windows_imports,
)
from test_stage605_link import _load_pe_linker

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / 'runtime/dbase/src/System.SysUtils.prg'


@pytest.mark.parametrize('target', ['pe32', 'pe64'])
def test_generated_include_name_original_lines_and_unchanged_exports(tmp_path, target):
    source = SOURCE.read_text('utf-8')
    result = compile_dbase_to_assembly(
        source, filename=str(SOURCE), target=target,
        source_kind='library', include_paths=[str(SOURCE.parent)])
    original = result.assembly
    asm_path = tmp_path / f'System.SysUtils.generated.{target}.asm'
    # GUI extraction order: first imports, then export declarations.
    imported_asm, import_path, import_text = externalize_windows_imports(original, asm_path)
    asm, inc_path, inc_text = externalize_windows_exports(imported_asm, asm_path)
    assert inc_path == tmp_path / f'System.SysUtils.{target}.inc'
    assert asm.count(f'%include "System.SysUtils.{target}.inc"') == 1
    assert re.search(r'(?m)^%line \d+$', asm)
    assert 'export "' not in asm
    assert len(inc_text.splitlines()) >= 20
    assert all(row.startswith('export "') for row in inc_text.splitlines())
    assert 'export "__dbase_cls_exception_create"' in inc_text

    # The line after %line must recover the *logical* number in the
    # already-generated ASM (after its import sidecar extraction).
    after_marker = next(i for i, row in enumerate(asm.splitlines())
                        if row.startswith('%line '))
    original_rows = imported_asm.splitlines()
    kept = asm.splitlines()[after_marker + 1]
    original_line = original_rows.index(kept) + 1
    assert asm.splitlines()[after_marker] == f'%line {original_line}'

    asm_path.write_text(asm, encoding='utf-8')
    assert import_path is not None
    import_path.write_text(import_text, encoding='utf-8')
    inc_path.write_text(inc_text, encoding='utf-8')
    linker = _load_pe_linker()
    assemble = linker[f'assemble_{target}_object_source']
    direct = assemble(original, filename=str(asm_path))
    include = assemble(asm, filename=str(asm_path))
    assert include.exports == direct.exports
    assert include.code == direct.code
    assert include.data == direct.data
    assert include.bss_size == direct.bss_size
    write = linker['write_coff32_object' if target == 'pe32' else 'write_coff64_object']
    link = linker['link_coff32_objects' if target == 'pe32' else 'link_coff64_objects']
    blob = write(include)
    dll = link((blob,), entry_symbol='__d64_dll_entry', dll=True, dll_name='RuntimeDB.dll')
    assert dll.executable.startswith(b'MZ')


@pytest.mark.parametrize('target', ['pe32','pe64'])
def test_line_mapping_inside_include_and_after_include(tmp_path, target):
    path = tmp_path / f'System.SysUtils.generated.{target}.asm'
    original = (f'bits {64 if target == "pe64" else 32}\n'
                'entry start\n'
                'export "start", start\n'
                'export "another", another\n'
                'section .text\n'
                'start:\n'
                '    ret\n'
                'another:\n'
                '    ret\n')
    compact, inc, text = externalize_windows_exports(original, path)
    assert '%line 5\nsection .text\n' in compact
    inc.write_text(text, 'utf8')
    linker = _load_pe_linker()
    source = linker['_preprocess_windows_assembly'](
        compact, str(path),
        linker['PE64AssemblerError' if target == 'pe64' else 'PE32AssemblerError'])
    assert (str(inc), 1) in source.locations
    assert (str(path), 5) in source.locations
    assert (str(path), 6) in source.locations

    # Intentional error after include: it must point to the original logical
    # ASM line, not the compacted physical line.
    bad = compact.replace('    ret\n', '    unsupported_instruction\n', 1)
    with pytest.raises(Exception) as exc:
        linker[f'assemble_{target}_object_source'](bad, filename=str(path))
    assert f'{path}:7:' in str(exc.value)

    # Intentional error in included file: retain include filename/line.
    inc.write_text(text + 'invalid_op\n', 'utf-8')
    with pytest.raises(Exception) as exc:
        linker[f'assemble_{target}_object_source'](compact, filename=str(path))
    assert f'{inc}:3:' in str(exc.value)


def test_no_exports_is_no_op_and_unusual_filename_diagnostic():
    src = 'bits 32\nentry _start\n_start: ret\n'
    result = externalize_windows_exports(src, 'demo.generated.pe32.asm')
    assert result == (src, None, None)
    with pytest.raises(ValueError, match='EXPORT-Auslagerung'):
        externalize_windows_exports('export "a", a\n', 'demo.asm')


def test_gui_dbase_export_externalization_and_saving_is_wired():
    gui = (ROOT / 'd64_dism.py').read_text('utf-8')
    begin = gui.index('        def _finish_compile_stage(')
    end = gui.index('        def ', begin + 20)
    block = gui[begin:end]
    assert 'if getattr(generated, "source_kind", "program") == "library"' in block
    assert '_small_asm, _export_path, _export_text = externalize_windows_exports(' in block
    assert '_asm_export_include = (_export_path, _export_text)' in block
    assert '_asm_export_include is not None:' in block
    assert 'self._write_assembled_program(_inc_path, _inc_text.encode("utf-8"))' in block


def test_noncontiguous_export_blocks_get_one_include_and_each_line_restored(tmp_path):
    original = ('bits 32\n'
                'export "a", a\n'
                '; comment between export groups\n'
                'export "b", b\n'
                'section .text\n'
                'a:\n    ret\n'
                'b:\n    ret\n')
    main, path, included = externalize_windows_exports(
        original, tmp_path / 'Demo.generated.pe32.asm')
    assert main.count('%include "Demo.pe32.inc"') == 1
    assert included == 'export "a", a\nexport "b", b\n'
    assert '%line 3\n; comment between export groups\n' in main
    assert '%line 5\nsection .text\n' in main
    path.write_text(included, encoding='utf-8')
    linker = _load_pe_linker()
    assembler = linker['assemble_pe32_object_source']
    direct = assembler(original)
    externalized = assembler(main, filename=str(tmp_path / 'Demo.generated.pe32.asm'))
    assert direct.code == externalized.code
    assert direct.exports == externalized.exports


@pytest.mark.parametrize('target', ['pe32', 'pe64'])
def test_att_syntax_keeps_dbase_exports_from_intel_include(tmp_path, target):
    from windows_asm_att import intel_to_att
    original = (f'bits {64 if target == "pe64" else 32}\n'
                'export "start", start\n'
                'entry start\n'
                'section .text\n'
                'start:\n    mov eax, 1\n    ret\n')
    filename = tmp_path / f'System.SysUtils.generated.{target}.asm'
    asm, path, content = externalize_windows_exports(original, filename)
    path.write_text(content, encoding='utf-8')
    att = intel_to_att(asm, target=target)
    linker = _load_pe_linker()
    obj = linker[f'assemble_{target}_object_source'](att, filename=str(filename))
    assert obj.exports == {'start': 'start'}
    assert obj.code.endswith(b'\xc3')
