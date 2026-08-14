import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CPP = (ROOT / "d64qt5" / "d64qt5_bridge.cpp").read_text(encoding="utf-8")


class DBaseLoginWarningStage33Tests(unittest.TestCase):
    def test_failed_login_closes_login_dialog_and_opens_warning(self):
        self.assertIn('QDialog::reject();\n        show_runtime_warning(QStringLiteral("Anmeldung fehlgeschlagen."));', CPP)
        self.assertNotIn('m_passwordEdit->setFocus();\n        m_passwordEdit->selectAll();', CPP)

    def test_warning_is_non_modal(self):
        warning = CPP[CPP.index("class WarningDialog final") : CPP.index("\nvoid cancel_login_dialog()\n", CPP.index("class WarningDialog final"))]
        self.assertIn("setWindowModality(Qt::NonModal);", warning)
        self.assertIn("setModal(false);", warning)
        self.assertNotIn("dialog.exec();", warning)

    def test_warning_is_persistent_heap_dialog(self):
        self.assertIn("WarningDialog *dialog = new WarningDialog(message, g_window);", CPP)
        self.assertIn("dialog->show();", CPP)
        self.assertIn("dialog->deleteLater();", CPP)

    def test_warning_moves_in_character_grid(self):
        warning = CPP[CPP.index("class WarningDialog final") : CPP.index("\nvoid show_runtime_warning(const QString &message)\n", CPP.index("class WarningDialog final"))]
        self.assertIn("dxCells", warning)
        self.assertIn("dyCells", warning)
        self.assertIn("setStoredGridPosition", warning)
        self.assertIn("repositionToStoredGrid", warning)
        self.assertIn("g_console->viewport()->mapToGlobal", warning)

    def test_warning_is_clipped_to_80x25_viewport(self):
        warning = CPP[CPP.index("class WarningDialog final") : CPP.index("\nvoid show_runtime_warning(const QString &message)\n", CPP.index("class WarningDialog final"))]
        self.assertIn("DBASE_TEXT_COLUMNS", warning)
        self.assertIn("DBASE_TEXT_ROWS", warning)
        self.assertIn("updateViewportClipMask", warning)
        self.assertIn("setMask(QRegion(visibleLocal));", warning)

    def test_zoom_resizes_warning_without_modal_block(self):
        self.assertIn("if (g_warning_dialog)\n        g_warning_dialog->updateForGrid(true);", CPP)
        self.assertIn("g_zoom_in", CPP)
        self.assertIn("g_zoom_out", CPP)

    def test_warning_keeps_requested_appearance_and_ok(self):
        warning = CPP[CPP.index("class WarningDialog final") : CPP.index("\nvoid show_runtime_warning(const QString &message)\n", CPP.index("class WarningDialog final"))]
        self.assertIn('setWindowTitle(QStringLiteral("Warnung"));', warning)
        self.assertIn('background-color: #ff0000', warning)
        self.assertIn('color: #000000', warning)
        self.assertIn('QColor(255, 255, 255)', warning)
        self.assertIn('new QPushButton(QStringLiteral("OK"), this)', warning)


if __name__ == "__main__":
    unittest.main()
