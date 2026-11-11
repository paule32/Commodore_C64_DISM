"""Stage 565 – Log-Datei-Konfiguration, Dialog-Anbindung und Regressionen."""
from __future__ import annotations

import ast
import json
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace

from installer_log_settings import (
    LOG_FILE_DEFAULTS, LOG_FILE_SECTION, encode_log_settings,
    parse_log_settings, validate_log_settings,
)
from software_installer_model import InstallerProject

ROOT = Path(__file__).parent
DIALOGS = (ROOT / 'software_installer_dialogs.py').read_text(encoding='utf-8')
WORKBENCH = (ROOT / 'software_installer.py').read_text(encoding='utf-8')
HELP = ROOT / 'help/software_installer'


class Stage565ModelTests(unittest.TestCase):
    def test_defaults_and_original_placeholders(self):
        result = parse_log_settings('')
        self.assertEqual(result, LOG_FILE_DEFAULTS)
        self.assertFalse(result['enabled'])
        self.assertEqual(result['filename'], r'%TempFolder%\%ProductName% Setup Log.txt')
        self.assertEqual(result['write_mode'], 'append')

    def test_append_and_overwrite_roundtrip(self):
        for mode in ('append', 'overwrite'):
            with self.subTest(mode=mode):
                options = {'enabled': True, 'filename': r'%TempFolder%\%ProductName% Setup Log.txt',
                           'write_mode': mode}
                self.assertEqual(parse_log_settings(encode_log_settings(options)), options)

    def test_disabled_configuration_retains_name_and_mode(self):
        options = {'enabled': False, 'filename': r'D:\Reports\setup.log',
                   'write_mode': 'overwrite'}
        self.assertEqual(parse_log_settings(encode_log_settings(options)), options)

    def test_partial_format_defaults(self):
        result = parse_log_settings(json.dumps({'version': 1, 'settings': {'enabled': True}}))
        self.assertTrue(result['enabled'])
        self.assertEqual(result['filename'], LOG_FILE_DEFAULTS['filename'])
        self.assertEqual(result['write_mode'], 'append')

    def test_reject_invalid_settings(self):
        invalids = (
            {'enabled': 1}, {'enabled': 'true'}, {'filename': None},
            {'enabled': True, 'filename': '  '}, {'filename': 'a\nb'},
            {'filename': 'a\x00b'}, {'filename': 'x' * 4097},
            {'write_mode': 'invalid'}, {'unknown': 99},
        )
        for bad in invalids:
            with self.subTest(bad=repr(bad)[:60]):
                with self.assertRaises(ValueError):
                    validate_log_settings(bad)
        for bad in ([], 123, 'text'):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                validate_log_settings(bad)

    def test_broken_stored_document_reports_error(self):
        for bad in ('{', '[]', '{}', '{"version": 2, "settings": {}}',
                    '{"version": 1, "settings": null}'):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                parse_log_settings(bad)

    def test_project_roundtrip_does_not_discard_other_sections(self):
        project = InstallerProject(name='App', sections={'Systemanforderungen': 'keep',
                        LOG_FILE_SECTION: encode_log_settings({'enabled': True,
                             'filename': r'C:\temp\my_setup.txt', 'write_mode': 'overwrite'})})
        with tempfile.TemporaryDirectory() as directory:
            filename = Path(directory) / 'demo.installer.json'
            project.save(str(filename))
            restored = InstallerProject.load(str(filename))
            self.assertEqual(restored.sections['Systemanforderungen'], 'keep')
            settings = parse_log_settings(restored.sections[LOG_FILE_SECTION])
            self.assertEqual(settings['filename'], r'C:\temp\my_setup.txt')
            self.assertEqual(settings['write_mode'], 'overwrite')


class Stage565GuiStructureTests(unittest.TestCase):
    def test_syntax(self):
        for filename in ('software_installer.py', 'software_installer_dialogs.py',
                         'installer_log_settings.py'):
            ast.parse((ROOT / filename).read_text(encoding='utf-8'))

    def test_dialog_inherits_theme_and_matches_previous_geometry(self):
        start = DIALOGS.index('class InstallerLogFileDialog(')
        end = DIALOGS.index('class InstallerDestinationDialog(', start)
        dialog = DIALOGS[start:end]
        self.assertIn('class InstallerLogFileDialog(InstallerThemedDialog)', dialog)
        self.assertIn('gradient_title=True', dialog)
        self.assertIn('self.setFixedSize(WIZARD_SIZE[0] - 140, WIZARD_SIZE[1] - 40)', dialog)
        self.assertIn('self.setWindowTitle("Log-Datei")', dialog)
        self.assertIn('("OK", "Abbrechen", "Hilfe")', dialog)
        self.assertIn('self.help_callback("Log-Datei")', dialog)

    def test_fields_and_indentation(self):
        start = DIALOGS.index('class InstallerLogFileDialog(')
        end = DIALOGS.index('class InstallerDestinationDialog(', start)
        dialog = DIALOGS[start:end]
        for expected in ('"Log-Datei anlegen"', '"Dateiname:"', '"Schreibmodus:"',
                         'QLineEdit(', '"Anhängen"', '"Überschreiben"',
                         'indent_row.addSpacing(26)',
                         'self.mode_buttons.setExclusive(True)',
                         'self.enable_check.toggled.connect(self.details.setEnabled)',
                         'self.details.setEnabled(self.enable_check.isChecked())',
                         'self.serialized = encode_log_settings(self.settings())',
                         '(self._accept_changes, self.reject, self._help)'):
            with self.subTest(expected=expected):
                self.assertIn(expected, dialog)

    def test_button_is_routed_to_new_dialog(self):
        self.assertIn('"Log-Datei": self.edit_log_file', WORKBENCH)
        self.assertIn('InstallerLogFileDialog, installer_themed_warning', WORKBENCH)
        self.assertIn('self.project.sections[LOG_FILE_SECTION] = dialog.serialized', WORKBENCH)
        self.assertIn('return bool(self.save_configuration())', WORKBENCH)

    def test_new_help_topic_is_reachable(self):
        self.assertTrue((HELP / 'log_datei.html').is_file())
        for filename in ('installer.hhp', 'installer.hhc', 'installer.hhk', 'index.html'):
            with self.subTest(filename=filename):
                content = (HELP / filename).read_text(encoding='utf-8')
                self.assertEqual(content.count('log_datei.html'), 1)
        self.assertIn('Log-Datei', (HELP / 'installer.hhc').read_text(encoding='utf-8'))


class Stage565HandlerBehaviorTests(unittest.TestCase):
    """Echte Handler-Methode unabhängig von einem Qt-Display ausführen."""

    @classmethod
    def setUpClass(cls):
        module = ast.parse(WORKBENCH)
        workbench = next(n for n in module.body
                         if isinstance(n, ast.ClassDef) and n.name == 'SoftwareInstallerWorkbench')
        method = next(n for n in workbench.body
                      if isinstance(n, ast.FunctionDef) and n.name == 'edit_log_file')
        cls.method_code = compile(ast.Module(body=[method], type_ignores=[]),
                                  '<stage565-handler>', 'exec')

    def invoke(self, accepted, serialized, initial=None, raise_on_init=None):
        current = dict(initial or {})
        class FakeHost:
            project = SimpleNamespace(sections=current)
            _dark_mode = True
            save_calls = 0
            dirty_calls = 0
            def _show_help_topic(self, _topic):
                pass
            def _mark_dirty(self):
                self.dirty_calls += 1
            def save_configuration(self):
                self.save_calls += 1
                return True
        class FakeDialog:
            def __init__(self, *args, **kwargs):
                if raise_on_init:
                    raise raise_on_init
                self.serialized = serialized
            def exec_(self):
                return 1 if accepted else 0
        warnings = []
        namespace = {
            'InstallerLogFileDialog': FakeDialog,
            'QDialog': SimpleNamespace(Accepted=1),
            'LOG_FILE_SECTION': LOG_FILE_SECTION,
            'installer_themed_warning': lambda *a, **k: warnings.append((a, k)),
        }
        exec(self.method_code, namespace)
        host = FakeHost()
        result = namespace['edit_log_file'](host)
        return host, result, warnings

    def test_ok_writes_only_log_section_and_triggers_save(self):
        value = encode_log_settings({'enabled': True, 'write_mode': 'overwrite'})
        host, result, warnings = self.invoke(True, value, {'Other': 'kept'})
        self.assertTrue(result)
        self.assertEqual(host.project.sections, {'Other': 'kept', LOG_FILE_SECTION: value})
        self.assertEqual(host.save_calls, 1)
        self.assertEqual(host.dirty_calls, 1)
        self.assertFalse(warnings)

    def test_cancel_discards_every_change(self):
        host, result, _ = self.invoke(False, 'new-setting', {LOG_FILE_SECTION: 'old-setting'})
        self.assertFalse(result)
        self.assertEqual(host.project.sections[LOG_FILE_SECTION], 'old-setting')
        self.assertEqual((host.save_calls, host.dirty_calls), (0, 0))

    def test_unchanged_ok_does_not_write_again(self):
        value = encode_log_settings({})
        host, result, _ = self.invoke(True, value, {LOG_FILE_SECTION: value})
        self.assertTrue(result)
        self.assertEqual((host.save_calls, host.dirty_calls), (0, 0))

    def test_invalid_existing_section_shows_theme_warning_without_update(self):
        host, result, warnings = self.invoke(True, 'new', {LOG_FILE_SECTION: 'broken'},
                                              raise_on_init=ValueError('ungültig'))
        self.assertFalse(result)
        self.assertEqual(host.project.sections[LOG_FILE_SECTION], 'broken')
        self.assertEqual(host.save_calls, 0)
        self.assertEqual(len(warnings), 1)
        self.assertTrue(warnings[0][1]['dark_mode'])


if __name__ == '__main__':
    unittest.main()
