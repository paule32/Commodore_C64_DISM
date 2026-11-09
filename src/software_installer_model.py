"""Stage 553: Qt-unabhaengiges Datenmodell fuer den Software-Installer-Editor.

Dies ist eine Bearbeitungsoberflaeche; das Modell baut noch kein Setup-Programm.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List

INSTALLER_REGISTRY_FILENAME = "software_installer_projects.json"

INSTALLER_COLUMNS = (
    "Name", "Ziel", "Lokaler Pfad", "Größe", "Datum",
    "Datei Version", "Status", "Package", "Short Cut",
)

INSTALLER_GROUPS = (
    ("Dateien", (
        "Datei hinzufügen", "Pfad hinzufügen", "Elemente Löschen", "Datei Eigenschaften",
    )),
    ("Einstellungen", (
        "Session Variable", "Hintergrund Fenster", "Benötigte Resourcen",
        "Log-Datei", "Sicherheit", "Packages", "Sprachen",
    )),
    ("Bildschirme", (
        "Projekt Theme", "Vor der Installation", "Während der Installation",
        "Nach der Installation",
    )),
    ("Aktionen", (
        "OnStartup", "OnPreInstall", "OnInstallError", "OnPostInstall",
    )),
)

INSTALLER_FILTERS = (
    ("Alle Elemente", "all"),
    ("Nur Archiv", "archive"),
    ("Nur Extern", "external"),
    ("Vorhandene Dateien", "exists"),
    ("Fehlende Dateien", "missing"),
)


def entry_visible(filter_key: str, tab_key: str, status: str) -> bool:
    """Filter fuer beide Tabellen: Typ-Filter wechselt Tab, Status filtert Zeilen."""
    if filter_key in ("archive", "external"):
        return filter_key == tab_key
    if filter_key == "exists":
        return status.casefold() == "vorhanden"
    if filter_key == "missing":
        return status.casefold() == "fehlt"
    return True


@dataclass
class InstallerEntry:
    name: str = ""
    target: str = ""
    local_path: str = ""
    size: str = ""
    date: str = ""
    file_version: str = ""
    status: str = "Neu"
    package: str = ""
    shortcut: str = ""

    @classmethod
    def from_path(cls, value: str, target: str = "") -> "InstallerEntry":
        path = Path(value)
        status = "Vorhanden" if path.exists() else "Fehlt"
        size = ""
        date = ""
        try:
            info = path.stat()
            size = str(info.st_size) if path.is_file() else "<DIR>"
            date = datetime.fromtimestamp(info.st_mtime).strftime("%Y-%m-%d %H:%M")
        except OSError:
            pass
        return cls(name=path.name, target=target, local_path=str(path),
                   size=size, date=date, status=status)

    def values(self) -> tuple[str, ...]:
        return (
            self.name, self.target, self.local_path, self.size, self.date,
            self.file_version, self.status, self.package, self.shortcut,
        )

    def update_from_values(self, values) -> None:
        if len(values) != len(INSTALLER_COLUMNS):
            raise ValueError("Ungültige Anzahl Installer-Tabellenspalten")
        for attr, value in zip(
            ("name", "target", "local_path", "size", "date", "file_version",
             "status", "package", "shortcut"), values
        ):
            setattr(self, attr, str(value))


@dataclass
class InstallerProject:
    entries: Dict[str, List[InstallerEntry]] = field(
        default_factory=lambda: {"archive": [], "external": []}
    )
    sections: Dict[str, str] = field(default_factory=dict)
    general: Dict[str, str] = field(default_factory=dict)
    name: str = "Unbenannt"

    def add_paths(self, tab_key: str, paths) -> int:
        if tab_key not in self.entries:
            raise ValueError("Unbekannter Installer-Tab")
        existing = {str(e.local_path).casefold() for e in self.entries[tab_key]
                    if e.local_path}
        count = 0
        for value in paths:
            path = str(Path(value))
            if path.casefold() in existing:
                continue
            self.entries[tab_key].append(InstallerEntry.from_path(path))
            existing.add(path.casefold())
            count += 1
        return count

    def delete_rows(self, tab_key: str, rows) -> int:
        entries = self.entries[tab_key]
        indices = sorted({int(n) for n in rows if 0 <= int(n) < len(entries)}, reverse=True)
        for index in indices:
            del entries[index]
        return len(indices)

    def to_dict(self) -> dict:
        return {
            "format": "d64-software-installer",
            "version": 1,
            "archive": [asdict(e) for e in self.entries["archive"]],
            "external": [asdict(e) for e in self.entries["external"]],
            "sections": dict(self.sections),
            "general": dict(self.general),
            "name": self.name,
        }

    @classmethod
    def from_dict(cls, document: dict) -> "InstallerProject":
        if not isinstance(document, dict) or document.get("format") != "d64-software-installer":
            raise ValueError("Ungültiges Software-Installer-Projekt")
        if document.get("version") != 1:
            raise ValueError("Unbekannte Software-Installer-Projektversion")
        result = cls()
        for key in ("archive", "external"):
            rows = document.get(key, [])
            if not isinstance(rows, list):
                raise ValueError("Ungültige Tabelleneinträge")
            result.entries[key] = [InstallerEntry(**row) for row in rows]
        sections = document.get("sections", {})
        if not isinstance(sections, dict):
            raise ValueError("Ungültige Einstellungen")
        result.sections = {str(k): str(v) for k, v in sections.items()}
        general = document.get("general", {})
        if not isinstance(general, dict):
            raise ValueError("Ungueltige Wizard-Projekteinstellungen")
        result.general = {str(k): str(v) for k, v in general.items()}
        result.name = str(document.get("name", "Unbenannt") or "Unbenannt")
        return result

    def save(self, filename: str) -> None:
        """Atomar schreiben, damit ein Abbruch die letzte Version nicht loescht."""
        path = Path(filename)
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", dir=str(path.parent),
                prefix=path.name + ".", suffix=".tmp", delete=False,
            ) as handle:
                temporary = Path(handle.name)
                json.dump(self.to_dict(), handle, ensure_ascii=False, indent=2)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, path)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)

    @classmethod
    def load(cls, filename: str) -> "InstallerProject":
        return cls.from_dict(json.loads(Path(filename).read_text(encoding="utf-8")))


def installer_registry_path(executable: str | Path | None = None) -> Path:
    """Globale Projektliste neben der IDE-EXE, im Quellbetrieb neben d64_dism.py."""
    if executable is not None:
        base = Path(executable).expanduser().resolve()
    elif getattr(sys, "frozen", False):
        base = Path(sys.executable).resolve()
    elif sys.argv and sys.argv[0] and Path(sys.argv[0]).is_file():
        base = Path(sys.argv[0]).resolve()
    else:
        base = Path(__file__).resolve().parent / "d64_dism.py"
    return base.parent / INSTALLER_REGISTRY_FILENAME


class InstallerProjectRegistry:
    """Atomar gespeicherte, projektuebergreifende Liste der Installer-Dateien."""

    def __init__(self, filename: str | Path | None = None):
        self.filename = Path(filename) if filename is not None else installer_registry_path()

    def read(self) -> list[dict]:
        if not self.filename.exists():
            return []
        data = json.loads(self.filename.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or data.get("format") != "d64-installer-project-registry":
            raise ValueError("Ungueltige Installer-Projektliste")
        if data.get("version") != 1 or not isinstance(data.get("projects"), list):
            raise ValueError("Unbekanntes Format der Installer-Projektliste")
        return [entry for entry in data["projects"] if isinstance(entry, dict)
                and isinstance(entry.get("path"), str)]

    def available(self) -> list[dict]:
        """Nur tatsaechlich vorhandene Projektdateien im Dialog anzeigen."""
        return [entry for entry in self.read() if Path(entry["path"]).is_file()]

    def register(self, filename: str | Path, project: InstallerProject) -> None:
        path = str(Path(filename).expanduser().resolve())
        projects = [entry for entry in self.read()
                    if str(entry["path"]).casefold() != path.casefold()]
        projects.insert(0, {
            "name": str(project.name or Path(path).stem),
            "path": path,
            "settings": project.to_dict(),
            "saved_at": datetime.now().isoformat(timespec="seconds"),
        })
        self.filename.parent.mkdir(parents=True, exist_ok=True)
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", dir=str(self.filename.parent),
                prefix=self.filename.name + ".", suffix=".tmp", delete=False,
            ) as handle:
                temporary = Path(handle.name)
                json.dump({"format": "d64-installer-project-registry", "version": 1,
                           "projects": projects}, handle, ensure_ascii=False, indent=2)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, self.filename)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
