# -*- coding: utf-8 -*-
"""Stage 574: Dark-/Light-Mode der Grammatikparser-Meldungsdialoge."""
import ast
import importlib.util
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
SOURCE = (HERE / "agent_0001.py").read_text(encoding="utf-8")
TREE = ast.parse(SOURCE)


def test_all_grammar_dialogs_are_themable_instances():
    assert 'class _GrammarMessageBox(QMessageBox):' in SOURCE
    assert 'def set_dark_mode(self, enabled):' in SOURCE
    assert 'dialog = _GrammarMessageBox(self)' in SOURCE
    assert 'dialog.set_dark_mode(self._dark)' in SOURCE
    assert 'return dialog.exec_()' in SOURCE
    assert not any(x in SOURCE for x in (
        'QMessageBox.question(', 'QMessageBox.warning(', 'QMessageBox.information(',
    ))
    assert SOURCE.count('self._show_grammar_dialog(') == 6


def test_explicit_dark_and_light_palette_and_widgets():
    for marker in (
        '"#202630", "#171c24", "#ffffff", "#596779"',
        '"#f0f0f0", "#ffffff", "#000000", "#9b9b9b"',
        'palette.setColor(QPalette.Highlight, QColor(accent))',
        'QMessageBox#agent_0001_message_box QLabel',
        'QMessageBox#agent_0001_message_box QPushButton',
        'QMessageBox#agent_0001_message_box QPushButton:default',
        'self.setAttribute(Qt.WA_StyledBackground, True)',
        'self.setPalette(palette)',
        'for child in self.findChildren(QWidget):',
    ):
        assert marker in SOURCE, marker


def test_question_is_no_by_default_and_no_cancel_is_saved():
    assert 'buttons=QMessageBox.Yes | QMessageBox.No' in SOURCE
    assert 'default_button=QMessageBox.No' in SOURCE
    assert 'dialog.setEscapeButton(QMessageBox.No)' in SOURCE
    assert 'if choice != QMessageBox.Yes:' in SOURCE


def test_native_windows_titlebar_dark_and_light():
    assert 'def showEvent(self, event):' in SOURCE
    assert 'self._apply_native_title_theme()' in SOURCE
    assert 'ctypes.windll.dwmapi.DwmSetWindowAttribute' in SOURCE
    assert 'ctypes.c_int(1 if self._dark_mode else 0)' in SOURCE
    assert 'for attribute in (20, 19):' in SOURCE
    assert 'if sys.platform != "win32":' in SOURCE


def test_first_json_error_follows_actual_theme_and_later_switches():
    assert 'self._dark = self._find_application_dark_mode()' in SOURCE
    widget = next(x for x in TREE.body if isinstance(x, ast.ClassDef) and x.name == 'GermanGrammarWidget')
    init = next(x for x in widget.body if isinstance(x, ast.FunctionDef) and x.name == '__init__')
    calls = [x.value.func.attr for x in ast.walk(init) if isinstance(x, ast.Expr)
             and isinstance(x.value, ast.Call) and isinstance(x.value.func, ast.Attribute)]
    assert calls.index('set_dark_mode') < calls.index('_reload_examples')
    assert 'for dialog in self.findChildren(_GrammarMessageBox):' in SOURCE


@pytest.mark.skipif(importlib.util.find_spec("PyQt5") is None, reason="PyQt5 nicht installiert")
def test_real_message_boxes_light_dark_buttons_and_parent(tmp_path, monkeypatch):
    import os
    os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
    from PyQt5.QtWidgets import QApplication, QMessageBox
    from PyQt5.QtGui import QPalette
    from PyQt5.QtCore import QTimer
    from agent_0001 import GermanGrammarWidget, _GrammarMessageBox
    from agent_0001_data import ExampleStore

    app = QApplication.instance() or QApplication([])
    w = GermanGrammarWidget(store=ExampleStore(tmp_path / 'example.json'))
    for dark, expected in ((True, '#202630'), (False, '#f0f0f0'), (True, '#202630')):
        w.set_dark_mode(dark)
        dlg = _GrammarMessageBox(w)
        dlg.setWindowTitle('Neue Texte speichern?')
        dlg.setText('Test der Meldungsfenster')
        dlg.setIcon(QMessageBox.Question)
        dlg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        dlg.setDefaultButton(QMessageBox.No)
        dlg.setEscapeButton(QMessageBox.No)
        dlg.set_dark_mode(w._dark)
        assert dlg.palette().color(QPalette.Window).name() == expected
        assert 'QPushButton:default' in dlg.styleSheet()
        QTimer.singleShot(0, lambda d=dlg: d.done(QMessageBox.No))
        assert dlg.exec_() == QMessageBox.No
    w.close()
