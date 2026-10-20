"""Stage 399: Kontextmenue BASIC -> Commodore C= 64.

Isolierte Regressionstests fuer den Originalcode, ohne PyQt5-Abhaengigkeit.
"""
import ast
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from typing import Optional

SOURCE = Path(__file__).with_name('d64_dism.py')
TEXT = SOURCE.read_text(encoding='utf-8')
TREE = ast.parse(TEXT)


def method(name):
    matches = [node for node in ast.walk(TREE)
               if isinstance(node, ast.FunctionDef) and node.name == name]
    assert len(matches) == 1, (name, len(matches))
    return matches[0]


def load(name, **env):
    scope = {'QTreeWidgetItem': Item}
    scope.update(env)
    module = ast.fix_missing_locations(ast.Module(body=[method(name)], type_ignores=[]))
    exec(compile(module, str(SOURCE), 'exec'), scope)
    return scope[name]


class Item:
    def __init__(self, parent=None, titles=()):
        self.parent_item = parent
        self.title = titles[0] if titles else ''
        self.values = {}
        self.children = []
        if parent is not None:
            parent.children.append(self)
    def setData(self, col, role, value): self.values[role] = value
    def data(self, col, role): return self.values.get(role)
    def setToolTip(self, col, value): pass
    def setIcon(self, col, value): pass
    def setExpanded(self, value): pass
    def parent(self): return self.parent_item
    def childCount(self): return len(self.children)
    def child(self, i): return self.children[i]
    def text(self, col): return self.title
    def isExpanded(self): return True


class Menu:
    requested_label = None
    history = []
    def __init__(self, parent): self.actions=[]
    def addAction(self, text):
        action = SimpleNamespace(label=text)
        self.actions.append(action)
        return action
    def exec_(self, position):
        self.__class__.history = [a.label for a in self.actions]
        return next((a for a in self.actions if a.label == self.requested_label), None)


class Document:
    def __init__(self, text, display_name):
        self.path = None
        self.display_name = display_name
        self.text = text
        self.raw_editor = SimpleNamespace(
            set_basic_editor_mode=lambda enabled, initial_source=None: None)
        self.saved = False
    def set_build_target(self, value): self.build_target = value
    def update_syntax_highlighting(self): pass
    def mark_saved(self): self.saved = True
    def _apply_source_editor_font(self): pass
    def focus_preferred_editor(self): pass


class TestContext(unittest.TestCase):
    def test_first_context_action_launches_correct_existing_creator(self):
        root = Item(titles=['Commodore C= 64'])
        root.setData(0, 1305, 'basic')
        fake = SimpleNamespace(UserRole=1000)
        func = load('_show_project_c64_menu',
                    Qt=fake, QMenu=Menu,
                    PROJECT_NODE_C64_TARGET='c64_target',
                    PROJECT_NODE_C64_RESOURCE_ROOT='c64_resource_root',
                    PROJECT_NODE_C64_RESOURCE_FILE='c64_resource_file',
                    PROJECT_NODE_C64_SOURCE_FILE='c64_source_file')
        called = []
        class Owner:
            project_tree = SimpleNamespace(viewport=lambda: SimpleNamespace(
                mapToGlobal=lambda p: p))
            def _project_item_kind(self, item): return 'c64_target'
            def _new_unsaved_c64_source_document(self, *a, **kw): called.append((a,kw))
            def add_project_entries(self, item): called.append(('add',item))
            def add_project_c64_files(self, key): called.append(('other',key))
        Menu.requested_label = 'Neues BASIC Programm'
        func(Owner(), root, (0,0))
        self.assertEqual(Menu.history[0], 'Neues BASIC Programm')
        self.assertEqual(Menu.history[1], 'C64 BASIC-Programm hinzufügen …')
        self.assertEqual(called, [(('basic',), {'use_template': True, 'under_c64_target': True})])

    def test_old_assembler_menu_unchanged(self):
        root = Item(titles=['Commodore C= 64'])
        root.setData(0, 1305, 'assembler')
        called=[]
        func = load('_show_project_c64_menu',
                    Qt=SimpleNamespace(UserRole=1000), QMenu=Menu,
                    PROJECT_NODE_C64_TARGET='c64_target',
                    PROJECT_NODE_C64_RESOURCE_ROOT='c64_resource_root',
                    PROJECT_NODE_C64_RESOURCE_FILE='c64_resource_file',
                    PROJECT_NODE_C64_SOURCE_FILE='c64_source_file')
        class Owner:
            project_tree = SimpleNamespace(viewport=lambda: SimpleNamespace(mapToGlobal=lambda p:p))
            def _project_item_kind(self, item): return 'c64_target'
            def add_project_c64_files(self, lang): called.append(lang)
        Menu.requested_label = 'C64-Quellprogramm hinzufügen …'
        func(Owner(), root, (0,0))
        self.assertEqual(Menu.history[0], 'C64-Quellprogramm hinzufügen …')
        self.assertNotIn('Neues BASIC Programm', Menu.history)
        self.assertEqual(called, ['assembler'])

    def test_new_basic_is_leaf_of_c64_target_and_remains_unsaved(self):
        func=load('_new_unsaved_c64_source_document',
                  Optional=Optional, DocumentEditor=Document,
                  Path=Path, QTreeWidgetItem=Item,
                  Qt=SimpleNamespace(UserRole=1000),
                  PROJECT_NODE_C64_SOURCE_FILE='c64_source_file')
        with tempfile.TemporaryDirectory() as tmp:
            basic_root=Item(titles=['BASIC - Programme'])
            c64_root=Item(basic_root, ['Commodore C= 64'])
            class Owner:
                project_root_items={'basic':basic_root}
                project_c64_target_nodes={'basic':c64_root}
                project_tree=SimpleNamespace(setCurrentItem=lambda v:None)
                def _ensure_project_for_new_document(self): pass
                def _project_existing_names(self): return []
                def _project_new_file_directory(self): return Path(tmp)
                def new_document(self, *,text, display_name):
                    self.document=Document(text,display_name)
                    return self.document
                def set_project_modified(self, state): pass
                def _update_document_tab(self, doc): pass
                def statusBar(self): return SimpleNamespace(showMessage=lambda *a:None)
                def show_error(self, *a): raise AssertionError(a)
            win=Owner()
            doc=func(win,'basic',under_c64_target=True)
            self.assertIs(doc._c64_project_tree_item.parent(), c64_root)
            self.assertEqual(doc._c64_project_tree_item.data(0,1303), 'c64_source_file')
            self.assertTrue(doc._c64_project_tree_item.data(0,1307))
            self.assertTrue(doc._is_new_c64_project_file)
            self.assertIsNone(doc.path)
            self.assertIn('PRINT "HALLO C64"',doc.text)
            self.assertEqual(list(Path(tmp).iterdir()),[])
            # Bestehender Datei->Neu-Weg bleibt unter BASIC - Programme.
            another=func(win,'basic')
            self.assertIs(another._c64_project_tree_item.parent(),basic_root)

    def test_saved_c64_basic_leaf_is_restored_as_c64_source(self):
        func=load('_add_project_entry',
                  Optional=Optional, Path=Path, QTreeWidgetItem=Item,
                  Qt=SimpleNamespace(UserRole=1000),
                  QFileInfo=lambda x:x,
                  PROJECT_NODE_C64_SOURCE_FILE='c64_source_file')
        with tempfile.TemporaryDirectory() as tmp:
            c64_root=Item(titles=['Commodore C= 64'])
            basic_root=Item(titles=['BASIC - Programme'])
            class Owner:
                project_root_items={'c64':c64_root,'basic':basic_root}
                icon_provider=SimpleNamespace(icon=lambda x:x)
                project_tree=SimpleNamespace(setCurrentItem=lambda x:None)
                def set_project_modified(self, flag): pass
            owner=Owner()
            for name in ('demo.bas','demo2.basic'):
                item=func(owner,'c64',Path(tmp)/name)
                self.assertIs(item.parent(),c64_root)
                self.assertEqual(item.data(0,1303),'c64_source_file')
                self.assertEqual(item.data(0,1305),'c64')
            classic=func(owner,'c64',Path(tmp)/'classic.prg')
            self.assertIsNone(classic.data(0,1303))
            self.assertEqual(c64_root.childCount(),3)

    def test_c64_category_persists_nested_basic_leaf(self):
        body = method('collect_project_entries')
        src = ast.unparse(body)
        self.assertIn('for key, _title, _extensions in PROJECT_CATEGORIES:',src)
        self.assertIn('entries[key].append',src)
        self.assertIn('path_value = str(child.data(0, Qt.UserRole + 302)',src)
        self.assertIn('if path_value:',src)


if __name__=='__main__':
    unittest.main()
