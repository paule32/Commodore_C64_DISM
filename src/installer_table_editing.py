"""Qt-unabhaengige Zeilen-Zwischenablage und Undo/Redo fuer Installer-Tabellen.

Stage 569: Die Datenansicht und die beiden Projekt-Tabellen nutzen dieselben
Operationen. Eine Projektspeicherung findet hier absichtlich nicht statt.
"""
from __future__ import annotations

from dataclasses import asdict
import csv
import io
import json

from software_installer_model import INSTALLER_COLUMNS, InstallerEntry

INSTALLER_ROW_MIME = "application/x-d64-installer-rows+json"
ENTRY_FIELDS = tuple(InstallerEntry.__dataclass_fields__)
MAX_TABLE_HISTORY = 100
MAX_PASTE_ROWS = 10000


def snapshot_rows(entries):
    """Wertkopie fuer History ohne gemeinsam genutzte InstallerEntry-Objekte."""
    return [asdict(entry) for entry in entries]


def entries_from_snapshot(snapshot):
    return [InstallerEntry(**row) for row in snapshot]


def rows_to_tsv(entries):
    """Textformat fuer Excel und andere Tabellen: alle neun Spalten."""
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, delimiter="\t", lineterminator="\r\n")
    writer.writerows(entry.values() for entry in entries)
    return stream.getvalue()


def rows_to_mime_json(entries):
    return json.dumps({"format": "d64-installer-rows", "version": 1,
                       "entries": snapshot_rows(entries)}, ensure_ascii=False).encode("utf-8")


def rows_from_clipboard(mime_json=None, text=""):
    """Internes verlustfreies Format bevorzugen, sonst TSV aus Fremdprogrammen.

    Bei fehlenden/ungueltigen Daten nicht still Daten verlieren, sondern
    ValueError ausloesen. Eine Textspalte wird als Name interpretiert.
    """
    if mime_json:
        try:
            document = json.loads(bytes(mime_json).decode("utf-8"))
        except (ValueError, UnicodeError, TypeError) as error:
            raise ValueError("Ungültiges Installer-Zwischenablageformat") from error
        if not isinstance(document, dict) or document.get("format") != "d64-installer-rows" or document.get("version") != 1:
            raise ValueError("Unbekanntes Installer-Zwischenablageformat")
        data = document.get("entries")
        if not isinstance(data, list) or len(data) > MAX_PASTE_ROWS:
            raise ValueError("Ungültige Anzahl einzufügender Zeilen")
        result = []
        for row in data:
            if not isinstance(row, dict) or set(row) != set(ENTRY_FIELDS) or any(not isinstance(v, str) for v in row.values()):
                raise ValueError("Ungültiger Installer-Datensatz in der Zwischenablage")
            result.append(InstallerEntry(**row))
        return result
    if not text:
        return []
    try:
        records = list(csv.reader(io.StringIO(text, newline=""), delimiter="\t"))
    except csv.Error as error:
        raise ValueError("Tabellendaten können nicht gelesen werden") from error
    if len(records) > MAX_PASTE_ROWS:
        raise ValueError("Zu viele einzufügende Tabellenzeilen")
    result = []
    for record in records:
        if not record or (len(record) == 1 and not record[0].strip()):
            continue
        if len(record) == 1:
            result.append(InstallerEntry(name=record[0]))
        elif len(record) == len(INSTALLER_COLUMNS):
            entry = InstallerEntry()
            entry.update_from_values(record)
            result.append(entry)
        else:
            raise ValueError("Die Zwischenablage muss 1 oder 9 Spalten je Zeile enthalten")
    return result


class InstallerTableHistory:
    """Getrennte Undo-/Redo-Verläufe fuer Archiv und Extern."""

    def __init__(self):
        self.clear()

    def clear(self):
        self._undo = {"archive": [], "external": []}
        self._redo = {"archive": [], "external": []}

    def can_undo(self, tab_key):
        return bool(self._undo[tab_key])

    def can_redo(self, tab_key):
        return bool(self._redo[tab_key])

    def record(self, tab_key, before, entries):
        after = snapshot_rows(entries)
        if before == after:
            return False
        history = self._undo[tab_key]
        history.append(before)
        if len(history) > MAX_TABLE_HISTORY:
            del history[0]
        self._redo[tab_key].clear()
        return True

    def undo(self, tab_key, entries):
        if not self.can_undo(tab_key):
            return None
        current = snapshot_rows(entries)
        previous = self._undo[tab_key].pop()
        self._redo[tab_key].append(current)
        return entries_from_snapshot(previous)

    def redo(self, tab_key, entries):
        if not self.can_redo(tab_key):
            return None
        current = snapshot_rows(entries)
        next_state = self._redo[tab_key].pop()
        self._undo[tab_key].append(current)
        return entries_from_snapshot(next_state)
