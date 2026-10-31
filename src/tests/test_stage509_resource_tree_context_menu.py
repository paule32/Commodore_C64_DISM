# -*- coding: utf-8 -*-
"""Stage 509: context menu, Menu resource, live tree behavior (Qt-independent)."""
from pathlib import Path
from types import SimpleNamespace
import textwrap
import pytest

from resource_rc_templates import (
    RESOURCE_TEMPLATE_KINDS, rc_template, insertable_rc_template,
    uncompiled_rc_template_markers,
)
from test_stage504_resource_hex_codepage import SCOPE

SOURCE = Path(__file__).with_name("d64_dism.py").read_text(encoding="utf-8")
EDITOR = SOURCE.split('class WindowsResourceEditorWidget(QWidget):', 1)[1].split('\n    def set_target(', 1)[0]


def _method(name):
    start = SOURCE.index('    def ' + name + '(', SOURCE.index('class WindowsResourceEditorWidget(QWidget):'))
    end = SOURCE.find('\n    def ', start + 1)
    return textwrap.dedent(SOURCE[start: (end if end >= 0 else len(SOURCE))])


def test_new_toolbar_menu_action_is_directly_after_dialog():
    assert RESOURCE_TEMPLATE_KINDS == (
        'Dialog', 'Menu', 'Text', 'Icon', 'Bitmap', 'Cursor', 'RCDATA'
    )
    assert 'for label in ("Dialog", "Menu", "Text", "Icon", "Bitmap", "Cursor", "RCDATA"):' in EDITOR
    assert 'self.resource_tree.setContextMenuPolicy(Qt.CustomContextMenu)' in EDITOR
    assert 'self.resource_tree.customContextMenuRequested.connect(self._show_resource_tree_context_menu)' in EDITOR


def test_menu_template_is_valid_and_repeated_insertions_get_unique_ids(tmp_path):
    one = rc_template('Menu')
    two = rc_template('Menu', one)
    assert one.startswith('IDM_MENU_1 MENU\n')
    assert 'POPUP "Datei"' in one and 'MENUITEM SEPARATOR' in one
    assert 'MENUITEM "Öffnen", 3011' in one
    assert two.startswith('IDM_MENU_2 MENU\n')
    assert 'MENUITEM "Öffnen", 3021' in two
    combined = one + '\n' + two
    p = tmp_path / 'main_menu.rc'
    p.write_text(combined, encoding='utf-8')
    compilation = SCOPE['compile_rc'](p)
    entries = compilation.entries
    assert len(entries) == 2
    assert all(e.type_id == SCOPE['RT_MENU'] and len(e.data) > 20 for e in entries)
    assert {e.name_id for e in entries} == {'IDM_MENU_1', 'IDM_MENU_2'}


@pytest.mark.parametrize('kind', RESOURCE_TEMPLATE_KINDS)
def test_templates_still_have_unique_insertable_rc_source(kind):
    one = rc_template(kind)
    assert one and one.endswith('\n')
    assert insertable_rc_template(kind, '/* exists */\n', 13).startswith('\n')


def test_uncompiled_outline_only_reports_source_declarations_not_compiled_data():
    rc = '\n'.join((rc_template('Dialog'), rc_template('Menu'), rc_template('Icon'), rc_template('Bitmap'), rc_template('Cursor'), rc_template('RCDATA'), rc_template('Text')))
    markers = uncompiled_rc_template_markers(rc)
    assert ('DIALOGEX', 'IDD_DIALOG_1') in markers
    assert ('MENU', 'IDM_MENU_1') in markers
    assert ('ICON', 'IDI_ICON_1') in markers
    assert ('BITMAP', 'IDB_BITMAP_1') in markers
    assert ('CURSOR', 'IDC_CURSOR_1') in markers
    assert ('RCDATA', 'IDR_RCDATA_1') in markers
    assert ('STRINGTABLE', 'Text (STRINGTABLE)') in markers


class Signal:
    def __init__(self): self.callbacks=[]
    def connect(self, fn): self.callbacks.append(fn)
    def fire(self):
        for fn in self.callbacks: fn()


class Action:
    def __init__(self, text):
        self.text=text
        self.enabled=True
        self.triggered=Signal()
    def setObjectName(self, name): self.name=name
    def setEnabled(self, enabled): self.enabled=enabled
    def setShortcut(self, shortcut): self.shortcut=shortcut


class Menu:
    last=None
    def __init__(self, parent):
        self.items=[]
        self.deleted=False
        Menu.last=self
    def addAction(self, label):
        result=Action(label)
        self.items.append(result)
        return result
    def addSeparator(self): self.items.append(None)
    def exec_(self, pos): self.pos=pos
    def deleteLater(self): self.deleted=True


class FakeCursor:
    def __init__(self, selection=True): self.selection=selection
    def hasSelection(self): return self.selection


class FakeEditor:
    def __init__(self, readonly=False):
        self.readonly=readonly
        self.cursor=FakeCursor(True)
    def isReadOnly(self): return self.readonly
    def textCursor(self): return self.cursor


class FakeTree:
    def __init__(self): self.current=None
    def itemAt(self, position): return 'entry'
    def setCurrentItem(self, item): self.current=item
    def viewport(self): return self
    def mapToGlobal(self, pos): return pos


class FakeHost:
    _show_resource_tree_context_menu=None
    def __init__(self, readonly=False):
        self.resource_tree=FakeTree()
        self.source_edit=FakeEditor(readonly)
        self.calls=[]
    def _insert_tree_resource_template(self, kind): self.calls.append(('new', kind))
    def _resource_source_select_all(self): self.calls.append('all')
    def _resource_source_copy(self): self.calls.append('copy')
    def _resource_source_paste(self): self.calls.append('paste')
    def _resource_source_delete(self): self.calls.append('delete')
    def save(self): self.calls.append('save'); return True
    def save_as(self): self.calls.append('save_as'); return True


def test_tree_menu_exact_labels_order_and_seven_insertion_callbacks():
    namespace={'QMenu':Menu,'Qt':SimpleNamespace(UserRole=32),
               'QKeySequence':SimpleNamespace(Save='Ctrl+S')}
    exec(_method('_show_resource_tree_context_menu'), namespace)
    FakeHost._show_resource_tree_context_menu=namespace['_show_resource_tree_context_menu']
    host=FakeHost()
    host._show_resource_tree_context_menu((10, 20))
    menu=Menu.last
    assert [a.text if a else None for a in menu.items] == [
        'Speichern', 'Speichern unter ...', None,
        'Neu:  Dialog','Neu:  Menü','Neu:  Text','Neu:  Icon',
        'Neu:  Bitmap','Neu:  Cursor','Neu:  RCDATA',None,
        'Alles auswählen','Kopieren','Einfügen','Löschen'
    ]
    assert host.resource_tree.current=='entry'
    assert menu.deleted
    assert menu.items[0].name == 'resource_tree_save'
    assert menu.items[0].shortcut == 'Ctrl+S'
    assert menu.items[1].name == 'resource_tree_save_as'
    menu.items[0].triggered.fire()
    menu.items[1].triggered.fire()
    assert host.calls[:2] == ['save', 'save_as']
    for action in menu.items[3:10]: action.triggered.fire()
    assert host.calls[2:] == [('new',kind) for kind in ('Dialog','Menu','Text','Icon','Bitmap','Cursor','RCDATA')]
    for action in menu.items[11:]: action.triggered.fire()
    assert host.calls[-4:]==['all','copy','paste','delete']


def test_readonly_res_disables_all_mutating_context_actions():
    host=FakeHost(readonly=True)
    host._show_resource_tree_context_menu((0, 0))
    items=Menu.last.items
    assert items[0].enabled and items[1].enabled  # .res can be saved too
    assert not any(a.enabled for a in items[3:10])
    assert items[11].enabled and items[12].enabled
    assert not items[13].enabled and not items[14].enabled


def test_source_preview_is_forced_immediately_and_missing_files_cannot_be_compiled():
    method=_method('insert_resource_template')
    assert 'refresh()' in method and 'timer.stop()' in method
    preview=_method('_refresh_source_preview')
    assert 'outline(source)' in preview
    assert 'self.entries = compiled.entries' in preview
    outline=_method('_show_uncompiled_template_outline')
    assert 'uncompiled_rc_template_markers' in outline
    assert 'self.entries.append' not in outline
    assert 'self.entries =' not in outline
