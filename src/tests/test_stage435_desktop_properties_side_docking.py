# -*- coding: utf-8 -*-
"""Stage 435 – Gegenseitiges horizontales Desktop-Properties-Docking.

Qt-unabhaengige Kontrolltests auf Quellstruktur und Methoden-Verhalten.
Ein echter PyQt5/Windows-GUI-Lauf bleibt separat erforderlich.
"""
from __future__ import annotations

from pathlib import Path
import textwrap
from types import SimpleNamespace

SOURCE = (Path(__file__).parent / 'd64_dism.py').read_text(encoding='utf-8')


def _method_source(name: str) -> str:
    marker = f'        def {name}('
    start = SOURCE.index(marker)
    end = SOURCE.find('\n        def ', start + len(marker))
    if end < 0:
        raise AssertionError(name)
    return textwrap.dedent(SOURCE[start:end])


class FakeQt:
    LeftDockWidgetArea = 1
    RightDockWidgetArea = 2
    Horizontal = 3
    Vertical = 4
    WindowMaximized = 8
    WindowFullScreen = 16


class FakeTimer:
    calls = []

    @staticmethod
    def singleShot(delay, callback):
        FakeTimer.calls.append((delay, callback))


class FakeDock:
    def __init__(self, area, width=300):
        self.area = area
        self._width = width
        self.allowed = None
        self.visible = False
        self.floating = False

    def isFloating(self):
        return self.floating

    def setAllowedAreas(self, area):
        self.allowed = area

    def show(self):
        self.visible = True

    def width(self):
        return self._width


class FakeHost:
    def __init__(self, project_area, settings_area, width=1120):
        self._settings_workspace_active = True
        self._settings_dock_rearranging = False
        self._width = width
        self.right_dock = FakeDock(project_area, 250)
        self.settings_dock = FakeDock(settings_area)
        self.moves = []
        self.resizes = []
        self.enforced = 0
        self._geometry = (50, 90, width, 720)
        self._window_state = 0

    def dockWidgetArea(self, dock):
        return dock.area

    def addDockWidget(self, area, dock):
        self.moves.append(area)
        dock.area = area

    def resizeDocks(self, docks, sizes, orientation):
        self.resizes.append((docks, sizes, orientation))

    def width(self):
        return self._width

    def _enforce_project_information_dock_width(self):
        self.enforced += 1

    def geometry(self):
        return self._geometry

    def windowState(self):
        return self._window_state

    def _preserve_desktop_settings_window_geometry(self, geometry, state):
        PRESERVE(self, geometry, state)

    def setGeometry(self, new_geometry):
        self._geometry = new_geometry


NAMESPACE = {'Qt': FakeQt, 'QTimer': FakeTimer, 'QRect': lambda obj: tuple(obj)}
exec(_method_source('_dock_desktop_properties_next_to_project'), NAMESPACE)
exec(_method_source('_preserve_desktop_settings_window_geometry'), NAMESPACE)
exec(_method_source('_settings_dock_location_changed'), NAMESPACE)
DOCK = NAMESPACE['_dock_desktop_properties_next_to_project']
PRESERVE = NAMESPACE['_preserve_desktop_settings_window_geometry']
LOCATION_CHANGED = NAMESPACE['_settings_dock_location_changed']


def test_project_right_desktop_left_full_remainder():
    host = FakeHost(FakeQt.RightDockWidgetArea, FakeQt.RightDockWidgetArea)
    DOCK(host)
    assert host.moves == [FakeQt.LeftDockWidgetArea]
    assert host.settings_dock.allowed == FakeQt.LeftDockWidgetArea
    assert host.settings_dock.visible is True
    assert host.resizes == [([host.settings_dock], [858], FakeQt.Horizontal)]
    assert host._geometry == (50, 90, 1120, 720)
    assert host._settings_dock_rearranging is False
    assert FakeTimer.calls[-1][0] == 0


def test_project_left_desktop_right_full_remainder():
    host = FakeHost(FakeQt.LeftDockWidgetArea, FakeQt.LeftDockWidgetArea)
    DOCK(host)
    assert host.moves == [FakeQt.RightDockWidgetArea]
    assert host.settings_dock.allowed == FakeQt.RightDockWidgetArea
    assert host.resizes[0][2] == FakeQt.Horizontal
    assert not any(e[-1] == FakeQt.Vertical for e in host.resizes)


def test_project_side_change_reflows_desktop_without_stacking():
    host = FakeHost(FakeQt.RightDockWidgetArea, FakeQt.LeftDockWidgetArea)
    DOCK(host)
    assert not host.moves  # already on correct side
    host.right_dock.area = FakeQt.LeftDockWidgetArea
    DOCK(host)
    assert host.settings_dock.area == FakeQt.RightDockWidgetArea
    assert host.settings_dock.allowed == FakeQt.RightDockWidgetArea


def test_float_and_inactive_are_respected():
    host = FakeHost(FakeQt.RightDockWidgetArea, FakeQt.RightDockWidgetArea)
    host.settings_dock.floating = True
    DOCK(host)
    assert not host.moves
    host.settings_dock.floating = False
    host._settings_workspace_active = False
    DOCK(host)
    assert not host.moves


def test_preserve_window_position_and_size_but_not_maximized_state():
    host = FakeHost(FakeQt.RightDockWidgetArea, FakeQt.LeftDockWidgetArea)
    previous = (20, 30, 800, 690)
    PRESERVE(host, previous, 0)
    assert host.geometry() == previous
    host._geometry = (0, 0, 1120, 720)
    PRESERVE(host, previous, FakeQt.WindowMaximized)
    assert host.geometry() == (0, 0, 1120, 720)


def test_settings_creation_is_not_split_with_filesystem():
    source = _method_source('_ensure_settings_dock')
    assert 'self.splitDockWidget' not in source
    assert 'self.addDockWidget(initial_area, dock)' in source
    assert 'dock.setMinimumSize(0, 0)' in source
    assert 'dock.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)' in source
    assert 'dock.dockLocationChanged.connect(self._settings_dock_location_changed)' in source


def test_workspace_hides_filesystem_and_restores_state():
    enter = _method_source('_enter_settings_workspace')
    restore = _method_source('_restore_settings_workspace')
    assert 'left.hide()' in enter
    assert 'left.show()' not in enter
    assert '"left": getattr(self, "left_dock", None)' in enter
    assert '"left", "left_dock"' in restore
    assert 'dock.show()' in restore
    assert 'else:' in restore and 'dock.hide()' in restore


def test_open_uses_horizontal_side_layout_and_preserves_geometry():
    show = _method_source('show_settings_dock')
    assert 'geometry_before = QRect(self.geometry())' in show
    assert 'self._dock_desktop_properties_next_to_project()' in show
    assert 'self._preserve_desktop_settings_window_geometry(geometry_before, state_before)' in show
    assert '100000' not in show
    assert 'Qt.Vertical' not in show
    assert 'left.show()' not in show


def test_project_dock_location_change_tracks_opposite_side():
    handler = _method_source('_project_information_dock_location_changed')
    assert 'QTimer.singleShot(0, self._dock_desktop_properties_next_to_project)' in handler
    FakeTimer.calls.clear()
    host = FakeHost(FakeQt.RightDockWidgetArea, FakeQt.LeftDockWidgetArea)
    host._dock_desktop_properties_next_to_project = lambda: DOCK(host)
    LOCATION_CHANGED(host, FakeQt.RightDockWidgetArea)
    assert len(FakeTimer.calls) == 1
