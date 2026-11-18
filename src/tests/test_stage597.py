"""Stage 597: per-output project names, module/Unit ownership and menus.

These tests do not require Qt or a Windows host. GUI methods are extracted
from the real source code and exercised with small Qt-compatible doubles.
"""
from __future__ import annotations

import configparser
from pathlib import Path
import unittest

import project_named_targets as targets
from d64qt5.dbase_project_new import DBASE_NEW_MENU, DBASE_GROUP_NEW_MENU, new_dbase_file_content
from test_stage596 import FakeCombo, extracted_class

ROOT = Path(__file__).parent


class Node:
    def __init__(self, name, lang, kind, role="", target="", path="", parent=None):
        self.name = name
        self.lang = lang
        self.kind = kind
        self.role = role
        self.target = target
        self.path = path
        self._parent = parent

    def data(self, _col, role):
        values = {256 + 301: self.lang, 256 + 302: self.path,
                  256 + 303: self.kind, 256 + 305: self.target,
                  256 + 306: self.role}
        return values.get(role)

    def text(self, _col):
        return self.name

    def parent(self):
        return self._parent

    def childCount(self):
        return 0


class Stage597Tests(unittest.TestCase):
    def test_old_project_names_migrate_into_both_pascal_and_dbase_outputs(self):
        names = targets.normalize_names({"pascal": "AltPas", "dbase": "AltDB"})
        self.assertEqual(targets.profile_name(names, "pascal", "program"), "AltPas")
        self.assertEqual(targets.profile_name(names, "pascal", "library"), "AltPas")
        self.assertEqual(targets.profile_name(names, "dbase", "program"), "AltDB")
        self.assertEqual(targets.profile_name(names, "dbase", "library"), "AltDB")

    def test_new_names_keep_distinct_exe_and_dll_including_empty_fields(self):
        names = targets.normalize_names({
            "pascal_program": "Foo", "pascal_library": "FooPlugin",
            "dbase_program": "DbExe", "dbase_library": "DbRuntime",
            "pascal": "Legacy", "dbase": "OldRuntime",
        })
        self.assertEqual(targets.profile_name(names, "pascal", "program"), "Foo")
        self.assertEqual(targets.profile_name(names, "pascal", "library"), "FooPlugin")
        self.assertEqual(targets.profile_name(names, "dbase", "library"), "DbRuntime")
        names["pascal_library"] = ""
        self.assertEqual(targets.profile_name(names, "pascal", "library"), "")

    def test_profile_names_and_project_kinds_are_persisted_separately(self):
        parser = configparser.ConfigParser(interpolation=None)
        parser.optionxform = str
        names = {"basic": "Basic", "pascal_program": "Foo",
                 "pascal_library": "Bar", "dbase_program": "DBaseApp",
                 "dbase_library": "DBaseRuntime"}
        assignments = {
            '@group:pascal:pe32:modules': 'pascal|program',
            targets.leaf_key('C:/foo/Library.pas', 'pascal_source',
                             ['Pascal-Programme', 'Windows PE32+', 'Module']): 'pascal|library',
        }
        targets.encode_names(parser, names, ('pascal', 'library'), assignments)
        loaded_names, selection, loaded_assignments = targets.decode_names(parser)
        self.assertEqual(loaded_names['pascal_program'], 'Foo')
        self.assertEqual(loaded_names['pascal_library'], 'Bar')
        self.assertEqual(loaded_names['dbase_library'], 'DBaseRuntime')
        self.assertEqual(selection, ('pascal', 'library'))
        self.assertEqual(loaded_assignments, assignments)
        self.assertEqual(targets.rebase_leaf_key('@group:pascal:pe32:modules',
                                                Path('X:/Demo.pro'), to_storage=True,
                                                path_converter=lambda path, _: 'MUTATED'),
                         '@group:pascal:pe32:modules')

    def test_legacy_language_only_assignments_still_match_both_kinds(self):
        self.assertTrue(targets.assignment_matches('pascal', 'pascal', 'program'))
        self.assertTrue(targets.assignment_matches('pascal', 'pascal', 'library'))
        self.assertTrue(targets.assignment_matches('pascal|library', 'pascal', 'library'))
        self.assertFalse(targets.assignment_matches('pascal|library', 'pascal', 'program'))
        self.assertFalse(targets.assignment_matches('dbase|program', 'pascal', 'program'))

    def test_new_dbase_module_is_first_creation_action(self):
        self.assertEqual(DBASE_NEW_MENU[0][:2], ('Neu: Modul', 'modules'))
        self.assertEqual(DBASE_GROUP_NEW_MENU[('modules', '')][0], 'Neu: Modul')
        self.assertEqual(new_dbase_file_content('modules', Path('Module1.prg')), '')
        source = (ROOT / 'd64_dism.py').read_text(encoding='utf-8')
        self.assertIn('("modules", "Module",', source)
        self.assertIn('PROJECT_DBASE_MODULES_KEY: "Category.dbase.modules"', source)
        self.assertIn('role in {"programs", "modules"}', source)

    def test_top_project_combo_uses_different_program_and_library_names(self):
        Explorer = extracted_class()
        state = Explorer()
        state.project_name_combo = FakeCombo()
        state._named_project_names = targets.normalize_names({
            'pascal_program': 'ProgrammFoo', 'pascal_library': 'BibliothekBar',
            'dbase_program': 'App', 'dbase_library': 'Runtime',
        })
        state._named_project_selected = ('pascal', 'library')
        state._project_named_refresh_selection()
        pairs = {name: data for name, data in state.project_name_combo.items}
        self.assertEqual(pairs['Programm: ProgrammFoo'], 'pascal|program')
        self.assertEqual(pairs['Bibliothek: BibliothekBar'], 'pascal|library')
        self.assertEqual(pairs['Bibliothek: Runtime'], 'dbase|library')
        self.assertEqual(state.project_name_combo.currentData(), 'pascal|library')

    def test_pascal_group_assignment_is_inherited_and_leaf_can_override(self):
        Explorer = extracted_class()
        Explorer._project_named_leaf_key.__globals__.update({
            'PROJECT_NODE_PASCAL_MODULE_ROOT': 'pascal_module_root',
            'PROJECT_NODE_PASCAL_UNIT_ROOT': 'pascal_unit_root',
            'PROJECT_NODE_DBASE_GROUP': 'dbase_group',
        })
        state = Explorer()
        state._project_item_kind = lambda node: node.kind
        group = Node('Module', 'pascal', 'pascal_module_root', 'modules', 'pe32')
        leaf1 = Node('Test.pas', 'pascal', 'pascal_target_source',
                     'modules', 'pe32', 'C:/src/Test.pas', group)
        leaf2 = Node('Test2.pas', 'pascal', 'pascal_target_source',
                     'modules', 'pe32', 'C:/src/Test2.pas', group)
        state._named_project_names = targets.normalize_names({
            'pascal_program': 'Foo', 'pascal_library': 'Bar'})
        state._named_project_selected = ('pascal', 'library')
        state._named_project_assignments = {
            '@group:pascal:pe32:modules': 'pascal|library',
        }
        self.assertTrue(state._project_named_matches_item(leaf1))
        state._named_project_selected = ('pascal', 'program')
        self.assertFalse(state._project_named_matches_item(leaf1))
        state._named_project_assignments[state._project_named_leaf_key(leaf2)] = 'pascal|program'
        self.assertTrue(state._project_named_matches_item(leaf2))
        self.assertFalse(state._project_named_matches_item(leaf1))

    def test_gui_wires_separate_fields_and_build_output_name(self):
        src = (ROOT / 'd64_dism.py').read_text(encoding='utf-8')
        for title in ('Pascal EXE', 'Pascal DLL', 'dBASE EXE', 'dBASE DLL'):
            self.assertIn(title, (ROOT / 'project_named_targets.py').read_text(encoding='utf-8'))
        self.assertIn('NAMED_PROJECT_PROFILE_FIELDS', src)
        self.assertIn('output_path = output_path.with_name(_stem + _suffix)', src)
        self.assertIn('output_path.name if is_library else None', src)
        self.assertIn('build_kind = _project_kind', src)
        self.assertIn('Pascal: Programm', src)
        self.assertIn('Pascal: Bibliothek', src)
        self.assertIn('dBASE: Runtime', src)
        self.assertIn('QTreeWidget#project_tree QHeaderView::section', src)
        self.assertIn('QToolButton[projectNameButton=', src)


if __name__ == '__main__':
    unittest.main()
