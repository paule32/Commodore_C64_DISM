"""Stage 560: synchronisierte Spaltenbreiten in Session-Variablen-Tabellen.

Die eigentliche synchronisierende Methode wird aus dem AST des Dialogmoduls
extrahiert und mit einfachen Testobjekten ausgefuehrt; deshalb benoetigen
die Kerntests kein PyQt5.
"""
from __future__ import annotations

import ast
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parent
SOURCE = (ROOT / "software_installer_dialogs.py").read_text(encoding="utf-8")


def _sync_function():
    tree = ast.parse(SOURCE)
    dialog = next(node for node in tree.body if isinstance(node, ast.ClassDef)
                  and node.name == "InstallerSessionVariablesDialog")
    method = next(node for node in dialog.body if isinstance(node, ast.FunctionDef)
                  and node.name == "_sync_session_name_column")
    unit = ast.fix_missing_locations(ast.Module(body=[method], type_ignores=[]))
    namespace = {}
    exec(compile(unit, "software_installer_dialogs.py", "exec"), namespace)
    return namespace[method.name]


class _FakeViewport:
    def __init__(self, width):
        self._width = width

    def width(self):
        return self._width


class _FakeTable:
    def __init__(self, width=195, viewport_width=480, visible=True):
        self._width = width
        self._viewport = _FakeViewport(viewport_width)
        self._visible = visible
        self.owner = None
        self.changed = 0

    def isVisible(self):
        return self._visible

    def viewport(self):
        return self._viewport

    def columnWidth(self, col):
        assert col == 0
        return self._width

    def setColumnWidth(self, col, width):
        assert col == 0
        old = self._width
        self._width = width
        self.changed += 1
        if self.owner is not None:
            self.owner._sync_session_name_column(0, old, width)


class _FakeDialog:
    _sync_session_name_column = _sync_function()

    def __init__(self, widths=(195, 195, 195), viewport_width=480):
        self._syncing_session_columns = False
        self._session_name_column_width = 195
        self.panels = {}
        for category, width in zip(("product", "directories", "custom"), widths):
            table = _FakeTable(width, viewport_width)
            table.owner = self
            self.panels[category] = SimpleNamespace(table=table)


class Stage560Tests(unittest.TestCase):
    def test_source_compiles_and_headerless_resize_is_enabled(self):
        ast.parse(SOURCE)
        for code in (
            'class InstallerResizableSessionTable(QTableWidget):',
            'self.table = InstallerResizableSessionTable(0, 2, self)',
            'header.hide()',
            'header.setSectionResizeMode(0, QHeaderView.Interactive)',
            'header.setSectionResizeMode(1, QHeaderView.Stretch)',
            'header.setSectionsMovable(False)',
            'sectionResized.connect(',
            'self.table.setFixedHeight(',
        ):
            self.assertIn(code, SOURCE)
        self.assertNotIn('header.setFixedHeight(15)', SOURCE)
        self.assertNotIn('setSectionResizeMode(0, QHeaderView.ResizeToContents)', SOURCE)

    def test_first_column_follows_resize_from_any_table(self):
        dlg = _FakeDialog()
        table = dlg.panels["directories"].table
        table.setColumnWidth(0, 250)
        self.assertEqual([p.table.columnWidth(0) for p in dlg.panels.values()],
                         [250, 250, 250])
        self.assertEqual(dlg._session_name_column_width, 250)

    def test_hidden_panel_is_also_updated(self):
        dlg = _FakeDialog()
        dlg.panels["custom"].table._visible = False
        dlg.panels["product"].table.setColumnWidth(0, 230)
        self.assertEqual(dlg.panels["custom"].table.columnWidth(0), 230)

    def test_second_column_resizing_does_not_change_first(self):
        dlg = _FakeDialog()
        dlg._sync_session_name_column(1, 180, 170)
        self.assertEqual([p.table.columnWidth(0) for p in dlg.panels.values()],
                         [195, 195, 195])

    def test_recursive_signals_are_guarded(self):
        dlg = _FakeDialog(widths=(150, 195, 120))
        dlg._sync_session_name_column(0, 150, 216)
        self.assertEqual([p.table.columnWidth(0) for p in dlg.panels.values()],
                         [216, 216, 216])
        self.assertFalse(dlg._syncing_session_columns)
        self.assertLess(sum(p.table.changed for p in dlg.panels.values()), 5)

    def test_column_width_leaves_space_for_value_column(self):
        dlg = _FakeDialog(viewport_width=340)
        dlg._sync_session_name_column(0, 195, 340)
        self.assertEqual([p.table.columnWidth(0) for p in dlg.panels.values()],
                         [244, 244, 244])

    def test_too_narrow_requested_width_uses_minimum(self):
        dlg = _FakeDialog()
        dlg._sync_session_name_column(0, 195, 30)
        self.assertEqual([p.table.columnWidth(0) for p in dlg.panels.values()],
                         [96, 96, 96])


if __name__ == "__main__":
    unittest.main()
