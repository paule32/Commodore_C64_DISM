"""Stage 528 TreeList regression tests, adjusted for Stage 529 tab removal."""
from __future__ import annotations
import ast
import re
from pathlib import Path

from debug_options import DebugOptions

SOURCE = (Path(__file__).parent / 'd64_dism.py').read_text('utf-8')
AST = ast.parse(re.sub(r'(?m)^(\s*)lazy (from|import) ', r'\1\2 ', SOURCE))


def get_class(name):
    matches = [n for n in ast.walk(AST) if isinstance(n, ast.ClassDef) and n.name == name]
    assert len(matches) == 1, f'Expected one class {name}, got {len(matches)}'
    return matches[0]


def get_method(cls, name):
    matches = [n for n in cls.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == name]
    assert len(matches) == 1, (cls.name, name, len(matches))
    return matches[0]


def test_windows_debug_treelist_structure():
    cls = get_class('WindowsCompilerDirectorySettingsPage')
    ctor = ast.get_source_segment(SOURCE, get_method(cls, '__init__'))
    tree_change = ast.get_source_segment(SOURCE, get_method(cls, '_tree_changed'))
    assert '"Linker", "Debug"' in ctor, 'Missing Debug root alongside compiler/linker tree roots'
    assert 'self.debug_page = DebugSettingsPage(' in ctor
    assert 'self.stack.addWidget(self.debug_page)' in ctor
    assert 'elif key == "debug":' in tree_change
    assert 'page = self.debug_page' in tree_change


def test_options_independent_without_qt():
    """Stage 530 changes the former shared state into distinct ABI settings."""
    from test_stage530 import test_independent_pages_no_sync
    test_independent_pages_no_sync()


if __name__ == '__main__':
    test_windows_debug_treelist_structure()
    test_options_independent_without_qt()
    print('Stage 528 TreeList regression tests adapted to Stage 530: 2')
