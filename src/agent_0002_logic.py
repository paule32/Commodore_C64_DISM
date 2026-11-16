# -*- coding: utf-8 -*-
"""Logische Geometrieprüfung für Agent 0002 mit dem vorhandenen d64prolog-Resolver.

Es wird ausschließlich eine begrenzte euklidische Geometrie-Wissensbasis
verwendet. Das Fehlen eines Beweises ist keine Bestätigung der Aussage.
Prolog-Atome stammen nur aus einer Whitelist, nicht aus freiem Benutzercode.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from agent_0001_data import application_directory
from d64prolog import (KnowledgePredicate, PrologKnowledgeBase,
                       PrologCompilerError)

KNOWLEDGE_FILENAME = "agent_0002_geometrie.pl"

# Flektierte Formen deutscher geometrischer Adjektive -> Prolog-Atome.
# Die Muster sind absichtlich eng: keine allgemeine Lemmatisierung behaupten.
_PROPERTY_PATTERNS = (
    ("quadratisch", re.compile(r"^quadratisch(?:e|er|es|en|em)?$", re.I)),
    ("dreieckig", re.compile(r"^dreieckig(?:e|er|es|en|em)?$", re.I)),
    ("rund", re.compile(r"^rund(?:e|er|es|en|em)?$", re.I)),
    ("kreisfoermig", re.compile(r"^kreisf(?:ö|oe)rmig(?:e|er|es|en|em)?$", re.I)),
)
_SHAPE_PATTERNS = {
    "kreis": r"kreis(?:e|es|en)?",
    "dreieck": r"dreieck(?:e|es|en)?",
    "quadrat": r"quadrat(?:e|es|en)?",
}
_WORD = r"[A-Za-zÄÖÜäöüßẞ]+"


@dataclass(frozen=True)
class LogicResult:
    status: str  # widerspruch | vereinbar | unbekannt | fehler
    property_name: str | None
    object_name: str | None
    explanation: str


def knowledge_path() -> Path:
    """Quellenstart: neben .py; EXE: im data-Verzeichnis neben der EXE."""
    return application_directory() / "data" / KNOWLEDGE_FILENAME


def adjective_lemma(word: str) -> str | None:
    for lemma, pattern in _PROPERTY_PATTERNS:
        if pattern.fullmatch(word.strip()):
            return lemma
    return None


def find_property_for_shape(sentence: str, shape: str) -> str | None:
    """Nur benachbarte Attribute oder einfache Kopulasätze sicher zuordnen.

    Bewusst keine pauschale Suche nach Adjektiven irgendwo im Satz; das
    würde etwa 'quadratisches Blatt neben einem Kreis' falsch zuordnen.
    """
    shape_pattern = _SHAPE_PATTERNS.get(shape)
    if not shape_pattern:
        return None
    adjective = r"(?:quadratisch|dreieckig|rund|kreisf(?:ö|oe)rmig)(?:e|er|es|en|em)?"
    forms = [
        # 'einen quadratischen Kreis', 'quadratischen Kreis'
        rf"\b(?P<property>{adjective})\s+(?:sehr\s+)?{shape_pattern}\b",
        # 'Der Kreis ist quadratisch', 'Kreis sieht quadratisch aus'
        rf"\b{shape_pattern}\s+(?:(?:ist|sei|wird)\s+|sieht\s+)(?P<property>{adjective})\b",
    ]
    for pattern in forms:
        match = re.search(pattern, sentence, re.I)
        if match:
            return adjective_lemma(match.group("property"))
    return None


def check_geometric_consistency(
    adjective: str,
    shape: str,
    *,
    path: Path | None = None,
) -> LogicResult:
    """SLD-Abfrage der Projekt-Prolog-Engine, ohne freie Goals zu akzeptieren.

    Nicht aus dem negativen Ergebnis von 'widerspruch' auf Wahrheit schließen:
    Dafür muss 'vereinbar' ebenfalls explizit beweisbar sein.
    """
    if adjective not in {entry[0] for entry in _PROPERTY_PATTERNS} or shape not in _SHAPE_PATTERNS:
        return LogicResult("unbekannt", adjective, shape,
                           "Für diese Eigenschaft/Form liegt keine sichere Regel vor.")
    source_path = Path(path) if path is not None else knowledge_path()
    try:
        kb = PrologKnowledgeBase.from_file(source_path)
        args = [kb.parse_value(adjective), kb.parse_value(shape)]
        contradiction = kb.accepts(KnowledgePredicate("widerspruch", 2), args)
        compatible = kb.accepts(KnowledgePredicate("vereinbar", 2), args)
    except (OSError, ValueError, RuntimeError, RecursionError, PrologCompilerError) as exc:
        return LogicResult("fehler", adjective, shape,
                           f"Prolog-Wissensbasis konnte nicht geprüft werden ({source_path.name}): {exc}")
    # Für beschädigte / unvollständige Regeln nicht widersprüchliche Antworten
    # als 'grün' durchreichen.
    if contradiction and compatible:
        return LogicResult("fehler", adjective, shape,
                           "Wissensbasis widersprüchlich: sowohl vereinbar als auch unvereinbar bewiesen.")
    if contradiction:
        name = "kreisförmig" if adjective == "kreisfoermig" else adjective
        return LogicResult("widerspruch", adjective, shape,
                           f"Logischer Widerspruch: '{name}' ist mit '{shape}' in der "
                           "euklidischen Geometrie nicht vereinbar "
                           "(unterschiedliche Eckenzahl). Keine Zeichnung erstellt.")
    if compatible:
        return LogicResult("vereinbar", adjective, shape,
                           f"Eigenschaft '{adjective}' und Form '{shape}' sind bezüglich "
                           "der in Prolog hinterlegten Eckenzahl vereinbar.")
    return LogicResult("unbekannt", adjective, shape,
                       "Aus den vorhandenen Prolog-Fakten lässt sich weder ein "
                       "Widerspruch noch eine Vereinbarkeit beweisen.")
