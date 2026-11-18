# -*- coding: utf-8 -*-
"""Qt-unabhängige Logiktests der Stage-614-dBASE-Modul-Erweiterung."""
from __future__ import annotations
import ast
import copy
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from project_named_targets import leaf_key as named_project_leaf_key

SOURCE_PATH = Path(__file__).with_name('d64_dism.py')
SOURCE = SOURCE_PATH.read_text(encoding='utf-8').replace(
    'lazy from app_lang.deu', 'from app_lang.deu').replace(
    'lazy from app_lang.enu', 'from app_lang.enu')
SOURCE_TREE = ast.parse(SOURCE)
FUNCS = {}
for node in ast.walk(SOURCE_TREE):
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        FUNCS.setdefault(node.name, node)


class Qt:
    UserRole = 1000


class QStyle:
    SP_FileIcon = 'file_icon'


class QFileInfo:
    def __init__(self, value): self.value = value


class FakeTreeItem:
    def __init__(self, parent=None, labels=None):
        self._parent = parent
        self._children = []
        if parent is not None: parent._children.append(self)
        self._text = (labels or [''])[0]
        self._data = {}
        self._tooltip = ''
        self._expanded = False
    def text(self, column): return self._text
    def setText(self, column, value): self._text = value
    def data(self, column, role): return self._data.get(role)
    def setData(self, column, role, value): self._data[role] = value
    def setToolTip(self, column, value): self._tooltip = value
    def setIcon(self, column, value): self.icon = value
    def setExpanded(self, value): self._expanded = value
    def parent(self): return self._parent
    def childCount(self): return len(self._children)
    def child(self, index): return self._children[index]
    def indexOfChild(self, item): return self._children.index(item)
    def takeChild(self, index):
        item = self._children.pop(index)
        item._parent = None
        return item


class FakeTree:
    def __init__(self): self.current = None
    def setCurrentItem(self, item): self.current = item
    def scrollToItem(self, item): pass


class FakeBar:
    def __init__(self): self.messages = []
    def showMessage(self, msg, *args): self.messages.append(msg)


class FakeEditorDoc:
    def isModified(self): return False


class FakeEditor:
    def document(self): return FakeEditorDoc()


class FakeDocument:
    def __init__(self, filename):
        self.custom_display_name = filename
        self.path = None
        self.content = 'WRITE "Hallo"\n'
        self.raw_editor = FakeEditor()
        self.binary_disassembly_mode = False
        self.is_prolog_document = False
        self.is_modified = False
        self.is_build_document = True
        self._dbase_module_needs_save_as = False
    @property
    def display_name(self):
        return self.custom_display_name or (self.path.name if self.path else 'Unbenannt')
    def set_build_target(self, value): self.build_target = value
    def update_syntax_highlighting(self): pass
    def mark_saved(self): self.saved = True
    def data_for_saving(self, suffix): return self.content.encode('utf-8')
    def source_language(self): return self.language_override
    def invalidate_assembly_result(self, text): pass
    def focus_preferred_editor(self): pass


def extract_class(*names):
    node = ast.ClassDef(name='Logic', bases=[], keywords=[], body=[
        copy.deepcopy(FUNCS[name]) for name in names
    ], decorator_list=[])
    mod = ast.Module(body=[node], type_ignores=[])
    ast.fix_missing_locations(mod)
    env = {'Qt': Qt, 'QTreeWidgetItem': FakeTreeItem, 'QStyle': QStyle,
           'QFileInfo': QFileInfo, 'Path': Path, 'DocumentEditor': FakeDocument,
           'QMessageBox': type('Msg', (), {'Save': 0x10, 'Cancel': 0x20,
                                         'Question': 0x30}),
           'PROJECT_NODE_DBASE_FILE': 'dbase_file',
           'named_project_leaf_key': named_project_leaf_key}
    exec(compile(mod, '<stage614-methods>', 'exec'), env)
    return env['Logic']


Logic = extract_class(
    '_new_unsaved_dbase_module', '_is_unsaved_dbase_module_leaf',
    '_activate_unsaved_dbase_module_leaf',
    '_project_named_leaf_key', '_project_named_is_file_leaf',
    '_save_document', '_confirm_pending_dbase_module_before_other_action',
)


class FakeHost(Logic):
    def __init__(self, directory):
        self.directory = Path(directory)
        self.current_directory = self.directory
        self.current_project_path = None
        self.project_tree = FakeTree()
        self.group = FakeTreeItem(labels=['Module'])
        self.project_dbase_group_nodes = {'modules': self.group}
        self._status = FakeBar()
        self._documents = []
        self._named_project_assignments = {}
        self.logs = []
        self.errors = []
        self.project_saves = 0
        self.chosen_path = None
        self.document_tabs = type('Tabs', (), {
            'count': lambda slf: len(self._documents),
            'widget': lambda slf, index: self._documents[index],
            'setCurrentWidget': lambda slf, document: None})()
        self.icon_provider = type('Provider', (), {'icon': lambda slf, info: 'icon'})()
        self._current = None
    def _ensure_project_for_new_document(self): pass
    def _project_new_file_directory(self): return self.directory
    def _project_existing_names(self): return []
    def _confirm_pending_dbase_module_before_other_action(self, next_item=None): return True
    def new_document(self, *, text, display_name):
        doc = FakeDocument(display_name)
        self._documents.append(doc)
        self._current = doc
        return doc
    def current_document(self): return self._current
    def style(self): return type('Style', (), {'standardIcon': lambda slf, name: 'file'})()
    def _project_named_assign_new_leaf(self, item): pass
    def _project_named_schedule_refresh(self): self.refreshed = True
    def set_project_modified(self, value): self.project_modified = value
    def _update_document_tab(self, doc): pass
    def _project_activate_document_tab(self, doc): self._current = doc
    def statusBar(self): return self._status
    def log(self, msg): self.logs.append(msg)
    def show_error(self, title, message): self.errors.append((title, message))
    def _choose_document_filename(self, doc): return self.chosen_path
    def _find_open_document(self, target): return None
    def _write_editor_bytes_verified(self, target, data): target.write_bytes(data)
    def _apply_document_theme(self, doc): pass
    def _update_editor_status_panels(self): pass
    def _refresh_favorites_menu(self): pass
    def populate_file_list(self): pass
    def _remember_recent_file(self, path): pass
    def _sync_document_marker_to_project(self, doc, kind, *, persist): return False
    def _project_item_kind(self, item): return str(item.data(0, Qt.UserRole+303) or '')
    def save_project(self): self.project_saves += 1


class Stage614Tests(unittest.TestCase):
    def test_module_is_unsaved_and_uses_dbase_editor(self):
        with TemporaryDirectory() as folder:
            host = FakeHost(folder)
            doc = host._new_unsaved_dbase_module()
            self.assertEqual(doc.display_name, 'unbenannt.prg')
            self.assertIsNone(doc.path)
            self.assertTrue(doc._dbase_module_needs_save_as)
            self.assertEqual(doc.language_override, 'dbase')
            self.assertEqual(doc.build_target, 'pe32')
            self.assertTrue(host._is_unsaved_dbase_module_leaf(host.group.child(0)))
            self.assertEqual(host.group.child(0).text(0), 'unbenannt.prg')
            self.assertEqual(list(Path(folder).glob('*.prg')), [])
            self.assertTrue(any('Speichern unter' in message for message in host.logs))

    def test_name_collision_creates_unique_pending_name(self):
        with TemporaryDirectory() as folder:
            host = FakeHost(folder)
            first = host._new_unsaved_dbase_module()
            second = host._new_unsaved_dbase_module()
            self.assertEqual(first.display_name, 'unbenannt.prg')
            self.assertEqual(second.display_name, 'unbenannt_1.prg')
            self.assertEqual(host.group.childCount(), 2)

    def test_existing_file_is_never_used_for_new_name(self):
        with TemporaryDirectory() as folder:
            (Path(folder) / 'unbenannt.prg').write_bytes(b'Original')
            host = FakeHost(folder)
            doc = host._new_unsaved_dbase_module()
            self.assertEqual(doc.display_name, 'unbenannt_1.prg')

    def test_unsaved_leaf_has_named_combo_eligibility(self):
        with TemporaryDirectory() as folder:
            host = FakeHost(folder)
            host._new_unsaved_dbase_module()
            item = host.group.child(0)
            self.assertTrue(host._project_named_is_file_leaf(item))
            self.assertTrue(host._project_named_leaf_key(item).startswith('@unsaved:dbase:'))

    def test_first_save_updates_leaf_and_transfers_assignment(self):
        with TemporaryDirectory() as folder:
            host = FakeHost(folder)
            doc = host._new_unsaved_dbase_module()
            item = host.group.child(0)
            old_key = host._project_named_leaf_key(item)
            host._named_project_assignments[old_key] = 'dbase|program'
            host.chosen_path = Path(folder) / 'meine_datei.prg'
            self.assertTrue(host._save_document(doc, save_as=True))
            self.assertEqual(host.chosen_path.read_text(encoding='utf-8'), doc.content)
            self.assertEqual(doc.path, host.chosen_path)
            self.assertFalse(doc._dbase_module_needs_save_as)
            self.assertEqual(item.text(0), 'meine_datei.prg')
            self.assertEqual(item.data(0, Qt.UserRole + 302), str(host.chosen_path))
            self.assertFalse(host._is_unsaved_dbase_module_leaf(item))
            self.assertEqual(host._named_project_assignments[host._project_named_leaf_key(item)], 'dbase|program')
            self.assertNotIn(old_key, host._named_project_assignments)

    def test_first_save_never_overwrites_existing_file(self):
        with TemporaryDirectory() as folder:
            host = FakeHost(folder)
            doc = host._new_unsaved_dbase_module()
            host.chosen_path = Path(folder) / 'existing.prg'
            host.chosen_path.write_text('SAFE', encoding='utf-8')
            self.assertFalse(host._save_document(doc, save_as=True))
            self.assertEqual(host.chosen_path.read_text(encoding='utf-8'), 'SAFE')
            self.assertIsNone(doc.path)
            self.assertTrue(doc._dbase_module_needs_save_as)

    def test_cancel_save_keeps_unsaved_flag(self):
        with TemporaryDirectory() as folder:
            host = FakeHost(folder)
            doc = host._new_unsaved_dbase_module()
            host.chosen_path = None
            self.assertFalse(host._save_document(doc, save_as=True))
            self.assertTrue(doc._dbase_module_needs_save_as)
            self.assertEqual(host.group.childCount(), 1)

    def test_context_menus_have_module_action_first(self):
        for name in ('_show_project_dbase_root_menu',
                     '_show_project_dbase_group_menu',
                     '_show_project_dbase_file_menu'):
            function = FUNCS[name]
            calls = [n for n in ast.walk(function)
                     if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                     and n.func.attr == 'addAction' and n.args]
            self.assertTrue(any(isinstance(call.args[0], ast.Constant)
                                and call.args[0].value == 'Neu:  Module'
                                for call in calls), name)


if __name__ == '__main__': unittest.main()
