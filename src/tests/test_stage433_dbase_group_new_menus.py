# -*- coding: utf-8 -*-
"""Stage 433: dBASE-Zweig-Kontextaktionen, Archive und Windows-Ressourcen.

Die Daten-/Dateitests benoetigen kein PyQt5; die Qt-Anbindung wird ueber die
gezielt extrahierten Methoden und einen minimalen Kontextmenue-Test verifiziert.
"""
from __future__ import annotations

import ast
from pathlib import Path
from types import SimpleNamespace

import pytest

from dbase_project_new import (
    DBASE_NEW_MENU, DBASE_GROUP_NEW_MENU, create_dbase_project_file,
)

ROOT = Path(__file__).parent
MAIN = (ROOT / "d64_dism.py").read_text(encoding="utf-8")


def _method_source(name):
    """Extract exactly one class-indented method, no 140k-line AST needed."""
    prefix = f"        def {name}("
    start = MAIN.index(prefix)
    next_method = MAIN.find("\n        def ", start + len(prefix))
    end = len(MAIN) if next_method < 0 else next_method
    return MAIN[start:end]


def test_all_eight_submenu_items_and_storage_targets():
    expected = {
        ("forms", ""): ("Neu:  Formular-Datei", ".wfm"),
        ("tables", ""): ("Neu:  Tabelle", ".dbf"),
        ("queries", ""): ("Neu:  Abfrage Datei", ".d64sql"),
        ("reports", ""): ("Neu:  Bericht Datei", ".d64report"),
        ("labels", ""): ("Neu:  Etikett Datei", ".d64label"),
        ("archives", ""): ("Neu:  Archiv Datei", ".a"),
        ("resources", "pe32"): ("Neu:  Windows PE32 Ressource Datei", ".rc"),
        ("resources", "pe64"): ("Neu:  Windows PE32+ Ressource Datei", ".rc"),
    }
    assert set(DBASE_GROUP_NEW_MENU) == set(expected)
    for key, (caption, suffix) in expected.items():
        spec = DBASE_GROUP_NEW_MENU[key]
        assert spec[0] == caption
        assert spec[1] == key[0]
        assert suffix in spec[2]
        assert spec[3].endswith(suffix)
        assert spec[4] == key[1]
    assert len(DBASE_NEW_MENU) == 8  # bisheriges Hauptmenue bleibt unveraendert


def test_archive_creation_valid_ar_and_no_overwrite(tmp_path):
    path = tmp_path / "Neue Bibliothek.a"
    assert create_dbase_project_file(path, "archives") == path
    assert path.read_bytes() == b"!<arch>\n"
    with pytest.raises(FileExistsError):
        create_dbase_project_file(path, "archives")
    assert path.read_bytes() == b"!<arch>\n"


def test_archive_parser_accepts_new_file(tmp_path):
    # Reale Formatprüfung mit dem unveränderten COFF-Archivanalysecode aus
    # Stage 432 (nur diese reine Funktion, keine Qt-Anwendung importieren).
    path = tmp_path / "empty.a"
    create_dbase_project_file(path, "archives")
    start = MAIN.index('def analyze_coff_archive_bytes(payload: bytes)')
    end = MAIN.index('\n# ---------------------------------------------------------------------------\n# Qt5-Anwendung', start)
    definition = MAIN[start:end]
    node = ast.parse(definition).body[0]
    ns = {'AR_MAGIC': b'!<arch>\n', 'Dict': dict}
    exec(compile(ast.Module(body=[node], type_ignores=[]), '<archive parser>', 'exec'), ns)
    info = ns['analyze_coff_archive_bytes'](path.read_bytes())
    assert info['size'] == 8
    assert info['members'] == []
    assert info['architectures'] == []


def test_group_menu_puts_new_action_first_and_dispatches_role():
    source = _method_source("_show_project_dbase_group_menu")
    assert source.index('new_file_action = menu.addAction(new_file_spec[0])') < source.index('add_action = menu.addAction(')
    assert source.index('new_file_action = menu.addAction(new_file_spec[0])') < source.index('clear_action = menu.addAction(')
    assert 'self._new_dbase_project_file(role, caption_override=new_file_spec[0])' in source
    assert 'self._create_new_dbase_program_item(use_template=False)' in source
    # Alle alten Aktionen bleiben erhalten.
    assert 'self.add_project_dbase_entries(item)' in source
    assert 'self.clear_project_dbase_group(item)' in source


def test_group_menu_simulated_qt_action_dispatch():
    """Menu method dynamically executed against small Qt-free fake widgets."""
    class Menu:
        latest = None
        def __init__(self, _parent):
            self.actions = []
            Menu.latest = self
        def addAction(self, label):
            action = SimpleNamespace(text=label, enabled=True)
            action.setEnabled = lambda enabled: setattr(action, 'enabled', enabled)
            self.actions.append(action)
            return action
        def addSeparator(self):
            self.actions.append(None)
        def exec_(self, _pos):
            return self.actions[0]
    class Item:
        def __init__(self, role): self.role = role
        def data(self, column, role): return self.role
        def childCount(self): return 0
        def isExpanded(self): return True
        def setExpanded(self, _val): pass
    fake_qt = SimpleNamespace(UserRole=0)
    class FakeTree:
        def viewport(self): return self
        def mapToGlobal(self, point): return point
    # Das AST fuer eine einzelne Methode wird als freie Funktion kompiliert.
    source = _method_source('_show_project_dbase_group_menu')
    method = ast.parse('class Dummy:\n' + source).body[0].body[0]
    ns = {'QMenu': Menu, 'Qt': fake_qt, 'DBASE_GROUP_NEW_MENU': DBASE_GROUP_NEW_MENU, 'QTreeWidgetItem': Item}
    exec(compile(ast.Module(body=[method], type_ignores=[]), '<group menu>', 'exec'), ns)
    for role in ('forms', 'tables', 'queries', 'reports', 'labels', 'archives'):
        calls = []
        host = SimpleNamespace(project_tree=FakeTree(),
                               _new_dbase_project_file=lambda *args, **kwargs: calls.append((args, kwargs)))
        ns['_show_project_dbase_group_menu'](host, Item(role), (0, 0))
        assert Menu.latest.actions[0].text == DBASE_GROUP_NEW_MENU[(role, '')][0]
        assert calls == [((role,), {'caption_override': DBASE_GROUP_NEW_MENU[(role, '')][0]})]


def test_windows_targets_dispatch_only_dbase_and_both_architectures():
    source = _method_source('show_project_context_menu')
    assert 'if kind == PROJECT_NODE_WINDOWS_TARGET:' in source
    fragment = source.split('if kind == PROJECT_NODE_WINDOWS_TARGET:', 1)[1].split('if kind == PROJECT_NODE_RESOURCE_ROOT:', 1)[0]
    assert 'if language == "dbase" else None' in fragment
    assert 'DBASE_GROUP_NEW_MENU.get(("resources", target))' in fragment
    assert 'menu.addAction(new_resource_spec[0])' in fragment
    assert fragment.index('menu.addAction(new_resource_spec[0])') < fragment.index('toggle_action = menu.addAction(')
    assert '"resources", target, caption_override=new_resource_spec[0]' in fragment
    assert ('resources', 'pe32') in DBASE_GROUP_NEW_MENU
    assert ('resources', 'pe64') in DBASE_GROUP_NEW_MENU


def test_existing_file_workflow_reused_and_archives_supported():
    source = _method_source('_new_dbase_project_file')
    assert 'for entry in DBASE_NEW_MENU' in source
    assert 'DBASE_GROUP_NEW_MENU.get((role, target))' in source
    assert 'if caption_override:' in source
    assert 'DBaseProjectOpenFileDialog(' in source
    assert 'dark_mode=self.dark_mode_enabled' in source
    assert 'self._add_project_dbase_entry(role, path, title=path.name)' in source
    assert 'self._add_project_resource_entry(' in source
    assert 'self.open_project_item(child)' in source
    assert 'self.save_project()' in source
    assert 'is_dbase_program_text(path)' in source
