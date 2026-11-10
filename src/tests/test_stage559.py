"""Stage 559: Qt-unabhaengige Sessionvariablen-/Persistenz-Regressionen."""
from __future__ import annotations

import ast
import json
import tempfile
import unittest
from pathlib import Path

from installer_session_variables import (
    SESSION_SECTION, check_variable_name, default_session_groups,
    effective_session_groups, encode_session_variables,
    normalize_variable_name, parse_session_variables,
)
from software_installer_model import InstallerProject, InstallerProjectRegistry

ROOT = Path(__file__).resolve().parent
DIALOG = (ROOT / 'software_installer_dialogs.py').read_text('utf-8')
WORKBENCH = (ROOT / 'software_installer.py').read_text('utf-8')


class Stage559ModelTests(unittest.TestCase):
    def test_wizard_defaults_and_explicit_presets(self):
        defaults = default_session_groups({
            'product': 'Mein Produkt', 'company': 'Meine Firma',
            'version': '2.3', 'website': 'https://beispiel.de',
        })
        info = defaults['product']
        self.assertEqual(info['%ProductName%'], 'Mein Produkt')
        self.assertEqual(info['%CompanyName%'], 'Meine Firma')
        self.assertEqual(info['%ProductVersion%'], '2.3')
        self.assertEqual(info['%CompanyURL%'], 'https://beispiel.de')
        self.assertEqual(info['%Copyright%'], 'Copyright (c) #CURRENTYEAR# %CompanyName%')
        self.assertEqual(info['%WindowTitle%'], '%ProductName% Setup')
        self.assertEqual(info['%WindowTitleUninstall%'], '%ProductName% Uninstaller')
        self.assertEqual(defaults['directories']['%AppFolder%'],
                         '%ProgramFilesFolder%\\%ProductName%')
        self.assertEqual(defaults['directories']['%AppShortcutFolderName%'], '%ProductName%')

    def test_empty_wizard_values_apply_placeholders(self):
        defaults = default_session_groups({'company': '', 'product': '', 'version': '', 'website': ''})
        self.assertEqual(defaults['product']['%ProductName%'], 'Ihr Produkt')
        self.assertEqual(defaults['product']['%CompanyName%'], 'Ihre Firma')
        self.assertEqual(defaults['product']['%ProductVersion%'], '1.0')
        self.assertEqual(defaults['product']['%CompanyURL%'], 'https://www.firma.de')

    def test_name_validation_and_normalization(self):
        self.assertEqual(normalize_variable_name('ABC_1'), '%ABC_1%')
        self.assertEqual(normalize_variable_name('%ABC_1%'), '%ABC_1%')
        for bad in ('', '%no space%', '%1abc%', '%A-B%', '%abc', 'abc%', 'name%x'):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    normalize_variable_name(bad)
        with self.assertRaisesRegex(ValueError, 'bereits vorhanden'):
            check_variable_name('%productname%', ('%ProductName%',))
        with self.assertRaisesRegex(ValueError, 'bereits vorhanden'):
            check_variable_name('%myvariable%', ('%MyVariable%', '%Custom%'))
        self.assertEqual(check_variable_name('%MyVariable%', ('%MyVariable%',),
                                             previous='%MyVariable%'), '%MyVariable%')

    def test_roundtrip_with_custom_and_overrides(self):
        general = {'product': 'App', 'company': 'Firma GmbH', 'version': '4.0'}
        groups = effective_session_groups(general)
        groups['product']['%WindowTitle%'] = 'Installiere App'
        groups['directories']['%AppFolder%'] = 'C:\\Programme\\App'
        groups['custom']['%LicenseCode%'] = 'ABCD-1234'
        groups['custom']['%Flag%'] = 'Ja'
        stored = encode_session_variables(general, groups)
        self.assertEqual(json.loads(stored)['version'], 1)
        self.assertEqual(list(json.loads(stored)['custom']), ['%LicenseCode%', '%Flag%'])
        self.assertEqual(effective_session_groups(general, stored), groups)

    def test_wizard_changes_update_unmodified_fields(self):
        groups = effective_session_groups({'product': 'Alpha', 'company': 'Alt'})
        groups['product']['%WindowTitle%'] = 'Spezial Installer'
        stored = encode_session_variables({'product': 'Alpha', 'company': 'Alt'}, groups)
        updated = effective_session_groups({'product': 'Beta', 'company': 'Neu'}, stored)
        self.assertEqual(updated['product']['%ProductName%'], 'Beta')
        self.assertEqual(updated['product']['%CompanyName%'], 'Neu')
        self.assertEqual(updated['product']['%WindowTitle%'], 'Spezial Installer')

    def test_duplicate_custom_variable_rejected_at_encoding(self):
        groups = effective_session_groups()
        groups['custom']['%ProductName%'] = 'duplicate'
        with self.assertRaises(ValueError):
            encode_session_variables({}, groups)
        groups['custom'].clear()
        groups['custom']['%ABC%'] = 'one'
        groups['custom']['%abc%'] = 'two'
        with self.assertRaises(ValueError):
            encode_session_variables({}, groups)

    def test_invalid_json_is_not_silently_ignored(self):
        for text in ('{', '[]', '{"version": 5}', '{"custom": []}',
                     '{"custom": {"%ProductName%": "oops"}}',
                     '{"custom": {"%MY%": 1}}'):
            with self.subTest(text=text):
                with self.assertRaises((ValueError, json.JSONDecodeError)):
                    parse_session_variables(text)

    def test_project_file_and_registry_roundtrip(self):
        project = InstallerProject(name='Meine Installation', general={'company': 'Sonnenschein GmbH'})
        groups = effective_session_groups(project.general)
        groups['custom']['%VAR%'] = 'Wert'
        project.sections[SESSION_SECTION] = encode_session_variables(project.general, groups)
        with tempfile.TemporaryDirectory() as dirname:
            path = Path(dirname) / 'installer.installer.json'
            registry = InstallerProjectRegistry(Path(dirname) / 'projects.json')
            project.save(str(path))
            registry.register(path, project)
            loaded = InstallerProject.load(str(path))
            self.assertEqual(effective_session_groups(loaded.general,
                loaded.sections[SESSION_SECTION])['custom']['%VAR%'], 'Wert')
            self.assertIn(SESSION_SECTION, registry.available()[0]['settings']['sections'])

    def test_model_python_sources_compile(self):
        for name in ('installer_session_variables.py','software_installer_dialogs.py',
                     'software_installer.py'):
            ast.parse((ROOT / name).read_text('utf-8'))

    def test_wizard_dimensions_and_session_dimensions(self):
        self.assertIn('WIZARD_SIZE = (760, 590)', DIALOG)
        self.assertIn('self.setFixedSize(WIZARD_SIZE[0] - 140, WIZARD_SIZE[1] - 40)', DIALOG)
        self.assertIn('class InstallerSessionVariablesDialog(InstallerThemedDialog)', DIALOG)

    def test_three_panel_tables_and_editability(self):
        for term in ('"Produkt Informationen"', '"Standard-Verzeichnisse"',
                     '"Benutzerdefiniert"', 'QScrollArea(', 'header.hide()',
                     'QAbstractItemView.SelectRows',
                     'name_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)',
                     'value_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable)'):
            self.assertIn(term, DIALOG)

    def test_dialog_add_rename_remove_and_help(self):
        for term in ('"Hinzufügen"','"Entfernen"','"Umbenennen"',
                     '"OK", self', '"Abbrechen", self', '"Hilfe", self',
                     '"%VariableName%"', '"Wert"',
                     'check_variable_name(new_name, self._all_names(), previous=old_name)',
                     'check_variable_name(name, self._all_names())',
                     'self.help_callback("Session Variablen")'):
            self.assertIn(term, DIALOG)

    def test_button_handler_commits_then_saves(self):
        self.assertIn('"Session Variable": self.edit_session_variables', WORKBENCH)
        self.assertIn('self.project.sections["Session Variable"] = serialized', WORKBENCH)
        self.assertIn('return bool(self.save_configuration())', WORKBENCH)

    def test_help_is_registered(self):
        helpdir = ROOT / 'help/software_installer'
        self.assertTrue((helpdir / 'session_variablen.html').is_file())
        for name in ('installer.hhc','installer.hhk','installer.hhp','index.html'):
            self.assertIn('session_variablen.html', (helpdir / name).read_text('utf-8'))


if __name__ == '__main__':
    unittest.main()
