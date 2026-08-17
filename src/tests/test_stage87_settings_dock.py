from __future__ import annotations

import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / 'd64_dism.py').read_text(encoding='utf-8')


class Stage87SettingsDockTests(unittest.TestCase):
    def test_source_parses(self):
        ast.parse(SOURCE)

    def test_settings_classes_present(self):
        self.assertIn('class UserBdeAliasesTab(QWidget):', SOURCE)
        self.assertIn('class SourceAliasesTab(QWidget):', SOURCE)
        self.assertIn('class DesktopPropertiesDialog(QWidget):', SOURCE)

    def test_all_requested_tabs_present(self):
        for title in (
            'Country', 'Table', 'Data Entry', 'Files', 'Application',
            'Programming', 'Source Aliases', 'User-BDE-Aliases',
        ):
            self.assertIn(f'tr("{title}")', SOURCE)

    def test_settings_is_real_dock_workspace(self):
        self.assertIn('QDockWidget("Desktop Properties", self)', SOURCE)
        self.assertIn('self.splitDockWidget(self.left_dock, dock, Qt.Horizontal)', SOURCE)
        self.assertIn('def _enter_settings_workspace(self) -> None:', SOURCE)
        self.assertIn('def _restore_settings_workspace(self) -> None:', SOURCE)

    def test_menu_action_and_shortcut(self):
        self.assertIn('QAction("Desktop-Einstellungen ...", self)', SOURCE)
        self.assertIn('QKeySequence("Ctrl+Alt+S")', SOURCE)
        self.assertIn('tools_menu.addAction(self.settings_action)', SOURCE)

    def test_aliases_are_persistent(self):
        self.assertIn('desktop/aliases/source', SOURCE)
        self.assertIn('desktop/aliases/user_bde', SOURCE)
        self.assertIn('json.dumps(self.source_aliases_tab.model()', SOURCE)
        self.assertIn('json.dumps(self.user_bde_aliases_tab.model()', SOURCE)

    def test_file_dialogs_are_non_native(self):
        self.assertGreaterEqual(SOURCE.count('QFileDialog.DontUseNativeDialog'), 6)


if __name__ == '__main__':
    unittest.main()
