"""Optionale PyQt5-Offscreen-Tests fuer die Geometrie von Stage 563."""
import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
try:
    from PyQt5.QtWidgets import QApplication
    from software_installer_model import InstallerProject
    from software_installer_dialogs import InstallerBackgroundWindowDialog
except ImportError:
    QApplication = None


@unittest.skipUnless(QApplication is not None, "PyQt5 ist nicht installiert")
class Stage563QtTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_column_alignment_and_full_text_width(self):
        dialog = InstallerBackgroundWindowDialog(InstallerProject(), dark_mode=True)
        try:
            dialog.show()
            self.app.processEvents()
            left = dialog.findChild(type(dialog.text_group.parentWidget()),
                                    "installerBackgroundLeftColumn")
            self.assertIsNotNone(left)
            # Gemeinsamer Koordinatenraum aller GroupBoxes: scroll body.
            top_left = dialog.mode_group.mapTo(dialog.scroll.widget(), dialog.mode_group.rect().topLeft())
            top_right = dialog.text_group.mapTo(dialog.scroll.widget(), dialog.text_group.rect().topLeft())
            self.assertEqual(top_left.y(), top_right.y())
            bottom_left = dialog.appearance_group.mapTo(
                dialog.scroll.widget(), dialog.appearance_group.rect().bottomLeft())
            bottom_right = dialog.text_group.mapTo(
                dialog.scroll.widget(), dialog.text_group.rect().bottomLeft())
            self.assertLessEqual(abs(bottom_left.y() - bottom_right.y()), 1)
            for key in ("title", "version", "footer"):
                with self.subTest(key=key):
                    edit = dialog.text_edits[key]
                    button = dialog.text_font_buttons[key]
                    color = dialog.text_colors[key]
                    self.assertGreater(button.y(), edit.y() + edit.height() - 1)
                    self.assertLessEqual(
                        abs(color.geometry().center().y() - button.geometry().center().y()), 2)
                    self.assertGreaterEqual(edit.width(), button.width() + color.width())
                    self.assertGreaterEqual(button.width(), 116)
        finally:
            dialog.close()


if __name__ == "__main__":
    unittest.main()
