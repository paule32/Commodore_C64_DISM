from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "d64_dism.py").read_text(encoding="utf-8")


class Stage79LocalizeDockTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.localize = SOURCE[
            SOURCE.index("class LocalizeToolWindow(QDialog)"):
            SOURCE.index("class AssemblerSyntaxHighlighter", SOURCE.index("class LocalizeToolWindow(QDialog)"))
        ]
        cls.window = SOURCE[SOURCE.index("class ExplorerWindow(QMainWindow)"):]

    def test_localize_tool_supports_embedded_widget_mode(self):
        self.assertIn("embedded: bool = False", self.localize)
        self.assertIn("self._embedded = bool(embedded)", self.localize)
        self.assertIn("self.setWindowFlags(Qt.Widget)", self.localize)
        self.assertIn("self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)", self.localize)

    def test_localize_cancel_can_hide_dock(self):
        self.assertIn("dock_close_requested = pyqtSignal()", self.localize)
        self.assertIn("self.dock_close_requested.emit()", self.localize)
        self.assertIn("if self._confirm_close():", self.localize)

    def test_main_window_tracks_localize_dock(self):
        self.assertIn("self.localize_tool_window = None", self.window)
        self.assertIn("self.localize_dock = None", self.window)
        self.assertIn("self._localize_replaced_filesystem_dock = False", self.window)

    def test_localize_uses_existing_left_dock_area(self):
        start = self.window.index("def _ensure_localize_dock")
        end = self.window.index("def localize_dialog", start)
        block = self.window[start:end]
        self.assertIn('QDockWidget("Localize PO/MO", self)', block)
        self.assertIn('dock.setObjectName("localize_po_mo_dock")', block)
        self.assertIn("self.addDockWidget(Qt.LeftDockWidgetArea, dock)", block)
        self.assertIn("LocalizeToolWindow(self, dock, embedded=True)", block)

    def test_localize_hides_filesystem_and_restores_it(self):
        start = self.window.index("def _localize_dock_visibility_changed")
        end = self.window.index("def _expand_localize_dock", start)
        block = self.window[start:end]
        self.assertIn("self.left_dock.hide()", block)
        self.assertIn("self.left_dock.show()", block)
        self.assertIn("self._localize_replaced_filesystem_dock", block)

    def test_localize_action_is_no_longer_modal_exec(self):
        start = self.window.index("def localize_dialog")
        end = self.window.index("def create_coff32_archive_dialog", start)
        block = self.window[start:end]
        self.assertNotIn("exec_()", block)
        self.assertIn("dock.show()", block)
        self.assertIn("dock.raise_()", block)
        self.assertIn("self.left_dock.hide()", block)

    def test_localize_and_knowledge_browser_do_not_compete_for_left_area(self):
        start = self.window.index("def open_prolog_knowledge_browser")
        end = self.window.index("def _show_project_prolog_knowledge_root_menu", start)
        block = self.window[start:end]
        self.assertIn('localize_dock = getattr(self, "localize_dock", None)', block)
        self.assertIn("localize_dock.hide()", block)

    def test_localize_settings_alias_preserves_existing_state_logic(self):
        init = self.window[self.window.index("def __init__"):self.window.index("def _create_green_beige_window_chrome")]
        self.assertIn("self._settings = self.settings", init)


if __name__ == "__main__":
    unittest.main()
