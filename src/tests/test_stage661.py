"""Stage 661: Projekt-Informationen stays docked beside Turbo Help.

Small fake-Qt tests execute the production workspace/snap methods from
`d64_dism.py`. Stage 660 had addressed Projekt-Einstellungen by mistake;
its obsolete regression test is replaced by this correction.
"""
from pathlib import Path
from types import SimpleNamespace
import textwrap
import pytest

SOURCE = Path(__file__).with_name('d64_dism.py').read_text(encoding='utf-8')
Qt = SimpleNamespace(LeftDockWidgetArea=1, RightDockWidgetArea=2,
                     NoDockWidgetArea=0, Horizontal=1, Vertical=2)


class Dock:
    def __init__(self, host, visible=False, area=1, width=300):
        self.host = host
        self.visible = visible
        self.area = area
        self.w = width
        self.floating = False
        self.blocked = False
    def parentWidget(self): return self.host
    def isVisible(self): return self.visible
    def isHidden(self): return not self.visible
    def isFloating(self): return self.floating
    def setFloating(self, value): self.floating = bool(value)
    def blockSignals(self, value):
        old = self.blocked
        self.blocked = value
        return old
    def show(self): self.visible = True
    def hide(self): self.visible = False
    def setVisible(self, value): self.visible = bool(value)
    def width(self): return self.w
    def raise_(self): pass
    def updateGeometry(self): pass
    def setMinimumSize(self, *args): pass
    def setSizePolicy(self, *args): pass
    def allowedAreas(self): return 3


class Central(Dock):
    minw, maxw, minh, maxh = 80, 10000, 60, 10000
    def minimumWidth(self): return self.minw
    def maximumWidth(self): return self.maxw
    def minimumHeight(self): return self.minh
    def maximumHeight(self): return self.maxh
    def setMinimumWidth(self, value): self.minw = value
    def setMaximumWidth(self, value): self.maxw = value
    def setMinimumHeight(self, value): self.minh = value
    def setMaximumHeight(self, value): self.maxh = value
    def setMinimumSize(self, w, h): self.minw, self.minh = w, h
    def setMaximumSize(self, w, h): self.maxw, self.maxh = w, h


class Window:
    def __init__(self, info_visible=True, info_area=2, settings_visible=True):
        self.project_settings_dock = Dock(self, settings_visible, 1, 430)
        self.turbo_help_compiler_dock = Dock(self, False, 1, 540)
        self.right_dock = Dock(self, info_visible, info_area, 210)
        self.left_dock = Dock(self, True, 1)
        self.other_tool = Dock(self, False)
        self.docks = [self.project_settings_dock, self.turbo_help_compiler_dock,
                      self.right_dock, self.left_dock, self.other_tool]
        self.central = Central(self, True)
        self._exclusive_tool_workspace = None
        self._exclusive_tool_workspace_transitioning = False
        self.resize_calls = []
    def _project_information_dock_width_limit(self): return self.width() // 4
    def centralWidget(self): return self.central
    def findChildren(self, cls): return self.docks
    def dockWidgetArea(self, dock): return dock.area
    def addDockWidget(self, area, dock): dock.area = area
    def saveState(self): return [(d, d.area, d.floating) for d in self.docks]
    def restoreState(self, state):
        for dock, area, floating in state:
            dock.area, dock.floating = area, floating
    def geometry(self): return (0, 0, 1000, 800)
    def setGeometry(self, rect): pass
    def isMaximized(self): return False
    def width(self): return 1000
    def height(self): return 800
    def resizeDocks(self, docks, sizes, orientation):
        self.resize_calls.append((docks, sizes, orientation))
    def open_help(self):
        self._activate_exclusive_tool_workspace(self.turbo_help_compiler_dock)
        self.turbo_help_compiler_dock.show()
        self._expand_exclusive_tool_workspace(self.turbo_help_compiler_dock)


def bind_method(name):
    start = SOURCE.index(f'        def {name}(')
    end = SOURCE.find('\n        def ', start + 16)
    if end < 0:
        raise AssertionError(f'End of method not found for {name}')
    decorator = SOURCE.find('\n        @', start + 16, end)
    if decorator != -1:
        end = decorator
    ns = {'Qt': Qt, 'QDockWidget': Dock, 'QPoint': object, 'QByteArray': lambda x: x,
          'QSizePolicy': SimpleNamespace(Expanding=1),
          'QTimer': SimpleNamespace(singleShot=lambda _ms, callback: callback())}
    exec(textwrap.dedent(SOURCE[start:end]), ns)
    setattr(Window, name, ns[name])


for _name in (
    '_activate_exclusive_tool_workspace', '_expand_exclusive_tool_workspace',
    '_restore_exclusive_tool_workspace', '_turbo_help_project_info_workspace_active',
    '_sync_turbo_help_project_information_side',
    '_project_information_dock_visibility_changed',
    '_is_primary_side_dock', '_finish_project_dock_snap',
):
    bind_method(_name)


@pytest.mark.parametrize('area', [1, 2])
def test_help_keeps_project_information_visible_on_its_current_side(area):
    w = Window(info_area=area)
    w.open_help()
    assert w.right_dock.visible
    assert w.right_dock.area == area
    assert w.turbo_help_compiler_dock.area == 3 - area
    assert w.turbo_help_compiler_dock.visible
    assert not w.project_settings_dock.visible
    assert not w.left_dock.visible
    docks, sizes, axis = w.resize_calls[-2]
    assert docks == [w.right_dock, w.turbo_help_compiler_dock]
    assert axis == Qt.Horizontal
    assert sizes[0] <= w.width() // 4
    assert sum(sizes) == w.width() - 12
    w._restore_exclusive_tool_workspace(w.turbo_help_compiler_dock)
    assert w.right_dock.visible and not w.turbo_help_compiler_dock.visible
    assert w.project_settings_dock.visible and w.left_dock.visible
    assert w.central.visible


def test_hidden_information_dock_is_not_forced_visible():
    w = Window(info_visible=False)
    w.open_help()
    assert not w.right_dock.visible
    assert w.turbo_help_compiler_dock.visible
    assert w.resize_calls[-2][0] == [w.turbo_help_compiler_dock]
    w._restore_exclusive_tool_workspace(w.turbo_help_compiler_dock)
    assert not w.right_dock.visible


def test_project_settings_are_no_longer_the_special_help_companion():
    w = Window(info_visible=True, settings_visible=True)
    w.open_help()
    assert w.right_dock.visible
    assert not w.project_settings_dock.visible
    assert w.right_dock in w._exclusive_tool_workspace['visibility']


def test_changing_information_side_moves_help_to_opposite_side_and_survives_close():
    w = Window(info_area=2)
    w.open_help()
    w.right_dock.area = Qt.LeftDockWidgetArea
    w._sync_turbo_help_project_information_side()
    assert w.right_dock.area == 1
    assert w.turbo_help_compiler_dock.area == 2
    assert not w.left_dock.visible
    w._restore_exclusive_tool_workspace(w.turbo_help_compiler_dock)
    assert w.right_dock.area == 1
    assert w.right_dock.visible and w.left_dock.visible


def test_closed_project_information_is_not_resurrected_on_help_close():
    w = Window()
    w.open_help()
    w.right_dock.hide()
    w._project_information_dock_visibility_changed(False)
    assert w.turbo_help_compiler_dock.visible
    w._restore_exclusive_tool_workspace(w.turbo_help_compiler_dock)
    assert not w.right_dock.visible


def test_transient_floating_signal_does_not_change_project_visibility_snapshot():
    w = Window()
    w.open_help()
    w.right_dock.floating = True
    w._project_information_dock_visibility_changed(False)
    assert w._exclusive_tool_workspace['visibility'][w.right_dock] is True


def test_another_exclusive_tool_keeps_original_behavior():
    w = Window()
    w._activate_exclusive_tool_workspace(w.other_tool)
    w.other_tool.show()
    assert not w.right_dock.visible
    assert not w.project_settings_dock.visible
    w._restore_exclusive_tool_workspace(w.other_tool)
    assert w.right_dock.visible and w.project_settings_dock.visible


@pytest.mark.parametrize('area', [1, 2])
def test_project_snap_during_help_does_not_reopen_filesystem(area):
    w = Window()
    w.open_help()
    w.right_dock.setFloating(True)
    w._ensure_dock_snap_overlay = lambda: SimpleNamespace(
        update_target=lambda _: area, active_target='project-help',
        target_spec=lambda _: (None, area, Qt.Horizontal, 'after', 'side'),
        hide_overlay=lambda: None)
    assert w._finish_project_dock_snap(w.right_dock, object())
    assert w.right_dock.area == area
    assert w.turbo_help_compiler_dock.area == 3 - area
    assert not w.right_dock.isFloating()
    assert not w.left_dock.visible


def test_ui_wires_only_project_information_for_help():
    assert 'dock.objectName() == "d64_content_dock"' in SOURCE
    assert 'specs[f"{side}:project-help"]' in SOURCE
    assert 'self.right_dock.setAllowedAreas(\n                Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea' in SOURCE
    assert 'self.right_dock.visibilityChanged.connect(\n                self._project_information_dock_visibility_changed' in SOURCE
    assert 'if keep_info:' in SOURCE
    assert 'keep_settings' not in SOURCE
