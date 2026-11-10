"""Stage 561: Spaltengrenzen in Session-Tabellen ohne Header ziehen.

Qt-unabhaengige Struktur-/Geometriepruefungen; die native Mausinteraktion
ist in test_stage561_qt.py abgedeckt.
"""
from __future__ import annotations

import ast
import unittest
from pathlib import Path
from types import SimpleNamespace

SOURCE = (Path(__file__).resolve().parent / 'software_installer_dialogs.py').read_text('utf-8')


def _divider_method():
    root = ast.parse(SOURCE)
    klass = next(node for node in root.body
                 if isinstance(node, ast.ClassDef)
                 and node.name == 'InstallerResizableSessionTable')
    method = next(node for node in klass.body
                  if isinstance(node, ast.FunctionDef)
                  and node.name == '_near_session_divider')
    unit = ast.fix_missing_locations(ast.Module(body=[method], type_ignores=[]))
    namespace = {}
    exec(compile(unit, '<divider>', 'exec'), namespace)
    return namespace['_near_session_divider']


class _FakeDividerTable:
    RESIZE_GRAB_WIDTH = 6
    _near_session_divider = _divider_method()

    def __init__(self, boundary):
        self.boundary = boundary

    def columnViewportPosition(self, column):
        assert column == 1
        return self.boundary


class Stage561Tests(unittest.TestCase):
    def test_source_parses(self):
        ast.parse(SOURCE)

    def test_header_is_completely_hidden(self):
        self.assertIn('header.hide()', SOURCE)
        self.assertNotIn('header.setFixedHeight(15)', SOURCE)
        self.assertNotIn('self.table.setHorizontalHeaderLabels(("", ""))', SOURCE)
        self.assertNotIn('QTableWidget#installerSessionTable QHeaderView::section', SOURCE)

    def test_resize_is_based_on_viewport_mouse_events(self):
        for needle in ('class InstallerResizableSessionTable(QTableWidget):',
                       'def mousePressEvent(self, event):',
                       'def mouseMoveEvent(self, event):',
                       'def mouseReleaseEvent(self, event):',
                       'self.viewport().setMouseTracking(True)',
                       'self.viewport().setCursor(Qt.SplitHCursor)',
                       'self._resize_start_width + event.x() - self._resize_start_x',
                       'self.setColumnWidth(0, max(96, int(requested)))'):
            self.assertIn(needle, SOURCE)

    def test_mouse_hit_zone_uses_true_column_position(self):
        table = _FakeDividerTable(195)
        self.assertTrue(table._near_session_divider(189))
        self.assertTrue(table._near_session_divider(195))
        self.assertTrue(table._near_session_divider(201))
        self.assertFalse(table._near_session_divider(188))
        self.assertFalse(table._near_session_divider(202))
        table.boundary = -1
        self.assertFalse(table._near_session_divider(-1))

    def test_empty_custom_table_remains_drag_accessible(self):
        self.assertIn('max(1, len(variables)) * self.table.verticalHeader().defaultSectionSize()', SOURCE)

    def test_original_signal_propagation_remains(self):
        self.assertIn('panel.table.horizontalHeader().sectionResized.connect(', SOURCE)
        self.assertIn('self._sync_session_name_column)', SOURCE)
        self.assertIn('self._syncing_session_columns', SOURCE)
        self.assertIn('header.setSectionResizeMode(1, QHeaderView.Stretch)', SOURCE)


if __name__ == '__main__':
    unittest.main()
