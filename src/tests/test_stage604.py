"""Stage 604: Projekt-Einstellungen 1 Punkt groesser (Qt-unabhaengige Tests)."""
from pathlib import Path
import re
import unittest

SOURCE = Path(__file__).with_name('d64_dism.py').read_text(encoding='utf-8')

class ProjectSettingsFontTests(unittest.TestCase):
    def _method(self):
        start = SOURCE.index('        def _ensure_project_settings_dock(self) -> None:')
        end = SOURCE.index('        def _enter_project_settings_workspace(self) -> None:', start)
        return SOURCE[start:end]

    def test_font_is_dock_local(self):
        body = self._method()
        self.assertIn('settings_font = QFont(dock.font())', body)
        self.assertIn('dock.setFont(settings_font)', body)
        self.assertNotIn('QApplication.setFont(', body)

    def test_font_precedes_child_widgets(self):
        body = self._method()
        self.assertLess(body.index('dock.setFont(settings_font)'), body.index('scroll = QScrollArea(dock)'))
        self.assertLess(body.index('dock.setFont(settings_font)'), body.index('panel = ProjectSettingsPanel(self, scroll)'))

    def test_exactly_one_point_extra(self):
        body = self._method()
        self.assertEqual(body.count('settings_font.setPointSizeF(settings_point_size + 1.0)'), 1)
        self.assertEqual(body.count('dock.setFont(settings_font)'), 1)

    def test_existing_theme_and_editor_preview_unchanged(self):
        self.assertIn('panel.set_dark_mode(self.application_dark_mode(self.dark_mode_enabled))', self._method())
        self.assertIn('self.editor_preview_text.setFont(preview_font)', SOURCE)
        self.assertIn('self.editor_preview_gutter.setFont(preview_font)', SOURCE)

    def test_font_code_in_python_ast(self):
        import ast
        # Python 3.15 supports lazy imports; the test host may be <3.15.
        normalized = re.sub(r'(?m)^(\s*)lazy (from|import)\b', r'\1\2', SOURCE)
        ast.parse(normalized)

if __name__ == '__main__':
    unittest.main()
