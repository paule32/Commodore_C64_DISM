# -*- coding: utf-8 -*-
"""Stage 438: Test of exclusive QDockWidget state without PyQt installation."""
from __future__ import annotations
from pathlib import Path
from types import SimpleNamespace
import textwrap

ROOT = Path(__file__).parent
SOURCE = (ROOT / 'd64_dism.py').read_text(encoding='utf-8')


def _load_methods():
    names = (
        '_activate_exclusive_tool_workspace',
        '_expand_exclusive_tool_workspace',
        '_exclusive_tool_workspace_visibility_changed',
        '_restore_exclusive_tool_workspace',
    )
    namespace = {
        'QDockWidget': type('QDockWidget', (), {}),
        'QByteArray': lambda payload: payload,
        'QSizePolicy': SimpleNamespace(Expanding=2),
        'Qt': SimpleNamespace(LeftDockWidgetArea=1, RightDockWidgetArea=2,
                              Horizontal=3, Vertical=4),
        'QTimer': SimpleNamespace(singleShot=lambda delay, callback: callback()),
    }
    for name in names:
        prefix = '        def ' + name + '('
        start = SOURCE.index(prefix)
        next_method = SOURCE.find('\n        def ', start + len(prefix))
        code = textwrap.dedent(SOURCE[start:next_method])
        exec(code, namespace)
    return namespace


class FakeWidget:
    def __init__(self, parent, visible=False):
        self._parent = parent
        self._visible = visible
        self.blocked = False
        self._minw, self._maxw = 40, 3000
        self._minh, self._maxh = 20, 1800

    def parentWidget(self): return self._parent
    def isVisible(self): return self._visible
    def hide(self): self._visible = False
    def show(self): self._visible = True
    def setVisible(self, yes): self._visible = bool(yes)
    def blockSignals(self, yes):
        old = self.blocked
        self.blocked = bool(yes)
        return old
    def minimumWidth(self): return self._minw
    def maximumWidth(self): return self._maxw
    def minimumHeight(self): return self._minh
    def maximumHeight(self): return self._maxh
    def setMinimumWidth(self, value): self._minw = value
    def setMaximumWidth(self, value): self._maxw = value
    def setMinimumHeight(self, value): self._minh = value
    def setMaximumHeight(self, value): self._maxh = value
    def setMinimumSize(self, width, height):
        self._minw, self._minh = width, height
    def setMaximumSize(self, width, height):
        self._maxw, self._maxh = width, height


class FakeDock(FakeWidget):
    def __init__(self, parent, visible=False, width=270):
        super().__init__(parent, visible)
        self._floating = False
        self._width = width
        self._updates = 0
    def isFloating(self): return self._floating
    def setFloating(self, yes): self._floating = bool(yes)
    def width(self): return self._width
    def setSizePolicy(self, *args): pass
    def updateGeometry(self): self._updates += 1


class FakeHost:
    def __init__(self, ns):
        for name in (
            '_activate_exclusive_tool_workspace',
            '_expand_exclusive_tool_workspace',
            '_exclusive_tool_workspace_visibility_changed',
            '_restore_exclusive_tool_workspace',
        ):
            setattr(self, name, ns[name].__get__(self, self.__class__))
        self._exclusive_tool_workspace = None
        self._exclusive_tool_workspace_transitioning = False
        self._geometry = (100, 80, 1260, 840)
        self._docks = []
        self._areas = {}
        self.central = FakeWidget(self, True)
        self.right_dock = None
        self.restore_count = 0
        self.expansions = []
        self.localize_dock = None
        self.localize_tool_window = None
    def add(self, dock, area):
        self._docks.append(dock)
        self._areas[dock] = area
        return dock
    def findChildren(self, cls): return list(self._docks)
    def centralWidget(self): return self.central
    def geometry(self): return self._geometry
    def setGeometry(self, rect): self._geometry = rect
    def isMaximized(self): return False
    def saveState(self): return dict(self._areas)
    def restoreState(self, state):
        self.restore_count += 1
        self._areas.update(state)
        return True
    def dockWidgetArea(self, dock): return self._areas[dock]
    def addDockWidget(self, area, dock): self._areas[dock] = area
    def width(self): return self._geometry[2]
    def height(self): return self._geometry[3]
    def resizeDocks(self, docks, sizes, orientation):
        self.expansions.append((docks[0], sizes[0], orientation))


def _fixture():
    ns = _load_methods()
    host = FakeHost(ns)
    left = host.add(FakeDock(host, True), 1)
    project = host.add(FakeDock(host, True), 2)
    bottom = host.add(FakeDock(host, True), 1)
    hidden = host.add(FakeDock(host, False), 1)
    host.right_dock = project
    editor = host.add(FakeDock(host, False), 1)
    second = host.add(FakeDock(host, False), 1)
    return host, left, project, bottom, hidden, editor, second


def test_hide_every_dock_then_restore_only_previous_visibles():
    host, left, project, bottom, hidden, editor, _ = _fixture()
    original_geometry = host.geometry()
    host._activate_exclusive_tool_workspace(editor)
    editor.show()
    assert editor.isVisible()
    assert not any(d.isVisible() for d in (left, project, bottom, hidden))
    assert not host.central.isVisible()
    assert host.central.maximumWidth() == 0
    editor.hide()
    host._exclusive_tool_workspace_visibility_changed(False, editor)
    assert all(d.isVisible() for d in (left, project, bottom))
    assert not hidden.isVisible() and not editor.isVisible()
    assert host.central.isVisible()
    assert host.central.minimumWidth() == 40
    assert host.central.maximumWidth() == 3000
    assert host.geometry() == original_geometry
    assert host._exclusive_tool_workspace is None
    assert host.restore_count == 1


def test_switching_between_tools_keeps_original_snapshot():
    host, left, project, bottom, hidden, editor, second = _fixture()
    host._activate_exclusive_tool_workspace(editor)
    editor.show()
    original = host._exclusive_tool_workspace
    host._activate_exclusive_tool_workspace(second)
    second.show()
    assert host._exclusive_tool_workspace is original
    assert not editor.isVisible()
    assert not any(d.isVisible() for d in (left, project, bottom))
    host._exclusive_tool_workspace_visibility_changed(False, editor)
    assert host._exclusive_tool_workspace is original
    second.hide()
    host._exclusive_tool_workspace_visibility_changed(False, second)
    assert host._exclusive_tool_workspace is None
    assert left.isVisible() and project.isVisible() and bottom.isVisible()


def test_resource_builder_docks_opposite_side_to_project():
    for project_side, expected_builder_side in ((1, 2), (2, 1)):
        host, left, project, bottom, hidden, builder, _ = _fixture()
        host._areas[project] = project_side
        host._activate_exclusive_tool_workspace(builder, beside_project=True)
        builder.show()
        assert host.dockWidgetArea(builder) == expected_builder_side
        assert project.isVisible()
        assert not left.isVisible() and not bottom.isVisible()
        assert not host.central.isVisible()
        host._expand_exclusive_tool_workspace(builder)
        assert host.expansions[0][1] == host.width() - project.width() - 12
        builder.hide()
        host._exclusive_tool_workspace_visibility_changed(False, builder)
        assert host.dockWidgetArea(project) == project_side
        assert all(d.isVisible() for d in (left, project, bottom))


def test_project_originally_hidden_stays_hidden_after_builder_close():
    host, left, project, bottom, hidden, builder, _ = _fixture()
    project.hide()
    host._activate_exclusive_tool_workspace(builder, beside_project=True)
    builder.show()
    assert project.isVisible()
    builder.hide()
    host._exclusive_tool_workspace_visibility_changed(False, builder)
    assert not project.isVisible()


def test_entry_points_use_shared_workspace_lifecycle():
    assert 'self._activate_exclusive_tool_workspace(dock)' in SOURCE
    assert 'beside_project=(kind == "alias_builder")' in SOURCE
    for kind in ('characters', 'palettes', 'text_screen', 'pixel_screen', 'alias_builder'):
        assert f'"{kind}"' in SOURCE
    assert 'dock.visibilityChanged.connect(self._localize_dock_visibility_changed)' in SOURCE
    assert 'dock.visibilityChanged.connect(\n                    self._doxygen_dock_visibility_changed' in SOURCE
    assert 'self._activate_exclusive_tool_workspace(dock)\n            dock.show()' in SOURCE
    assert 'html_editor_workspace_scroll' in SOURCE
    assert 'self.html_editor_dock.show()' not in SOURCE
