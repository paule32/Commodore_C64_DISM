# -*- coding: utf-8 -*-
"""Regelbasierte Text->Form-Assoziationen für Agent 0002 (ohne Qt).

Kein allgemeines Sprachmodell. Nur sicher erkannte geometrische Begriffe
werden als Grafik ausgegeben; mehrdeutige Sätze bleiben ohne Zuordnung.
"""
from __future__ import annotations

from dataclasses import dataclass
import re

from agent_0002_logic import (check_geometric_consistency,
                              find_property_for_shape)

_WORD = re.compile(r"[A-Za-zÄÖÜäöüßẞ]+(?:-[A-Za-zÄÖÜäöüßẞ]+)*|\d+|[^\w\s]", re.UNICODE)
_CIRCLE = re.compile(r"\bkreis(?:e|es|en)?\b", re.IGNORECASE)
_TRIANGLE = re.compile(r"\bdreieck(?:e|es|en)?\b", re.IGNORECASE)
_NEGATION = re.compile(r"\b(?:kein(?:e|en|em|er|es)?|nicht|ohne)\b", re.IGNORECASE)
_QUESTION = re.compile(r"^\s*(?:was\s+ist|wie\s+sieht|wie\s+ist)\b", re.IGNORECASE)
_COMMAND = re.compile(r"^\s*(?:zeige|zeig|zeichne|male|darstelle|erstelle)\b", re.IGNORECASE)

DEFAULT_EXAMPLES = (
    "Was ist ein Kreis?",
    "Wie sieht ein Kreis aus?",
    "Zeige mir ein Dreieck",
)


@dataclass(frozen=True)
class AssociationResult:
    text: str
    shape: str | None       # "kreis", "dreieck" oder None
    intent: str             # fragen, zeichnen, beschreiben, unbekannt
    message: str
    tokens: tuple[str, ...]
    logic_status: str = "nicht_geprüft"
    logic_property: str | None = None


def recognize_association(text: str) -> AssociationResult:
    source = " ".join(str(text).split())
    tokens = tuple(_WORD.findall(source))
    if not source:
        return AssociationResult(source, None, "unbekannt",
                                 "Bitte einen Satz eingeben.", tokens)
    circle = bool(_CIRCLE.search(source))
    triangle = bool(_TRIANGLE.search(source))
    if circle and triangle:
        return AssociationResult(source, None, "mehrdeutig",
                                 "Mehrere Formen genannt: bitte Kreis oder Dreieck auswählen.", tokens)
    if not circle and not triangle:
        return AssociationResult(source, None, "unbekannt",
                                 "Keine bekannte geometrische Form erkannt. Unterstützt: Kreis, Dreieck.", tokens)
    if _NEGATION.search(source):
        return AssociationResult(source, None, "mehrdeutig",
                                 "Verneinte Formbeschreibung: keine Zeichnung erzeugt.", tokens)
    # Der Parser kennt nur klare Fragen, Befehle und einfache Beschreibungen.
    if _COMMAND.match(source):
        intent = "zeichnen"
    elif _QUESTION.match(source) or source.endswith("?"):
        intent = "fragen"
    else:
        intent = "beschreiben"
    shape = "kreis" if circle else "dreieck"
    adjective = find_property_for_shape(source, shape)
    if adjective:
        logic = check_geometric_consistency(adjective, shape)
        if logic.status != "vereinbar":
            # Im Zweifel keine grafische Behauptung bei bekanntem Adjektiv:
            # 'widerspruch', 'unbekannt' und 'fehler' sind getrennte Zustände.
            return AssociationResult(source, None, intent, logic.explanation,
                                     tokens, logic.status, adjective)
        caption = logic.explanation
        return AssociationResult(source, shape, intent, caption, tokens,
                                 "vereinbar", adjective)
    if circle:
        return AssociationResult(
            source, "kreis", intent,
            "Kreis erkannt: Alle Randpunkte haben denselben Abstand vom Mittelpunkt.",
            tokens)
    return AssociationResult(
        source, "dreieck", intent,
        "Dreieck erkannt: Eine geometrische Figur mit drei Seiten und drei Ecken.",
        tokens)
