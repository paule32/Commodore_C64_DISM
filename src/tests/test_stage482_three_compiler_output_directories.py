"""Stage 482: restore three independent directory controls for Windows builds.

Qt5 is unavailable on the test host. GUI structure and signal plumbing are
therefore checked statically; path selection is tested with actual functions.
"""
from pathlib import Path
from types import SimpleNamespace
import ast
import os
import textwrap
import re
import pytest

CODE = Path(__file__).with_name('d64_dism.py').read_text(encoding='utf8')
TREE = ast.parse(CODE)


def _member(name):
    nodes = [n for n in ast.walk(TREE) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == name]
    assert len(nodes) >= 1, name
    source = textwrap.dedent(ast.get_source_segment(CODE, nodes[0]))
    scope = {'Path': Path, 'os': os, 'Optional': __import__('typing').Optional}
    exec('from __future__ import annotations\n' + source, scope)
    return scope[name]


def _owner(tmp_path, target, relative, unit_path):
    root = tmp_path / 'projekt'
    src = root / 'quellen' / 'App.pas'
    return SimpleNamespace(
        _project_windows_target_key=lambda value: value,
        _project_windows_base_directory=lambda: root,
        _document_windows_output_path=lambda doc: root / 'bin',
        project_windows_pascal_unit_output_directories={target: str(unit_path) if unit_path else ''},
        project_windows_relative_paths={target: {'output': relative}},
    ), SimpleNamespace(path=src, build_target=target)


@pytest.mark.parametrize('target', ['pe32', 'pe64'])
@pytest.mark.parametrize('relative', [True, False])
def test_unit_and_object_output_uses_third_directory(tmp_path, target, relative):
    root = tmp_path / 'projekt'
    owner, doc = _owner(tmp_path, target, relative, root / 'objekte')
    method = _member('_document_windows_pascal_unit_output_path')
    destination = method(owner, doc)
    expected = ((doc.path.parent if relative else root) / 'objekte').resolve()
    assert destination == expected
    # Generated .o path uses the same directory; EXE remains in root/bin.
    object_path = _member('_project_generated_object_path')
    obj = object_path(owner, doc.path, target, output_directory=destination)
    assert obj == expected / 'App.o'
    assert owner._document_windows_output_path(doc) == root / 'bin'


def test_legacy_output_directory_if_third_is_empty(tmp_path):
    owner, doc = _owner(tmp_path, 'pe32', True, '')
    assert _member('_document_windows_pascal_unit_output_path')(owner, doc) == tmp_path / 'projekt' / 'bin'


def test_exactly_three_editor_and_browse_pairs_and_labels():
    gui = CODE.split('            # Compiler -> Ausgabe-Verzeichnis', 1)[1].split('            # Stage 479:', 1)[0]
    assert gui.count('QLineEdit(self.output_directory_page)') == 3
    assert gui.count('QPushButton("...", self.output_directory_page)') == 3
    for label in ('Assembler-Zwischenspeicherung', 'ausführbare Datei', 'Bit *.pui und *.o Dateien'):
        assert label in gui
    assert 'relative Pfade' in gui
    assert 'Erzeugte {target_tag}-Bit *.pui- und *.o-Dateien werden' not in gui
    assert gui.index('Assembler-Zwischenspeicherung') < gui.index('ausführbare Datei') < gui.index('Bit *.pui und *.o Dateien')


def test_browse_button_signals_and_directory_result():
    for field in ('assembler_cache', 'output_directory', 'pascal_unit_output'):
        choose = '_choose_output_directory' if field == 'output_directory' else f'_choose_{field}_directory'
        edited = '_output_directory_edited' if field == 'output_directory' else f'_{field}_edited'
        assert f'self.{field}_button.clicked.connect(self.{choose})' in CODE
        assert f'self.{field}_edit.editingFinished.connect(self.{edited})' in CODE
    choose = ast.get_source_segment(CODE, next(n for n in ast.walk(TREE) if isinstance(n, ast.FunctionDef) and n.name == '_choose_pascal_unit_output_directory'))
    assert 'QFileDialog.getExistingDirectory' in choose
    assert 'self.pascal_unit_output_edit.setText(' in choose
    assert 'self._pascal_unit_output_edited()' in choose


def test_persistence_and_unit_routing_contract():
    for target in ('pe32', 'pe64'):
        assert f'"__windows_{target}_pascal_unit_output__"' in CODE
    assert '"PascalUnitOutput"' in CODE
    assert 'parser.get(_output_section, "PascalUnitOutput", fallback="")' in CODE
    assert 'entries[_settings["pascal_unit_output_key"]]' in CODE
    assert 'self.set_project_windows_pascal_unit_output_directory(' in CODE
    assert 'output_directory=_pascal_unit_output_directory' in CODE
    assert 'self._document_windows_pascal_unit_output_path(document)' in CODE


def test_default_project_document_objects_and_exe_are_distinct(tmp_path):
    output_fn = next(n for n in TREE.body if isinstance(n, ast.FunctionDef) and n.name == '_project_document_output_path')
    scope = {'Path': Path, 'os': os, 'AssemblerError': ValueError}
    exec('from __future__ import annotations\n' + ast.get_source_segment(CODE, output_fn), scope)
    func = scope['_project_document_output_path']
    root = tmp_path / 'project'
    owner = SimpleNamespace(
        project_windows_assembler_cache={'pe32': str(root / 'asm')},
        project_windows_output_directories={'pe32': str(root / 'bin')},
        project_windows_pascal_unit_output_directories={'pe32': str(root / 'unit')},
        project_windows_relative_paths={'pe32': {'output': True}},
        _project_windows_base_directory=lambda: root,
    )
    doc = SimpleNamespace(path=root / 'src' / 'Unit1.pas', build_target='pe32', window=lambda: owner)
    assert func(doc, 'Unit1.generated.pe32.asm') == (root / 'src' / 'asm' / 'Unit1.generated.pe32.asm').resolve()
    assert func(doc, 'Unit1.pui') == (root / 'src' / 'unit' / 'Unit1.pui').resolve()
    assert func(doc, 'Unit1.o') == (root / 'src' / 'unit' / 'Unit1.o').resolve()
    assert func(doc, 'Unit1.exe') == (root / 'src' / 'bin' / 'Unit1.exe').resolve()
