"""Stage 557: Fuenfte Wizard-Seite fuer Projekt-Theme."""
import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DIALOGS = (ROOT / "software_installer_dialogs.py").read_text(encoding="utf-8")
IDE = (ROOT / "software_installer.py").read_text(encoding="utf-8")
HELP = ROOT / "help" / "software_installer"


class WizardStage557Tests(unittest.TestCase):
    def test_python_sources_are_valid(self):
        ast.parse(DIALOGS)
        ast.parse(IDE)

    def test_fifth_page_theme_dialog_exists(self):
        for needle in (
            'class InstallerProjectThemeDialog(InstallerWizardDialog):',
            '"Projekt Theme"',
            '"Wizard Seite 5"',
            '"Wählen Sie das Projekt-Theme aus"',
            '"Standard 1"',
            '"Standard 2"',
            '"project_theme": self.theme_combo.currentText().strip() or "Standard 1"',
        ):
            self.assertIn(needle, DIALOGS)

    def test_theme_preview_widget_draws_both_standards(self):
        for needle in (
            'class InstallerThemePreview(QFrame):',
            'def draw_standard1():',
            'def draw_standard2():',
            '"Verknüpfung"',
            '"Für jeden Windows-Benutzer Installieren"',
            '"Für den aktuellen Windows-Benutzer installieren"',
        ):
            self.assertIn(needle, DIALOGS)

    def test_wizard_flow_contains_five_pages(self):
        segment = IDE[IDE.index('def _run_wizard('):IDE.index('def _confirm_replace_project(', IDE.index('def _run_wizard('))]
        for needle in ('InstallerGeneralInfoDialog', 'InstallerPlatformDialog',
                       'InstallerSourcesDialog', 'InstallerAppearanceDialog',
                       'InstallerProjectThemeDialog'):
            self.assertIn(needle, segment)

    def test_help_contains_fifth_page(self):
        self.assertTrue((HELP / 'wizard_seite_5.html').is_file())
        for index in ('index.html', 'installer.hhc', 'installer.hhk', 'installer.hhp'):
            self.assertIn('wizard_seite_5.html', (HELP / index).read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()
