"""Stage 493: WFM generated target filenames and safe assembler dispatch."""
from __future__ import annotations

import ast
from pathlib import Path
from types import SimpleNamespace
import os
import textwrap

import pytest

CODE = Path(__file__).with_name('d64_dism.py').read_text(encoding='utf-8')
TREE = ast.parse(CODE)


def member(name, symbols=None):
    nodes = [node for node in ast.walk(TREE) if isinstance(node, ast.FunctionDef) and node.name == name]
    assert nodes, name
    src = textwrap.dedent(ast.get_source_segment(CODE, nodes[-1]))
    ns = {'Path': Path, 'os': os, 'AssemblerError': ValueError,
          '_project_document_output_path': member('_project_document_output_path') if name == '_dbase_assembly_output_path' else None}
    ns.update(symbols or {})
    exec('from __future__ import annotations\n' + src, ns)
    return ns[name]


@pytest.mark.parametrize('target', ('pe32', 'pe64', 'linux32', 'linux64'))
def test_all_four_generated_assembly_names(tmp_path, target):
    path = tmp_path / 'Form2.wfm'
    doc = SimpleNamespace(path=path, build_target=target, window=lambda: None)
    assert member('_dbase_assembly_output_path')(doc) == tmp_path / f'Form2.generated.{target}.asm'


def test_dbase_linux_targets_are_not_disabled_by_document_syntax_refresh():
    nodes = [n for n in ast.walk(TREE) if isinstance(n, ast.FunctionDef) and n.name == 'update_syntax_highlighting']
    assert nodes
    source = ast.get_source_segment(CODE, nodes[0])
    assert 'elif is_dbase:' in source and 'item.setEnabled(index in {2, 3, 4, 5})' in source
    assert 'if (is_lisp or is_prolog or is_dbase) and self.build_target not in {"pe32", "pe64"}' not in source


def make_form_assemble_context(tmp_path, *, selected='linux64', built='linux64', path_target='linux64', doc_target='linux64'):
    source = tmp_path / 'Form2.wfm'
    generated = tmp_path / f'Form2.generated.{path_target}.asm'
    generated.write_text('section .text\nentry _start\n_start:\n ret\n', encoding='utf8')
    executable = tmp_path / ('Form2.elf64' if selected == 'linux64' else 'Form2.elf32')
    executable.write_bytes(b'ELF testing')
    events = []
    doc = SimpleNamespace(
        build_target=doc_target, generated_assembly_build_target=built,
        generated_assembly_path=generated, path=source, assembled_program_path=executable,
        generated_assembly_editor=SimpleNamespace(toPlainText=lambda: generated.read_text()),
        set_windows_application_mode=lambda value: events.append(('mode', value)),
        generated_source_kind='form',
    )
    owner = SimpleNamespace(
        dbase_form_build_document=doc,
        dbase_form_tabs=None,
        dbase_form_source_page=None,
        dbase_form_target_combo=SimpleNamespace(currentData=lambda: selected),
        dbase_form_assemble_button=None,
        dbase_form_start_button=None,
        dbase_form_progress=None,
        dbase_form_build_status=None,
        dbase_form_current_path=source,
        build_menu=None,
        _dbase_form_progress_begin=lambda phase: events.append(('begin',phase)),
        _dbase_form_progress_done=lambda phase, ok: events.append(('done', phase, ok)),
        _dbase_form_progress_step=lambda index,total: events.append(('progress',index,total)),
        log=lambda message: events.append(('log',message)),
        show_error=lambda title,message: events.append(('error',title,message)),
        _project_windows_asm_include_paths=lambda target: (),
        _serialize_dbase_form_wfm=lambda: 'CLASS Form2 OF FORM\nENDCLASS\n',
        assemble_generated_document=lambda item: events.append(('assembler',item.build_target)) or True,
    )
    return owner, events


def test_assembler_rejects_old_pe32_filename_for_linux64(tmp_path):
    owner, events = make_form_assemble_context(tmp_path, path_target='pe32')
    fn = member('assemble_dbase_form', {'QEventLoop': SimpleNamespace(ExcludeUserInputEvents=1)})
    assert fn(owner) is False
    assert not any(e[0]=='assembler' for e in events)
    assert any(e[0]=='error' and 'Form2.generated.linux64.asm' in e[2] for e in events)


def test_assembler_rejects_changed_target_without_recompiling(tmp_path):
    owner, events = make_form_assemble_context(tmp_path, built='pe32')
    assert member('assemble_dbase_form')(owner) is False
    assert not any(e[0]=='assembler' for e in events)


def test_assembler_rejects_doc_fallback_to_pe32(tmp_path):
    owner, events = make_form_assemble_context(tmp_path, doc_target='pe32')
    assert member('assemble_dbase_form')(owner) is False
    assert any(e[0]=='error' for e in events)


def test_linux64_assembler_button_uses_linux_dispatch(tmp_path):
    owner, events = make_form_assemble_context(tmp_path)
    module = SimpleNamespace(locations=tuple(range(5)))
    fn=member('assemble_dbase_form', {'preprocess_windows_asm': lambda *a,**k: module,
        'WindowsAsmMacroError': ValueError})
    assert fn(owner) is True
    assert ('assembler','linux64') in events
    assert ('done','assemble', True) in events
    assert not any(e[0]=='error' for e in events)


def test_wfm_compile_marks_architecture_and_linux_output_name():
    node=next(n for n in ast.walk(TREE) if isinstance(n,ast.FunctionDef) and n.name=='compile_dbase_form')
    source=ast.get_source_segment(CODE,node)
    assert 'document.generated_assembly_build_target = target' in source
    assert 'expected_filename = f"{document.path.stem}.generated.{target}.asm"' in source
    assert 'target in {"linux32", "linux64"}' in source


def test_switch_and_open_new_form_invalidate_stale_build():
    for name in ('_dbase_form_target_changed','open_dbase_form_file'):
        node=next(n for n in ast.walk(TREE) if isinstance(n,ast.FunctionDef) and n.name==name)
        source=ast.get_source_segment(CODE,node)
        assert 'generated_assembly_build_target = None' in source
        assert 'generated_assembly_path = None' in source
