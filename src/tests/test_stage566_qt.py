"""Optionale GUI-Tests: mit PyQt5 z.B. unter Windows oder QT_QPA_PLATFORM=offscreen."""
import os
import unittest

try:
    from PyQt5.QtCore import Qt
    from PyQt5.QtWidgets import QApplication, QDialog, QHeaderView
    from software_installer_dialogs import (
        InstallerSecurityDialog, InstallerSerialListPropertiesDialog,
    )
    from software_installer_model import InstallerProject
    HAVE_QT = True
except ImportError:
    HAVE_QT = False


@unittest.skipUnless(HAVE_QT, 'PyQt5 nicht installiert')
class SecurityQtTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_parent_geometry_tabs_dark_and_resizable_headers(self):
        dlg = InstallerSecurityDialog(InstallerProject(), dark_mode=True)
        self.assertEqual((dlg.width(), dlg.height()), (620, 550))
        self.assertEqual([dlg.tabs.tabText(i) for i in range(dlg.tabs.count())],
                         ['Serial Nummer', 'Gültigkeits-Bereich'])
        self.assertTrue(dlg._gradient_title)
        self.assertIn('stop:0 #000000, stop:1 #ffffff', dlg.styleSheet())
        self.assertFalse(dlg.lists_table.verticalHeader().isVisible())
        self.assertEqual(dlg.lists_table.horizontalHeader().sectionResizeMode(0),
                         QHeaderView.Interactive)
        self.assertEqual(len(dlg.serial_lists), 0)
        self.assertEqual([button.text() for button in dlg.list_buttons],
                         ['Hinzufügen', 'Entfernen', 'Bearbeiten'])
        dlg.close()

    def test_child_controls_serial_table_and_undo_redo(self):
        dlg = InstallerSerialListPropertiesDialog(dark_mode=True)
        self.assertEqual((dlg.width(), dlg.height()), (620, 550))
        self.assertEqual(dlg.name_edit.text(), 'Neue Liste')
        self.assertEqual(dlg.configuration_tree.topLevelItem(0).text(0),
                         'Alle Konfigurationen')
        self.assertEqual(dlg.configuration_tree.topLevelItem(0).child(0).text(0),
                         'Standard')
        self.assertEqual(dlg.serial_table.columnCount(), 3)
        self.assertFalse(dlg.serial_table.verticalHeader().isVisible())
        self.assertIs(dlg.commands_button.menu(), dlg.commands_menu)
        dlg._change_rows(['ABCD', 'EFGH'])
        self.assertEqual(dlg._rows(), ['ABCD', 'EFGH'])
        dlg._undo()
        self.assertEqual(dlg._rows(), [])
        dlg._redo()
        self.assertEqual(dlg._rows(), ['ABCD', 'EFGH'])
        dlg._accept_changes()
        self.assertEqual(dlg.result(), QDialog.Accepted)
        self.assertEqual(dlg.result_entry['serial_numbers'], ['ABCD', 'EFGH'])
        dlg.close()

    def test_root_tree_checkbox_changes_standard(self):
        dlg = InstallerSerialListPropertiesDialog(dark_mode=True)
        root = dlg.configuration_tree.topLevelItem(0)
        leaf = root.child(0)
        root.setCheckState(0, Qt.Unchecked)
        self.assertEqual(leaf.checkState(0), Qt.Unchecked)
        leaf.setCheckState(0, Qt.Checked)
        self.assertEqual(root.checkState(0), Qt.Checked)
        dlg.close()


if __name__ == '__main__':
    unittest.main()
