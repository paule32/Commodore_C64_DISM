"""Qt 5 GUI-Tests fuer Stage 569 (ohne PyQt5 ausdruecklich skipped)."""
import os
import unittest

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
try:
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtCore import Qt
    from software_installer import SoftwareInstallerWorkbench
    from software_installer_model import InstallerEntry
except ImportError:
    QApplication = None


@unittest.skipUnless(QApplication is not None, 'PyQt5 ist nicht installiert')
class Stage569GuiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.widget = SoftwareInstallerWorkbench()
        self.widget.project.entries['archive'] = [InstallerEntry(name='alpha')]
        self.widget.project.entries['external'] = [InstallerEntry(name='external')]
        self.widget.refresh_tables()
        self.widget.show()
        self.app.processEvents()

    def tearDown(self):
        self.widget.close()
        self.app.processEvents()

    def test_actions_exist_in_both_tables(self):
        for key in ('archive', 'external'):
            table = self.widget.tables[key]
            self.assertEqual(len(table.commands), 10)
            self.assertEqual(table.commands['file'].shortcut().toString(), 'Ins')
            self.assertEqual(table.commands['cut'].shortcut().toString(), 'Ctrl+X')
            self.assertEqual(table.commands['undo'].shortcutContext(), Qt.WidgetWithChildrenShortcut)

    def test_copy_cut_paste_and_undo_redo(self):
        a = self.widget.tables['archive']
        b = self.widget.tables['external']
        a.selectRow(0)
        self.assertTrue(self.widget.copy_selected_rows('archive'))
        b.setCurrentCell(0, 0)
        self.assertTrue(self.widget.paste_rows('external'))
        self.assertEqual([x.name for x in self.widget.project.entries['external']], ['alpha','external'])
        self.assertTrue(self.widget.table_undo('external'))
        self.assertEqual([x.name for x in self.widget.project.entries['external']], ['external'])
        self.assertTrue(self.widget.table_redo('external'))
        self.assertEqual([x.name for x in self.widget.project.entries['external']], ['alpha','external'])
        a.selectRow(0)
        self.assertTrue(self.widget.cut_selected_rows('archive'))
        self.assertEqual(self.widget.project.entries['archive'], [])
        self.assertTrue(self.widget.table_undo('archive'))
        self.assertEqual(self.widget.project.entries['archive'][0].name, 'alpha')

    def test_edit_row_undo_and_history_reset(self):
        a = self.widget.tables['archive']
        a.item(0, 0).setText('changed')
        self.assertTrue(self.widget.table_history.can_undo('archive'))
        self.assertTrue(self.widget.table_undo('archive'))
        self.assertEqual(self.widget.project.entries['archive'][0].name, 'alpha')
        self.widget.new_unnamed_project()
        self.assertFalse(self.widget.table_history.can_undo('archive'))


if __name__ == '__main__':
    unittest.main()
