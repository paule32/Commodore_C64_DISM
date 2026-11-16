# -*- coding: utf-8 -*-
"""Stage 571 – JSON, Analyse und Qt-Stil-Regressionen."""
import json
from pathlib import Path
import pytest

from agent_0001_data import ExampleStore, ExampleStoreError, normalize_text
from agent_0001_core import check_sentence


@pytest.fixture
def store(tmp_path):
    seed = tmp_path / "vorlage.json"
    seed.write_text(json.dumps({"version": 1, "examples": [
        {"text": "Welcher Tag ist heute?"},
        {"text": "Was ist heute für ein Tag?"},
    ]}),encoding="utf-8")
    return ExampleStore(tmp_path / "settings" / "agent_0001_examples.json",seed)


def test_seed_read_without_file_creation(store):
    assert len(store.load()) == 2
    assert not store.path.exists()


def test_add_created_json_and_read_back(store):
    assert store.add("  Guten   Morgen!  ") is True
    data=json.loads(store.path.read_text(encoding="utf-8"))
    assert data["version"]==1
    assert data["examples"][-1]["text"]=="Guten Morgen!"
    assert len(ExampleStore(store.path,store.seed_path).load())==3


def test_duplicate_casefold_and_spacing_not_added(store):
    assert store.add("welcher   TAG ist heute?") is False
    assert not store.path.exists()


def test_corrupt_json_not_overwritten(store):
    store.path.parent.mkdir(parents=True)
    store.path.write_text('{"version":1,"examples":{bad}',encoding="utf-8")
    original = store.path.read_bytes()
    with pytest.raises(ExampleStoreError):
        store.add("Ein neuer Text.")
    assert store.path.read_bytes()==original


def test_malformed_structures_rejected(tmp_path):
    path=tmp_path / "examples.json"
    for raw in ([],{"version":2,"examples":[]},{"version":1,"examples":"x"},
                {"version":1,"examples":[{"x":"y"}]}):
        path.write_text(json.dumps(raw),encoding="utf-8")
        with pytest.raises(ExampleStoreError):
            ExampleStore(path).load()


def test_normalize_unicode_and_empty():
    assert normalize_text("  Grüß   dich  ")=="Grüß dich"
    with pytest.raises(ExampleStoreError):
        normalize_text(" \n ")


def test_expected_previous_grammar_examples():
    assert check_sentence("Was ist heute für ein Tag?").valid
    assert check_sentence("Welcher Tag ist heute?").valid
    assert not check_sentence("Heute ist für ein Tag?").valid
    assert not check_sentence("Wo du wohnst?").valid
    assert not check_sentence("Der Mann gehen nach Hause.").valid


def test_tokens_are_preserved():
    result=check_sentence("Wo du wohnst?")
    assert [t.text for t in result.tokens]==["Wo","du","wohnst","?"]
    assert result.intent=="Frage"


def test_main_application_hook_and_header_css():
    root=Path(__file__).resolve().parent
    src=(root / "d64_dism.py").read_text(encoding="utf-8")
    ui=(root / "agent_0001.py").read_text(encoding="utf-8")
    assert 'self.agent_0001_widget = GermanGrammarWidget(dock)' in src
    assert 'agent_set_theme(enabled)' in src
    # Stage 572: beide Header werden gemeinsam ueber die Header-Schleife gestaltet.
    assert 'class _GrammarHeader(QHeaderView)' in ui
    assert 'self.token_table.verticalHeader()' in ui
    assert 'QHeaderView::section' in ui
    assert 'self._show_grammar_dialog(' in ui
    assert 'self.store.add(text)' in ui


@pytest.mark.skipif(__import__('importlib').util.find_spec("PyQt5") is None,
                    reason="PyQt5 nicht installiert")
def test_qt_ui_smoke(store,monkeypatch):
    import os
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PyQt5.QtWidgets import QApplication, QMessageBox
    from agent_0001 import GermanGrammarWidget
    app=QApplication.instance() or QApplication([])
    w=GermanGrammarWidget(store=store)
    assert w.token_table.horizontalHeader().isVisible() is False or w.token_table.columnCount()==3
    w.set_dark_mode(True)
    assert '#303030' in w.token_table.horizontalHeader().styleSheet()
    w.example_combo.setEditText("Hallo Welt!")
    monkeypatch.setattr(GermanGrammarWidget, "_show_grammar_dialog",
                        lambda self, *args, **kwargs: QMessageBox.Yes)
    w.check_current_text()
    assert store.contains("Hallo Welt!")
    w.close()
