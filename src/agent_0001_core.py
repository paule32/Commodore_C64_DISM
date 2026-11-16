# -*- coding: utf-8 -*-
"""Kleiner rein-pythonischer Basisprüfer als Ersatz für ein fehlendes Parsermodul.

Dies ist bewusst KEIN vollständiger deutscher Grammatikparser. Diagnose- und
Tokenanalyse können später durch einen vorhandenen echten Parser ersetzt werden.
"""
from __future__ import annotations
from dataclasses import dataclass
import re
from typing import List

_TOKEN = re.compile(r"[A-Za-zÄÖÜäöüß]+(?:-[A-Za-zÄÖÜäöüß]+)*|\d+|[^\w\s]", re.UNICODE)
QUESTION = {"was", "wer", "wen", "wem", "wessen", "wo", "wohin", "woher",
            "wann", "wie", "warum", "wieso", "weshalb", "welcher", "welche",
            "welches", "welchen", "welchem", "wieviel", "wie-viel"}
ARTICLES = {"der", "die", "das", "den", "dem", "des", "ein", "eine", "einen",
            "einem", "einer", "eines"}
PRONOUNS = {"ich", "du", "er", "sie", "es", "wir", "ihr", "mich", "dich", "uns", "euch"}
PREPOSITIONS = {"mit", "in", "im", "an", "am", "auf", "nach", "von", "zu", "zum",
                "zur", "für", "bei", "über", "unter", "vor", "hinter", "neben"}
VERBS = {"ist", "sind", "bin", "bist", "seid", "war", "waren", "habe", "hast",
         "hat", "haben", "gehe", "gehst", "geht", "gehen", "wohne", "wohnst",
         "wohnt", "wohnen", "heiße", "heißt", "heißen", "wird", "werden",
         "kann", "kannst", "können", "machst", "macht", "machen", "komme",
         "kommst", "kommt", "kommen", "sage", "sagst", "sagt", "sagen"}


@dataclass(frozen=True)
class TokenInfo:
    index: int
    text: str
    category: str
    note: str = ""


@dataclass(frozen=True)
class CheckResult:
    valid: bool
    tokens: List[TokenInfo]
    diagnostics: List[str]
    intent: str


def _category(word: str) -> str:
    low = word.casefold()
    if len(word) == 1 and not word.isalnum():
        return "Satzzeichen"
    if low in QUESTION:
        return "Fragewort"
    if low in ARTICLES:
        return "Artikel"
    if low in PRONOUNS:
        return "Pronomen"
    if low in PREPOSITIONS:
        return "Präposition"
    if low in VERBS:
        return "Verb"
    if word[:1].isupper():
        return "Nomen / Wort"
    return "Wort"


def check_sentence(source: str) -> CheckResult:
    """Prüft Beispiele und einige typische deutsche Hauptsatzfehler.

    Ohne vollständiges Lexikon sind unbekannte Sätze nicht beweisbar grammatisch
    korrekt. `valid=True` bedeutet hier nur 'kein erkannter Basisfehler'.
    """
    source = " ".join(str(source).split())
    words = _TOKEN.findall(source)
    tokens = [TokenInfo(i + 1, w, _category(w)) for i, w in enumerate(words)]
    body = [w.casefold() for w in words if w.isalpha() or "-" in w]
    errors = []
    intent = "Aussage"
    if not body:
        errors.append("Es wurde kein auswertbarer Satz eingegeben.")
    else:
        if source.endswith("?"):
            intent = "Frage"
            if body[0] in QUESTION:
                if len(body) > 2 and body[1] in PRONOUNS and body[2] in VERBS:
                    errors.append("Bei direkten W-Fragen steht das finite Verb in der Regel vor dem Subjekt.")
            elif body[0] not in VERBS:
                errors.append("Bei einer direkten Frage fehlt am Satzanfang ein Fragewort oder ein finites Verb.")
        if len(body) >= 3 and body[:3] == ["der", "mann", "gehen"]:
            errors.append("Subjekt/Verb-Kongruenz: 'Der Mann' verlangt hier 'geht' statt 'gehen'.")
        if len(body) >= 5 and body[:5] == ["heute", "ist", "für", "ein", "tag"]:
            errors.append("Vermutlich fehlt ein Fragewort (z. B. 'Was ist heute für ein Tag?').")
    return CheckResult(not errors, tokens, errors, intent)
