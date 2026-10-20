# -*- coding: utf-8 -*-
"""Stage 457: project reopen may not dereference a deleted DBF QTabWidget."""
from pathlib import Path
import textwrap

SOURCE = Path(__file__).with_name('d64_dism.py').read_text(encoding='utf-8')


def _method(name):
    token = '        def ' + name + '('
    a = SOURCE.index(token)
    b = SOURCE.find('\n        def ', a + len(token))
    if b < 0:
        raise AssertionError('Cannot extract ' + name)
    return textwrap.dedent(SOURCE[a:b])


class FakeTabBar:
    def __init__(self):
        self.visible = True

    def isVisible(self):
        return self.visible

    def setVisible(self, value):
        self.visible = bool(value)

    def hide(self):
        self.visible = False


class FakeDocumentTabs:
    def __init__(self):
        self.pages = []
        self.current = -1
        self.bar = FakeTabBar()

    def addTab(self, page, title):
        self.pages.append(page)
        return len(self.pages) - 1

    def removeTab(self, index):
        # Qt QTabWidget.removeTab() does NOT delete the page.
        self.pages.pop(index)
        self.current = min(self.current, len(self.pages) - 1)

    def indexOf(self, page):
        try:
            return self.pages.index(page)
        except ValueError:
            return -1

    def currentIndex(self):
        return self.current

    def setCurrentIndex(self, index):
        self.current = index

    def setCurrentWidget(self, page):
        self.current = self.indexOf(page)

    def count(self):
        return len(self.pages)

    def tabBar(self):
        return self.bar


class FakeDbfPage:
    def __init__(self):
        self.widths = None

    def set_column_width_preferences(self, preferences):
        self.widths = preferences


class FakeDesignerTabs:
    def __init__(self):
        self.alive = True
        self.pages = [FakeDbfPage()]

    def count(self):
        if not self.alive:
            raise RuntimeError('wrapped C/C++ object of type QTabWidget has been deleted')
        return len(self.pages)

    def widget(self, index):
        return self.pages[index]


class FakeDesigner:
    def __init__(self):
        self.table_tabs = FakeDesignerTabs()

    def show(self):
        pass

    def updateGeometry(self):
        pass


class FakeCentralPage:
    def __init__(self, designer):
        self.designer = designer
        self.visible = True
        self.deleted = False

    def hide(self):
        self.visible = False

    def show(self):
        self.visible = True

    def updateGeometry(self):
        pass

    def deleteLater(self):
        self.deleted = True
        self.designer.table_tabs.alive = False


class FakeDock:
    def hide(self):
        pass


def test_project_reopen_reuses_live_table_designer_after_workspace_restore():
    scope = {'tr': lambda s: s, 'DBaseTablePage': FakeDbfPage}
    for name in (
        '_unmount_dbase_table_designer_central',
        '_mount_dbase_table_designer_central',
        'set_project_column_widths',
    ):
        exec(_method(name), scope)

    designer = FakeDesigner()
    # Call the actual DBaseTableDesignerWidget.set_project_column_widths method
    # to reproduce the traceback, including the failing .table_tabs.count().
    designer.set_project_column_widths = scope['set_project_column_widths'].__get__(designer)
    page = FakeCentralPage(designer)
    tabs = FakeDocumentTabs()
    tabs.addTab(object(), 'Code')
    tabs.addTab(page, 'dBase Tabelle - Designer')
    tabs.setCurrentWidget(page)
    tabs.tabBar().hide()

    class Host:
        _unmount_dbase_table_designer_central = scope['_unmount_dbase_table_designer_central']
        _mount_dbase_table_designer_central = scope['_mount_dbase_table_designer_central']

        def _ensure_dbase_table_designer(self):
            assert self.dbase_table_designer_widget is designer
            assert self._dbase_table_central_page is page


    host = Host()
    host.document_tabs = tabs
    host.dbase_table_designer_widget = designer
    host.dbase_table_designer_dock = FakeDock()
    host._dbase_table_central_page = page
    host._dbase_table_centralized = True
    host._dbase_table_previous_document_index = 0
    host._dbase_table_previous_tabbar_visible = True

    for cycle in range(3):
        host._unmount_dbase_table_designer_central()
        assert not page.deleted
        assert tabs.indexOf(page) == -1
        assert not page.visible
        # Reproduces the exact stage456 load_project_file() action.
        widths = {'a.dbf': {'Feld': 122 + cycle}}
        designer.set_project_column_widths(widths)
        assert designer.table_tabs.pages[0].widths is widths
        host._mount_dbase_table_designer_central()
        assert tabs.indexOf(page) >= 0
        assert page.visible
        assert host.dbase_table_designer_widget is designer


def test_lifecycle_fix_keeps_shared_tab_widget_on_unmount():
    method = _method('_unmount_dbase_table_designer_central')
    assert 'self.document_tabs.removeTab(index)' in method
    assert 'page.hide()' in method
    assert 'page.deleteLater()' not in method
    assert 'self._dbase_table_central_page = None' not in method
