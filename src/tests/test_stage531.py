"""Stage 531: Compiler -> Sicherheit / Protector Cookie (GUI + .pro)."""
from __future__ import annotations

import ast
import configparser
from pathlib import Path
import re

ROOT = Path(__file__).parent
SOURCE = (ROOT / 'd64_dism.py').read_text('utf-8')
# Stage 530 contains PEP 810 syntax not supported by older Python parsers.
AST = ast.parse(re.sub(r'(?m)^(\s*)lazy (from|import) ', r'\1\2 ', SOURCE))
KEYS = {'pe32': '__stage531_compiler_security_pe32__',
        'pe64': '__stage531_compiler_security_pe64__'}


def find_class(name):
    found = [node for node in ast.walk(AST)
             if isinstance(node, ast.ClassDef) and node.name == name]
    assert len(found) == 1, name
    return found[0]


def find_method(name, owner=None):
    body = owner.body if owner else AST.body
    found = [node for node in body
             if isinstance(node, ast.FunctionDef) and node.name == name]
    assert len(found) == 1, (name,len(found))
    return found[0]


def code(node):
    return ast.get_source_segment(SOURCE, node)


def test_ast_and_controls():
    assert AST
    gui = find_class('WindowsCompilerSecuritySettingsPage')
    ctor = code(find_method('__init__', gui))
    assert 'QGroupBox("Stack: ", body)' in ctor
    assert 'QCheckBox(\n                "Protector Cookie", self.stack_group' in ctor
    assert 'self.protector_cookie_checkbox.setChecked(False)' in ctor
    assert 'stack_layout.addWidget(self.protector_cookie_checkbox)' in ctor
    assert 'self.setWidget(body)' in ctor
    assert 'project_windows_{target_tag}_compiler_protector_cookie' in ctor


def test_tree_navigation():
    gui = find_class('WindowsCompilerDirectorySettingsPage')
    ctor = code(find_method('__init__', gui))
    tree = code(find_method('_tree_changed', gui))
    assert 'self.nodes["compiler"], ["Sicherheit"]' in ctor
    assert '"compiler.security"' in ctor
    assert 'self.security_page = WindowsCompilerSecuritySettingsPage' in ctor
    assert 'self.stack.addWidget(self.security_page)' in ctor
    assert 'elif key == "compiler.security":\n                page = self.security_page' in tree
    assert '("Umgebung", "Compiler", "Assembler", "Linker", "Debug")' in ctor


def test_panel_independent_values():
    cls = find_class('ProjectSettingsPanel')
    methods = [find_method(name, cls) for name in
               ('_stack_cookie_changed', 'set_stack_cookie_options',
                'stack_cookie_options', '_target_key')]
    module = ast.fix_missing_locations(ast.Module(body=[ast.ClassDef(
        name='Panel', bases=[], keywords=[], body=methods, decorator_list=[]
    )], type_ignores=[]))
    context = {'stage531_default_compiler_security_options':
               lambda: {'pe32': {'protector_cookie': False},
                        'pe64': {'protector_cookie': False}}}
    exec(compile(module, '<security-panel>', 'exec'), context)

    class FakeCheckbox:
        def __init__(self): self._blocked = False
        def blockSignals(self, state):
            old = self._blocked
            self._blocked = bool(state)
            return old

    class FakePage:
        def __init__(self):
            self.protector_cookie_checkbox = FakeCheckbox()
            self.value = False
        def options(self): return {'protector_cookie': self.value}
        def set_options(self, settings):
            assert self.protector_cookie_checkbox._blocked
            self.value = bool(settings.get('protector_cookie', False))

    class Owner:
        def __init__(self):
            self.project_windows_compiler_security_options = {}
            self.modified = []
        def set_project_modified(self, value): self.modified.append(value)

    panel = object.__new__(context['Panel'])
    panel.owner = Owner()
    p32, p64 = FakePage(), FakePage()
    panel._security_pages = {'pe32': p32, 'pe64': p64}
    panel.set_stack_cookie_options({'pe32': {'protector_cookie': True},
                                    'pe64': {'protector_cookie': False}})
    assert panel.stack_cookie_options('pe32')['protector_cookie'] is True
    assert panel.stack_cookie_options('pe64')['protector_cookie'] is False
    assert not panel.owner.modified
    p64.value = True
    panel._stack_cookie_changed('pe64')
    assert p32.value is True and p64.value is True
    assert panel.owner.modified == [True]
    p32.value = False
    panel._stack_cookie_changed('pe32')
    assert panel.stack_cookie_options() == {
        'pe32': {'protector_cookie': False},
        'pe64': {'protector_cookie': True}}
    assert panel.owner.modified == [True, True]
    assert not any(p.protector_cookie_checkbox._blocked for p in (p32,p64))


def security_loop(func_name):
    fn=find_method(func_name)
    found=[n for n in fn.body if isinstance(n,ast.For)
           and 'Settings.Windows.{_suffix}.Compiler.Security' in code(n)]
    assert len(found)==1,func_name
    return found[0]


def exec_loop(node, **vars):
    ns = vars.copy()
    compiled = compile(ast.fix_missing_locations(ast.Module(
        body=[node], type_ignores=[])), '<security-iniprocess>', 'exec')
    exec(compiled, ns)
    return ns


def parse_bool(v, default=False):
    v = str(v).strip().casefold()
    return default if not v else v not in ('false','0','no','off')


def test_ini_both_targets_roundtrip():
    cfg = configparser.ConfigParser(interpolation=None)
    cfg.optionxform = str
    entries = {KEYS['pe32']: [{'protector_cookie': True}],
               KEYS['pe64']: [{'protector_cookie': False}]}
    exec_loop(security_loop('format_project_ini'), parser=cfg, entries=entries,
              PROJECT_WINDOWS_COMPILER_SECURITY_KEYS=KEYS,
              _parse_project_bool=parse_bool)
    assert cfg.getboolean('Settings.Windows.32Bit.Compiler.Security', 'ProtectorCookie')
    assert not cfg.getboolean('Settings.Windows.64Bit.Compiler.Security', 'ProtectorCookie')
    result = {}
    exec_loop(security_loop('parse_project_ini'), parser=cfg, entries=result,
              PROJECT_WINDOWS_COMPILER_SECURITY_KEYS=KEYS,
              _parse_project_bool=parse_bool)
    assert result == entries
    # Updating the x86 value must not overwrite the x64 section.
    entries[KEYS['pe32']][0]['protector_cookie'] = False
    exec_loop(security_loop('format_project_ini'), parser=cfg, entries=entries,
              PROJECT_WINDOWS_COMPILER_SECURITY_KEYS=KEYS,
              _parse_project_bool=parse_bool)
    assert not cfg.getboolean('Settings.Windows.64Bit.Compiler.Security', 'ProtectorCookie')


def test_old_projects_default_disabled():
    cfg = configparser.ConfigParser(interpolation=None)
    cfg.read_string('[Project]\nFormat=dBase2Many Project\n')
    entries = {}
    exec_loop(security_loop('parse_project_ini'), parser=cfg, entries=entries,
              PROJECT_WINDOWS_COMPILER_SECURITY_KEYS=KEYS,
              _parse_project_bool=parse_bool)
    assert entries == {key: [{'protector_cookie': False}] for key in KEYS.values()}
    cfg['Settings.Windows.32Bit.Compiler.Security'] = {'ProtectorCookie':'true'}
    entries={}
    exec_loop(security_loop('parse_project_ini'), parser=cfg, entries=entries,
              PROJECT_WINDOWS_COMPILER_SECURITY_KEYS=KEYS,
              _parse_project_bool=parse_bool)
    assert entries[KEYS['pe32']][0]['protector_cookie'] is True
    assert entries[KEYS['pe64']][0]['protector_cookie'] is False


def test_project_lifecycle():
    owner=find_class('ExplorerWindow')
    collect=code(find_method('collect_project_entries',owner))
    assert 'panel.stack_cookie_options()' in collect
    assert 'PROJECT_WINDOWS_COMPILER_SECURITY_KEYS[target]' in collect
    open_project=SOURCE[SOURCE.index('            self.project_windows_compiler_security_options = {\n'):]
    assert '_debug_panel.set_stack_cookie_options(self.project_windows_compiler_security_options)' in open_project
    assert SOURCE.count('self.project_windows_compiler_security_options = stage531_default_compiler_security_options()') == 3
    assert SOURCE.count('                _panel.set_stack_cookie_options(self.project_windows_compiler_security_options)') == 2
    assert 'panel.set_stack_cookie_options(getattr(' in SOURCE
    assert 'self.project_settings_panel.set_stack_cookie_options(getattr(' in SOURCE


if __name__ == '__main__':
    tests=[test_ast_and_controls,test_tree_navigation,test_panel_independent_values,
           test_ini_both_targets_roundtrip,test_old_projects_default_disabled,
           test_project_lifecycle]
    for t in tests:
        t()
        print('PASS',t.__name__)
    print(f'Stage 531: {len(tests)} tests passed')
