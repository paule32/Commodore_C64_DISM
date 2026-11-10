"""Stage 556: Installer-Wizard-Struktur und JSON-Persistenz ohne PyQt5."""
import ast
import json
import tempfile
import unittest
from pathlib import Path

from software_installer_model import InstallerProject, InstallerProjectRegistry

ROOT = Path(__file__).resolve().parent
DIALOGS = (ROOT / "software_installer_dialogs.py").read_text(encoding="utf-8")
IDE = (ROOT / "software_installer.py").read_text(encoding="utf-8")
HELP = ROOT / "help" / "software_installer"


class WizardStage556Tests(unittest.TestCase):
    def test_python_sources_are_valid(self):
        ast.parse(DIALOGS)
        ast.parse(IDE)

    def test_custom_gradient_title_instead_of_native_for_wizard(self):
        self.assertIn('Qt.FramelessWindowHint', DIALOGS)
        self.assertIn('qlineargradient(x1:0, y1:0, x2:1, y2:0', DIALOGS)
        self.assertIn('stop:0 #000000, stop:1 #ffffff', DIALOGS)
        self.assertIn('class InstallerGradientTitleBar(QFrame):', DIALOGS)
        self.assertIn('self.window().move(event.globalPos() - self._drag_offset)', DIALOGS)
        self.assertIn('self.close_button.clicked.connect(dialog.reject)', DIALOGS)

    def test_project_start_browse_is_left_aligned(self):
        self.assertIn('browse_row.addWidget(self.browse_button)', DIALOGS)
        self.assertIn('browse_row.addStretch(1)', DIALOGS)
        self.assertNotIn('layout.addWidget(self.browse_button, 0, Qt.AlignRight)', DIALOGS)

    def test_all_wizard_pages_use_same_base_and_geometry(self):
        for cls in ('InstallerGeneralInfoDialog', 'InstallerPlatformDialog',
                    'InstallerSourcesDialog', 'InstallerAppearanceDialog'):
            self.assertIn(f'class {cls}(InstallerWizardDialog):', DIALOGS)
        self.assertIn('WIZARD_SIZE = (760, 590)', DIALOGS)
        self.assertIn('self.setFixedSize(*WIZARD_SIZE)', DIALOGS)
        self.assertIn('self.image_box.setFixedWidth(140)', DIALOGS)
        self.assertIn('layout.addSpacing(20)', DIALOGS)

    def test_general_information_has_placeholders_and_uses_them(self):
        for field in ('"company"', '"product"', '"version"', '"website"'):
            self.assertIn(field, DIALOGS)
        self.assertIn('edit.text().strip() or edit.placeholderText()', DIALOGS)

    def test_second_page_platform_32_and_64(self):
        for needle in ('"Platform"', '"32 - Bit Setup"', '"64 - Bit Setup"',
                       '"platform": "64" if self.radio_64.isChecked() else "32"'):
            self.assertIn(needle, DIALOGS)

    def test_third_page_source_directory_and_subdirectories(self):
        for needle in ('"Quelldateien"', '"Pfad des Verzeichnisses"',
                       '"Einbeziehung der Unterverzeichnisse"',
                       'QFileDialog.getExistingDirectory',
                       '"source_directory": self.directory_edit.text().strip()',
                       '"include_subdirectories": "true"'):
            self.assertIn(needle, DIALOGS)

    def test_fourth_page_window_appearance_choices_and_colors(self):
        for needle in ('"Fenster Einstellungen"', '"Wizard mit Hintergrund-Fenster"',
                       '"Statische Farbe"', '"Verlauf"', '"Bild"',
                       '"static_color"', '"gradient_start"', '"gradient_end"',
                       '"background_image"', 'QColorDialog.getColor(',
                       'class InstallerColorLineEdit(QLineEdit):',
                       'def mouseDoubleClickEvent(self, event):'):
            self.assertIn(needle, DIALOGS)

    def test_wizard_state_and_cancel_persisted_by_workbench(self):
        segment = IDE[IDE.index('def _run_wizard('):IDE.index('def _confirm_replace_project(', IDE.index('def _run_wizard('))]
        for needle in ('InstallerGeneralInfoDialog', 'InstallerPlatformDialog',
                       'InstallerSourcesDialog', 'InstallerAppearanceDialog',
                       'values.update(dialog.values())', 'page = max(0, page - 1)',
                       'self.project.general = values', 'self.new_unnamed_project()'):
            self.assertIn(needle, segment)

    def test_project_roundtrip_all_new_fields(self):
        settings = {
            'company': 'Ihre Firma', 'product': 'Ihr Produkt',
            'version': '1.0', 'website': 'https://www.firma.de',
            'platform': '64', 'source_directory': r'C:\Sources',
            'include_subdirectories': 'true', 'window_mode': 'background',
            'appearance_style': 'gradient', 'static_color': '#20385f',
            'gradient_start': '#102030', 'gradient_end': '#abcdef',
            'background_image': r'C:\Bilder\setup.png',
        }
        with tempfile.TemporaryDirectory() as folder:
            filepath = Path(folder) / 'Setup.installer.json'
            registry = InstallerProjectRegistry(Path(folder) / 'projects.json')
            project = InstallerProject(name='Setup', general=settings)
            project.save(str(filepath))
            registry.register(filepath, project)
            self.assertEqual(InstallerProject.load(filepath).general, settings)
            self.assertEqual(registry.available()[0]['settings']['general'], settings)
            self.assertEqual(json.loads(filepath.read_text(encoding='utf-8'))['version'], 1)

    def test_help_navigates_all_pages(self):
        for i in range(1, 5):
            file = f'wizard_seite_{i}.html'
            self.assertTrue((HELP / file).is_file(), file)
            for index in ('installer.hhc', 'installer.hhk', 'installer.hhp'):
                self.assertIn(file, (HELP / index).read_text(encoding='utf-8'))
            self.assertIn(f'"Wizard Seite {i}"', DIALOGS)


if __name__ == '__main__':
    unittest.main()
