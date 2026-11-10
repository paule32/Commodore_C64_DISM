"""Stage 558: Wizard-Seiten 6+7, Optionen und Persistenz ohne Qt."""
from __future__ import annotations

import ast
import json
from pathlib import Path
import tempfile
import unittest

from installer_wizard_options import (
    WINDOWS_LANGUAGES, DEFAULT_LANGUAGES, DEFAULT_LANGUAGE,
    WINDOWS_VERSION_TREE, DEFAULT_WINDOWS_VERSIONS, windows_leaf_ids,
    decode_selection, encode_selection, normalized_default_language,
)
from software_installer_model import InstallerProject, InstallerProjectRegistry

ROOT = Path(__file__).resolve().parent
DIALOGS = (ROOT / 'software_installer_dialogs.py').read_text(encoding='utf-8')
IDE = (ROOT / 'software_installer.py').read_text(encoding='utf-8')
HELP = ROOT / 'help' / 'software_installer'


class Stage558Tests(unittest.TestCase):
    def test_sources_are_syntactically_valid(self):
        for name in ('software_installer_dialogs.py', 'software_installer.py',
                     'installer_wizard_options.py'):
            with self.subTest(source=name):
                ast.parse((ROOT / name).read_text(encoding='utf-8'))

    def test_language_catalog_is_unique_and_has_correct_defaults(self):
        codes = [code for _name, code in WINDOWS_LANGUAGES]
        labels = [name for name, _code in WINDOWS_LANGUAGES]
        self.assertEqual(len(codes), len(set(codes)))
        self.assertGreaterEqual(len(codes), 40)
        self.assertTrue(set(DEFAULT_LANGUAGES).issubset(codes))
        self.assertIn(DEFAULT_LANGUAGE, DEFAULT_LANGUAGES)
        self.assertEqual(dict(WINDOWS_LANGUAGES)['Deutsch'], 'de-DE')
        self.assertEqual(dict(WINDOWS_LANGUAGES)['Englisch'], 'en-US')
        self.assertEqual(labels, sorted(labels, key=str.casefold))

    def test_language_codec_persists_selection_as_str(self):
        codes = [code for _name, code in WINDOWS_LANGUAGES]
        value = encode_selection(['de-DE', 'en-US', 'fr-FR'])
        self.assertIsInstance(value, str)
        self.assertEqual(decode_selection(value, codes),
                         [code for code in codes if code in ('de-DE', 'en-US', 'fr-FR')])
        self.assertEqual(decode_selection('[]', codes, DEFAULT_LANGUAGES), [])
        self.assertEqual(decode_selection('broken', codes, DEFAULT_LANGUAGES),
                         [code for code in codes if code in DEFAULT_LANGUAGES])
        self.assertEqual(decode_selection('"not a list"', codes, DEFAULT_LANGUAGES),
                         [code for code in codes if code in DEFAULT_LANGUAGES])
        self.assertEqual(decode_selection('["de-DE", "de-DE", "xx"]', codes), ['de-DE'])

    def test_default_language_uses_enabled_codes(self):
        self.assertEqual(normalized_default_language(['de-DE', 'en-US']), 'de-DE')
        self.assertEqual(normalized_default_language(['fr-FR', 'en-US'], 'de-DE'), 'fr-FR')
        self.assertEqual(normalized_default_language(['fr-FR', 'en-US'], 'en-US'), 'en-US')
        self.assertEqual(normalized_default_language([]), '')

    def test_windows_leaf_ids_and_unique_group_ids(self):
        ids = []
        group_count = 0
        def visit(nodes):
            nonlocal group_count
            for key, title, children in nodes:
                self.assertTrue(key and title)
                ids.append(key)
                if children:
                    group_count += 1
                    visit(children)
        visit(WINDOWS_VERSION_TREE)
        self.assertEqual(len(ids), len(set(ids)))
        self.assertGreaterEqual(group_count, 3)
        leaves = windows_leaf_ids()
        self.assertGreaterEqual(len(leaves), 10)
        self.assertEqual(len(leaves), len(set(leaves)))
        self.assertTrue(set(DEFAULT_WINDOWS_VERSIONS).issubset(leaves))
        self.assertIn('win-11', leaves)
        self.assertIn('win-server-2025', leaves)

    def test_seven_wizard_pages_have_consistent_geometry_and_navigation(self):
        self.assertIn('WIZARD_SIZE = (760, 590)', DIALOGS)
        self.assertIn('self.image_box.setFixedWidth(140)', DIALOGS)
        for cls in ('InstallerGeneralInfoDialog', 'InstallerPlatformDialog',
                    'InstallerSourcesDialog', 'InstallerAppearanceDialog',
                    'InstallerProjectThemeDialog', 'InstallerLanguagesDialog',
                    'InstallerRequirementsDialog'):
            self.assertIn(f'class {cls}(InstallerWizardDialog):', DIALOGS)
        requirements = DIALOGS.split('class InstallerRequirementsDialog(', 1)[1].split(
            '\nclass InstallerDestinationDialog(', 1)[0]
        language = DIALOGS.split('class InstallerLanguagesDialog(', 1)[1].split(
            '\nclass InstallerRequirementsDialog(', 1)[0]
        project_theme = DIALOGS.split('class InstallerProjectThemeDialog(', 1)[1].split(
            '\nclass InstallerLanguagesDialog(', 1)[0]
        self.assertIn('final_page=True', requirements)
        self.assertNotIn('final_page=True', project_theme)
        self.assertNotIn('final_page=True', language)

    def test_page_six_has_checklist_and_dynamic_default_combo(self):
        for text in ('"Sprachen"', '"Welche Sprache(n) möchten Sie unterstützen ?"',
                     '"Welche Standard-Sprache soll genutzt werden ?"',
                     'self.languages_list = QListWidget(self)',
                     'self.default_language_combo = QComboBox(self)',
                     'self.languages_list.itemChanged.connect(self._sync_default_languages)',
                     'Qt.ItemIsUserCheckable',
                     'self.default_language_combo.addItem(item.text(), code)',
                     '"languages": encode_selection(selected)',
                     '"default_language": default'):
            self.assertIn(text, DIALOGS)

    def test_page_seven_has_three_options_and_cascading_tree(self):
        for text in ('"Un-Install unterstützen"',
                     '"Log-Datei während der Installation führen"',
                     '"Benutzer warnen, wenn Administrator-Rechte erforderlich sind"',
                     '"Wählen Sie das/die gewünschte / erforderliche System"',
                     'self.windows_tree = QTreeWidget(self)',
                     'self.windows_tree.itemChanged.connect(self._on_item_changed)',
                     'self._set_descendants(item, state)',
                     'Qt.PartiallyChecked',
                     'self._updating_tree = True',
                     'self._recompute_parent(parent)',
                     '"windows_versions": encode_selection(self._checked_leaves())',
                     '"support_uninstall"', '"installation_log"', '"warn_administrator"'):
            self.assertIn(text, DIALOGS)

    def test_workbench_uses_all_seven_pages_and_preserves_back_values(self):
        section = IDE.split('def _run_wizard(', 1)[1].split('def _confirm_replace_project(', 1)[0]
        for cls in ('InstallerLanguagesDialog', 'InstallerRequirementsDialog'):
            self.assertIn(cls, section)
        self.assertIn('values.update(dialog.values())', section)
        self.assertIn('page = max(0, page - 1)', section)
        self.assertIn('self.project.general = values', section)

    def test_checkbox_cascade_and_parent_partial_without_qt(self):
        """Fuehrt die *echten* QTreeWidget-Methoden mit Test-Items aus.

        Die GUI-Bibliothek wird hier nicht geladen; die Dialogmethoden stammen
        direkt aus dem AST der produktiven Implementierung.
        """
        from types import SimpleNamespace
        module = ast.parse(DIALOGS)
        klass = next(node for node in module.body
                     if isinstance(node, ast.ClassDef) and
                     node.name == 'InstallerRequirementsDialog')
        method_names = {'_set_descendants', '_recompute_parent', '_on_item_changed',
                        '_checked_leaves'}
        methods = [node for node in klass.body if isinstance(node, ast.FunctionDef)
                   and node.name in method_names]
        self.assertEqual({m.name for m in methods}, method_names)
        test_ast = ast.Module(body=[ast.ClassDef(name='TreeActions', bases=[], keywords=[],
                                                 body=methods, decorator_list=[])],
                              type_ignores=[])
        ast.fix_missing_locations(test_ast)
        Qt = SimpleNamespace(Unchecked=0, PartiallyChecked=1, Checked=2, UserRole=32)
        environment = {'Qt': Qt}
        exec(compile(test_ast, 'software_installer_dialogs.py', 'exec'), environment)
        TreeActions = environment['TreeActions']

        class FakeItem:
            def __init__(self, identifier, parent=None, state=0):
                self.identifier = identifier
                self._parent = parent
                self._children = []
                self._state = state
                self.callback = None
                if parent is not None:
                    parent._children.append(self)

            def childCount(self):
                return len(self._children)

            def child(self, index):
                return self._children[index]

            def checkState(self, _column):
                return self._state

            def setCheckState(self, _column, value):
                if self._state != value:
                    self._state = value
                    if self.callback:
                        self.callback(self, 0)

            def parent(self):
                return self._parent

            def data(self, _column, _role):
                return self.identifier

        root = FakeItem('desktop', state=Qt.Unchecked)
        old = FakeItem('old', root, Qt.Unchecked)
        old_a = FakeItem('win-7', old)
        old_b = FakeItem('win-8', old)
        modern = FakeItem('new', root, Qt.Checked)
        new_a = FakeItem('win-10', modern, Qt.Checked)
        new_b = FakeItem('win-11', modern, Qt.Checked)
        class FakeTree:
            def topLevelItemCount(self):
                return 1
            def topLevelItem(self, _index):
                return root
        harness = TreeActions()
        harness.windows_tree = FakeTree()
        harness._updating_tree = False
        for node in (root, old, old_a, old_b, modern, new_a, new_b):
            node.callback = harness._on_item_changed
        harness._recompute_parent(root)
        self.assertEqual(root.checkState(0), Qt.PartiallyChecked)
        # Elternknoten markieren -> alle Nachkommen an.
        root.setCheckState(0, Qt.Checked)
        self.assertTrue(all(n.checkState(0) == Qt.Checked
                            for n in (old, old_a, old_b, modern, new_a, new_b)))
        # Einzelnes Blatt deaktivieren -> Gruppe und Wurzel teilweise an.
        new_a.setCheckState(0, Qt.Unchecked)
        self.assertEqual(modern.checkState(0), Qt.PartiallyChecked)
        self.assertEqual(root.checkState(0), Qt.PartiallyChecked)
        self.assertEqual(set(harness._checked_leaves()), {'win-7', 'win-8', 'win-11'})
        # Gruppenwahl aus -> alle Blaetter aus, kein Endlossignal.
        root.setCheckState(0, Qt.Unchecked)
        self.assertEqual(harness._checked_leaves(), [])
        self.assertTrue(all(n.checkState(0) == Qt.Unchecked
                            for n in (old, old_a, old_b, modern, new_a, new_b)))

    def test_roundtrip_registry_preserves_all_new_fields(self):
        values = {'languages': encode_selection(['de-DE', 'en-US', 'fr-FR']),
                  'default_language': 'de-DE',
                  'windows_versions': encode_selection(['win-10', 'win-11', 'win-server-2022']),
                  'support_uninstall': 'true', 'installation_log': 'false',
                  'warn_administrator': 'true', 'project_theme': 'Standard 2'}
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'sample.installer.json'
            registry = InstallerProjectRegistry(Path(folder) / 'projects.json')
            project = InstallerProject(name='Test Setup', general=values)
            project.save(str(path))
            registry.register(path, project)
            loaded = InstallerProject.load(str(path))
            self.assertEqual(loaded.general, values)
            self.assertEqual(registry.available()[0]['settings']['general'], values)
            self.assertEqual(json.loads(path.read_text(encoding='utf-8'))['version'], 1)

    def test_new_help_topics_exist_and_are_registered(self):
        for i in (6, 7):
            target = f'wizard_seite_{i}.html'
            self.assertTrue((HELP / target).is_file())
            for catalog in ('index.html', 'installer.hhc', 'installer.hhk', 'installer.hhp'):
                self.assertIn(target, (HELP / catalog).read_text(encoding='utf-8'))
            self.assertIn(f'"Wizard Seite {i}"', DIALOGS)


if __name__ == '__main__':
    unittest.main()
