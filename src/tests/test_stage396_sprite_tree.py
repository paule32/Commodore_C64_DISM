"""Stage 396: Sprite-Projektbaum, Persistenz und Wechsel vom Entwurf zum Dateiblatt.

Isolierte Tests: Qt5 wird für die strukturelle Prüfung nicht benötigt.
"""
import ast
import configparser
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

SRC = Path(__file__).with_name('d64_dism.py')
TREE = ast.parse(SRC.read_text('utf-8'))
KEY = '__c64_sprites__'
SECTION = 'Category.c64.sprites'


def method(name):
    matches = [n for n in ast.walk(TREE)
               if isinstance(n, ast.FunctionDef) and n.name == name]
    assert len(matches) == 1, (name, len(matches))
    return matches[0]


def execute_block(node, namespace):
    module = ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[]))
    exec(compile(module, str(SRC), 'exec'), namespace)


class Item:
    def __init__(self, parent=None, labels=()):
        self._parent = parent
        self._text = (labels[0] if labels else '')
        self._data = {}
        self.children = []
        if parent is not None:
            parent.children.append(self)

    def setData(self, col, role, value): self._data[(col, role)] = value
    def data(self, col, role): return self._data.get((col, role))
    def setText(self, col, value): self._text = value
    def text(self, col): return self._text
    def setToolTip(self, col, value): pass
    def setIcon(self, col, icon): pass
    def setExpanded(self, flag): pass
    def parent(self): return self._parent
    def childCount(self): return len(self.children)
    def child(self, index): return self.children[index]
    def indexOfChild(self, item): return self.children.index(item)
    def takeChild(self, index):
        item = self.children.pop(index)
        item._parent = None
        return item


class SpriteTreeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ns = {'Path': Path, 'Optional': __import__('typing').Optional,
              'QTreeWidgetItem': Item,
              'Qt': SimpleNamespace(UserRole=256),
              'PROJECT_C64_SPRITE_EXTENSIONS': ('.c64sprite', '.spr', '.sprite', '.bin', '.bmsprite', '.bmspr'),
              'C64BitmapSpriteEditorDialog': type('MockBitmapSpriteEditor', (), {}),
              'PROJECT_NODE_C64_SPRITE_FILE': 'c64_sprite_file',
              'QStyle': SimpleNamespace(SP_FileIcon=1),
              'QFileInfo': lambda path: str(path)}
        for name in ('_add_project_c64_sprite_entry', '_register_c64_sprite_editor_file',
                     '_cleanup_pending_sprite_leaves'):
            execute_block(method(name), ns)
        cls.Owner = type('Owner', (), {name: ns[name] for name in (
            '_add_project_c64_sprite_entry', '_register_c64_sprite_editor_file',
            '_cleanup_pending_sprite_leaves')})

    def owner(self):
        owner = self.Owner()
        owner.project_c64_sprites_root = Item()
        owner.style = lambda: SimpleNamespace(standardIcon=lambda *_: '')
        owner.icon_provider = SimpleNamespace(icon=lambda *_: '')
        owner.set_project_modified = lambda *_: None
        return owner

    def test_unsaved_sprite_leaf_becomes_saved_leaf(self):
        owner = self.owner()
        item = owner._add_project_c64_sprite_entry()
        self.assertEqual(item.text(0), 'Sprite_1.spr')
        self.assertEqual(item.data(0, 256 + 302), '')
        editor = SimpleNamespace(_c64_sprite_tree_item=item)
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / 'avatar.spr'
            owner._register_c64_sprite_editor_file(editor, dest)
            self.assertIs(editor._c64_sprite_tree_item, item)
            self.assertEqual(item.text(0), 'avatar.spr')
            self.assertEqual(item.data(0, 256 + 302), str(dest.resolve()))
            self.assertFalse(item.data(0, 256 + 312))

    def test_existing_files_unique_and_reject_wrong_extension(self):
        owner = self.owner()
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / 'hero.spr'
            item = owner._add_project_c64_sprite_entry(dest)
            self.assertIs(item, owner._add_project_c64_sprite_entry(dest))
            self.assertIsNone(owner._add_project_c64_sprite_entry(Path(tmp) / 'a.txt'))
            self.assertEqual(owner.project_c64_sprites_root.childCount(), 1)

    def test_conflict_merges_new_unsaved_leaf_into_existing(self):
        owner = self.owner()
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / 'existing.sprite'
            existing = owner._add_project_c64_sprite_entry(dest)
            pending = owner._add_project_c64_sprite_entry()
            editor = SimpleNamespace(_c64_sprite_tree_item=pending)
            owner._register_c64_sprite_editor_file(editor, dest)
            self.assertIs(editor._c64_sprite_tree_item, existing)
            self.assertEqual(owner.project_c64_sprites_root.childCount(), 1)

    def test_discard_removes_unsaved_only(self):
        owner = self.owner()
        with tempfile.TemporaryDirectory() as tmp:
            saved = owner._add_project_c64_sprite_entry(Path(tmp) / 'saved.spr')
            owner._add_project_c64_sprite_entry()
            owner._cleanup_pending_sprite_leaves()
            self.assertEqual(owner.project_c64_sprites_root.childCount(), 1)
            self.assertIs(owner.project_c64_sprites_root.child(0), saved)

    def test_ini_roundtrip_block_from_real_source(self):
        fmt = method('format_project_ini')
        parse = method('parse_project_ini')
        write_nodes = [node for node in fmt.body
                       if isinstance(node, (ast.Assign, ast.For))
                       and (SECTION in ast.unparse(node) or
                            'PROJECT_C64_SPRITES_' in ast.unparse(node))]
        # Counter assignment is part of the same block but doesn't mention the constant.
        idx = next(i for i,n in enumerate(fmt.body)
                   if 'parser[PROJECT_C64_SPRITES_SECTION]' in ast.unparse(n))
        block = fmt.body[idx:idx+3]
        self.assertIn('sprite_index', ast.unparse(block[1]))
        read_block = next(n for n in parse.body if isinstance(n, ast.If)
                          and 'parser.has_section(PROJECT_C64_SPRITES_SECTION)' in ast.unparse(n.test))
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / 'demo.pro'
            sprite = Path(tmp) / 'hero.spr'
            ent = {KEY: [{'title':'Hero', 'path':str(sprite)}, {'title':'new', 'path':''}]}
            cp = configparser.ConfigParser(interpolation=None)
            cp.optionxform = str
            namespace = dict(parser=cp, entries=ent, project_path=project,
                             PROJECT_C64_SPRITES_ENTRY_KEY=KEY,
                             PROJECT_C64_SPRITES_SECTION=SECTION,
                             PROJECT_C64_SPRITE_EXTENSIONS=('.c64sprite','.spr','.sprite','.bin'),
                             _project_storage_path=lambda x,y: str(Path(x).relative_to(y.parent)),
                             _project_loaded_path=lambda x,y: str((y.parent / x).resolve()),
                             json=json, Path=Path)
            for node in block:
                execute_block(node, namespace)
            self.assertEqual(len(cp.items(SECTION)), 2)  # Title + one saved sprite
            restored = dict(namespace)
            restored['entries'] = {KEY: []}
            execute_block(read_block, restored)
            self.assertEqual(restored['entries'][KEY], [{'title':'Hero', 'path':str(sprite)}])
            restored['parser'] = configparser.ConfigParser()
            restored['entries'] = {KEY: []}
            execute_block(read_block, restored)
            self.assertEqual(restored['entries'][KEY], [])

    def test_tree_wiring(self):
        src = SRC.read_text('utf-8')
        for token in ('"C= 64 Sprites"', '"Neues Sprite"',
                      '"Sprite-Dateien hinzufügen …"',
                      '"Sprite Editor", self.new_c64_sprite_project',
                      'PROJECT_NODE_C64_SPRITES_ROOT',
                      'PROJECT_NODE_C64_SPRITE_FILE'):
            self.assertIn(token, src)


if __name__ == '__main__':
    unittest.main()
