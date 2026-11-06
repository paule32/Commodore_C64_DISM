"""Agent 0001: kleiner, erweiterbarer regelbasierter Grammatikparser (Deutsch).

Kein Vollparser der deutschen Sprache. Unbekannte Konstruktionen werden explizit
als 'nicht_erkannt' gemeldet und nicht fälschlich als grammatisch falsch.
Keine Abhängigkeiten außerhalb der Python-Standardbibliothek.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional, Sequence

TOKEN_RE = re.compile(r"[A-Za-zÄÖÜäöüßẞ]+|\d+|[^\s]", re.UNICODE)

# Die Merkmale gelten für die *Form*, nicht bloß für den Verbstamm.
# (Lemma, Person, Numerus)
VERBS = {
    "bin": ("sein", 1, "sg"), "bist": ("sein", 2, "sg"),
    "ist": ("sein", 3, "sg"), "sind": ("sein", 3, "pl"),
    "seid": ("sein", 2, "pl"),
    "gehe": ("gehen", 1, "sg"), "gehst": ("gehen", 2, "sg"),
    "geht": ("gehen", 3, "sg"), "gehen": ("gehen", 3, "pl"),
    "wohne": ("wohnen", 1, "sg"), "wohnst": ("wohnen", 2, "sg"),
    "wohnt": ("wohnen", 3, "sg"), "wohnen": ("wohnen", 3, "pl"),
    "mache": ("machen", 1, "sg"), "machst": ("machen", 2, "sg"),
    "macht": ("machen", 3, "sg"), "machen": ("machen", 3, "pl"),
    "lese": ("lesen", 1, "sg"), "liest": ("lesen", 3, "sg"),
    "lest": ("lesen", 2, "pl"), "lesen": ("lesen", 3, "pl"),
    "schlafe": ("schlafen", 1, "sg"), "schläfst": ("schlafen", 2, "sg"),
    "schläft": ("schlafen", 3, "sg"), "schlafen": ("schlafen", 3, "pl"),
    "habe": ("haben", 1, "sg"), "hast": ("haben", 2, "sg"),
    "hat": ("haben", 3, "sg"), "haben": ("haben", 3, "pl"),
}
# Synkretismus: manche Formen sind auch mit 'wir' kompatibel.
PLURAL_WIR_FORMS = {"sind", "gehen", "wohnen", "machen", "lesen", "schlafen", "haben"}
PRONOUNS = {
    "ich": (1, "sg"), "du": (2, "sg"), "er": (3, "sg"),
    "sie": (3, "amb"), "es": (3, "sg"), "wir": (1, "pl"),
    "ihr": (2, "pl"),
}
NOUNS = {
    "tag": ("m", "sg"), "monat": ("m", "sg"),
    "feiertag": ("m", "sg"), "mann": ("m", "sg"),
    "frau": ("f", "sg"), "kind": ("n", "sg"),
    "kinder": ("n", "pl"), "buch": ("n", "sg"),
    "hund": ("m", "sg"), "hunde": ("m", "pl"),
    "unterricht": ("m", "sg"),
}
DETERMINERS = {
    "der", "die", "das", "ein", "eine", "einen", "einem", "einer",
    "den", "dem", "des",
}
TIME_WORDS = {"heute", "morgen", "gestern", "jetzt"}
QUESTION_WORDS = {"was", "wer", "wo", "wann", "wie", "warum", "welcher", "welche", "welches"}
OTHERS = {
    "für": "Präposition", "nach": "Präposition", "zu": "Präposition",
    "hause": "Nomen/Adverb", "spät": "Adjektiv",
    "müde": "Adjektiv", "schön": "Adjektiv", "krank": "Adjektiv",
    "gut": "Adjektiv", "schnell": "Adjektiv",
    "einkaufen": "Infinitiv", "nicht": "Negation",
    "und": "Konjunktion",
}


@dataclass(frozen=True)
class Token:
    text: str
    norm: str
    start: int
    end: int
    part_of_speech: str


@dataclass(frozen=True)
class Diagnostic:
    code: str
    message: str
    position: Optional[int] = None


@dataclass(frozen=True)
class ParseResult:
    status: str                 # korrekt | fehlerhaft | nicht_erkannt
    sentence_kind: str
    intent: Optional[str]
    tokens: tuple[Token, ...]
    diagnostics: tuple[Diagnostic, ...]
    suggestion: Optional[str] = None

    @property
    def is_valid(self) -> bool:
        return self.status == "korrekt"


def tokenize(sentence: str) -> tuple[Token, ...]:
    tokens = []
    for match in TOKEN_RE.finditer(sentence):
        word = match.group(0)
        lower = word.casefold()
        if lower in VERBS:
            pos = "Verb (finit)"
        elif lower in PRONOUNS:
            pos = "Pronomen"
        elif lower in QUESTION_WORDS:
            pos = "Fragewort"
        elif lower in TIME_WORDS:
            pos = "Zeitadverb"
        elif lower in DETERMINERS:
            pos = "Artikel"
        elif lower in NOUNS:
            pos = "Nomen"
        elif lower in OTHERS:
            pos = OTHERS[lower]
        elif word in ".?!,;:":
            pos = "Satzzeichen"
        else:
            pos = "Unbekannt"
        tokens.append(Token(word, lower, match.start(), match.end(), pos))
    return tuple(tokens)


def _result(status: str, kind: str, tokens: Sequence[Token],
            message: str, code: str, *, intent: Optional[str] = None,
            suggestion: Optional[str] = None, position: Optional[int] = None) -> ParseResult:
    return ParseResult(status, kind, intent, tuple(tokens),
                       (Diagnostic(code, message, position),), suggestion)


def _subject(words: Sequence[str], offset: int):
    """Liefert (Person, Numerus, nächster Index); nur kleine NP-Teilgrammatik."""
    if offset >= len(words):
        return None
    w = words[offset]
    if w in PRONOUNS:
        return (*PRONOUNS[w], offset + 1)
    if w in DETERMINERS and offset + 1 < len(words):
        noun = words[offset + 1]
        if noun in NOUNS:
            gender, number = NOUNS[noun]
            if number == "pl" and w == "die":
                return (3, "pl", offset + 2)
            if number == "sg" and (
                (gender == "m" and w in ("der", "ein")) or
                (gender == "f" and w in ("die", "eine")) or
                (gender == "n" and w in ("das", "ein"))
            ):
                return (3, "sg", offset + 2)
    return None


def _conjugation_matches(verb: str, subject: tuple[int, str, int]) -> bool:
    person, num, _ = subject
    actual_person, actual_num = VERBS[verb][1:]
    if num == "pl" and person == 1 and verb in PLURAL_WIR_FORMS:
        return True
    # "sie" kann feminin Singular oder Plural (auch höfliches "Sie") sein.
    if num == "amb" and person == 3:
        return actual_person == 3 and actual_num in ("sg", "pl")
    return (person, num) == (actual_person, actual_num)


def _validate_subject_verb(verb: str, subject: tuple[int, str, int],
                           tokens: Sequence[Token], verb_index: int, sentence: str,
                           kind: str, intent: Optional[str] = None):
    if _conjugation_matches(verb, subject):
        return _result("korrekt", kind, tokens, "Satzmuster und Verbform erkannt.",
                       "OK", intent=intent)
    return _result("fehlerhaft", kind, tokens,
                   f"Verbform '{verb}' stimmt nicht mit Person/Numerus des Subjekts überein.",
                   "E_KONGRUENZ", position=tokens[verb_index].start)


def _recognize_was_fuer(words: list[str], tokens: Sequence[Token], sentence: str):
    if not words or words[0] != "was" or "für" not in words:
        return None
    fi = words.index("für")
    if fi + 2 >= len(words) or words[fi + 1] not in DETERMINERS:
        return _result("fehlerhaft", "Was-für-Frage", tokens,
                       "Nach 'für' wird hier eine Artikel-Nomen-Gruppe erwartet.",
                       "E_FRAGEGRUPPE", position=tokens[fi].start)
    if words[fi + 2] not in NOUNS:
        return _unknown(tokens)
    # Was ist heute für ein Tag? / Was ist morgen für ein Feiertag?
    if fi >= 3 and words[1] == "ist" and all(w in TIME_WORDS for w in words[2:fi]) and fi + 3 == len(words):
        return _result("korrekt", "Was-für-Frage (getrennt)", tokens,
                       "Zusammengehörige Teile 'was' und 'für ein ...' erkannt.",
                       "OK", intent="ask_day_type")
    # Was für ein Tag ist heute?
    if fi == 1 and len(words) >= 6 and words[fi + 3] == "ist" and \
       all(w in TIME_WORDS for w in words[fi + 4:]):
        return _result("korrekt", "Was-für-Frage (zusammen)", tokens,
                       "Zusammenhängende Fragegruppe 'was für ein ...' erkannt.",
                       "OK", intent="ask_day_type")
    if len(words) >= 3 and words[1] in TIME_WORDS:
        return _result("fehlerhaft", "Was-für-Frage", tokens,
                       "Bei dieser direkten Frage muss die finite Verbform an zweiter Stelle stehen.",
                       "E_WORTSTELLUNG", position=tokens[1].start)
    return _unknown(tokens)


def parse_sentence(sentence: str) -> ParseResult:
    """Analysiert ausgewählte deutsche Hauptsatz-/Fragemuster.

    'nicht_erkannt' ist bewusst von 'fehlerhaft' getrennt: Der Parser behauptet
    bei fehlender Regel keine Aussage über grammatische Korrektheit.
    """
    tokens = tokenize(sentence)
    if not tokens:
        return _result("nicht_erkannt", "-", tokens,
                       "Bitte einen deutschen Satz eingeben.", "W_LEER")
    punctuation = tokens[-1].text if tokens[-1].text in ("?", ".", "!") else ""
    content = tokens[:-1] if punctuation else tokens
    words = [t.norm for t in content]
    if not words:
        return _result("nicht_erkannt", "-", tokens,
                       "Der Text enthält keine Wörter.", "W_LEER")

    # Präziser Fehler für das Nutzerbeispiel, ohne jede 'für'-Phrase zu verbieten.
    if (len(words) == 5 and words[0] in TIME_WORDS and words[1] == "ist"
            and words[2:4] == ["für", "ein"] and words[4] in NOUNS
            and punctuation == "?"):
        return _result("fehlerhaft", "Was-für-Frage", tokens,
                       "Das einleitende Fragewort 'Was' fehlt bei 'für ein ...'.",
                       "E_FRAGEWORT", suggestion="Was ist " + words[0] + " für ein " +
                       content[4].text + "?", position=content[2].start)

    if words[0] == "was" and "für" in words:
        parsed = _recognize_was_fuer(words, tokens, sentence)
        if parsed is not None:
            if punctuation != "?" and parsed.is_valid:
                return _result("fehlerhaft", parsed.sentence_kind, tokens,
                               "Eine direkte Frage endet mit '?'.", "E_SATZZEICHEN",
                               suggestion=sentence.rstrip(". !") + "?")
            return parsed

    # Welcher Tag ist heute? / Welcher Monat ist heute?
    if (len(words) == 4 and words[0] in ("welcher", "welche", "welches")
            and words[1] in NOUNS and words[2] == "ist" and words[3] in TIME_WORDS):
        if words[0] != {"m": "welcher", "f": "welche", "n": "welches"}[NOUNS[words[1]][0]]:
            return _result("fehlerhaft", "Welcher-Frage", tokens,
                           "Das Fragewort stimmt im Genus nicht mit dem Nomen überein.",
                           "E_GENUS", position=content[0].start)
        return _result("korrekt", "Welcher-Frage", tokens,
                       "Frage nach einer Zeitbezeichnung erkannt.", "OK", intent="ask_day") \
            if punctuation == "?" else _result(
                "fehlerhaft", "Welcher-Frage", tokens,
                "Eine direkte Frage endet mit '?'.", "E_SATZZEICHEN")

    # Wie spät ist es?
    if words == ["wie", "spät", "ist", "es"]:
        return _result("korrekt", "Wie-Frage", tokens,
                       "Frage nach der Uhrzeit erkannt.", "OK", intent="ask_time") \
            if punctuation == "?" else _result(
                "fehlerhaft", "Wie-Frage", tokens,
                "Fragezeichen fehlt.", "E_SATZZEICHEN")

    # W-Frage: Wo wohnst du? / Was machst du heute?
    if words[0] in QUESTION_WORDS:
        if len(words) > 1 and words[1] not in VERBS:
            if words[1] not in (set(PRONOUNS) | TIME_WORDS | DETERMINERS):
                return _unknown(tokens)
            return _result("fehlerhaft", "W-Frage", tokens,
                           "In einer direkten W-Frage steht das finite Verb hier an zweiter Stelle.",
                           "E_VERBSTELLUNG", position=content[1].start)
        if len(words) >= 3 and words[1] in VERBS:
            subject = _subject(words, 2)
            if subject is not None:
                result = _validate_subject_verb(words[1], subject, tokens, 1,
                                                sentence, "W-Frage", "question")
                if result.is_valid and punctuation != "?":
                    return _result("fehlerhaft", "W-Frage", tokens,
                                   "Fragezeichen fehlt.", "E_SATZZEICHEN")
                if result.is_valid and not _known_remainder(words, subject[2]):
                    return _unknown(tokens)
                return result

    # Ja/Nein-Frage: Ist heute ein Feiertag? / Bist du heute müde?
    if words[0] in VERBS and punctuation == "?":
        pos = 1
        while pos < len(words) and words[pos] in TIME_WORDS:
            pos += 1
        subject = _subject(words, pos)
        if subject is not None:
            if not _known_remainder(words, subject[2]):
                return _unknown(tokens)
            return _validate_subject_verb(words[0], subject, tokens, 0,
                                          sentence, "Ja/Nein-Frage", "yes_no_question")
        return _unknown(tokens)

    # Aussagesatz (Subjekt zuerst, danach finites Verb).
    subject = _subject(words, 0)
    if subject is not None:
        vi = subject[2]
        if vi >= len(words):
            return _result("fehlerhaft", "Aussagesatz", tokens,
                           "Nach dem Subjekt fehlt ein finites Verb.",
                           "E_VERBSTELLUNG")
        if words[vi] not in VERBS:
            if words[vi] not in (set(PRONOUNS) | TIME_WORDS | DETERMINERS):
                return _unknown(tokens)
            return _result("fehlerhaft", "Aussagesatz", tokens,
                           "Das finite Verb steht nicht an der erwarteten Position.",
                           "E_VERBSTELLUNG")
        if not _known_remainder(words, vi+1):
            return _unknown(tokens)
        return _validate_subject_verb(words[vi], subject, tokens, vi,
                                      sentence, "Aussagesatz", "statement")

    # Vorfeldadverb + Verb + Subjekt: Heute bin ich müde.
    if words[0] in TIME_WORDS:
        if len(words) < 2:
            return _result("fehlerhaft", "Aussagesatz", tokens,
                           "Nach dem vorangestellten Zeitadverb fehlt das finite Verb.",
                           "E_VERBZWEIT")
        if words[1] not in VERBS:
            if words[1] not in (set(PRONOUNS) | TIME_WORDS | DETERMINERS):
                return _unknown(tokens)
            return _result("fehlerhaft", "Aussagesatz", tokens,
                           "Nach dem vorangestellten Zeitadverb muss das finite Verb folgen.",
                           "E_VERBZWEIT", position=content[1].start)
        subject = _subject(words, 2)
        if subject is not None:
            if not _known_remainder(words, subject[2]):
                return _unknown(tokens)
            return _validate_subject_verb(words[1], subject, tokens, 1,
                                          sentence, "Aussagesatz", "statement")

    return _unknown(tokens)


def _known_remainder(words: Sequence[str], start: int) -> bool:
    """Die Restgrammatik ist begrenzt; bei Unsicherheit nicht 'gültig' behaupten."""
    for word in words[start:]:
        if word not in (TIME_WORDS | DETERMINERS | set(NOUNS) | set(OTHERS) | set(PRONOUNS)):
            return False
    return True


def _unknown(tokens: Sequence[Token]) -> ParseResult:
    return _result("nicht_erkannt", "nicht klassifiziert", tokens,
                   "Für diese Konstruktion gibt es noch keine ausreichend sichere Grammatikregel. "
                   "Das bedeutet nicht automatisch, dass der Satz falsch ist.",
                   "W_KEINE_REGEL")
