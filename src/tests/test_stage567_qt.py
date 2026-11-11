"""Optionale echte PyQt5-Checks (unter Windows oder QT_QPA_PLATFORM=offscreen)."""
from __future__ import annotations
import unittest
from unittest.mock import patch

try:
    from PyQt5.QtWidgets import QApplication
    from software_installer_dialogs import (
        InstallerSecurityDialog, InstallerSerialListPropertiesDialog,
    )
    from software_installer_model import InstallerProject
    HAVE_QT = True
except ImportError:
    HAVE_QT = False


@unittest.skipUnless(HAVE_QT, "PyQt5 nicht installiert")
class InstallerStage567QtChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_parent_header_dark_and_light(self):
        dlg = InstallerSecurityDialog(InstallerProject(), dark_mode=True)
        header = dlg.lists_table.horizontalHeader()
        self.assertIn("#343b48", header.styleSheet())
        dlg.apply_theme(False)
        self.assertIn("#e4e9ef", header.styleSheet())
        dlg.close()

    def test_child_font_preview_and_dark_header(self):
        dlg = InstallerSerialListPropertiesDialog(dark_mode=True)
        dlg._set_rows(["AAAA-BBBB", "CCCC-DDDD"])
        self.assertIn("#343b48", dlg.serial_table.horizontalHeader().styleSheet())
        font = dlg.serial_table.item(0, 0).font()
        if hasattr(font, "families"):
            self.assertEqual(font.families(), ["Consolas", "Courier New", "Courier"])
        else:
            self.assertEqual(font.family(), "Consolas")
        doc = dlg._serial_print_document()
        content = doc.toPlainText()
        self.assertIn("AAAA-BBBB", content)
        self.assertIn("CCCC-DDDD", content)
        with patch("PyQt5.QtPrintSupport.QPrintPreviewDialog") as Preview:
            dlg._print()
            preview = Preview.return_value
            preview.setWindowTitle.assert_called_once_with("Druckvorschau - Serial Nummern")
            preview.paintRequested.connect.assert_called_once()
            preview.exec_.assert_called_once()
        dlg.close()


if __name__ == "__main__":
    unittest.main()
