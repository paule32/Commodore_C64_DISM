"""Stage 470: Windows PE32/PE64 macro preprocessor, include import externalization."""
from pathlib import Path

import pytest

from windows_asm_macros import (
    WindowsAsmMacroError, preprocess_windows_asm, externalize_windows_imports,
)
from test_stage446_real_pe_link import linkers


def test_conditions_nested_string_and_numeric_and_line_macros(tmp_path):
    include = tmp_path / 'extern.inc'
    include.write_text('''%define VERSION 2
%define LABEL "Hallo"
import ExitProcess, "kernel32.dll", "#392"
''', encoding='utf8')
    source = '''%include "<extern.inc>"
%define MAKRO 2
%if MAKRO == VERSION
  %if MAKRO <= 2
mov eax, MAKRO
  %else
mov eax, 250
  %endif
%elif MAKRO => 3
mov eax, 200
%else
mov eax, 0
%endif
%ifdef LABEL
value: db LABEL
%endif
%if LABEL == "Hallo"
msg: db "LABEL", "Hello"
%endif
%ifndef UNDEFINED
__BREAK__
%endif
lino: dd __LINE__
clock: db __TIME__, __DATE__
'''
    res = preprocess_windows_asm(source, filename=str(tmp_path / 'app.asm'))
    assert 'import ExitProcess, "kernel32.dll", "#392"' in res.source
    assert 'mov eax, 2' in res.source
    assert 'mov eax, 0' not in res.source
    assert 'mov eax, 250' not in res.source
    assert 'value: db "Hallo"' in res.source
    assert 'msg: db "LABEL", "Hello"' in res.source
    assert 'int3' in res.source
    assert 'lino: dd 23' in res.source  # original file line number
    assert '__TIME__' not in res.source
    assert '__DATE__' not in res.source
    assert len(res.source.splitlines()) >= len(source.splitlines())


@pytest.mark.parametrize('target', ['pe32', 'pe64'])
def test_real_windows_coff_import_assembly_and_link_with_include(tmp_path, target):
    (tmp_path / 'extern.inc').write_text(
        'import ExitProcess, "kernel32.dll", "#392"\n'
        '%define EXIT_STATUS 4\n', encoding='utf8'
    )
    source = '''%include "extern.inc"
section .text
entry _start
_start:
%if EXIT_STATUS >= 4
mov eax, EXIT_STATUS
%elif EXIT_STATUS < 3
mov eax, 3
%else
mov eax, 8
%endif
ret
'''
    name = tmp_path / f'hello.{target}.asm'
    name.write_text(source, encoding='utf8')
    ns = linkers()
    obj = ns[f'assemble_{target}_object_source'](source, filename=str(name))
    assert obj.code.startswith(b'\xb8\x04\x00\x00\x00')
    assert obj.imports['exitprocess'] == ('kernel32.dll', '#392')
    coff = ns[f'write_coff{64 if target == "pe64" else 32}_object'](obj)
    exe = ns[f'link_coff{64 if target == "pe64" else 32}_objects'](
        (coff,), entry_symbol='_start', gui=True
    )
    assert exe.executable.startswith(b'MZ')


@pytest.mark.parametrize('target', ['pe32', 'pe64'])
def test_real_dbase_wfm_imports_can_be_externalized(tmp_path, target):
    from test_stage460_wfm_typed_slot_optimization import compile_slot_optimized
    original = compile_slot_optimized(target, False, True)
    compact, external, content = externalize_windows_imports(
        original, tmp_path / f'Form1.generated.{target}.asm'
    )
    assert external is not None and content is not None
    assert 'import DBaseQt' not in compact
    assert len(compact) < len(original)
    assert compact.startswith('%include "Form1.generated.')
    external.write_text(content, encoding='utf8')
    ns = linkers()
    srcpath = tmp_path / f'Form1.generated.{target}.asm'
    obj = ns[f'assemble_{target}_object_source'](compact, filename=str(srcpath))
    assert obj.imports.get('dbaseqtformcreate')
    coff = ns[f'write_coff{64 if target == "pe64" else 32}_object'](obj)
    exe = ns[f'link_coff{64 if target == "pe64" else 32}_objects'](
        (coff,), entry_symbol='__d64_wfm_entry', gui=True
    )
    assert exe.executable.startswith(b'MZ')
    assert b'libd64_qt5.dll' in exe.executable


def test_cyclic_missing_and_unbalanced_include_error(tmp_path):
    src = tmp_path / 'main.asm'
    src.write_text('%include "other.inc"\n', encoding='utf8')
    (tmp_path / 'other.inc').write_text('%include "main.asm"\n', encoding='utf8')
    with pytest.raises(WindowsAsmMacroError, match='Zyklisches Include'):
        preprocess_windows_asm('%include "other.inc"', filename=str(src))
    with pytest.raises(WindowsAsmMacroError, match='Include-Datei nicht gefunden'):
        preprocess_windows_asm('%include "missing.inc"', filename=str(src))
    with pytest.raises(WindowsAsmMacroError, match='endif fehlt'):
        preprocess_windows_asm('%if 2 != 1\nmov eax, 3', filename=str(src))


def test_invalid_condition_does_not_execute_eval_and_reports_location(tmp_path):
    with pytest.raises(WindowsAsmMacroError, match='%if/%elif erwartet'):
        preprocess_windows_asm('%if __import__("os")\nmov eax, 1\n%endif', filename=str(tmp_path/'x.asm'))


def test_macro_error_references_included_file(tmp_path):
    (tmp_path/'err.inc').write_text('section .text\nwrong_asm 123\n', encoding='utf8')
    ns = linkers()
    src = '%include "err.inc"\n_start:\nret\n'
    for target in ['pe32','pe64']:
        with pytest.raises(Exception) as ei:
            ns[f'assemble_{target}_object_source'](src, filename=str(tmp_path / 'main.asm'))
        assert 'err.inc:2' in str(ei.value)


@pytest.mark.parametrize('target', ['pe32', 'pe64'])
def test_compiler_input_directories_used_for_nested_includes_and_linking(tmp_path, target):
    root = tmp_path / 'source'
    inp = tmp_path / 'projekt' / target / 'includes'
    sub = inp / 'sub'
    root.mkdir(); sub.mkdir(parents=True)
    (inp / 'extern.inc').write_text('%include "sub/imports.inc"\n%define STATUS 12\n', encoding='utf8')
    (sub / 'imports.inc').write_text('import ExitProcess, "kernel32.dll", "#392"\n', encoding='utf8')
    path = root / 'source.asm'
    source = '%include "extern.inc"\nsection .text\nentry _start\n_start:\nmov eax, STATUS\nret\n'
    path.write_text(source, encoding='utf8')
    macro = preprocess_windows_asm(source, filename=str(path), include_dirs=[inp])
    assert 'mov eax, 12' in macro.source
    assert str(sub / 'imports.inc') in {name for name, _ in macro.locations}
    ns = linkers()
    obj = ns[f'assemble_{target}_object_source'](source, filename=str(path), include_dirs=[inp])
    assert obj.code[:5] == b'\xb8\x0c\x00\x00\x00'
    assert obj.imports['exitprocess'] == ('kernel32.dll', '#392')
    coff = ns[f'write_coff{64 if target == "pe64" else 32}_object'](obj)
    linked = ns[f'link_coff{64 if target == "pe64" else 32}_objects']((coff,), entry_symbol='_start', gui=True)
    assert linked.executable.startswith(b'MZ')


def test_include_precedence_and_search_failure_lists_all_paths(tmp_path):
    root = tmp_path / 'root'; a = tmp_path / 'settingsA'; b = tmp_path / 'settingsB'
    for folder in (root, a, b): folder.mkdir()
    (root / 'priority.inc').write_text('%define PRIORITY 1\n', encoding='utf8')
    (a / 'priority.inc').write_text('%define PRIORITY 2\n', encoding='utf8')
    (b / 'priority.inc').write_text('%define PRIORITY 3\n', encoding='utf8')
    src = '%include "priority.inc"\nmov eax, PRIORITY\n'
    assert 'mov eax, 1' in preprocess_windows_asm(src, filename=str(root / 'main.asm'), include_dirs=[a,b]).source
    (root / 'priority.inc').unlink()
    assert 'mov eax, 2' in preprocess_windows_asm(src, filename=str(root / 'main.asm'), include_dirs=[a,b]).source
    (a / 'priority.inc').unlink()
    assert 'mov eax, 3' in preprocess_windows_asm(src, filename=str(root / 'main.asm'), include_dirs=[a,b]).source
    with pytest.raises(WindowsAsmMacroError) as exc:
        preprocess_windows_asm('%include "nope.inc"', filename=str(root/'main.asm'), include_dirs=[a,b])
    err = str(exc.value)
    assert 'geprüfte Pfade' in err
    for folder in (root, a, b):
        assert str(folder / 'nope.inc') in err


def test_gui_routes_project_settings_to_all_assembler_paths():
    source = (Path(__file__).parent / 'd64_dism.py').read_text(encoding='utf8')
    assert 'def _project_windows_asm_include_paths(self, target:' in source
    assert 'return self._project_windows_link_search_paths(target)' in source
    assert source.count('include_dirs=self._project_windows_asm_include_paths(document.build_target)') >= 6

@pytest.mark.parametrize('target', ['pe32', 'pe64'])
def test_breakpoint_macro_compiles_to_int3_in_both_windows_assemblers(target):
    ns = linkers()
    source = ('%define DEBUG 1\nsection .text\nentry _start\n_start:\n'
              '%ifdef DEBUG\n__BREAK__\n%endif\nret\n')
    obj = ns[f'assemble_{target}_object_source'](source)
    assert obj.code == b'\xcc\xc3'


def test_dll_import_detection_inside_project_include(tmp_path):
    project_inc = tmp_path / 'settings' / 'inc'
    project_inc.mkdir(parents=True)
    (project_inc / 'extern.inc').write_text('import DBaseConsoleWrite, "c64_dbase_runtime.dll", "#8"\n', encoding='utf8')
    main = tmp_path / 'source.asm'
    result = preprocess_windows_asm('%include "extern.inc"', filename=str(main), include_dirs=[project_inc])
    assert '"c64_dbase_runtime.dll"' in result.source
