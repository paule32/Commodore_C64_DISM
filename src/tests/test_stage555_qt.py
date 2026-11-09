"""Optionale native PyQt5-Tests; mit QT_QPA_PLATFORM=offscreen ausführbar."""
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
try:
    from PyQt5.QtWidgets import QApplication, QDialog
    from software_installer import SoftwareInstallerWorkbench
    from software_installer_dialogs import (
        InstallerGeneralInfoDialog, InstallerProjectStartDialog,
        InstallerProjectNameDialog, InstallerDestinationDialog,
    )
    from software_installer_model import InstallerProject, InstallerProjectRegistry
except ImportError:
    QApplication = None


@unittest.skipUnless(QApplication is not None, 'PyQt5 ist nicht installiert')
class InstallerDialogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_start_dialog_radio_and_browse_states(self):
        with tempfile.TemporaryDirectory() as folder:
            registry = InstallerProjectRegistry(Path(folder) / 'projects.json')
            dialog = InstallerProjectStartDialog(registry, dark_mode=True)
            self.assertEqual(dialog.windowTitle(), 'Neues Projekt starten')
            self.assertFalse(dialog.projects_list.isEnabled())
            self.assertFalse(dialog.browse_button.isEnabled())
            self.assertTrue(dialog.wizard_check.isEnabled())
            dialog.existing_radio.setChecked(True)
            self.assertTrue(dialog.projects_list.isEnabled())
            self.assertTrue(dialog.browse_button.isEnabled())
            self.assertFalse(dialog.wizard_check.isEnabled())
            dialog.close()

    def test_registry_list_and_manual_choice(self):
        with tempfile.TemporaryDirectory() as folder:
            file = Path(folder) / 'Beispiel.installer.json'
            project = InstallerProject(name='Beispiel')
            project.save(str(file))
            registry = InstallerProjectRegistry(Path(folder) / 'projects.json')
            registry.register(file, project)
            dialog = InstallerProjectStartDialog(registry)
            dialog.existing_radio.setChecked(True)
            self.assertEqual(dialog.projects_list.count(), 1)
            dialog.projects_list.setCurrentRow(0)
            dialog._accept_choice()
            self.assertEqual(dialog.selected_path, str(file.resolve()))
            dialog.close()

    def test_first_wizard_values_and_disabled_back(self):
        wizard = InstallerGeneralInfoDialog(dark_mode=True)
        self.assertFalse(wizard.back_button.isEnabled())
        wizard.inputs['company'].setText('ACME')
        wizard.inputs['product'].setText('IDE')
        self.assertEqual(wizard.values()['company'], 'ACME')
        self.assertEqual(wizard.values()['product'], 'IDE')
        self.assertEqual(wizard.windowTitle(), 'Allgemeine Informationen')
        wizard.close()

    def test_second_wizard_back(self):
        dialog = InstallerDestinationDialog()
        dialog.buttons[0].click()
        self.assertEqual(dialog.result(), InstallerDestinationDialog.BACK)

    def test_global_save_as_roundtrip_without_file_dialog(self):
        with tempfile.TemporaryDirectory() as folder:
            registry_file = Path(folder) / 'software_installer_projects.json'
            workbench = SoftwareInstallerWorkbench()
            workbench.registry = InstallerProjectRegistry(registry_file)
            workbench.project.general['company'] = 'ACME'
            with patch('software_installer.installer_registry_path', return_value=registry_file), \
                 patch.object(InstallerProjectNameDialog, 'exec_', return_value=QDialog.Accepted):
                self.assertTrue(workbench.save_configuration())
            self.assertTrue(Path(workbench.project_filename).is_file())
            self.assertFalse(workbench.needs_save_as)
            self.assertFalse(workbench.dirty)
            self.assertEqual(workbench.registry.available()[0]['settings']['general']['company'], 'ACME')
            workbench.new_unnamed_project()
            self.assertEqual(workbench.project.name, 'Unbenannt')
            self.assertTrue(workbench.needs_save_as)
            self.assertIsNone(workbench.project_filename)
            workbench.close()


if __name__ == '__main__':
    unittest.main()
