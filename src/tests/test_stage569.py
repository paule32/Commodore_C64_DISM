"""Stage 569: Kontextmenue, Shortcut-Definitionen und Qt-unabhaengige History."""
from __future__ import annotations

import ast
from pathlib import Path
import tempfile
import unittest

from installer_table_editing import (
    INSTALLER_ROW_MIME, InstallerTableHistory, rows_from_clipboard,
    rows_to_mime_json, rows_to_tsv, snapshot_rows,
)
from software_installer_model import InstallerEntry, InstallerProject

SRC = (Path(__file__).resolve().parent / "software_installer.py").read_text(encoding="utf8")
TREE = ast.parse(SRC)


def method(cls_name, fn_name):
    cls = next(n for n in TREE.body if isinstance(n, ast.ClassDef) and n.name == cls_name)
    fn = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == fn_name)
    return ast.get_source_segment(SRC, fn)


class Stage569ContextSourceTests(unittest.TestCase):
    def test_menu_all_actions_order_separators_and_shortcuts(self):
        setup = method("InstallerTable", "_setup_table_actions")
        for name, shortcut in (
            ("Wiederherstellen", "Ctrl+Z"), ("Rückgängig", "Ctrl+Y"),
            ("Ausschneiden", "Ctrl+X"), ("Kopieren", "Ctrl+C"),
            ("Einfügen", "Ctrl+V"), ("Entfernen", "Delete"),
            ("Hinzufügen:  Datei", "Insert"), ("Hinzufügen:  Pfad", "Ctrl+Insert"),
            ("Datei:  öffnen", "Ctrl+D"), ("Eigenschaften", "Ctrl+Enter"),
        ):
            with self.subTest(name=name):
                self.assertIn('"' + name + '"', setup)
                self.assertIn('"' + shortcut + '"', setup)
        self.assertIn('Qt.WidgetWithChildrenShortcut', setup)
        self.assertIn('self.addAction(action)', setup)
        source = method("InstallerTable", "_show_context_menu")
        for block in ('"undo", "redo", None', '"cut", "copy", "paste", "remove", None',
                      '"file", "folder", None', '"open", "properties"'):
            self.assertIn(block, source)
        self.assertIn('installerTableContextMenu', source)
        self.assertIn('self._update_action_states()', source)

    def test_shortcuts_are_enabled_without_context_menu_open(self):
        init = method("InstallerTable", "__init__")
        self.assertIn('selectionChanged.connect(self._update_action_states)', init)
        self.assertIn('dataChanged.connect(self._update_action_states)', init)
        self.assertIn('self._update_action_states()', init)
        self.assertIn('self.tables[key]._update_action_states()', method(
            'SoftwareInstallerWorkbench', '_commit_rows'))

    def test_operations_use_correct_tab_and_history(self):
        for name in ('add_files', 'add_folder', 'show_file_properties',
                     'delete_selected_rows', 'copy_selected_rows',
                     'cut_selected_rows', 'paste_rows', 'open_selected_file'):
            self.assertIn('tab_key or self.current_tab_key()', method('SoftwareInstallerWorkbench', name))
        self.assertIn('self.table_history.clear()', method('SoftwareInstallerWorkbench', 'new_unnamed_project'))
        self.assertIn('self.table_history.clear()', method('SoftwareInstallerWorkbench', '_load_project_file'))
        self.assertIn('QDesktopServices.openUrl', method('SoftwareInstallerWorkbench', 'open_selected_file'))
        self.assertIn('entry.update_from_values(values)', method('SoftwareInstallerWorkbench', 'update_row').replace('entries[row].update_from_values(values)', 'entry.update_from_values(values)'))


class Stage569ClipboardAndHistoryTests(unittest.TestCase):
    def setUp(self):
        self.rows = [
            InstallerEntry(name='a.exe', target='C:\\Apps', local_path='C:\\Temp\\a.exe',
                           size='12', date='2026-11-10 10:00', file_version='1.0',
                           status='Vorhanden', package='Main', shortcut='Start'),
            InstallerEntry(name='b\twith_tab.txt', local_path='B:\\Source\\b.txt',
                           package='Line1\nLine2'),
        ]

    def test_complete_lossless_mime_roundtrip(self):
        blob = rows_to_mime_json(self.rows)
        back = rows_from_clipboard(blob)
        self.assertEqual(snapshot_rows(back), snapshot_rows(self.rows))
        self.assertEqual(INSTALLER_ROW_MIME, 'application/x-d64-installer-rows+json')

    def test_tsv_roundtrip_with_tabs_newlines(self):
        tsv = rows_to_tsv(self.rows)
        back = rows_from_clipboard(text=tsv)
        self.assertEqual(snapshot_rows(back), snapshot_rows(self.rows))

    def test_plain_text_single_col_and_wrong_cols(self):
        self.assertEqual([r.name for r in rows_from_clipboard(text='alpha\nbeta\n')], ['alpha', 'beta'])
        with self.assertRaises(ValueError):
            rows_from_clipboard(text='a\tb\n')
        with self.assertRaises(ValueError):
            rows_from_clipboard(mime_json=b'{malformed')
        with self.assertRaises(ValueError):
            rows_from_clipboard(mime_json=b'{"format":"wrong","version":1,"entries":[]}')

    def test_undo_redo_and_independent_tabs(self):
        history = InstallerTableHistory()
        a, e = [InstallerEntry(name='a')], [InstallerEntry(name='external')]
        before = snapshot_rows(a)
        a.append(InstallerEntry(name='b'))
        self.assertTrue(history.record('archive', before, a))
        self.assertTrue(history.can_undo('archive'))
        self.assertFalse(history.can_undo('external'))
        previous = history.undo('archive', a)
        self.assertEqual([r.name for r in previous], ['a'])
        self.assertTrue(history.can_redo('archive'))
        after = history.redo('archive', previous)
        self.assertEqual([r.name for r in after], ['a', 'b'])
        self.assertEqual([r.name for r in e], ['external'])

    def test_redo_invalidated_by_new_edit_and_empty_not_recorded(self):
        history = InstallerTableHistory()
        rows = [InstallerEntry(name='a')]
        original = snapshot_rows(rows)
        self.assertFalse(history.record('archive', original, rows))
        rows[0].name = 'b'
        history.record('archive', original, rows)
        restored = history.undo('archive', rows)
        self.assertEqual(restored[0].name, 'a')
        restored[0].name = 'c'
        history.record('archive', snapshot_rows([InstallerEntry(name='a')]), restored)
        self.assertFalse(history.can_redo('archive'))
        history.clear()
        self.assertFalse(history.can_undo('archive'))

    def test_project_json_roundtrip_after_cut_paste_and_undo(self):
        project = InstallerProject()
        project.entries['archive'] = self.rows
        project.entries['external'] = [InstallerEntry(name='separate')]
        pasted = rows_from_clipboard(rows_to_mime_json(project.entries['archive'][:1]))
        project.entries['external'].extend(pasted)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'stage569.installer.json'
            project.save(str(path))
            reloaded = InstallerProject.load(str(path))
        self.assertEqual([r.name for r in reloaded.entries['external']], ['separate', 'a.exe'])
        self.assertEqual(reloaded.entries['archive'][0].local_path, self.rows[0].local_path)


if __name__ == '__main__':
    unittest.main()
