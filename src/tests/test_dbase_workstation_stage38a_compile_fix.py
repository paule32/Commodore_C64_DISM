import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BRIDGE = (ROOT / "d64qt5" / "d64qt5_bridge.cpp").read_text(encoding="utf-8")


class Stage38ACompileFixTests(unittest.TestCase):
    def test_grid_enforcer_forward_declared_before_db_callback(self):
        declaration = "void enforce_console_80x25_grid();"
        callback = "void workstation_db_requested()"
        definition = "void enforce_console_80x25_grid()\n{"
        self.assertIn(declaration, BRIDGE)
        self.assertIn(callback, BRIDGE)
        self.assertIn(definition, BRIDGE)
        self.assertLess(BRIDGE.index(declaration), BRIDGE.index(callback))
        self.assertLess(BRIDGE.index(callback), BRIDGE.index(definition))

    def test_db_callback_may_resize_after_show(self):
        start = BRIDGE.index("void workstation_db_requested()")
        end = BRIDGE.index("void show_runtime_warning", start)
        block = BRIDGE[start:end]
        self.assertIn("g_window->show();", block)
        self.assertIn("enforce_console_80x25_grid();", block)
        self.assertLess(block.index("g_window->show();"), block.index("enforce_console_80x25_grid();"))

    def test_btx_callback_launches_executable_not_internal_dialog(self):
        start = BRIDGE.rindex("void workstation_btx_requested()")
        end = BRIDGE.rindex("void workstation_db_requested()")
        block = BRIDGE[start:end]
        self.assertIn("launch_btx_executable();", block)
        self.assertNotIn("show_btx_dialog();", block)


if __name__ == "__main__":
    unittest.main()
