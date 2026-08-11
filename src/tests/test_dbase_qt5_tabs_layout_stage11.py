from __future__ import annotations

import unittest
from pathlib import Path

from d64dbase import compile_dbase_to_assembly

ROOT = Path(__file__).resolve().parents[1]
BRIDGE = ROOT / "d64qt5" / "d64qt5_bridge.cpp"


class DBaseQt5TabsLayoutStage11Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bridge = BRIDGE.read_text(encoding="utf-8")

    def test_console_tab_is_always_present(self):
        text = self.bridge
        self.assertIn('g_tab_bar->addTab(QStringLiteral("Konsole"))', text)
        self.assertIn('select_console();', text)

    def test_debug_on_off_adds_or_removes_only_debug_tab(self):
        text = self.bridge
        self.assertIn('g_tab_bar->addTab(QStringLiteral("DEBUG"))', text)
        self.assertIn('g_tab_bar->removeTab(index);', text)
        self.assertIn('g_debug_visible = false;', text)

    def test_layout_expands_to_full_mainwindow_client_area(self):
        text = self.bridge
        self.assertIn('g_root = new QWidget(g_window);', text)
        self.assertIn('auto *root_layout = new QVBoxLayout(g_root);', text)
        self.assertIn('root_layout->addWidget(g_stack, 1);', text)
        self.assertIn('g_window->setCentralWidget(g_root);', text)
        self.assertIn('QSizePolicy::Expanding, QSizePolicy::Expanding', text)
        self.assertIn('g_debug_input->setSizePolicy(QSizePolicy::Expanding, QSizePolicy::Fixed);', text)

    def test_no_corner_widget_can_squeeze_tabs(self):
        text = self.bridge
        self.assertIn('new QTabBar(g_header)', text)
        self.assertIn('new QStackedWidget(g_root)', text)
        self.assertNotIn('setCornerWidget(', text)

    def test_append_keeps_horizontal_scroll_at_left(self):
        text = self.bridge
        self.assertIn('editor->horizontalScrollBar()', text)
        self.assertIn('h->setValue(h->minimum())', text)
        self.assertIn('v->setValue(v->maximum())', text)

    def test_generated_code_controls_debug_visibility_at_runtime(self):
        source = '''
? "console"
SET DEBUG ON
? "debug"
SET DEBUG OFF
? "console2"
'''
        result = compile_dbase_to_assembly(source, filename="tabs.dbase", target="pe32")
        asm = result.assembly
        self.assertGreaterEqual(asm.count('call DBaseQtSetDebugVisible'), 3)
        self.assertIn('call DBaseQtAppendConsole', asm)
        self.assertIn('call DBaseQtAppendDebug', asm)

    def test_debug_is_hidden_before_first_window_show(self):
        result = compile_dbase_to_assembly('? "hello"\n', filename="startup.dbase", target="pe32")
        asm = result.assembly
        hide = asm.index('call DBaseQtSetDebugVisible')
        show = asm.index('call DBaseQtShowWindow')
        self.assertLess(hide, show)


if __name__ == "__main__":
    unittest.main()
