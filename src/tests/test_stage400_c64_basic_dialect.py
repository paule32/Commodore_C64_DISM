"""Stage 400: isolation tests without an installed PyQt5 package."""
import ast
import configparser
import types
import unittest
from pathlib import Path

SOURCE = Path(__file__).with_name('d64_dism.py')
TREE = ast.parse(SOURCE.read_text(encoding='utf-8'))
DIALECTS = ('68000', '68010', '68020', '68030')

def one_function(name):
    return next(n for n in TREE.body if isinstance(n, ast.FunctionDef) and n.name == name)

def isolate(nodes, env):
    mod = ast.fix_missing_locations(ast.Module(body=list(nodes), type_ignores=[]))
    exec(compile(mod, str(SOURCE), 'exec'), env)

def c64_settings_for_loop(func):
    return next(n for n in ast.walk(func) if isinstance(n, ast.For)
                and isinstance(n.iter, ast.Call)
                and isinstance(n.iter.func, ast.Attribute)
                and isinstance(n.iter.func.value, ast.Name)
                and n.iter.func.value.id == 'PROJECT_C64_BASIC_DIALECT_PROFILES')

class Stage400Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.env = {}
        nodes = [n for n in TREE.body if isinstance(n, ast.Assign)
                 and any(isinstance(t, ast.Name) and t.id == 'PROJECT_C64_BASIC_DIALECT_PROFILES'
                         for t in n.targets)]
        isolate(nodes + [one_function('_normalize_project_c64_basic_dialect')], cls.env)

    def test_all_four_profiles_are_available(self):
        self.assertEqual(tuple(self.env['PROJECT_C64_BASIC_DIALECT_PROFILES']), DIALECTS)

    def test_normalization_and_fallback(self):
        fn = self.env['_normalize_project_c64_basic_dialect']
        for val in (None, '', 'unknown', 'BASIC V2', 'basic_v2'):
            self.assertEqual(fn(val), 'basic_v2')
        for val in ('Simon BASIC', 'simon_basic', 'SIMONS BASIC'):
            self.assertEqual(fn(val), 'simon_basic')

    def test_ini_save_and_read_four_distinct_profiles(self):
        env=dict(self.env)
        env['parser'] = configparser.ConfigParser(interpolation=None)
        env['parser'].optionxform = str
        env['entries'] = {
            item['dialect_key']: [{'value': 'simon_basic' if i%2 else 'basic_v2'}]
            for i, item in enumerate(env['PROJECT_C64_BASIC_DIALECT_PROFILES'].values())
        }
        isolate([c64_settings_for_loop(one_function('format_project_ini'))],env)
        for i, profile in enumerate(DIALECTS):
            section=f'Settings.C64.{profile}.Compiler.BASIC'
            self.assertEqual(env['parser'].get(section,'Dialect'),
                             'simon_basic' if i%2 else 'basic_v2')
        content = configparser.ConfigParser(interpolation=None)
        content.read_string('''[Settings.C64.68020.Compiler.BASIC]\nDialect = Simon BASIC\n''')
        read_env=dict(self.env, parser=content, entries={
            item['dialect_key']:[{'value':'basic_v2'}]
            for item in self.env['PROJECT_C64_BASIC_DIALECT_PROFILES'].values()
        })
        isolate([c64_settings_for_loop(one_function('parse_project_ini'))], read_env)
        self.assertEqual(read_env['entries']['__c64_68020_basic_dialect__'][0]['value'],'simon_basic')
        self.assertEqual(read_env['entries']['__c64_68000_basic_dialect__'][0]['value'],'basic_v2')
        self.assertEqual(read_env['entries']['__c64_68010_basic_dialect__'][0]['value'],'basic_v2')

    def test_new_tree_contains_basic_and_uses_exclusive_qbutton_group(self):
        text=SOURCE.read_text('utf-8')
        for phrase in (
            'self.compiler_basic_item = QTreeWidgetItem(self.compiler_item, ["BASIC"])',
            'self.compiler_basic_item.setData(0, Qt.UserRole, "compiler.basic")',
            'self.pages["compiler.basic"] = self.basic_page',
            'self.basic_dialect_groupbox = QGroupBox("Dialekt", self.basic_page)',
            'self.basic_dialect_group.setExclusive(True)',
            '("basic_v2", "BASIC V2")',
            '("simon_basic", "Simon BASIC")',
            'radio.toggled.connect(self._basic_dialect_changed)',
            'self.set_basic_dialect("basic_v2")',
        ):
            self.assertIn(phrase,text)

    def test_owner_sync_marks_modified_and_saves_only_on_change(self):
        meths=[n for n in ast.walk(TREE) if isinstance(n, ast.FunctionDef)
               and n.name=='set_project_c64_basic_dialect']
        self.assertEqual(len(meths),1)
        env=dict(self.env)
        isolate([meths[0]],env)
        calls=[]
        instance=types.SimpleNamespace(project_c64_basic_dialect={p:'basic_v2' for p in DIALECTS},
                                       project_settings_panel=None,
                                       current_project_path=Path('test.pro'),
                                       set_project_modified=lambda x: calls.append(('modified',x)),
                                       save_project=lambda: calls.append(('save',)))
        method=env['set_project_c64_basic_dialect']
        method(instance,'68010','Simon BASIC')
        self.assertEqual(instance.project_c64_basic_dialect['68010'],'simon_basic')
        self.assertEqual(calls, [('modified',True),('save',)])
        method(instance,'68010','Simon BASIC')
        self.assertEqual(calls, [('modified',True),('save',)])
        method(instance,'68010','basic_v2',mark_modified=False)
        self.assertEqual(calls, [('modified',True),('save',)])

if __name__=='__main__':
    unittest.main()
