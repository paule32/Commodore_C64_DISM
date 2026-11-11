"""Stage 566: Sicherheit und Serial-Nummern-Listen (Qt-unabhängig)."""
import ast
import json
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace

from installer_security_settings import (
    SECURITY_SECTION, SECURITY_VERSION, SECURITY_DEFAULTS,
    validate_serial_list, validate_security_settings,
    parse_security_settings, encode_security_settings,
)
from software_installer_model import InstallerProject

BASE = Path(__file__).parent
UI = (BASE / 'software_installer_dialogs.py').read_text('utf-8')
WORKBENCH = (BASE / 'software_installer.py').read_text('utf-8')
HELP = BASE / 'help/software_installer'


class SecurityModelTest(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(parse_security_settings(''), SECURITY_DEFAULTS)
        self.assertEqual(parse_security_settings(None), SECURITY_DEFAULTS)

    def test_roundtrip_lists_and_german_letters(self):
        data = {'serial_lists': [
            {'name': 'Büro', 'configurations': ['Standard'],
             'serial_numbers': ['AAAA-BBBB-1234', 'AAAA-BBBB-5678']},
            {'name': 'Test', 'configurations': [], 'serial_numbers': []},
        ]}
        encoded = encode_security_settings(data)
        self.assertEqual(json.loads(encoded)['version'], SECURITY_VERSION)
        self.assertEqual(parse_security_settings(encoded), data)

    def test_no_mutable_model_aliases(self):
        original = {'serial_lists': [{'name': 'A', 'configurations': ['Standard'],
                                       'serial_numbers': ['123']}]}
        cleaned = validate_security_settings(original)
        original['serial_lists'][0]['serial_numbers'].append('456')
        original['serial_lists'][0]['configurations'].clear()
        self.assertEqual(cleaned['serial_lists'][0]['serial_numbers'], ['123'])
        self.assertEqual(cleaned['serial_lists'][0]['configurations'], ['Standard'])

    def test_duplicate_list_names_ignoring_case(self):
        with self.assertRaisesRegex(ValueError, 'Listenname'):
            validate_security_settings({'serial_lists': [
                {'name': 'Privat', 'configurations': [], 'serial_numbers': []},
                {'name': 'privat', 'configurations': [], 'serial_numbers': []},
            ]})

    def test_duplicate_numbers_ignoring_case(self):
        with self.assertRaisesRegex(ValueError, 'Doppelte'):
            validate_serial_list({'name': 'A', 'configurations': [],
                                  'serial_numbers': ['ab1', 'AB1']})

    def test_configuration_default_and_empty(self):
        for configs in ([], ['Standard']):
            self.assertEqual(validate_serial_list(
                {'name': 'A', 'configurations': configs,
                 'serial_numbers': []})['configurations'], configs)

    def test_bad_list_structure(self):
        cases = (
            {'name': '', 'configurations': [], 'serial_numbers': []},
            {'name': 'a\nb', 'configurations': [], 'serial_numbers': []},
            {'name': 'x' * 121, 'configurations': [], 'serial_numbers': []},
            {'name': 'A', 'configurations': ['Unbekannt'], 'serial_numbers': []},
            {'name': 'A', 'configurations': ['Standard', 'Standard'], 'serial_numbers': []},
            {'name': 'A', 'configurations': [], 'serial_numbers': ['']},
            {'name': 'A', 'configurations': [], 'serial_numbers': ['1\n2']},
            {'name': 'A', 'configurations': [], 'serial_numbers': [123]},
            {'name': 'A', 'configurations': [], 'serial_numbers': 'abc'},
            {'name': 'A', 'configurations': [], 'serial_numbers': [], 'extra': 1},
        )
        for value in cases:
            with self.subTest(value=str(value)[:50]), self.assertRaises(ValueError):
                validate_serial_list(value)

    def test_reject_invalid_section(self):
        cases = ('{', '[]', '{}', 'null',
                 '{"version": 2, "settings": {"serial_lists": []}}',
                 '{"version": 1, "settings": null}',
                 '{"version": 1, "settings": {"unknown": 1}}')
        for value in cases:
            with self.subTest(value=value), self.assertRaises(ValueError):
                parse_security_settings(value)

    def test_project_roundtrip_keeps_older_sections(self):
        data = encode_security_settings({'serial_lists': [
            {'name': 'Lizenz', 'configurations': ['Standard'],
             'serial_numbers': ['1111-2222']}]})
        project = InstallerProject(name='Example', sections={
            'Log-Datei': 'unchanged', 'Systemanforderungen': 'unchanged',
            SECURITY_SECTION: data,
        })
        with tempfile.TemporaryDirectory() as temp:
            filename = str(Path(temp)/'example.installer.json')
            project.save(filename)
            restored = InstallerProject.load(filename)
            self.assertEqual(restored.sections['Log-Datei'], 'unchanged')
            self.assertEqual(restored.sections['Systemanforderungen'], 'unchanged')
            self.assertEqual(parse_security_settings(restored.sections[SECURITY_SECTION]),
                             parse_security_settings(data))


class SecurityUiSourceTest(unittest.TestCase):
    def test_compilation(self):
        for name in ('software_installer.py', 'software_installer_dialogs.py',
                     'installer_security_settings.py'):
            with self.subTest(name=name):
                ast.parse((BASE / name).read_text('utf-8'))

    def test_parent_theme_geometry_tabs_and_table(self):
        chunk = UI[UI.index('class InstallerSecurityDialog('):
                   UI.index('class InstallerDestinationDialog(', UI.index('class InstallerSecurityDialog('))]
        for needle in (
            'class InstallerSecurityDialog(InstallerThemedDialog)',
            'gradient_title=True',
            'setFixedSize(WIZARD_SIZE[0] - 140, WIZARD_SIZE[1] - 40)',
            'self.tabs = QTabWidget(',
            '"Serial Nummer"', '"Gültigkeits-Bereich"', '"Serial Nummer Liste"',
            '"Listen Name", "Anzahl", "Konfiguration"',
            'self.lists_table.verticalHeader().setVisible(False)',
            'setSectionResizeMode(QHeaderView.Interactive)',
            '"Hinzufügen"', '"Entfernen"', '"Bearbeiten"',
            '("OK", "Abbrechen", "Hilfe")',
            'encode_security_settings(',
            'self.help_callback("Sicherheit")',
        ):
            with self.subTest(needle=needle):
                self.assertIn(needle, chunk)

    def test_child_theme_geometry_and_fields(self):
        chunk = UI[UI.index('class InstallerSerialListPropertiesDialog('):
                   UI.index('class InstallerSecurityDialog(', UI.index('class InstallerSerialListPropertiesDialog('))]
        for needle in ('gradient_title=True',
                       'setWindowTitle("Serial Nummer - Listen Eigenschaften")',
                       'setFixedSize(WIZARD_SIZE[0] - 140, WIZARD_SIZE[1] - 40)',
                       '"Listen Name"', '"Konfigurationen"',
                       '"Alle Konfigurationen"', '"Standard"',
                       '"Serial Nummern"', '"Kommandos"',
                       'self.serial_table = QTableWidget(0, 3, self)',
                       'self.serial_table.verticalHeader().setVisible(False)',
                       'setPopupMode(QToolButton.MenuButtonPopup)',
                       'self.result_entry = entry',
                       '("OK", "Abbrechen", "Hilfe")'):
            with self.subTest(needle=needle):
                self.assertIn(needle, chunk)

    def test_menu_actions_and_shortcuts(self):
        menu = UI[UI.index('    def _create_commands(self):', UI.index('class InstallerSerialListPropertiesDialog(')):
                  UI.index('    def _set_rows(self, rows):', UI.index('class InstallerSerialListPropertiesDialog('))]
        for title, shortcut in (
            ('Wiederherstellen', 'Ctrl+Z'), ('Rückgängig', 'Ctrl+Y'),
            ('Erstellen ...', 'Ctrl+G'), ('Finden', None), ('Sortieren', None),
            ('Ausschneiden', 'Ctrl+X'), ('Kopieren', 'Ctrl+C'),
            ('Einfügen', 'Ctrl+V'), ('Alle auswählen', 'Ctrl+A'),
            ('Alle Nummern löschen', 'Ctrl+L'),
            ('Selektierte Reihen Löschen', 'Ctrl+Delete'),
            ('Reihe Einfügen', 'Insert'), ('Reihen Einfügen', 'Ctrl+Insert'),
            ('Drucken', None), ('Importieren', None), ('Exportieren', None),
        ):
            with self.subTest(title=title):
                self.assertIn(repr(title), menu.replace('"', "'"))
                if shortcut:
                    self.assertIn(repr(shortcut), menu.replace('"', "'"))
        self.assertEqual(menu.count('            None,'), 4)

    def test_routes_to_new_dialog(self):
        self.assertIn('"Sicherheit": self.edit_security', WORKBENCH)
        self.assertIn('InstallerSecurityDialog(', WORKBENCH)
        self.assertIn('self.project.sections[SECURITY_SECTION] = dialog.serialized', WORKBENCH)
        self.assertIn('return bool(self.save_configuration())', WORKBENCH)

    def test_help_index_and_toc(self):
        self.assertTrue((HELP / 'sicherheit.html').is_file())
        for name in ('installer.hhp', 'installer.hhc', 'installer.hhk', 'index.html'):
            with self.subTest(name=name):
                self.assertEqual((HELP / name).read_text('utf8').count('sicherheit.html'), 1)


class SecurityHandlerBehaviorTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        module = ast.parse(WORKBENCH)
        workbench = next(node for node in module.body if isinstance(node, ast.ClassDef)
                         and node.name == 'SoftwareInstallerWorkbench')
        method = next(node for node in workbench.body if isinstance(node, ast.FunctionDef)
                      and node.name == 'edit_security')
        cls.code = compile(ast.Module(body=[method], type_ignores=[]), '<test-handler>', 'exec')

    def simulate(self, accepted, serialized=None, *, starting=None, load_error=None):
        class FakeHost:
            def __init__(self):
                self.project = SimpleNamespace(sections=dict(starting or {}))
                self._dark_mode = True
                self.dirty_calls = self.save_calls = 0
            def _show_help_topic(self, topic):
                pass
            def _mark_dirty(self):
                self.dirty_calls += 1
            def save_configuration(self):
                self.save_calls += 1
                return True
        class FakeDialog:
            def __init__(self, *args, **kwargs):
                if load_error:
                    raise load_error
                self.serialized = serialized
            def exec_(self):
                return 1 if accepted else 0
        warnings = []
        namespace = {'InstallerSecurityDialog': FakeDialog,
                     'installer_themed_warning': lambda *args, **kwargs:
                         warnings.append((args, kwargs)),
                     'QDialog': SimpleNamespace(Accepted=1),
                     'SECURITY_SECTION': SECURITY_SECTION}
        exec(self.code, namespace)
        host = FakeHost()
        ok = namespace['edit_security'](host)
        return host, ok, warnings

    def test_cancel_does_not_write(self):
        host, result, warnings = self.simulate(False, 'new',
                                                starting={SECURITY_SECTION: 'old'})
        self.assertFalse(result)
        self.assertEqual(host.project.sections[SECURITY_SECTION], 'old')
        self.assertEqual((host.dirty_calls, host.save_calls), (0, 0))
        self.assertFalse(warnings)

    def test_ok_writes_and_saves(self):
        value = encode_security_settings({'serial_lists': []})
        host, result, warnings = self.simulate(True, value, starting={'Log-Datei': 'kept'})
        self.assertTrue(result)
        self.assertEqual(host.project.sections, {'Log-Datei': 'kept', SECURITY_SECTION: value})
        self.assertEqual((host.dirty_calls, host.save_calls), (1, 1))
        self.assertFalse(warnings)

    def test_unchanged_ok_does_not_resave(self):
        value = encode_security_settings({'serial_lists': []})
        host, result, _ = self.simulate(True, value, starting={SECURITY_SECTION: value})
        self.assertTrue(result)
        self.assertEqual((host.dirty_calls, host.save_calls), (0, 0))

    def test_load_error_shows_dark_warning(self):
        host, result, warnings = self.simulate(False, 'new', load_error=ValueError('bad'))
        self.assertFalse(result)
        self.assertEqual(host.save_calls, 0)
        self.assertEqual(len(warnings), 1)
        self.assertTrue(warnings[0][1]['dark_mode'])


if __name__ == '__main__':
    unittest.main()
