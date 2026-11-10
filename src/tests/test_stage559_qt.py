"""Stage 559: Native Qt-Dialogtests (bei vorhandenem PyQt5 auch offscreen)."""
from __future__ import annotations
import json
import os
import unittest
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
try:
    from PyQt5.QtCore import Qt
    from PyQt5.QtWidgets import QApplication, QDialog, QMessageBox
    from software_installer_dialogs import (
        WIZARD_SIZE, InstallerSessionVariablesDialog,
    )
    from software_installer_model import InstallerProject
except ImportError:
    QApplication = None


@unittest.skipUnless(QApplication is not None, 'PyQt5 ist nicht installiert')
class Stage559QtTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def _dialog(self):
        return InstallerSessionVariablesDialog(InstallerProject(
            general={'product': 'Hello World', 'company': 'Beispiel'}), dark_mode=True)

    def test_geometry_and_panels(self):
        dialog = self._dialog()
        try:
            self.assertEqual(WIZARD_SIZE, (760,590))
            self.assertEqual((dialog.width(),dialog.height()),(620,550))
            self.assertEqual(len(dialog.panels),3)
            self.assertTrue(dialog.panels['product']._expanded)
            self.assertEqual(dialog.panels['product'].table.rowCount(),7)
            self.assertEqual(dialog.panels['directories'].table.rowCount(),2)
            dialog.panels['product'].toggle()
            self.assertFalse(dialog.panels['product']._expanded)
            dialog.panels['product'].toggle()
            self.assertTrue(dialog.panels['product']._expanded)
        finally:
            dialog.close()

    def test_fixed_first_column_and_mutable_value(self):
        dialog=self._dialog()
        try:
            table=dialog.panels['product'].table
            self.assertFalse(table.item(0,0).flags() & Qt.ItemIsEditable)
            self.assertTrue(table.item(0,1).flags() & Qt.ItemIsEditable)
            self.assertEqual(table.item(0,1).text(),'Hello World')
            table.item(0,1).setText('Geaendert')
            dialog._accept_changes()
            self.assertEqual(dialog.result(),QDialog.Accepted)
            self.assertEqual(json.loads(dialog.serialized)['overrides']['%ProductName%'],'Geaendert')
        finally:
            dialog.close()

    def test_cancel_does_not_mutate_project(self):
        project=InstallerProject()
        dialog=InstallerSessionVariablesDialog(project)
        try:
            dialog.panels['product'].table.item(0,1).setText('Niemals Speichern')
            dialog.reject()
            self.assertNotIn('Session Variable', project.sections)
        finally:
            dialog.close()


if __name__ == '__main__':
    unittest.main()
