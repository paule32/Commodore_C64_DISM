"""Stage 558: echte Qt-Dialogtests, auf Windows mit PyQt5/offscreen ausfuehren."""
from __future__ import annotations

import os
import unittest

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
try:
    from PyQt5.QtCore import Qt
    from PyQt5.QtWidgets import QApplication
    from software_installer_dialogs import (
        WIZARD_SIZE, InstallerProjectThemeDialog, InstallerLanguagesDialog,
        InstallerRequirementsDialog,
    )
    from installer_wizard_options import decode_selection, windows_leaf_ids
except ImportError:
    QApplication = None


@unittest.skipUnless(QApplication is not None, 'PyQt5 ist nicht installiert')
class Stage558QtTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_geometry_and_navigation_for_last_three_pages(self):
        dialogs = [InstallerProjectThemeDialog(), InstallerLanguagesDialog(),
                   InstallerRequirementsDialog()]
        try:
            for dialog in dialogs:
                self.assertEqual((dialog.width(), dialog.height()), WIZARD_SIZE)
                self.assertEqual(dialog.image_box.width(), 140)
                self.assertTrue(dialog.back_button.isEnabled())
            self.assertEqual(dialogs[0].next_button.text(), 'Weiter >')
            self.assertEqual(dialogs[1].next_button.text(), 'Weiter >')
            self.assertEqual(dialogs[2].next_button.text(), 'Fertigstellen')
        finally:
            for dialog in dialogs:
                dialog.close()

    def test_german_english_defaults_and_dynamic_language_list(self):
        dialog = InstallerLanguagesDialog()
        try:
            self.assertGreaterEqual(dialog.languages_list.count(), 40)
            self.assertEqual(dialog.values()['default_language'], 'de-DE')
            self.assertEqual(set(decode_selection(dialog.values()['languages'], ['de-DE', 'en-US'])),
                             {'de-DE', 'en-US'})
            self.assertEqual(dialog.default_language_combo.count(), 2)
            # Deutsch abwaehlen -> Englisch wird neue Standard-Sprache.
            for index in range(dialog.languages_list.count()):
                item = dialog.languages_list.item(index)
                if item.data(Qt.UserRole) == 'de-DE':
                    item.setCheckState(Qt.Unchecked)
                    break
            self.assertEqual(dialog.values()['default_language'], 'en-US')
            self.assertEqual(dialog.default_language_combo.count(), 1)
        finally:
            dialog.close()

    def test_restored_language_default_is_stable_when_checkboxes_change(self):
        dialog = InstallerLanguagesDialog(values={
            'languages': '["en-US","fr-FR"]', 'default_language': 'fr-FR'})
        try:
            self.assertEqual(dialog.default_language_combo.currentData(), 'fr-FR')
            self.assertEqual(dialog.values()['default_language'], 'fr-FR')
        finally:
            dialog.close()

    def test_windows_tree_parent_propagates_and_partial_is_recomputed(self):
        dialog = InstallerRequirementsDialog()
        try:
            desktop = dialog.windows_tree.topLevelItem(0)
            modern = desktop.child(1)
            self.assertEqual(modern.checkState(0), Qt.Checked)
            self.assertEqual(desktop.checkState(0), Qt.PartiallyChecked)
            # Alle modern-Windows-Ziele deaktivieren.
            modern.setCheckState(0, Qt.Unchecked)
            self.assertEqual(modern.child(0).checkState(0), Qt.Unchecked)
            self.assertEqual(modern.child(1).checkState(0), Qt.Unchecked)
            # Gesamte Desktop-Gruppe einschalten.
            desktop.setCheckState(0, Qt.Checked)
            self.assertEqual(desktop.checkState(0), Qt.Checked)
            for child_index in range(desktop.childCount()):
                group = desktop.child(child_index)
                self.assertEqual(group.checkState(0), Qt.Checked)
                for leaf_index in range(group.childCount()):
                    self.assertEqual(group.child(leaf_index).checkState(0), Qt.Checked)
            # Eine einzelne Windows-Version auswaehlen/abwaehlen.
            modern.child(0).setCheckState(0, Qt.Unchecked)
            self.assertEqual(modern.checkState(0), Qt.PartiallyChecked)
            self.assertEqual(desktop.checkState(0), Qt.PartiallyChecked)
            self.assertIn('win-11', decode_selection(dialog.values()['windows_versions'], windows_leaf_ids()))
        finally:
            dialog.close()

    def test_windows_flags_and_restored_options(self):
        dialog = InstallerRequirementsDialog(values={
            'support_uninstall': 'true', 'installation_log': 'true',
            'warn_administrator': 'true',
            'windows_versions': '["win-7","win-server-2025"]'})
        try:
            self.assertTrue(dialog.uninstall_check.isChecked())
            self.assertTrue(dialog.install_log_check.isChecked())
            self.assertTrue(dialog.warn_admin_check.isChecked())
            self.assertEqual(set(decode_selection(dialog.values()['windows_versions'],
                                                  windows_leaf_ids())),
                             {'win-7', 'win-server-2025'})
        finally:
            dialog.close()


if __name__ == '__main__':
    unittest.main()
