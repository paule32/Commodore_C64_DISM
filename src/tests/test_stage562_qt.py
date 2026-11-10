"""Native/offscreen Qt GUI-Tests fuer Stage 562 (Windows mit PyQt5)."""
import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
try:
    from PyQt5.QtCore import Qt
    from PyQt5.QtWidgets import QApplication, QDialog
    from installer_background_settings import BACKGROUND_SECTION, parse_background_settings
    from software_installer_model import InstallerProject
    from software_installer_dialogs import InstallerBackgroundWindowDialog, WIZARD_SIZE
    from software_installer import InstallerWorkspaceDock
except ImportError:
    QApplication = None


@unittest.skipUnless(QApplication is not None, "PyQt5 nicht installiert")
class Stage562QtTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_background_dialog_style_geometry_and_controls(self):
        dlg = InstallerBackgroundWindowDialog(InstallerProject(), dark_mode=True)
        try:
            self.assertEqual((dlg.width(), dlg.height()),
                             (WIZARD_SIZE[0] - 140, WIZARD_SIZE[1] - 40))
            self.assertTrue(dlg._gradient_title)
            self.assertEqual(len(dlg.mode_radios), 3)
            self.assertEqual(len(dlg.text_edits), 3)
            self.assertTrue(dlg.static_color.isEnabled())
            dlg.image_radio.setChecked(True)
            self.assertTrue(dlg.image_edit.isEnabled())
            self.assertFalse(dlg.static_color.isEnabled())
        finally:
            dlg.close()

    def test_accept_and_cancel(self):
        project = InstallerProject()
        dlg = InstallerBackgroundWindowDialog(project)
        try:
            dlg.show_background_check.setChecked(True)
            dlg.mode_radios['kiosk'].setChecked(True)
            dlg.image_radio.setChecked(True)
            dlg.image_edit.setText(r'C:\Example\background.png')
            dlg.text_edits['title'].setText('Neuer Titel')
            dlg.text_align_radios['title']['right'].setChecked(True)
            dlg._accept_changes()
            self.assertEqual(dlg.result(), QDialog.Accepted)
            settings = parse_background_settings(dlg.serialized)
            self.assertTrue(settings['enabled'])
            self.assertEqual(settings['mode'], 'kiosk')
            self.assertEqual(settings['appearance'], 'image')
            self.assertEqual(settings['title_text'], 'Neuer Titel')
            self.assertEqual(settings['title_align'], 'right')
            self.assertNotIn(BACKGROUND_SECTION, project.sections)
        finally:
            dlg.close()
        cancelled = InstallerBackgroundWindowDialog(project)
        try:
            cancelled.text_edits['title'].setText('Nicht speichern')
            cancelled.reject()
            self.assertIsNone(cancelled.serialized)
            self.assertNotIn(BACKGROUND_SECTION, project.sections)
        finally:
            cancelled.close()

    def test_dock_explicit_close_signal(self):
        dock = InstallerWorkspaceDock('Software Installer')
        emitted = []
        dock.explicitCloseRequested.connect(lambda: emitted.append(True))
        try:
            dock.show()
            self.app.processEvents()
            dock.close()
            self.app.processEvents()
            self.assertEqual(emitted, [True])
        finally:
            dock.close()


if __name__ == '__main__':
    unittest.main()
