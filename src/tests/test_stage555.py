"""Stage 555: Installer-Registry, Wizard-Daten und IDE-Integration (ohne Qt)."""
import ast
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from software_installer_model import (
    InstallerProject, InstallerProjectRegistry, installer_registry_path,
)

ROOT = Path(__file__).resolve().parent
GUI = (ROOT / "software_installer.py").read_text(encoding="utf-8")
DIALOGS = (ROOT / "software_installer_dialogs.py").read_text(encoding="utf-8")
IDE = (ROOT / "d64_dism.py").read_text(encoding="utf-8")


class InstallerRegistryTests(unittest.TestCase):
    def test_registry_follows_executable_directory(self):
        expected = Path('/tmp/testcase/myapp') / 'software_installer_projects.json'
        self.assertEqual(installer_registry_path('/tmp/testcase/myapp/d64_dism.exe'), expected)

    def test_no_registry_returns_empty_list(self):
        with tempfile.TemporaryDirectory() as tmp:
            registry = InstallerProjectRegistry(Path(tmp) / 'software_installer_projects.json')
            self.assertEqual(registry.read(), [])
            self.assertEqual(registry.available(), [])

    def test_registry_contains_project_name_path_and_settings(self):
        with tempfile.TemporaryDirectory() as tmp:
            project_path = Path(tmp) / 'installer_projects' / 'Alpha.installer.json'
            project = InstallerProject(name='Alpha', general={
                'company': 'ACME', 'product': 'Produkt', 'version': '2.5',
                'website': 'https://beispiel.de', 'destination': 'C:/Produkt',
            })
            project.sections['OnStartup'] = 'hello'
            project.save(str(project_path))
            registry = InstallerProjectRegistry(Path(tmp) / 'software_installer_projects.json')
            registry.register(project_path, project)
            items = registry.read()
            self.assertEqual(len(items), 1)
            self.assertEqual(items[0]['name'], 'Alpha')
            self.assertEqual(items[0]['path'], str(project_path.resolve()))
            self.assertEqual(items[0]['settings']['general'], project.general)
            self.assertEqual(items[0]['settings']['sections']['OnStartup'], 'hello')
            self.assertEqual(registry.available(), items)
            raw = json.loads(registry.filename.read_text(encoding='utf-8'))
            self.assertEqual(raw['version'], 1)

    def test_registration_updates_existing_entry_without_duplication(self):
        with tempfile.TemporaryDirectory() as tmp:
            filename = Path(tmp) / 'P.installer.json'
            project = InstallerProject(name='P')
            project.save(str(filename))
            registry = InstallerProjectRegistry(Path(tmp) / 'list.json')
            registry.register(filename, project)
            project.general['version'] = '4.0'
            registry.register(filename, project)
            self.assertEqual(len(registry.read()), 1)
            self.assertEqual(registry.read()[0]['settings']['general']['version'], '4.0')

    def test_list_does_not_show_deleted_projects(self):
        with tempfile.TemporaryDirectory() as tmp:
            filename = Path(tmp) / 'P.installer.json'
            project = InstallerProject(name='P')
            project.save(str(filename))
            registry = InstallerProjectRegistry(Path(tmp) / 'list.json')
            registry.register(filename, project)
            filename.unlink()
            self.assertEqual(registry.available(), [])
            self.assertEqual(len(registry.read()), 1)

    def test_corrupt_registry_does_not_get_silently_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            filename = Path(tmp) / 'list.json'
            filename.write_text('not-json', encoding='utf-8')
            registry = InstallerProjectRegistry(filename)
            with self.assertRaises(ValueError):
                registry.register(Path(tmp) / 'P.installer.json', InstallerProject())
            self.assertEqual(filename.read_text(encoding='utf-8'), 'not-json')

    def test_atomic_registry_write_preserves_old_file_on_failed_replace(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'P.installer.json'
            project = InstallerProject(name='A')
            project.save(str(path))
            registry = InstallerProjectRegistry(Path(tmp) / 'list.json')
            registry.register(path, project)
            previous = registry.filename.read_bytes()
            with patch('software_installer_model.os.replace', side_effect=OSError('disk full')):
                with self.assertRaises(OSError):
                    registry.register(path, InstallerProject(name='B'))
            self.assertEqual(previous, registry.filename.read_bytes())
            self.assertEqual(list(Path(tmp).glob('list.json.*.tmp')), [])

    def test_wizard_general_fields_are_backward_compatible(self):
        project = InstallerProject.from_dict({
            'format': 'd64-software-installer', 'version': 1,
            'archive': [], 'external': [], 'sections': {'Log-Datei': 'abc'},
        })
        self.assertEqual(project.name, 'Unbenannt')
        self.assertEqual(project.general, {})
        project.general.update(company='ACME', version='1.0')
        project.name = 'ACME Installer'
        self.assertEqual(InstallerProject.from_dict(project.to_dict()).to_dict(), project.to_dict())

    def test_bad_wizard_configuration_rejected(self):
        doc = InstallerProject().to_dict()
        doc['general'] = ['no', 'dict']
        with self.assertRaises(ValueError):
            InstallerProject.from_dict(doc)


class InstallerUiSourceTests(unittest.TestCase):
    def test_ui_sources_parse(self):
        ast.parse(GUI)
        ast.parse(DIALOGS)

    def test_start_dialog_modes_and_buttons(self):
        for text in ('Neues Projekt starten', 'Neues Projekt erstellen',
                     'Vorhandenes Projekt öffnen', 'start mit Wizard',
                     'Suchen', '"OK", "Abbrechen", "Hilfe"'):
            self.assertIn(text, DIALOGS)
        self.assertIn('self.projects_list.setEnabled(is_existing)', DIALOGS)
        self.assertIn('self.browse_button.setEnabled(is_existing)', DIALOGS)
        self.assertIn('self.wizard_check.setEnabled(not is_existing)', DIALOGS)
        self.assertIn('installerProjectList', DIALOGS)

    def test_first_wizard_page_fields_buttons_and_placeholders(self):
        for value in ('Allgemeine Informationen', 'Wie heißt Ihre Firma', 'Ihre Firma',
                      'Produktname oder Titel', 'Ihr Produkt', 'Produkt Version',
                      '1.0', 'Firmen Internetseite', 'https://www.firma.de',
                      '< Zurück', 'Weiter >', 'Abbrechen', 'Hilfe'):
            self.assertIn(value, DIALOGS)
        self.assertIn('self.back_button.setEnabled(not first_page)', DIALOGS)

    def test_second_wizard_page_and_back(self):
        self.assertIn('Installationsverzeichnis', DIALOGS)
        self.assertIn('InstallerPlatformDialog', GUI)
        self.assertIn('InstallerSourcesDialog', GUI)
        self.assertIn('InstallerAppearanceDialog', GUI)
        self.assertIn('self.project.general = values', GUI)
        self.assertIn('self.new_unnamed_project()', GUI)

    def test_input_name_dialog_is_dark_themed(self):
        self.assertIn('class InstallerProjectNameDialog(InstallerThemedDialog)', DIALOGS)
        self.assertIn('InstallerProjectNameDialog(', GUI)
        self.assertIn('if name_dialog.exec_() != QDialog.Accepted:', GUI)
        self.assertIn('needs_save_as = True', GUI)
        self.assertIn('software_installer_projects.json',
                      (ROOT / 'software_installer_model.py').read_text('utf-8'))

    def test_dark_mode_native_titlebar_on_windows(self):
        self.assertIn('DwmSetWindowAttribute', DIALOGS)
        self.assertIn('for attribute in (20, 19)', DIALOGS)
        self.assertIn('self.apply_theme(self._dark_mode)', DIALOGS)
        self.assertIn('QToolButton#softwareInstallerProjectOpenButton', GUI)
        self.assertIn('QToolButton#softwareInstallerProjectSaveButton', GUI)

    def test_main_ctrl_s_saves_installer_and_all_others(self):
        index = IDE.index('def save_all_open_documents(')
        end = IDE.index('def save_current_document(', index)
        method = IDE[index:end]
        self.assertIn('perform("Software Installer", installer.save_configuration)', method)
        self.assertIn('perform("Projektdatei", self.save_project)', method)
        self.assertIn('perform("HTML-Editor", html.save_document)', method)
        self.assertIn('installer_widget.project_changed.connect(', IDE)
        self.assertIn('has_installer_changes', IDE)

    def test_help_topics_navigation(self):
        self.assertIn('show_software_installer_help', IDE)
        self.assertIn('fixed_help_directory=sources', IDE)
        self.assertIn('self.help_callback(self.help_topic)', DIALOGS)
        files = (ROOT / 'help/software_installer')
        for filename in ('index.html', 'wizard_seite_1.html', 'wizard_seite_2.html',
                         'neues_projekt_starten.html', 'installer.hhc', 'installer.hhk', 'installer.hhp'):
            self.assertTrue((files / filename).is_file(), filename)
        self.assertIn('Wizard Seite 1', (files / 'installer.hhc').read_text('utf-8'))

    def test_one_dock_remains(self):
        self.assertIn('class SoftwareInstallerWorkbench(QWidget)', GUI)
        self.assertNotIn('QDockWidget(', GUI)
        self.assertIn('self.splitter = QSplitter(Qt.Horizontal, self)', GUI)


if __name__ == '__main__':
    unittest.main()
