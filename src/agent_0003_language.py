# -*- coding: utf-8 -*-
"""DBF-III-Wortschatz und begrenzte deutschsprachige Bildfragen fuer Agent 0003.

Kein Anspruch auf generelles Sprachverstehen; die Grammatikpruefung kombiniert
Agent 0001 mit nachpruefbaren Satzmustern aus fragen.dbf.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
import re
import struct

from agent_0001_core import check_sentence


# Kompaktes Schema seit Stage 616: Wortart und Kasus nur aus L-Feldern.
DBF_WORD_FIELDS = (
    ('ID', 'N', 10), ('WORT', 'C', 40),
    ('SUBSTANTIV', 'L', 1), ('VERB', 'L', 1), ('ADJEKTIV', 'L', 1),
    ('SINGULAR', 'L', 1), ('PLURAL', 'L', 1),
    ('DER', 'L', 1), ('DIE', 'L', 1), ('DAS', 'L', 1),
    ('MALE', 'L', 1), ('FEMALE', 'L', 1), ('NEUTRUM', 'L', 1),
    ('NOMINATIV', 'L', 1), ('GENITIV', 'L', 1),
    ('DATIV', 'L', 1), ('AKKUSATIV', 'L', 1),
)
DBF_QUESTION_FIELDS = (('ID', 'N', 10), ('FRAGE', 'C', 110), ('ABSICHT', 'C', 20))


def _safe_bytes(value, field_type: str, length: int) -> bytes:
    if field_type == 'L':
        return b'T' if bool(value) else b'F'
    if field_type == 'N':
        return str(int(value or 0)).rjust(length).encode('ascii')[:length]
    text = str(value or '').encode('cp1252', errors='replace')[:length]
    return text.ljust(length, b' ')


def write_dbf(path: Path, fields, rows) -> None:
    """dBASE III+ ohne Fremdbibliotheken, char/number/logical, CP1252."""
    fields = list(fields)
    rows = list(rows)
    if any(len(name.encode('ascii')) > 10 for name, _, _ in fields):
        raise ValueError('DBF-Feldname maximal 10 ASCII-Bytes')
    record_size = 1 + sum(length for _, _, length in fields)
    header_size = 33 + 32 * len(fields)
    today = date.today()
    result = bytearray(32)
    result[0] = 3
    result[1:4] = bytes((today.year % 100, today.month, today.day))
    struct.pack_into('<IHH', result, 4, len(rows), header_size, record_size)
    result[29] = 0x03  # Windows-1252
    for name, kind, length in fields:
        fld = bytearray(32)
        fld[:len(name)] = name.encode('ascii')
        fld[11] = ord(kind)
        fld[16] = length
        result.extend(fld)
    result.append(0x0D)
    for row in rows:
        result.append(ord(' '))
        for name, kind, length in fields:
            result.extend(_safe_bytes(row.get(name, ''), kind, length))
    result.append(0x1A)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + '.tmp')
    try:
        temp.write_bytes(result)
        temp.replace(path)
    finally:
        if temp.exists():
            temp.unlink()


def read_dbf(path: Path) -> list[dict]:
    """Leser fuer nicht geloeschte DBF-III-Datensaetze und C/N/L-Spalten."""
    buf = Path(path).read_bytes()
    if len(buf) < 33:
        raise ValueError(f'Ungültige DBF-Datei: {path}')
    count, head, size = struct.unpack_from('<IHH', buf, 4)
    if not 33 <= head <= len(buf) or size < 2:
        raise ValueError(f'DBF-Kopf beschädigt: {path}')
    fields = []
    offset = 1
    for pos in range(32, head - 1, 32):
        if buf[pos] == 0x0d: break
        name = buf[pos:pos + 11].split(b'\0', 1)[0].decode('ascii')
        kind = chr(buf[pos + 11])
        length = buf[pos + 16]
        fields.append((name, kind, offset, length))
        offset += length
    if offset > size:
        raise ValueError('DBF-Felddefinition ist länger als ein Datensatz')
    result = []
    for index in range(count):
        pos = head + index * size
        if pos + size > len(buf):
            raise ValueError('Abgeschnittene DBF-Datensätze')
        row = buf[pos:pos + size]
        if row[0] == 0x2a:
            continue
        current = {}
        for name, kind, start, length in fields:
            val = row[start:start + length].decode('cp1252', errors='replace').strip()
            if kind == 'L': current[name] = val.upper() in ('T', 'Y', 'J')
            elif kind == 'N': current[name] = int(val) if val.lstrip('-').isdigit() else 0
            else: current[name] = val
        result.append(current)
    return result


SHAPES = {
    'kreis': 'kreis', 'kreise': 'kreis', 'kreisen': 'kreis',
    'dreieck': 'dreieck', 'dreiecke': 'dreieck', 'dreiecken': 'dreieck',
    'rechteck': 'rechteck', 'rechtecke': 'rechteck', 'rechtecken': 'rechteck',
    'quadrat': 'quadrat', 'quadrate': 'quadrat', 'quadraten': 'quadrat',
    'polygon': 'polygon', 'polygone': 'polygon', 'polygonen': 'polygon',
    'figur': 'figur', 'figuren': 'figur', 'form': 'figur', 'formen': 'figur',
}
COLORS = {
    'rot': 'rot', 'rote': 'rot', 'roter': 'rot', 'roten': 'rot', 'rotem': 'rot', 'rotes': 'rot',
    'blau': 'blau', 'blaue': 'blau', 'blauer': 'blau', 'blauen': 'blau', 'blaues': 'blau',
    'grün': 'grün', 'grüne': 'grün', 'grüner': 'grün', 'grünen': 'grün', 'grünes': 'grün',
    'gelb': 'gelb', 'gelbe': 'gelb', 'gelber': 'gelb', 'gelben': 'gelb', 'gelbes': 'gelb',
    'orange': 'orange', 'oranger': 'orange', 'orangen': 'orange',
    'schwarz': 'schwarz', 'schwarze': 'schwarz', 'schwarzer': 'schwarz', 'schwarzen': 'schwarz',
    'weiß': 'weiß', 'weiße': 'weiß', 'weißer': 'weiß', 'weißen': 'weiß',
    'violett': 'violett', 'violette': 'violett', 'violetter': 'violett',
    'grau': 'grau', 'graue': 'grau', 'grauer': 'grau', 'grauen': 'grau',
}

QUESTION_PATTERNS = (
    ('wo befindet sich der {farbe} {form}', 'position'),
    ('wo befindet sich die {farbe} {form}', 'position'),
    ('wo befindet sich das {farbe} {form}', 'position'),
    ('wo ist der {farbe} {form}', 'position'),
    ('wo ist das {farbe} {form}', 'position'),
    ('wo ist die {farbe} {form}', 'position'),
    ('wo sind die {farbe} {form}', 'position'),
    ('wo befindet sich der {form}', 'position'),
    ('wo befindet sich die {form}', 'position'),
    ('wo befindet sich das {form}', 'position'),
    ('wo ist der {form}', 'position'),
    ('wo ist das {form}', 'position'),
    ('wo ist die {form}', 'position'),
    ('welcher {form} ist {farbe}', 'farbe'),
    ('welche {form} sind {farbe}', 'farbe'),
    ('welches {form} ist {farbe}', 'farbe'),
    ('zeige mir alle {form}', 'zeigen'),
    ('zeige mir die {farbe} {form}', 'zeigen'),
    ('zeige mir den {farbe} {form}', 'zeigen'),
    ('zeige mir alle {farbe} {form}', 'zeigen'),
    ('wie viele {form} sind im bild', 'anzahl'),
    ('wie viele {farbe} {form} sind im bild', 'anzahl'),
    ('wie viele {form} gibt es', 'anzahl'),
    ('welche farbe hat der {form}', 'farbfrage'),
    ('welche farbe hat das {form}', 'farbfrage'),
)


# Kuratierte, inhaltlich zu Bildfragen passende Basisformen (keine automatisch
# behauptete 10.000-Wort-Vollstaendigkeitsliste).
NOUN_FORMS = {
    'kreis': ('kreise', 'der'), 'dreieck': ('dreiecke', 'das'),
    'rechteck': ('rechtecke', 'das'), 'quadrat': ('quadrate', 'das'),
    'polygon': ('polygone', 'das'), 'figur': ('figuren', 'die'),
    'form': ('formen', 'die'), 'farbe': ('farben', 'die'),
    'bild': ('bilder', 'das'), 'stelle': ('stellen', 'die'),
    'position': ('positionen', 'die'), 'anzahl': ('anzahlen', 'die'),
    'linie': ('linien', 'die'), 'punkt': ('punkte', 'der'),
    'fläche': ('flächen', 'die'), 'winkel': ('winkel', 'der'),
    'seite': ('seiten', 'die'), 'ecke': ('ecken', 'die'),
    'kantenlänge': ('kantenlängen', 'die'), 'mitte': ('mitten', 'die'),
    'hintergrund': ('hintergründe', 'der'), 'vordergrund': ('vordergründe', 'der'),
    'bildschirm': ('bildschirme', 'der'), 'grafik': ('grafiken', 'die'),
    'objekt': ('objekte', 'das'), 'element': ('elemente', 'das'),
    'ausschnitt': ('ausschnitte', 'der'), 'auswahl': ('auswahlen', 'die'),
    'bilddatei': ('bilddateien', 'die'), 'umriss': ('umrisse', 'der'),
    'kontur': ('konturen', 'die'), 'pixel': ('pixel', 'das'),
    'breite': ('breiten', 'die'), 'höhe': ('höhen', 'die'),
    'größe': ('größen', 'die'), 'abstand': ('abstände', 'der'),
    'richtung': ('richtungen', 'die'), 'seite': ('seiten', 'die'),
    'beschreibung': ('beschreibungen', 'die'), 'antwort': ('antworten', 'die'),
    'frage': ('fragen', 'die'), 'satz': ('sätze', 'der'), 'wort': ('wörter', 'das'),
    'substantiv': ('substantive', 'das'), 'verb': ('verben', 'das'),
    'adjektiv': ('adjektive', 'das'), 'grammatik': ('grammatiken', 'die'),
    'sprache': ('sprachen', 'die'), 'fehler': ('fehler', 'der'),
    'text': ('texte', 'der'), 'datensatz': ('datensätze', 'der'),
}
VERB_FORMS = {
    'sein': ('bin', 'bist', 'ist', 'sind', 'seid', 'war', 'waren'),
    'haben': ('habe', 'hast', 'hat', 'habt'),
    'zeigen': ('zeige', 'zeigst', 'zeigt', 'zeigen', 'zeig'),
    'befinden': ('befinde', 'befindest', 'befindet', 'befinden'),
    'erkennen': ('erkenne', 'erkennst', 'erkennt', 'erkennen'),
    'zeichnen': ('zeichne', 'zeichnest', 'zeichnet', 'zeichnen'),
    'laden': ('lade', 'lädst', 'lädt', 'laden'),
    'prüfen': ('prüfe', 'prüfst', 'prüft', 'prüfen'),
    'lesen': ('lese', 'liest', 'lesen'),
    'schreiben': ('schreibe', 'schreibst', 'schreibt', 'schreiben'),
    'sehen': ('sehe', 'siehst', 'sieht', 'sehen'),
    'liegen': ('liege', 'liegst', 'liegt', 'liegen'),
    'stehen': ('stehe', 'stehst', 'steht', 'stehen'),
    'finden': ('finde', 'findest', 'findet', 'finden'),
    'suchen': ('suche', 'suchst', 'sucht', 'suchen'),
    'geben': ('gebe', 'gibst', 'gibt', 'geben'),
    'zählen': ('zähle', 'zählst', 'zählt', 'zählen'),
    'fragen': ('frage', 'fragst', 'fragt', 'fragen'),
    'antworten': ('antworte', 'antwortest', 'antwortet', 'antworten'),
}
FUNCTION_WORDS = {
    'Fragewort': ('wo','was','welcher','welche','welches','welchen','welchem','wie','warum','wer','wen'),
    'Artikel': ('der','die','das','den','dem','des','ein','eine','eines','einer','einen'),
    'Pronomen': ('ich','du','er','sie','es','wir','ihr','mich','dich','mir','dir','uns'),
    'Präposition': ('in','im','am','an','auf','unter','über','neben','hinter','vor','mit','bei','von','zu'),
    'Adverb': ('links','rechts','oben','unten','mittig','hier','dort','dahin','alle','auch','nur'),
    'Konjunktion': ('und','oder','aber','weil','dass','denn'),
    'Adjektiv': tuple(sorted(COLORS)),
}


def base_word_rows() -> list[dict]:
    entries = {}
    def add(wort, kind, lemma=None, singular=False, plural=False, article=''):
        word = wort.casefold()
        if not word: return
        # Vorhandene detaillierte Wortarten beim Zusammenfuehren vorziehen.
        if word in entries and entries[word]['SUBSTANTIV']:
            return
        entries[word] = dict(
            WORT=word, SUBSTANTIV=(kind == 'Substantiv'),
            VERB=(kind == 'Verb'), ADJEKTIV=(kind == 'Adjektiv'),
            SINGULAR=singular, PLURAL=plural,
            DER=(article == 'der'), DIE=(article == 'die'), DAS=(article == 'das'),
            MALE=(article == 'der'), FEMALE=(article == 'die'),
            NEUTRUM=(article == 'das'),
            NOMINATIV=(singular or plural), GENITIV=plural,
            DATIV=False, AKKUSATIV=(singular or plural),
        )
    for lemma, (plural, article) in NOUN_FORMS.items():
        add(lemma, 'Substantiv', lemma, singular=True, article=article)
        add(plural, 'Substantiv', lemma, plural=True, article=article)
    for lemma, forms in VERB_FORMS.items():
        add(lemma, 'Verb')
        for form in forms:
            add(form, 'Verb', lemma)
    for kind, words in FUNCTION_WORDS.items():
        for form in words:
            add(form, kind, COLORS.get(form) if kind == 'Adjektiv' else None)
    return [dict(item, ID=i+1) for i, item in enumerate(entries.values())]


def ensure_agent_databases(directory: Path) -> tuple[Path, Path]:
    directory = Path(directory)
    words = directory / 'woerter.dbf'
    questions = directory / 'fragen.dbf'
    if not words.is_file():
        write_dbf(words, DBF_WORD_FIELDS, base_word_rows())
    if not questions.is_file():
        rows = [dict(ID=i+1, FRAGE=pattern, ABSICHT=intent)
                for i, (pattern, intent) in enumerate(QUESTION_PATTERNS)]
        write_dbf(questions, DBF_QUESTION_FIELDS, rows)
    return words, questions


@dataclass(frozen=True)
class Query:
    intent: str
    shape: str | None
    color: str | None
    sentence: str


def _normalized(text: str) -> str:
    return ' '.join(re.findall(r'[a-zäöüß]+', str(text).casefold()))


def _regex_pattern(template: str) -> re.Pattern:
    parts = []
    tokens = re.split(r'(\{farbe\}|\{form\})', _normalized_template(template))
    for part in tokens:
        if part == '{farbe}':
            parts.append(r'(?P<farbe>[a-zäöüß]+)')
        elif part == '{form}':
            parts.append(r'(?P<form>[a-zäöüß]+)')
        elif part:
            parts.append(re.escape(part).replace(r'\ ', r'\s+'))
    return re.compile(r'^' + ''.join(parts) + r'$')


def _normalized_template(template: str) -> str:
    return ' '.join(re.findall(r'\{(?:farbe|form)\}|[a-zäöüß]+', str(template).casefold()))


class LanguageEngine:
    def __init__(self, word_path: Path, question_path: Path):
        self.words = {str(row.get('WORT', '')).casefold(): row
                      for row in read_dbf(word_path) if row.get('WORT')}
        self.questions = [(str(row['FRAGE']), str(row['ABSICHT']),
                           _regex_pattern(row['FRAGE']))
                          for row in read_dbf(question_path) if row.get('FRAGE')]

    def inspect(self, text: str):
        analysis = check_sentence(text)
        tokens = []
        for token in analysis.tokens:
            entry = self.words.get(token.text.casefold())
            if entry:
                # Keine redundante WORTART-/KASUS-Spalte: nur L-Felder auswerten.
                if entry.get('SUBSTANTIV'):
                    kind = 'Substantiv'
                elif entry.get('VERB'):
                    kind = 'Verb'
                elif entry.get('ADJEKTIV'):
                    kind = 'Adjektiv'
                else:
                    kind = next((name for name, forms in FUNCTION_WORDS.items()
                                 if token.text.casefold() in forms), 'Wort')
                number = ''.join((' / Singular' if entry.get('SINGULAR') else '',
                                  ' / Plural' if entry.get('PLURAL') else ''))
                category = kind + number
            else:
                category = token.category + (' (nicht im DBF)' if token.text.isalpha() else '')
            tokens.append((token.index, token.text, category))
        question = self.match_question(text)
        diagnostics = list(analysis.diagnostics)
        if question is None and text.strip():
            diagnostics.append('Keine passende Bildfrage in fragen.dbf; nur Basis-Grammatikprüfung möglich.')
        if question is not None and not diagnostics:
            diagnostics.append('Satzmuster erkannt; Grammatik im Rahmen der Bildfragen plausibel.')
        return analysis, tokens, question, diagnostics

    def match_question(self, text: str) -> Query | None:
        cleaned = _normalized(text)
        for template, intent, rx in self.questions:
            match = rx.fullmatch(cleaned)
            if not match:
                continue
            groups = match.groupdict()
            shape = SHAPES.get(groups.get('form', '')) if groups.get('form') else None
            color = COLORS.get(groups.get('farbe', '')) if groups.get('farbe') else None
            if ('form' in groups and not shape) or ('farbe' in groups and not color):
                continue
            return Query(intent, shape, color, template)
        return None

    def answer(self, text: str, figures, width: int, height: int):
        from agent_0003_core import figure_position
        question = self.match_question(text)
        if question is None:
            return 'Satz nicht als unterstützte Bildfrage erkannt.', []
        selected = [f for f in figures if
                    (not question.shape or question.shape == 'figur' or
                     f.kind == question.shape or
                     (question.shape == 'rechteck' and f.kind == 'quadrat')) and
                    (not question.color or f.color == question.color)]
        if question.intent == 'anzahl':
            return f'Anzahl erkannter passender Figuren: {len(selected)}', selected
        if question.intent == 'farbe':
            if not question.color:
                return 'Die Frage enthält keine eindeutige Farbangabe.', []
            return (f'Ja, {len(selected)} passende {question.shape or "Figuren"} '
                    f'sind {question.color}.' if selected else
                    f'Nein, keine passende {question.shape or "Figur"} '
                    f'ist als {question.color} erkannt.'), selected
        if not selected:
            return 'Keine passende Figur im geladenen Bild gefunden.', []
        if question.intent == 'position':
            lines = [f'{f.color} {f.label}: {figure_position(f, width, height)} (x={f.center[0]}, y={f.center[1]})'
                     for f in selected]
            return '\n'.join(lines), selected
        if question.intent == 'farbfrage':
            return '; '.join(f'{f.label}: {f.color}' for f in selected), selected
        return f'{len(selected)} passende Figur(en) gefunden.', selected
