# -*- coding: utf-8 -*-
"""Stage 432 regression updated for Stage 434 three-button chooser.

These tests are AST/source integration checks. A real Qt window smoke test
needs a Windows or X11 machine with PyQt5 installed.
"""
from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).parent
SOURCE = (ROOT / 'd64_dism.py').read_text(encoding='utf-8')
TREE = ast.parse(SOURCE)


def _clazz(name):
    return next(n for n in ast.walk(TREE) if isinstance(n, ast.ClassDef) and n.name == name)


def _method(name, cls):
    return next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == name)


def _body(name, cls):
    return ast.get_source_segment(SOURCE, _method(name, cls))


def test_dbase_new_file_uses_one_custom_open_dialog_for_every_role():
    # Method is deliberately located by name, independent of the main-window class name.
    method = next(n for n in ast.walk(TREE) if isinstance(n, ast.FunctionDef)
                  and n.name == '_new_dbase_project_file')
    src = ast.get_source_segment(SOURCE, method)
    assert 'for entry in DBASE_NEW_MENU' in src
    assert 'dialog = DBaseProjectOpenFileDialog(' in src
    assert 'dark_mode=self.dark_mode_enabled' in src
    assert 'default_name=default_name' in src
    assert "default_suffix=extensions[0].lstrip(\".\")" in src
    assert 'dialog.exec_() != QDialog.Accepted' in src
    assert 'selected = dialog.selectedFiles()' in src
    assert 'QFileDialog.getOpenFileName' not in src


def test_frame_titlebar_dragging_close_x_and_modal_rejection():
    cls = _clazz('DBaseProjectOpenFileDialog')
    init = _body('__init__', cls)
    assert 'Qt.Dialog | Qt.FramelessWindowHint | Qt.WindowCloseButtonHint' in init
    assert 'self.setModal(True)' in init
    assert 'self.setMinimumSize(640, 480)' in init
    assert 'self.setGeometry(x, y, 640, 480)' in init
    assert 'self.border_frame = QFrame(self)' in init
    assert 'self.title_bar = DBaseTableDialogTitleBar(' in init
    assert 'self.title_bar.close_button.setIcon(self._close_icon(self._dark_mode, 36))' in init
    assert 'self.file_dialog.accepted.connect(self._open_selected_file)' in init
    assert 'self.file_dialog.rejected.connect(self.reject)' in init
    icon = _body('_close_icon', cls)
    assert 'painter.drawLine(QPointF(margin, margin)' in icon
    assert 'painter.drawLine(QPointF(size - margin, margin)' in icon
    titlebar = _clazz('DBaseTableDialogTitleBar')
    paint = _body('paintEvent', titlebar)
    assert 'QLinearGradient(0, 0, self.width(), 0)' in paint
    assert 'QColor("#000000")' in paint
    assert 'QColor("#707070")' in paint
    assert 'self._dialog.reject' in _body('__init__', titlebar)


def test_file_browser_detail_and_dark_light_header_styling():
    cls = _clazz('DBaseProjectOpenFileDialog')
    init = _body('__init__', cls)
    theme = _body('_apply_theme', cls)
    assert 'QFileDialog.DontUseNativeDialog' in init
    assert 'QFileDialog.AcceptOpen' in init
    assert 'QFileDialog.AnyFile' in init
    assert 'QFileDialog.Detail' in init
    assert 'self.file_dialog.setWindowFlags(Qt.Widget)' in init
    assert 'border:3px solid {frame}' in theme
    assert '#202630' in theme and '#303844' in theme
    assert '#f2f4f7' in theme and '#dfe5ec' in theme
    assert 'QFileDialog QHeaderView::section' in theme
    assert 'QFileDialog QTableCornerButton::section' in theme
    assert 'for view in self.file_dialog.findChildren(QTreeView):' in theme
    assert 'header_widget.setStyleSheet(' in theme


def test_previous_dbase_validation_and_target_paths_not_dropped():
    method = next(n for n in ast.walk(TREE) if isinstance(n, ast.FunctionDef)
                  and n.name == '_new_dbase_project_file')
    src = ast.get_source_segment(SOURCE, method)
    for required in (
        'is_dbase_program_text(path)',
        'create_dbase_project_file(path, role)',
        'self._add_project_dbase_entry(role, path, title=path.name)',
        'self._add_project_resource_entry(',
        'self.open_project_item(child)',
        'self.save_project()',
        '"Datei ist keine gültige Programm-Datei"',
    ):
        assert required in src
