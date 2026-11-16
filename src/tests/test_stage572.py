# -*- coding: utf-8 -*-
"""Regressionen Stage 572: beide Eingabewege, Zustimmung, ComboBox, Dark-Header."""
from __future__ import annotations

import json
import sys
import types
from pathlib import Path
from types import SimpleNamespace

import pytest

from agent_0001_data import ExampleStore, ExampleStoreError


class _Combo:
    def __init__(self):
        self.items = []
        self.index = -1
        self.edit_text = ""
        self.blocked = False
        self.update_count = 0

    def blockSignals(self, value):
        was = self.blocked
        self.blocked = value
        return was

    def clear(self):
        self.items = []
        self.index = -1
        self.edit_text = ""

    def addItems(self, entries):
        self.items.extend(entries)

    def setCurrentIndex(self, i):
        self.index = i
        self.edit_text = self.items[i] if i >= 0 else ""

    def itemText(self, i):
        return self.items[i]

    def currentText(self):
        return self.edit_text

    def setEditText(self, text):
        self.edit_text = text
        self.index = -1

    def update(self):
        self.update_count += 1

    def view(self):
        return SimpleNamespace(viewport=lambda: SimpleNamespace(update=lambda: None))


class _Edit:
    def __init__(self):
        self.text = ""
        self.blocked = False

    def toPlainText(self):
        return self.text

    def setPlainText(self, text):
        self.text = text

    def blockSignals(self, value):
        previous = self.blocked
        self.blocked = value
        return previous


def _load_fake_gui(monkeypatch):
    """Lädt die echte Dialoglogik mit minimalen UI-Dummies (auch ohne PyQt5)."""
    class MessageBox:
        Yes, No = 1, 2
        NoButton, Ok, Question, Warning, Information = 0, 4, 8, 16, 32
        answer = Yes
        questions = []
        notices = []
        warnings = []

        @classmethod
        def question(cls, *args):
            cls.questions.append(args)
            return cls.answer

        @classmethod
        def information(cls, *args):
            cls.notices.append(args)

        @classmethod
        def warning(cls, *args):
            cls.warnings.append(args)

    fake_pyqt = types.ModuleType("PyQt5")
    fake_core = types.ModuleType("PyQt5.QtCore")
    fake_core.Qt = SimpleNamespace(AlignCenter=0)
    fake_gui = types.ModuleType("PyQt5.QtGui")
    fake_gui.QColor = object
    fake_gui.QPalette = object
    fake_gui.QPen = object
    fake_widgets = types.ModuleType("PyQt5.QtWidgets")
    for name in ("QWidget", "QVBoxLayout", "QHBoxLayout", "QGroupBox", "QSplitter",
                 "QLabel", "QComboBox", "QPushButton", "QTableWidget", "QTableWidgetItem",
                 "QHeaderView", "QPlainTextEdit", "QSizePolicy", "QAbstractItemView"):
        setattr(fake_widgets, name, object)
    fake_widgets.QMessageBox = MessageBox
    monkeypatch.setitem(sys.modules, "PyQt5", fake_pyqt)
    monkeypatch.setitem(sys.modules, "PyQt5.QtCore", fake_core)
    monkeypatch.setitem(sys.modules, "PyQt5.QtGui", fake_gui)
    monkeypatch.setitem(sys.modules, "PyQt5.QtWidgets", fake_widgets)

    module = types.ModuleType("_stage572_test_gui")
    filename = Path(__file__).with_name("agent_0001.py")
    exec(compile(filename.read_text(encoding="utf-8"), str(filename), "exec"), module.__dict__)

    # Für die Datenfluss-Regressionen wird nur die Anzeige gemockt; die echte
    # Stage-574-Dialogklasse mit ihren Qt-Paletten wird separat getestet.
    def fake_show_dialog(self, icon, title, message, *, buttons=None, default_button=None):
        args = (self, title, message, buttons, default_button)
        if icon == MessageBox.Question:
            MessageBox.questions.append(args)
            return MessageBox.answer
        if icon == MessageBox.Warning:
            MessageBox.warnings.append(args)
        else:
            MessageBox.notices.append(args)
        return MessageBox.Ok

    module.GermanGrammarWidget._show_grammar_dialog = fake_show_dialog
    return module.GermanGrammarWidget, MessageBox


@pytest.fixture
def harness(tmp_path, monkeypatch):
    with monkeypatch.context() as m:
        Widget, MessageBox = _load_fake_gui(m)
        seed = tmp_path / "seed.json"
        seed.write_text(json.dumps({"version": 1, "examples": [
            {"text": "Der Mann geht nach Hause."},
            {"text": "Was ist heute für ein Tag?"},
        ]}, ensure_ascii=False), encoding="utf-8")
        store = ExampleStore(tmp_path / "profile" / "agent_0001_examples.json", seed)
        widget = object.__new__(Widget)
        widget.store = store
        widget.example_combo = _Combo()
        widget.input_edit = _Edit()
        widget._stored_texts = []
        widget._updating_examples = False
        widget._last_edited_combo_text = None
        widget._active_input = "combo"
        widget._check_in_progress = False
        checked = []
        widget._run_check = lambda text: (checked.append(text), SimpleNamespace(valid=True, diagnostics=[]))[1]
        assert widget._reload_examples()
        yield widget, MessageBox, checked, store


def test_new_sentence_from_editor_asks_and_updates_json_and_combo(harness):
    widget, MessageBox, checked, store = harness
    widget.input_edit.text = "  Grüß    Gott!  "
    widget._editor_text_edited()
    widget.check_current_text()
    assert checked == ["Grüß Gott!"]
    assert len(MessageBox.questions) == 1
    assert store.contains("Grüß Gott!")
    assert widget.example_combo.items[-1] == "Grüß Gott!"
    assert widget.example_combo.index == 2  # tatsächlich ausgewählter Eintrag
    assert widget.example_combo.currentText() == "Grüß Gott!"
    assert widget.input_edit.toPlainText() == "Grüß Gott!"
    assert widget.example_combo.update_count >= 2
    assert len(json.loads(store.path.read_text(encoding="utf-8"))["examples"]) == 3


def test_new_sentence_typed_in_combo_asks_and_updates(harness):
    widget, MessageBox, checked, store = harness
    widget._combo_text_edited("Wo bist du?")
    # Qt kann bei Fokusverlust currentText() wieder auf das vorige Item setzen;
    # die letzte tatsächlich editierte Eingabe muss trotzdem erhalten bleiben.
    widget.example_combo.setEditText("Der Mann geht nach Hause.")
    widget.check_current_text()
    assert checked == ["Wo bist du?"]
    assert len(MessageBox.questions) == 1
    assert store.contains("Wo bist du?")
    assert widget.example_combo.currentText() == "Wo bist du?"


def test_user_declines_no_mutation_or_new_item(harness):
    widget, MessageBox, checked, store = harness
    MessageBox.answer = MessageBox.No
    widget._combo_text_edited("Satz ohne Speicherung!")
    widget.check_current_text()
    assert len(MessageBox.questions) == 1
    assert not store.path.exists()
    assert len(widget.example_combo.items) == 2


def test_invalid_grammar_still_can_be_saved_with_consent(harness):
    widget, MessageBox, checked, store = harness
    widget._run_check = lambda text: SimpleNamespace(valid=False, diagnostics=["Testfehler"])
    widget._combo_text_edited("Der Mann gehen nach Hause.")
    widget.check_current_text()
    assert len(MessageBox.questions) == 1
    assert "Testfehler" in MessageBox.questions[0][2]
    assert store.contains("Der Mann gehen nach Hause.")


def test_duplicate_does_not_prompt_and_selects_existing(harness):
    widget, MessageBox, checked, store = harness
    widget.input_edit.text = " der   MANN geht nach Hause. "
    widget._editor_text_edited()
    widget.check_current_text()
    assert not MessageBox.questions
    assert widget.example_combo.index == 0
    assert not store.path.exists()


def test_broken_user_json_never_overwritten(harness):
    widget, MessageBox, checked, store = harness
    store.path.parent.mkdir(parents=True, exist_ok=True)
    store.path.write_text('{"version": 1, "examples": not-json}', encoding="utf-8")
    before = store.path.read_bytes()
    widget._combo_text_edited("Neuer Satz")
    widget.check_current_text()
    assert not MessageBox.questions
    assert MessageBox.warnings
    assert store.path.read_bytes() == before


def test_empty_input_does_not_prompt(harness):
    widget, MessageBox, checked, store = harness
    widget.input_edit.text = "    "
    widget._editor_text_edited()
    widget.check_current_text()
    assert not MessageBox.questions
    assert MessageBox.notices
    assert checked == []


def test_dark_and_light_headers_and_dialog_wiring_exist():
    ui = Path(__file__).with_name("agent_0001.py").read_text(encoding="utf-8")
    for marker in (
        'self.token_table.verticalHeader().show()',
        'self.token_table.horizontalHeader()',
        'self.token_table.verticalHeader()',
        'header.setStyleSheet',
        'class _GrammarHeader(QHeaderView):',
        'def paintSection(self, painter, rect, logical_index):',
        'header.set_dark_mode(self._dark)',
        '"#303030", "#f5f5f5"',
        '"#e1e1e1", "#171717"',
        'self.input_edit.textChanged.connect(self._editor_text_edited)',
        'self.example_combo.lineEdit().textEdited.connect(self._combo_text_edited)',
        'self.check_button.clicked.connect(self.check_current_text)',
        'self.example_combo.lineEdit().returnPressed.connect(self.check_current_text)',
        'self.example_combo.setCurrentIndex(index)',
    ):
        assert marker in ui, marker


@pytest.mark.skipif(__import__('importlib').util.find_spec('PyQt5') is None,
                    reason='PyQt5 nicht vorhanden – native Qt-Tests nur unter Windows/Qt')
def test_real_qt_entry_and_both_header_styles(tmp_path, monkeypatch):
    import os
    os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
    from PyQt5.QtWidgets import QApplication, QMessageBox
    from agent_0001 import GermanGrammarWidget
    app = QApplication.instance() or QApplication([])
    seed = tmp_path / 'seed.json'
    seed.write_text('{"version":1,"examples":[{"text":"Heute ist Sonntag."}]}', encoding='utf8')
    store = ExampleStore(tmp_path / 'example.json', seed)
    widget = GermanGrammarWidget(store=store)
    widget.set_dark_mode(True)
    assert widget.token_table.verticalHeader().isHidden() is False
    assert '#303030' in widget.token_table.horizontalHeader().styleSheet()
    assert '#303030' in widget.token_table.verticalHeader().styleSheet()
    monkeypatch.setattr(GermanGrammarWidget, '_show_grammar_dialog',
                        lambda self, *args, **kwargs: QMessageBox.Yes)
    widget.input_edit.setPlainText('Das ist ein neuer Satz.')
    widget.check_current_text()
    assert store.contains('Das ist ein neuer Satz.')
    assert widget.example_combo.currentIndex() == widget.example_combo.count() - 1
    widget.close()
