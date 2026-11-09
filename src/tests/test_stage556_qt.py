"""Stage 556: echte UI-Tests mit PyQt5 (QT_QPA_PLATFORM=offscreen)."""
import os
import unittest
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
try:
    from PyQt5.QtGui import QColor
    from PyQt5.QtWidgets import QApplication
    from software_installer_dialogs import (
        WIZARD_SIZE, InstallerProjectStartDialog, InstallerGeneralInfoDialog,
        InstallerPlatformDialog, InstallerSourcesDialog, InstallerAppearanceDialog,
    )
    from software_installer_model import InstallerProjectRegistry
except ImportError:
    QApplication = None


@unittest.skipUnless(QApplication is not None, 'PyQt5 ist nicht installiert')
class Stage556QtTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_all_pages_identical_geometry_and_left_image(self):
        dialogs = [cls() for cls in (InstallerGeneralInfoDialog, InstallerPlatformDialog,
                                      InstallerSourcesDialog, InstallerAppearanceDialog)]
        try:
            for index, dialog in enumerate(dialogs):
                self.assertEqual((dialog.width(), dialog.height()), WIZARD_SIZE)
                self.assertEqual(dialog.image_box.width(), 140)
                self.assertEqual(dialog.gradient_title_bar.height(), 38)
                self.assertEqual(dialog.back_button.isEnabled(), index > 0)
        finally:
            for dialog in dialogs:
                dialog.close()

    def test_project_start_gradient_browse_left_and_radio_rules(self):
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as folder:
            dialog = InstallerProjectStartDialog(InstallerProjectRegistry(Path(folder) / 'registry.json'), dark_mode=True)
            try:
                self.assertTrue(dialog._gradient_title)
                self.assertFalse(dialog.browse_button.isEnabled())
                dialog.existing_radio.setChecked(True)
                self.assertTrue(dialog.browse_button.isEnabled())
            finally:
                dialog.close()

    def test_default_general_values_and_repopulated_back_navigation(self):
        dialog = InstallerGeneralInfoDialog()
        try:
            self.assertEqual(dialog.values(), {
                'company': 'Ihre Firma', 'product': 'Ihr Produkt',
                'version': '1.0', 'website': 'https://www.firma.de'})
            dialog.inputs['company'].setText('Firma A')
            restored = InstallerGeneralInfoDialog(values=dialog.values())
            try:
                self.assertEqual(restored.inputs['company'].text(), 'Firma A')
            finally:
                restored.close()
        finally:
            dialog.close()

    def test_platform_and_source_values_round_trip(self):
        page2 = InstallerPlatformDialog()
        try:
            page2.radio_64.setChecked(True)
            values = page2.values()
            self.assertEqual(values['platform'], '64')
            self.assertTrue(InstallerPlatformDialog(values=values).radio_64.isChecked())
        finally:
            page2.close()
        page3 = InstallerSourcesDialog(values={'source_directory': '/tmp/example',
                                               'include_subdirectories': 'true'})
        try:
            self.assertTrue(page3.include_check.isChecked())
            self.assertEqual(page3.values()['source_directory'], '/tmp/example')
        finally:
            page3.close()

    def test_appearance_controls_and_custom_color(self):
        dialog = InstallerAppearanceDialog()
        try:
            self.assertFalse(dialog.gradient_start.isEnabled())
            dialog.gradient_radio.setChecked(True)
            self.assertTrue(dialog.gradient_start.isEnabled())
            with patch('software_installer_dialogs.QColorDialog.getColor', return_value=QColor('#abcdef')):
                dialog.gradient_start.choose_custom_color()
            self.assertEqual(dialog.values()['gradient_start'], '#abcdef')
            dialog.image_radio.setChecked(True)
            self.assertTrue(dialog.image_edit.isEnabled())
            self.assertFalse(dialog.gradient_start.isEnabled())
            self.assertEqual(dialog.values()['appearance_style'], 'image')
        finally:
            dialog.close()


if __name__ == '__main__':
    unittest.main()
