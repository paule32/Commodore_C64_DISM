# -*- coding: utf-8 -*-
"""Stage 613: isolierte Tests des QFileDialog-Inline-Delegates ohne Qt-Runtime.

Der Qt-Integrationstest muss zusaetzlich auf Windows mit PyQt5 erfolgen.
"""
from __future__ import annotations

import ast
from pathlib import Path
import re
import unittest

SOURCE = Path(__file__).with_name('d64_dism.py')


class FakeRect:
    def __init__(self, x=12, y=18, width=90, height=24):
        self._x, self._y, self._w, self._h = x, y, width, height

    def x(self): return self._x
    def width(self): return self._w
    def setWidth(self, value): self._w = value
    def snapshot(self): return (self._x, self._y, self._w, self._h)


class FakeViewport:
    def __init__(self, width): self._width = width
    def width(self): return self._width


class FakeTreeView:
    def __init__(self, width=480): self._viewport = FakeViewport(width)
    def viewport(self): return self._viewport


class FakeListView:
    def __init__(self, width=480): self._viewport = FakeViewport(width)
    def viewport(self): return self._viewport


class FakeEditor:
    def __init__(self, rect=None):
        self.rect = rect or FakeRect()
        self.frame = True
        self.object_name = ''
        self.contents_margins = None
        self.text_margins = None
        self.style = ''
        self.geometry_updates = 0

    def setObjectName(self, value): self.object_name = value
    def setFrame(self, value): self.frame = value
    def setContentsMargins(self, *values): self.contents_margins = values
    def setTextMargins(self, *values): self.text_margins = values
    def setStyleSheet(self, value): self.style = value
    def geometry(self): return self.rect
    def setGeometry(self, rect):
        self.rect = rect
        self.geometry_updates += 1


class FakeDelegate:
    def __init__(self, parent): self._parent = parent
    def parent(self): return self._parent
    def createEditor(self, parent, option, index): return parent
    def updateEditorGeometry(self, editor, option, index): pass


def load_delegate():
    # Das Gesamtmodul verwendet Python-3.15-lazy-imports und kann im
    # Testcontainer ohne PyQt5 nicht direkt importiert werden.
    source = SOURCE.read_text(encoding='utf-8')
    source = re.sub(r'(?m)^lazy (?=(?:import|from) )', '', source)
    tree = ast.parse(source, filename=str(SOURCE))
    node = next(n for n in ast.walk(tree)
                if isinstance(n, ast.ClassDef)
                and n.name == 'DBaseProjectFileNameEditDelegate')
    module = ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[]))
    namespace = dict(QStyledItemDelegate=FakeDelegate,
                     QLineEdit=FakeEditor, QTreeView=FakeTreeView,
                     QListView=FakeListView)
    exec(compile(module, '<stage613-delegate>', 'exec'), namespace)
    return namespace['DBaseProjectFileNameEditDelegate'], tree, source


class Stage613InlineEditorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.Delegate, cls.tree, cls.source = load_delegate()

    def test_tree_editor_has_zero_margins_and_no_frame(self):
        editor = self.Delegate(FakeTreeView()).createEditor(FakeEditor(), None, None)
        self.assertFalse(editor.frame)
        self.assertEqual(editor.contents_margins, (0, 0, 0, 0))
        self.assertEqual(editor.text_margins, (0, 0, 0, 0))
        self.assertIn('margin:0px', editor.style)
        self.assertIn('padding:0px', editor.style)
        self.assertIn('border:0px', editor.style)

    def test_edit_field_expands_to_visible_viewport_right_edge(self):
        editor = FakeEditor(FakeRect(x=74, y=23, width=95, height=20))
        delegate = self.Delegate(FakeTreeView(width=520))
        delegate.updateEditorGeometry(editor, None, None)
        self.assertEqual(editor.rect.snapshot(), (74, 23, 446, 20))
        self.assertEqual(editor.geometry_updates, 1)

    def test_wide_tree_editor_is_not_shrunk(self):
        editor = FakeEditor(FakeRect(x=40, width=400))
        self.Delegate(FakeTreeView(width=330)).updateEditorGeometry(editor, None, None)
        self.assertEqual(editor.rect.width(), 400)
        self.assertEqual(editor.geometry_updates, 0)

    def test_list_view_does_not_expand_over_icon_grid(self):
        editor = FakeEditor(FakeRect(x=20, width=86))
        self.Delegate(FakeListView(width=600)).updateEditorGeometry(editor, None, None)
        self.assertEqual(editor.rect.width(), 86)
        self.assertEqual(editor.geometry_updates, 0)

    def test_non_text_editor_unaffected(self):
        editor = object()
        self.assertIs(self.Delegate(FakeTreeView()).createEditor(editor, None, None), editor)
        self.Delegate(FakeTreeView()).updateEditorGeometry(editor, None, None)

    def test_delegate_registered_only_for_filename_views(self):
        dialog = next(n for n in ast.walk(self.tree)
                      if isinstance(n, ast.ClassDef)
                      and n.name == 'DBaseProjectOpenFileDialog')
        initializer = next(n for n in dialog.body
                           if isinstance(n, ast.FunctionDef) and n.name == '__init__')
        snippet = ast.get_source_segment(self.source, initializer)
        self.assertIn('(QTreeView, "treeView")', snippet)
        self.assertIn('(QListView, "listView")', snippet)
        self.assertIn('view.setItemDelegateForColumn(0, delegate)', snippet)
        self.assertIn('self._filename_edit_delegates.append(delegate)', snippet)
        self.assertNotIn('view.setItemDelegate(delegate)', snippet)

    def test_only_inline_editors_receive_zero_padding_rule(self):
        dialog = next(n for n in ast.walk(self.tree)
                      if isinstance(n, ast.ClassDef)
                      and n.name == 'DBaseProjectOpenFileDialog')
        theme = next(n for n in dialog.body
                     if isinstance(n, ast.FunctionDef) and n.name == '_apply_theme')
        snippet = ast.get_source_segment(self.source, theme)
        self.assertIn('QFileDialog QLineEdit#dbase_project_inline_name_editor', snippet)
        self.assertIn('margin:0px;padding:0px;border:0px', snippet)
        self.assertIn('QFileDialog QTreeView::item:selected', snippet)


if __name__ == '__main__':
    unittest.main()
