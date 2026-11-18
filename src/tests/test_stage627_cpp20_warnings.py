"""Stage 627 – Regressionstests fuer die vom MinGW C++20 Compiler gemeldeten Warnungen."""
from pathlib import Path
import re
import unittest

BRIDGE = (Path(__file__).resolve().parents[1] / 'd64qt5' / 'd64qt5_bridge.cpp').read_text(encoding='utf-8')

class Stage627Cpp20WarningsTests(unittest.TestCase):
    def test_six_shortcuts_without_enum_arithmetic(self):
        for key in 'ZYXCVA':
            with self.subTest(key=key):
                self.assertIn(f'QKeySequence(static_cast<int>(Qt::CTRL) | static_cast<int>(Qt::Key_{key}))', BRIDGE)
                self.assertNotIn(f'Qt::CTRL + Qt::Key_{key}', BRIDGE)

    def test_delete_shortcut_is_not_changed(self):
        self.assertIn('QKeySequence(Qt::Key_Delete)', BRIDGE)

    def test_unused_legacy_debug_tab_function_preserved(self):
        self.assertIn('[[maybe_unused]] void install_debug_tab(bool select_it)', BRIDGE)
        self.assertIn('g_debug_visible = true;', BRIDGE)
        self.assertIn('void remove_debug_tab()', BRIDGE)

    def test_menu_text_unchanged(self):
        for name in ['Rückgängig','Wiederherstellen','Ausschneiden','Kopieren',
                     'Einfügen','Löschen','Alles auswählen']:
            with self.subTest(name=name):
                self.assertIn(f'QStringLiteral("{name}")', BRIDGE)
        self.assertIn('editMenu->addSeparator();', BRIDGE)

    def test_no_other_arithmetic_between_qt_modifier_key(self):
        self.assertIsNone(re.search(r'Qt::CTRL\s*\+\s*Qt::Key_', BRIDGE))

if __name__ == '__main__':
    unittest.main()
