# -*- coding: utf-8 -*-
"""Stage 577: Agent 0002 mit d64prolog-geometrischer Semantik."""
from __future__ import annotations

import ast
from pathlib import Path
import importlib.util
import pytest

from d64prolog import KnowledgePredicate, PrologKnowledgeBase
from agent_0002_core import recognize_association
from agent_0002_logic import (adjective_lemma, check_geometric_consistency,
                              find_property_for_shape, knowledge_path)

ROOT = Path(__file__).resolve().parent
PL = ROOT / 'data' / 'agent_0002_geometrie.pl'


def test_knowledge_file_and_existing_prolog_resolver():
    assert PL.exists()
    kb = PrologKnowledgeBase.from_file(PL)
    def query(p, a, b):
        return kb.accepts(KnowledgePredicate(p, 2),
                          [kb.parse_value(a), kb.parse_value(b)])
    assert query('widerspruch', 'quadratisch', 'kreis')
    assert query('widerspruch', 'dreieckig', 'kreis')
    assert query('widerspruch', 'rund', 'quadrat')
    assert not query('widerspruch', 'rund', 'kreis')
    assert query('vereinbar', 'rund', 'kreis')
    assert query('vereinbar', 'quadratisch', 'quadrat')
    assert not query('vereinbar', 'quadratisch', 'kreis')


@pytest.mark.parametrize('word,expected', [
    ('quadratisch', 'quadratisch'), ('quadratischen','quadratisch'),
    ('Quadratischer','quadratisch'), ('dreieckiges','dreieckig'),
    ('runden','rund'), ('kreisförmigen','kreisfoermig'),
    ('kreisfoermige','kreisfoermig'), ('normalen',None),
])
def test_adjective_lemma(word, expected):
    assert adjective_lemma(word) == expected


@pytest.mark.parametrize('sentence,shape,expected', [
    ('Zeige einen quadratischen Kreis.', 'kreis', 'quadratisch'),
    ('zeige quadratischen kreis', 'kreis', 'quadratisch'),
    ('Ein Kreis ist quadratisch.', 'kreis', 'quadratisch'),
    ('Ein quadratisches Blatt neben einem Kreis', 'kreis', None),
    ('Zeige einen runden Kreis.', 'kreis', 'rund'),
    ('Zeige ein dreieckiges Dreieck.', 'dreieck', 'dreieckig'),
    ('Zeige einen Kreis.', 'kreis', None),
])
def test_contextual_property_detection(sentence, shape, expected):
    assert find_property_for_shape(sentence, shape) == expected


@pytest.mark.parametrize('sentence,shape,status', [
    ('Zeige einen quadratischen Kreis', None, 'widerspruch'),
    ('zeige quadratischen kreis', None, 'widerspruch'),
    ('Wie sieht ein quadratischer Kreis aus?', None, 'widerspruch'),
    ('Zeige einen dreieckigen Kreis', None, 'widerspruch'),
    ('Zeige einen runden Kreis', 'kreis', 'vereinbar'),
    ('Zeige ein dreieckiges Dreieck', 'dreieck', 'vereinbar'),
    ('Was ist ein Kreis?', 'kreis', 'nicht_geprüft'),
    ('Wie sieht ein Kreis aus?', 'kreis', 'nicht_geprüft'),
    ('Zeige mir ein Dreieck', 'dreieck', 'nicht_geprüft'),
])
def test_associations(sentence, shape, status):
    result = recognize_association(sentence)
    assert result.shape == shape
    assert result.logic_status == status
    if status == 'widerspruch':
        assert 'Logischer Widerspruch' in result.message
        assert 'Keine Zeichnung' in result.message


def test_missing_kb_fails_closed(tmp_path):
    result = check_geometric_consistency('quadratisch','kreis',
                                         path=tmp_path/'missing.pl')
    assert result.status == 'fehler'
    assert 'Wissensbasis' in result.explanation


def test_corrupt_kb_fails_closed(tmp_path):
    path = tmp_path / 'kb.pl'
    path.write_text('widerspruch(quadratisch, kreis', encoding='utf8')
    result = check_geometric_consistency('quadratisch','kreis',path=path)
    assert result.status == 'fehler'


def test_no_rule_is_not_proof_of_correctness(tmp_path):
    path = tmp_path/'kb.pl'
    path.write_text('form(kreis).\n', encoding='utf8')
    result = check_geometric_consistency('quadratisch','kreis',path=path)
    assert result.status == 'unbekannt'


def test_conflicting_kb_does_not_claim_valid(tmp_path):
    path = tmp_path/'kb.pl'
    path.write_text('widerspruch(quadratisch, kreis).\n'
                    'vereinbar(quadratisch, kreis).\n', encoding='utf8')
    assert check_geometric_consistency('quadratisch','kreis',path=path).status == 'fehler'


def test_unchecked_syntax_is_not_injected():
    assert check_geometric_consistency('X):-true','kreis').status == 'unbekannt'
    assert check_geometric_consistency('quadratisch','X).').status == 'unbekannt'


def test_preserved_unrelated_behavior():
    a = recognize_association('Was ist ein Kreis und ein Dreieck?')
    assert a.shape is None and a.intent == 'mehrdeutig'
    b = recognize_association('Zeige mir kein Dreieck')
    assert b.shape is None and b.intent == 'mehrdeutig'
    c = recognize_association('Was ist ein Quader?')
    assert c.shape is None and c.intent == 'unbekannt'
    # Ein Adjektiv, das sich nur auf das Blatt bezieht, darf keinen Fehler zum Kreis auslösen.
    d = recognize_association('Ein quadratisches Blatt neben einem Kreis')
    assert d.shape == 'kreis' and d.logic_status == 'nicht_geprüft'


def test_program_directory_kb_name():
    assert knowledge_path().name == 'agent_0002_geometrie.pl'
    assert knowledge_path().parent.name == 'data'


def test_ui_integration_without_runtime_qt():
    src = (ROOT/'agent_0002.py').read_text(encoding='utf8')
    ast.parse(src)
    assert 'self.canvas.set_association(association)' in src
    assert '" | Prolog: " + association.logic_status' in src
    assert 'Logische Prüfung (d64prolog)' in src
    assert 'adjective_lemma(token.text)' in src
    # Der Bug der vorherigen Stage darf nicht wiederkehren.
    assert 'from agent_0001 import _GrammarHeader' not in src
    assert 'def set_dark_mode(self, enabled):' in src


@pytest.mark.skipif(importlib.util.find_spec('PyQt5') is None, reason='PyQt5 nicht installiert')
def test_qt_no_drawing_on_contradiction(monkeypatch):
    monkeypatch.setenv('QT_QPA_PLATFORM', 'offscreen')
    from PyQt5.QtWidgets import QApplication
    from agent_0002 import GermanAssociationWidget
    app = QApplication.instance() or QApplication([])
    widget = GermanAssociationWidget()
    widget._run_analysis('Zeige einen quadratischen Kreis')
    assert widget.canvas.shape is None
    assert 'widerspruch' in widget.result_label.text().lower()
    assert 'Logischer Widerspruch' in widget.diagnostics.toPlainText()
    widget._run_analysis('Was ist ein Kreis?')
    assert widget.canvas.shape == 'kreis'
    for dark in (True, False):
        widget.set_dark_mode(dark)
    widget.close()
