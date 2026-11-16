# -*- coding: utf-8 -*-
"""Persistente Beispieltexte von Agent 0001, direkt neben dem Programm.

In einer eingefrorenen EXE: <EXE-Ordner>/data/agent_0001_example.json.
Beim Python-Quellstart: <Modulordner>/data/agent_0001_example.json.
Ein nicht schreibbares Programmverzeichnis führt bewusst zu einer Meldung.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
import tempfile
import unicodedata

SCHEMA_VERSION = 1
DATA_FILENAME = "agent_0001_example.json"
DEFAULT_EXAMPLES = (
    "Was ist heute für ein Tag?",
    "Heute ist für ein Tag?",
    "Welcher Tag ist heute?",
    "Wo du wohnst?",
    "Der Mann gehen nach Hause.",
)
MAX_SENTENCE_LENGTH = 800


class ExampleStoreError(ValueError):
    """Fehler beim Lesen oder Validieren der JSON-Beispielsätze."""


def normalize_text(value: str) -> str:
    if not isinstance(value, str):
        raise ExampleStoreError("Ein Beispielsatz muss ein Text sein.")
    cleaned = " ".join(unicodedata.normalize("NFC", value).split())
    if not cleaned:
        raise ExampleStoreError("Bitte zuerst einen Text eingeben.")
    if len(cleaned) > MAX_SENTENCE_LENGTH:
        raise ExampleStoreError(
            f"Text zu lang (maximal {MAX_SENTENCE_LENGTH} Zeichen)."
        )
    return cleaned


def _key(text: str) -> str:
    return normalize_text(text).casefold()


def application_directory() -> Path:
    """Nicht aus CWD oder sys._MEIPASS ableiten: Daten neben der EXE."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def default_user_path() -> Path:
    """Historischer API-Name, nun bewusst in das lokale data-Verzeichnis."""
    return application_directory() / "data" / DATA_FILENAME


def legacy_user_path() -> Path:
    """Nur für einmalige Übernahme, wenn der neue Datenbestand noch fehlt."""
    if os.name == "nt":
        appdata = os.environ.get("APPDATA")
        base = Path(appdata) if appdata else Path.home() / "AppData" / "Roaming"
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
    return base / "d64_dism" / "agent_0001_examples.json"


class ExampleStore:
    def __init__(self, path=None, seed_path=None):
        self._local_data = path is None
        self.path = Path(path) if path is not None else default_user_path()
        self.seed_path = (
            Path(seed_path) if seed_path is not None
            else Path(__file__).resolve().parent / "data" / DATA_FILENAME
        )

    @staticmethod
    def _decode(raw):
        if not isinstance(raw, dict):
            raise ExampleStoreError("Die JSON-Wurzel muss ein Objekt sein.")
        if raw.get("version") != SCHEMA_VERSION:
            raise ExampleStoreError("Unbekannte Version der Beispiele-JSON-Datei.")
        entries = raw.get("examples")
        if not isinstance(entries, list):
            raise ExampleStoreError("'examples' muss eine Liste sein.")
        output = []
        used = set()
        for entry in entries:
            if isinstance(entry, str):
                text = entry  # auch ältere einfache String-Listen akzeptieren
            elif isinstance(entry, dict) and isinstance(entry.get("text"), str):
                text = entry["text"]
            else:
                raise ExampleStoreError("Einträge müssen Texte oder Objekte mit 'text' sein.")
            text = normalize_text(text)
            if _key(text) not in used:
                output.append(text)
                used.add(_key(text))
        return output

    @staticmethod
    def _read_path(path: Path):
        try:
            with path.open("r", encoding="utf-8-sig") as stream:
                raw = json.load(stream)
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise ExampleStoreError(f"Ungültige JSON-Datei: {path}: {exc}") from exc
        except OSError as exc:
            raise ExampleStoreError(f"JSON-Datei nicht lesbar: {path}: {exc}") from exc
        return ExampleStore._decode(raw)

    def load(self):
        if self.path.is_file():
            # Neue JSON ist die maßgebliche Datei. Beim erstmaligen Start der
            # Stage 575 liegt dort u.U. nur die mitgelieferte Beispielsammlung.
            current = self._read_path(self.path)
            if (self._local_data and
                    {_key(item) for item in current} ==
                    {_key(item) for item in DEFAULT_EXAMPLES} and
                    len(current) == len(DEFAULT_EXAMPLES)):
                previous = legacy_user_path()
                if previous.is_file() and previous.resolve() != self.path.resolve():
                    legacy = self._read_path(previous)
                    existing = {_key(item) for item in current}
                    additional = [item for item in legacy if _key(item) not in existing]
                    if additional:
                        current.extend(additional)
                        self._write(current)
            return current
        if self._local_data:
            # Alte benutzereigene Beispielsätze vorziehen, wenn das neue
            # data-Verzeichnis bisher keine JSON besitzt.
            previous = legacy_user_path()
            if previous.is_file():
                examples = self._read_path(previous)
            elif self.seed_path.is_file():
                examples = self._read_path(self.seed_path)
            else:
                examples = list(DEFAULT_EXAMPLES)
            self._write(examples)
            return examples
        if self.seed_path.is_file():
            return self._read_path(self.seed_path)
        return []

    def contains(self, text: str) -> bool:
        key = _key(text)
        return any(_key(entry) == key for entry in self.load())

    def _write(self, texts):
        data = {
            "version": SCHEMA_VERSION,
            "examples": [{"text": text} for text in texts],
        }
        tempname = None
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", suffix=".tmp",
                prefix="agent_0001_", dir=str(self.path.parent),
                delete=False,
            ) as output:
                tempname = output.name
                json.dump(data, output, indent=2, ensure_ascii=False)
                output.write("\n")
                output.flush()
                os.fsync(output.fileno())
            os.replace(tempname, self.path)
        except OSError as exc:
            if tempname and os.path.isfile(tempname):
                try:
                    os.unlink(tempname)
                except OSError:
                    pass
            raise ExampleStoreError(f"Beispiele konnten nicht gespeichert werden: {exc}") from exc

    def add(self, text: str) -> bool:
        cleaned = normalize_text(text)
        texts = self.load()  # Vor jedem Speichern neu lesen, um Änderungen nicht zu verlieren.
        if _key(cleaned) in {_key(existing) for existing in texts}:
            return False
        texts.append(cleaned)
        self._write(texts)
        return True

    def save_all(self, texts):
        checked = self._decode({
            "version": SCHEMA_VERSION,
            "examples": list(texts),
        })
        self._write(checked)
