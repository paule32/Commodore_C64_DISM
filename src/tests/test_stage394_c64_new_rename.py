"""Stage 394: isolated regression tests; PyQt5 not required."""
import ast
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from typing import Optional
from unittest.mock import patch

BASE = Path(__file__).resolve().parent
SOURCE = BASE / 'd64_dism.py'
TEXT = SOURCE.read_text(encoding='utf-8')
TREE = ast.parse(TEXT)


def source(name):
    for node in ast.walk(TREE):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return ast.get_source_segment(TEXT, node)
    raise KeyError(name)


def isolated(name, env):
    for node in ast.walk(TREE):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            local = dict(env)
            local.update({'Optional': Optional,
                          'DocumentEditor': local.get('DocumentEditor', FakeDocument),
                          'QTreeWidgetItem': local.get('QTreeWidgetItem', FakeItem)})
            exec(compile(ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[])), str(SOURCE), 'exec'), local)
            return local[name]
    raise KeyError(name)


class FakeItem:
    def __init__(self, parent=None, titles=()):
        self._parent = parent
        self.title = list(titles)[0] if titles else ''
        self.values = {}
        self.children = []
        if parent:
            parent.children.append(self)
    def setData(self, col, role, val): self.values[role] = val
    def data(self, col, role): return self.values.get(role)
    def setText(self, col, text): self.title = text
    def text(self, col): return self.title
    def setIcon(self, col, icon): self.icon = icon
    def setToolTip(self, col, text): self.tooltip = text
    def setExpanded(self, value): self.expanded = value
    def parent(self): return self._parent
    def indexOfChild(self, child): return self.children.index(child)
    def takeChild(self, index): return self.children.pop(index)

class FakeEditor:
    def __init__(self): self.basic = False; self.content = None
    def set_basic_editor_mode(self, value, *, initial_source=None):
        self.basic = value; self.content = initial_source

class FakeDocument:
    def __init__(self, title):
        self.path = None
        self.custom_display_name = title
        self.raw_editor = FakeEditor()
        self.target = None
        self.saved = False
    def set_build_target(self, value): self.target = value
    def update_syntax_highlighting(self): pass
    def mark_saved(self): self.saved = True
    def focus_preferred_editor(self): pass
    def _apply_source_editor_font(self): pass

class FakeStatus:
    def showMessage(self, *args): pass


class Tests(unittest.TestCase):
    def test_new_c64_templates_are_not_created_on_disk(self):
        with TemporaryDirectory() as folder:
            root_basic, root_asm = FakeItem(), FakeItem()
            class FakeWindow:
                current_project_path = None
                def __init__(self):
                    self.project_root_items = {'basic': root_basic}
                    self.project_c64_target_nodes = {'assembler': root_asm}
                    self.project_tree = SimpleNamespace(setCurrentItem=lambda item: None)
                def _ensure_project_for_new_document(self): pass
                def _project_existing_names(self): return []
                def _project_new_file_directory(self): return Path(folder)
                def new_document(self, *, text, display_name):
                    self.document = FakeDocument(display_name)
                    self.document.initial = text
                    return self.document
                def set_project_modified(self, flag): pass
                def _update_document_tab(self, doc): pass
                def statusBar(self): return FakeStatus()
                def show_error(self, *args): raise AssertionError(args)
            env = {
                'DocumentEditor': FakeDocument,
                'QTreeWidgetItem': FakeItem,
                'Qt': SimpleNamespace(UserRole=1000),
                'PROJECT_NODE_C64_SOURCE_FILE': 'c64_source_file',
                'Optional': object,
            }
            func = isolated('_new_unsaved_c64_source_document', env)
            win = FakeWindow()
            basic = func(win, 'basic', use_template=True)
            self.assertTrue(basic.raw_editor.basic)
            self.assertIn('PRINT "HALLO C64"', basic.raw_editor.content)
            self.assertEqual(basic.target, 'c64')
            self.assertEqual(basic._c64_project_tree_item.parent(), root_basic)
            self.assertIsNone(basic.path)
            self.assertTrue(basic._c64_project_tree_item.data(0, 1307))
            asm = func(win, 'assembler', use_template=True)
            self.assertIn('.org $080D', asm.initial)
            self.assertFalse(asm.raw_editor.basic)
            self.assertEqual(asm._c64_project_tree_item.parent(), root_asm)
            self.assertTrue(asm._c64_project_tree_item.data(0, 1307))
            self.assertEqual(list(Path(folder).iterdir()), [])

    def test_c64_first_save_dialog_suffix(self):
        class FakeChoose:
            @staticmethod
            def getSaveFileName(_parent, title, initial, filters):
                assert 'erstmals speichern' in title
                assert 'C64 BASIC' in filters
                return str(Path(tmp) / 'my_program'), filters
        env = {'Path': Path, 'Optional': object, 'QFileDialog': FakeChoose}
        with TemporaryDirectory() as tmp:
            func = isolated('_choose_document_filename', env)
            class FakeWindow:
                current_directory = Path(tmp)
                def _project_new_file_directory(self): return Path(tmp)
                def show_error(self,*args): raise AssertionError(args)
            doc = SimpleNamespace(
                path=None, display_name='Unbenannt_1.bas',
                binary_disassembly_mode=False, raw_editor=None,
                _is_new_c64_project_file=True,
            )
            path = func(FakeWindow(), doc)
            self.assertEqual(path.name, 'my_program.bas')
            self.assertEqual(path.parent, Path(tmp))

    def test_rename_physical_file_and_open_editor(self):
        with TemporaryDirectory() as folder:
            directory = Path(folder)
            old = directory/'test.asm'
            old.write_text('start:\n    rts\n', encoding='utf-8')
            item = FakeItem(None, ['test.asm'])
            item.setData(0, 1302, str(old))
            item.setData(0, 1301, 'assembler')
            document = SimpleNamespace(
                path=old, custom_display_name='test.asm',
                update_syntax_highlighting=lambda: None,
                invalidate_assembly_result=lambda msg: None,
            )
            class FakeWindow:
                current_project_path = None
                current_directory = Path('/some/other/directory')
                def __init__(self): self.errors=[]; self.replaced=[]
                def show_error(self, *x): self.errors.append(x)
                def _find_open_document(self, path): return document if path == old else None
                def _replace_project_path_reference(self, before, after):
                    self.replaced.append((before,after))
                    item.setData(0, 1302, str(after))
                def _update_document_tab(self, doc): pass
                def set_project_modified(self, value): pass
                def statusBar(self): return FakeStatus()
                def log(self, value): pass
                icon_provider = SimpleNamespace(icon=lambda x: 'icon')
            env = {'Path': Path,'Qt': SimpleNamespace(UserRole=1000),
                   'os': os,'QFileInfo': lambda p: p,
                   'PROJECT_C64_SOURCE_EXTENSIONS': {'assembler': ('.asm','.s','.a65','.inc')}}
            func = isolated('_commit_c64_program_rename', env)
            win = FakeWindow()
            self.assertTrue(func(win, item, 'renamed'))
            renamed = directory/'renamed.asm'
            self.assertTrue(renamed.is_file())
            self.assertFalse(old.exists())
            self.assertEqual(document.path, renamed)
            self.assertEqual(item.title, 'renamed.asm')
            self.assertEqual(item.data(0,1302), str(renamed))
            self.assertEqual(win.errors, [])

    def test_collision_does_not_change_anything(self):
        with TemporaryDirectory() as folder:
            old = Path(folder)/'before.bas'; old.write_text('10 END')
            (Path(folder)/'after.bas').write_text('keep')
            item = FakeItem(None, ['before.bas'])
            item.setData(0,1302,str(old)); item.setData(0,1301,'basic')
            class FakeWin:
                def __init__(self): self.errors=[]
                def show_error(self,*args): self.errors.append(args)
            env = {'Path': Path,'Qt': SimpleNamespace(UserRole=1000),
                   'os': os,'PROJECT_C64_SOURCE_EXTENSIONS': {'assembler':('.asm',)}}
            func = isolated('_commit_c64_program_rename',env)
            win=FakeWin()
            self.assertFalse(func(win,item,'after.bas'))
            self.assertTrue(old.exists())
            self.assertEqual((Path(folder)/'after.bas').read_text(),'keep')
            self.assertEqual(item.title,'before.bas')
            self.assertTrue(win.errors)

    def test_write_protection_error(self):
        with TemporaryDirectory() as folder:
            old = Path(folder)/'before.asm'; old.write_text('rts')
            item = FakeItem(None, ['before.asm'])
            item.setData(0,1302,str(old)); item.setData(0,1301,'assembler')
            class FakeWin:
                def __init__(self): self.errors=[]
                def show_error(self,*args): self.errors.append(args)
            env = {'Path': Path,'Qt': SimpleNamespace(UserRole=1000),
                   'os': os,'PROJECT_C64_SOURCE_EXTENSIONS': {'assembler':('.asm',)}}
            func = isolated('_commit_c64_program_rename',env)
            win=FakeWin()
            with patch('os.access', return_value=False):
                self.assertFalse(func(win,item,'new.asm'))
            self.assertTrue(old.exists())
            self.assertFalse((Path(folder)/'new.asm').exists())
            self.assertTrue(win.errors)

    def test_integration_guards_and_menus(self):
        self.assertIn('self._new_unsaved_c64_source_document(key, use_template=use_template)',source('new_source_document'))
        self.assertIn('document._is_new_c64_project_file = False',source('_save_document'))
        self.assertIn('Qt.UserRole + 307, False',source('_save_document'))
        self.assertIn('target.exists()',source('_save_document'))
        self.assertIn('"Umbenennen"',source('_show_project_c64_menu'))
        self.assertIn('"Umbenennen"',source('_show_project_source_menu'))
        self.assertIn('self._activate_unsaved_c64_leaf(item)',source('open_project_item'))
        self.assertIn('dark_mode=dark',source('_begin_dbase_program_rename'))
        self.assertIn('and not getattr(document, "_is_new_c64_project_file", False)',source('_confirm_close_document'))
        self.assertNotIn('self.views.setCurrentIndex(index)',source('show_assembled_hex_bytes'))

if __name__=='__main__': unittest.main()
