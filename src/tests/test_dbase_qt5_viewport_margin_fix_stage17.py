from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
CPP = (ROOT / "d64qt5" / "d64qt5_bridge.cpp").read_text(encoding="utf-8")


class DBaseQt5ViewportMarginFixStage17Tests(unittest.TestCase):
    def test_no_protected_set_viewport_margins_call(self):
        self.assertNotIn("setViewportMargins(", CPP)

    def test_zero_editor_geometry_remains(self):
        self.assertIn("g_console->setContentsMargins(0, 0, 0, 0);", CPP)
        self.assertIn("g_console->document()->setDocumentMargin(0.0);", CPP)
        self.assertIn('" margin: 0px;"', CPP)
        self.assertIn('" padding: 0px;"', CPP)

    def test_debug_document_margin_remains_zero(self):
        self.assertIn("g_debug->setContentsMargins(0, 0, 0, 0);", CPP)
        self.assertIn("g_debug->document()->setDocumentMargin(0.0);", CPP)


if __name__ == "__main__":
    unittest.main()
