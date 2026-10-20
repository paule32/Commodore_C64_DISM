# -*- coding: utf-8 -*-
"""Stage 436: dBASE Form Designer, CHM chrome, toolbar hover."""
from __future__ import annotations

import ast
from pathlib import Path
from textwrap import dedent

SRC = (Path(__file__).parent / 'd64_dism.py').read_text(encoding='utf-8')
TREE = ast.parse(SRC)


def _cls(name):
    return next(x for x in ast.walk(TREE) if isinstance(x, ast.ClassDef) and x.name == name)


def _method(cls, name):
    return next(x for x in cls.body if isinstance(x, ast.FunctionDef) and x.name == name)


def _source(cls, name):
    return ast.get_source_segment(SRC, _method(_cls(cls), name))


def test_form_designer_has_one_close_button_and_no_float_control():
    ensure = _source('ExplorerWindow', '_ensure_dbase_form_designer')
    assert 'designer_dock.setTitleBarWidget(' in ensure
    assert 'show_float_button=False' in ensure
    assert 'close_callback=self._close_dbase_form_designer_pair' in ensure
    title = _source('DockTitleBar', '__init__')
    assert 'if show_float_button:' in title
    assert 'self.float_button.hide()' in title
    assert 'close_callback() if close_callback is not None else dock.close()' in title


def test_form_close_closes_both_docks_and_restores_workspace():
    """Run actual extracted method against double objects without importing Qt."""
    src = dedent(_source('ExplorerWindow', '_close_dbase_form_designer_pair'))
    ns = {}
    exec(src, ns)

    class FakeDock:
        def __init__(self): self.closed = 0
        def close(self): self.closed += 1
    class FakeOwner:
        dbase_form_property_dock = FakeDock()
        dbase_form_designer_dock = FakeDock()
        def __init__(self): self.visibility = []
        def _dbase_form_dock_visibility_changed(self, arg): self.visibility.append(arg)
    owner = FakeOwner()
    ns['_close_dbase_form_designer_pair'](owner)
    assert owner.dbase_form_property_dock.closed == 1
    assert owner.dbase_form_designer_dock.closed == 1
    assert owner.visibility == [False]


def test_chm_titlebar_three_buttons_and_exact_gradient():
    constructor = _source('ChmViewerTitleBar', '__init__')
    assert 'chm_viewer_title_minimize' in constructor
    assert 'chm_viewer_title_maximize' in constructor
    assert 'chm_viewer_title_close' in constructor
    assert 'clicked.connect(dialog.showMinimized)' in constructor
    assert 'clicked.connect(self.toggle_maximized)' in constructor
    assert 'clicked.connect(dialog.reject)' in constructor
    paint = _source('ChmViewerTitleBar', 'paintEvent')
    assert 'QLinearGradient(0, 0, self.width(), 0)' in paint
    assert 'QColor("#000000")' in paint
    assert 'QColor("#707070")' in paint
    assert 'QColor("#d9dde4")' in paint
    assert 'dialog.windowTitleChanged.connect(self.title_label.setText)' in constructor


def test_chm_frame_is_3px_and_theme_switch_updates_titlebar():
    constructor = _source('ChmViewerDialog', '__init__')
    content = _source('ChmViewerDialog', 'create_content')
    theme = _source('ChmViewerDialog', 'set_dark_mode')
    css = _source('ChmViewerDialog', 'apply_widget_scrollbar_theme')
    assert 'Qt.FramelessWindowHint' in constructor
    assert 'layout.setContentsMargins(3, 3, 3, 3)' in content
    assert 'self.title_bar = ChmViewerTitleBar(self)' in content
    assert 'layout.addWidget(self.menu_bar)' in content
    assert 'border: 3px solid {dialog_frame}' in css
    assert 'self.title_bar.set_dark_mode(enabled)' in theme
    assert 'self.title_bar.sync_maximize_button()' in _source('ChmViewerDialog', 'changeEvent')
    assert 'self.saveGeometry()' in _source('ChmViewerDialog', 'done')
    assert 'self.status_bar.setSizeGripEnabled(True)' in _source('ChmViewerDialog', 'create_statusbar')


def test_dark_hover_toolbar_buttons_use_gray_background_and_black_icons():
    build = _source('ExplorerWindow', '_create_toolbar')
    icon = _source('ExplorerWindow', '_toolbar_symbol_icon')
    filter_method = _source('ExplorerWindow', 'eventFilter')
    assert 'self.toolbar.widgetForAction(action)' in build
    assert 'QToolButton:hover{background:#808080;color:#000000;' in build
    assert '(self.chm_viewer_action, "help")' in build
    assert '(self.zoom_in_action, "zoom_in")' in build
    assert '(self.zoom_out_action, "zoom_out")' in build
    assert 'hover: bool = False' in icon
    assert 'QColor(0, 0, 0) if self.dark_mode_enabled else QColor(45, 45, 45)' in icon
    assert 'getattr(self, "_main_toolbar_hover_buttons", {})' in filter_method
    assert 'event.type() in (QEvent.Enter, QEvent.Leave)' in filter_method
    assert 'action.setIcon(self._toolbar_symbol_icon(' in filter_method
    assert 'button.underMouse()' in _source('ExplorerWindow', 'toggle_editor_theme')
