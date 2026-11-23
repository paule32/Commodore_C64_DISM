# -*- coding: utf-8 -*-
"""Stage 663 – root Hilfe, project settings, dock switch, runtime help."""
import ast
import json
import textwrap
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).parent
MAIN = (ROOT / 'd64_dism.py').read_text(encoding='utf-8')
GUI = (ROOT / 'turbo_help_settings.py').read_text(encoding='utf-8')
HELP = (ROOT / 'd64qt5/d64_turbo_help_window.hpp').read_text(encoding='utf-8')
BRIDGE = (ROOT / 'd64qt5/d64qt5_bridge.cpp').read_text(encoding='utf-8')


def pure_functions():
    parsed = ast.parse(GUI)
    wanted = {'default_help_settings', 'normalize_help_settings',
              'search_directories', 'write_application_help_manifest'}
    selected = [node for node in parsed.body if isinstance(node, ast.FunctionDef)
                and node.name in wanted]
    ns = {'Path': Path, 'SCOPES': ('entwicklung', 'anwendung')}
    exec('from pathlib import Path\n' + '\n'.join(ast.get_source_segment(GUI, f)
         for f in selected), ns)
    return ns


def test_help_is_last_independent_root_not_debug_child():
    roots = 'for title in ("Umgebung", "Compiler", "Assembler", "Linker", "Debug", "Hilfe")'
    assert roots in MAIN
    assert 'self.nodes["hilfe"], ["Entwicklung"]' in MAIN
    assert 'self.nodes["hilfe"], ["Anwendung"]' in MAIN
    assert '"hilfe.entwicklung"' in MAIN and '"hilfe.anwendung"' in MAIN
    assert 'self.nodes["debug"], ["Hilfe"]' not in MAIN


def test_help_pages_have_search_paths_and_compressor_controls():
    assert "QGroupBox('Suchpfade:'" in GUI
    assert "QGroupBox('Compressor'" in GUI
    for name in ['Hinzufügen', 'Löschen', 'Abbrechen',
                 'relative Pfade', 'Microsoft CHM', 'internal',
                 'Verzeichnis:', 'Pfad:']:
        assert name in GUI
    assert 'QFileDialog.getExistingDirectory' in GUI
    assert 'QFileDialog.getOpenFileName' in GUI
    assert 'QMessageBox.question' in GUI


def test_help_project_settings_are_serialized_and_loaded():
    assert 'PROJECT_HELP_SETTINGS_SECTION = "Settings.Windows.Hilfe"' in MAIN
    assert '"Values": json.dumps(_help_rows[0]' in MAIN
    assert 'entries[PROJECT_HELP_SETTINGS_KEY] = [_help_values]' in MAIN
    assert 'self.project_help_settings = normalize_help_settings(' in MAIN


def test_default_settings_independent_and_normalize_bad_values():
    fn = pure_functions()
    settings = fn['default_help_settings']()
    assert list(settings) == ['entwicklung', 'anwendung']
    settings['entwicklung']['paths'].append('help/chm')
    assert settings['anwendung']['paths'] == []
    invalid = fn['normalize_help_settings']({'entwicklung': {'paths': 'bad',
                                       'compressor': 'oops', 'relative': True}})
    assert invalid['entwicklung']['paths'] == []
    assert invalid['entwicklung']['compressor'] == 'internal'
    assert invalid['entwicklung']['relative']


def test_help_manifest_is_named_after_executable_and_preserves_order(tmp_path):
    fn = pure_functions()
    exe = tmp_path / 'output' / 'MyApp.exe'
    settings = {'anwendung': {'relative': True, 'paths': ['help', 'doc', 'extra'],
                              'compressor': 'microsoft', 'hh_path': 'hh.exe'}}
    path = fn['write_application_help_manifest'](exe, settings)
    assert path == exe.with_suffix('.help.json')
    result = json.loads(path.read_text(encoding='utf-8'))
    assert result == {'format': 'd64-turbo-help-paths-v1',
                      'relative': True, 'directories': ['help', 'doc', 'extra']}
    assert list(tmp_path.glob('*.hlp')) == []


def test_relative_development_search_paths_use_project_parent(tmp_path):
    fn = pure_functions()
    file = tmp_path / 'project' / 'project.pro'
    dirs = fn['search_directories']({'entwicklung': {'paths': ['help', '../manuals']}},
                                    'entwicklung', file)
    assert dirs == [(file.parent / 'help').resolve(),
                    (file.parent / '../manuals').resolve()]


def test_help_dock_switch_checks_unsaved_work_and_restores_layout():
    # The handler is extracted verbatim and tested without Qt dependencies.
    beginning = MAIN.index('        def _hide_turbo_help_for_project_leaf(')
    end = MAIN.index('\n        def _on_project_item_double_clicked(', beginning)
    code = textwrap.dedent(MAIN[beginning:end])
    ns = {'PROJECT_NODE_TURBO_HELP_ROOT': 'root',
          'PROJECT_NODE_TURBO_HELP_FILE': 'thlp'}
    exec(code, ns)
    fn = ns['_hide_turbo_help_for_project_leaf']

    class Dock:
        visible = True
        def isVisible(self): return self.visible
        def hide(self): self.visible = False

    class Owner:
        def __init__(self, saved):
            self.turbo_help_compiler_dock = Dock()
            self.saved = saved
            self.restored = False
            self._exclusive_tool_workspace = {'owner': self.turbo_help_compiler_dock}
        def _project_item_kind(self, item): return item.kind
        def _turbo_help_active_editor(self):
            return SimpleNamespace(save_all_documents=lambda: self.saved)
        def _restore_exclusive_tool_workspace(self, dock):
            self.restored = True
    leaf = SimpleNamespace(kind='dbase_file', parent=lambda: object())
    owner = Owner(False)
    assert fn(owner, leaf) is False
    assert owner.turbo_help_compiler_dock.visible and not owner.restored
    owner.saved = True
    assert fn(owner, leaf) is True
    assert not owner.turbo_help_compiler_dock.visible and owner.restored
    owner = Owner(True)
    assert fn(owner, SimpleNamespace(kind='thlp', parent=lambda: object())) is True
    assert owner.turbo_help_compiler_dock.visible


def test_project_settings_title_close_button_is_100_pixels_after_label():
    assert 'titlebar.layout().insertSpacing(1, 100)' in MAIN
    assert 'titlebar.close_button.setText("schließen")' in MAIN
    assert 'titlebar.layout().insertWidget(2, titlebar.close_button)' in MAIN


def test_qt5_help_title_tracks_topic_and_latest_shadow():
    assert 'setOffset(5.0, 5.0)' in HELP  # Stage 664: requested 5-px offset
    assert 'setGraphicsEffect(shadow)' in HELP
    assert 'QStringLiteral("Hilfe:  ") + resolvedTopic' in HELP
    assert 'caption_ = caption' in HELP
    assert 'exeInfo.completeBaseName() + QStringLiteral(".help.json")' in BRIDGE
    assert 'exeDir.filePath(exeInfo.completeBaseName() + QStringLiteral(".hlp"))' in BRIDGE


def test_chm_backend_prefers_python_and_never_unconditionally_invokes_hh():
    assert 'def extract_with_pychm(' in MAIN
    assert 'from chm import chmlib' in MAIN
    assert 'if mode == "microsoft":' in MAIN
    assert 'cls.extract_with_windows_help(source, target, hh_path)' in MAIN
    assert 'cls.extract_with_pychm(source, target)' in MAIN
