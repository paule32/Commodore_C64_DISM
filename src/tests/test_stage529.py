"""Stage 529: only Windows TreeList Debug entries, no top-level Debug tab."""
from __future__ import annotations
import ast
import re
from pathlib import Path

SOURCE = (Path(__file__).parent / 'd64_dism.py').read_text(encoding='utf-8')
TREE = ast.parse(re.sub(r'(?m)^(\s*)lazy (from|import) ', r'\1\2 ', SOURCE))

def cls(name):
    matches = [n for n in ast.walk(TREE) if isinstance(n, ast.ClassDef) and n.name == name]
    assert len(matches) == 1
    return matches[0]

def method(c, name):
    result = [n for n in c.body if isinstance(n, ast.FunctionDef) and n.name == name]
    assert len(result) == 1
    return result[0]

def test_no_debug_main_tab():
    panel = cls('ProjectSettingsPanel')
    ctor = ast.get_source_segment(SOURCE, method(panel, '__init__'))
    assert 'self.tabs.addTab(self.windows_tab, "Windows")' in ctor
    assert 'self.tabs.addTab(self.amiga_tab, "AMIGA")' in ctor
    assert 'self.tabs.addTab(self.c64_tab, "C= 64")' in ctor
    assert 'self.tabs.addTab(self.debug_tab, "Debug")' not in ctor
    assert 'self.debug_tab' not in SOURCE
    assert ctor.count('self.windows_pe32_page.debug_page,') == 1
    assert ctor.count('self.windows_pe64_page.debug_page,') == 1
    assert '_debug_pages = {' in ctor

def test_tree_entries_and_independence():
    c = cls('WindowsCompilerDirectorySettingsPage')
    ctor = ast.get_source_segment(SOURCE, method(c, '__init__'))
    on_tree = ast.get_source_segment(SOURCE, method(c, '_tree_changed'))
    assert '("Umgebung", "Compiler", "Assembler", "Linker", "Debug")' in ctor
    assert 'self.stack.addWidget(self.debug_page)' in ctor
    assert 'elif key == "debug":' in on_tree
    assert 'page = self.debug_page' in on_tree
    panel = cls('ProjectSettingsPanel')
    opt = ast.get_source_segment(SOURCE, method(panel, 'debug_options'))
    assert 'self._debug_pages[self._target_key(target)].options()' in opt
    sync = ast.get_source_segment(SOURCE, method(panel, '_debug_options_changed'))
    assert 'stage527_set_debug_options(options, target=target)' in sync
    assert 'for page in self._debug_pages:' not in sync
    assert 'self.windows_pe32_page.debug_page' in sync

if __name__ == '__main__':
    test_no_debug_main_tab()
    test_tree_entries_and_independence()
    print('Stage 529 TreeList tests adapted to Stage 530: 2')
