# -*- coding: utf-8 -*-
"""Stage 437: Texte, Titelzeilen, Fensterknöpfe und zwei About-Menüpfade."""
from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).parent
MAIN = (ROOT / 'd64_dism.py').read_text(encoding='utf-8')
ABOUT = (ROOT / 'd64_about_dialog.py').read_text(encoding='utf-8')


def _method_text(name, cls=None, src=ABOUT):
    tree = ast.parse(src)
    nodes = ast.walk(tree) if cls is None else next(
        n for n in ast.walk(tree) if isinstance(n, ast.ClassDef) and n.name == cls
    ).body
    fn = next(n for n in nodes if isinstance(n, ast.FunctionDef) and n.name == name)
    return ast.get_source_segment(src, fn)


def test_app_about_text_is_exact_and_uses_two_color_roles():
    module = ast.parse(ABOUT)
    lines = next(n for n in module.body if isinstance(n, ast.Assign) and any(
        isinstance(t, ast.Name) and t.id == 'APP_ABOUT_LINES' for t in n.targets
    ))
    contents = ast.literal_eval(lines.value)
    assert contents == (
        'C= 64  Disassembler',
        'Version 0.0.1',
        '(c) 2026 bei Jens Kallup - paule32',
        'Alle Rechte vorbehalten.',
        'Lizenziert durch die MIT Lizenz',
    )
    app = _method_text('_create_application_content', 'D64AboutDialog')
    assert "'app_title'" in app
    assert "'version'" in app
    assert "'copyright'" in app
    assert "'rights'" in app
    assert "'license'" in app
    theme = _method_text('set_dark_mode', 'D64AboutDialog')
    assert "'#ffe15c'" in theme
    assert "'#ffffff'" in theme
    assert "role != 'license'" in theme
    assert 'self.title_bar.set_dark_mode(enabled)' in theme


def test_about_window_frame_is_three_px_and_titlebar_has_gradient():
    init = _method_text('__init__', 'D64AboutDialog')
    theme = _method_text('set_dark_mode', 'D64AboutDialog')
    title_paint = _method_text('paintEvent', 'D64AboutTitleBar')
    assert 'Qt.FramelessWindowHint' in init
    assert "self.setObjectName('d64_about_dialog')" in init
    assert "self.border_frame.setObjectName('d64_about_frame')" in init
    assert 'border:3px solid' in theme
    assert 'QLinearGradient(0, 0, self.width(), 0)' in title_paint
    assert "QColor('#000000')" in title_paint
    assert "QColor('#707070')" in title_paint
    assert 'if self._dark_mode:' in title_paint


def test_titlebar_has_working_close_x_and_is_draggable():
    init = _method_text('__init__', 'D64AboutTitleBar')
    icon = _method_text('_close_icon', 'D64AboutTitleBar')
    drag = _method_text('mouseMoveEvent', 'D64AboutTitleBar')
    assert "self.close_button.setObjectName('d64_about_close')" in init
    assert 'self.close_button.clicked.connect(dialog.reject)' in init
    assert 'painter.drawLine(6, 6, 18, 18)' in icon
    assert 'painter.drawLine(18, 6, 6, 18)' in icon
    assert 'self._dialog.move(' in drag
    assert "self.ok_button.clicked.connect(self.accept)" in _method_text('__init__', 'D64AboutDialog')


def test_qt_dialog_shows_runtime_qt_pyqt_information_not_fixed_version():
    qt = _method_text('_create_qt_content', 'D64AboutDialog')
    assert "f'Diese Anwendung verwendet Qt {qVersion()}.'" in qt
    assert "f'PyQt-Version: {PYQT_VERSION_STR}'" in qt
    assert 'www.qt.io' in qt
    assert "self.setWindowTitle('Über Qt5 ...' if about_qt else 'Über ...')" in _method_text('__init__', 'D64AboutDialog')


def test_main_menu_methods_use_one_shared_dialog_and_application_theme():
    assert 'from d64_about_dialog import D64AboutDialog' in MAIN
    assert 'self.about_action.triggered.connect(self.show_about_dialog)' in MAIN
    assert 'self.about_qt_action.triggered.connect(self.show_about_qt_dialog)' in MAIN
    app = _method_text('show_about_dialog', 'ExplorerWindow', MAIN)
    qt = _method_text('show_about_qt_dialog', 'ExplorerWindow', MAIN)
    assert 'D64AboutDialog(' in app and 'D64AboutDialog(' in qt
    assert 'about_qt=False' in app and 'about_qt=True' in qt
    for method in (app, qt):
        assert 'self.application_dark_mode(self.dark_mode_enabled)' in method
        assert 'dialog.exec_()' in method
    assert '_DOXYGEN_QMESSAGEBOX_CLASS.aboutQt' not in qt


def test_existing_dark_and_light_palettes_are_distinct():
    theme = _method_text('set_dark_mode', 'D64AboutDialog')
    assert "'#202630' if enabled else '#f3f5f8'" in theme
    assert "'#778391' if enabled else '#8996a5'" in theme
    assert "'#ffffff' if enabled else '#202630'" in theme
