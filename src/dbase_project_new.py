# -*- coding: utf-8 -*-
"""Stage 431: Dateiauswahl, Basistemplates und sichere PRG-Textprüfung.

Qt-frei, damit die Projektdateilogik unabhängig von GUI-Tests geprüft werden kann.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

# Beschriftung, Ziel-Unterknoten, erlaubte Endungen, Standardname, Buildziel.
DBASE_NEW_MENU = (
    ("Neu:  Formular", "forms", (".wfm",), "Form1.wfm", ""),
    ("Neu:  Programm", "programs", (".prg",), "Programm1.prg", ""),
    ("Neu:  Tabelle", "tables", (".dbf",), "Tabelle1.dbf", ""),
    ("Neu:  Abfrage", "queries", (".d64sql",), "Abfrage1.d64sql", ""),
    ("Neu:  Bericht", "reports", (".d64report",), "Bericht1.d64report", ""),
    ("Neu:  Etikett", "labels", (".d64label",), "Etikett1.d64label", ""),
    ("Neu:  Windows PE32 Ressource", "resources", (".rc", ".res"), "Ressource32.rc", "pe32"),
    ("Neu:  Windows PE32+ Ressource", "resources", (".rc", ".res"), "Ressource64.rc", "pe64"),
)


# Stage 433: erster Kontextmenü-Eintrag am jeweiligen dBASE-Unterknoten.
# Tupelformat identisch zu DBASE_NEW_MENU, damit Dateidialog und Erzeugung
# den bereits implementierten, themenfähigen Workflow wiederverwenden.
# Der bisherige Hauptknoten (DBASE_NEW_MENU) bleibt unverändert.
DBASE_GROUP_NEW_MENU = {
    ("forms", ""): ("Neu:  Formular-Datei", "forms", (".wfm",), "Form1.wfm", ""),
    ("tables", ""): ("Neu:  Tabelle", "tables", (".dbf",), "Tabelle1.dbf", ""),
    ("queries", ""): ("Neu:  Abfrage Datei", "queries", (".d64sql",), "Abfrage1.d64sql", ""),
    ("reports", ""): ("Neu:  Bericht Datei", "reports", (".d64report",), "Bericht1.d64report", ""),
    ("labels", ""): ("Neu:  Etikett Datei", "labels", (".d64label",), "Etikett1.d64label", ""),
    ("archives", ""): ("Neu:  Archiv Datei", "archives", (".a",), "Archiv1.a", ""),
    ("resources", "pe32"): ("Neu:  Windows PE32 Ressource Datei", "resources", (".rc", ".res"), "Ressource32.rc", "pe32"),
    ("resources", "pe64"): ("Neu:  Windows PE32+ Ressource Datei", "resources", (".rc", ".res"), "Ressource64.rc", "pe64"),
}


def is_dbase_program_text(path: Path) -> bool:
    """Nur Text-PRGs zulassen, z. B. keine C64-PRG, UTF-16 oder EXE-Daten.

    Tab, Zeilenumbruch und Formfeed sind erlaubt, ebenso UTF-8- und ältere
    ANSI/OEM-Bytes >= 128. Alle ASCII-Steuerbytes und NUL sind ausgeschlossen.
    Die ganze Datei wird in kleinen Blöcken untersucht (nicht nur der Header).
    """
    path = Path(path)
    try:
        with path.open("rb") as stream:
            first = stream.read(4)
            if first.startswith((b"\x7fELF", b"PK\x03\x04", b"\xff\xfe", b"\xfe\xff")):
                return False
            stream.seek(0)
            while True:
                chunk = stream.read(65536)
                if not chunk:
                    break
                for value in chunk:
                    if value == 0x7f or (value < 32 and value not in (9, 10, 12, 13)):
                        return False
    except OSError:
        return False
    return True


def new_dbase_file_content(role: str, path: Path) -> str:
    """Startinhalt für textbasierte Designer; `.dbf` wird separat geschrieben."""
    name = Path(path).stem
    if role == "programs":
        return ""  # Ein neues, bewusst leeres dBASE-Quellprogramm.
    if role == "forms":
        class_name = re.sub(r"\W", "_", name)
        if not class_name or not re.match(r"[A-Za-z_]", class_name):
            class_name = "Form1"
        return f"CLASS {class_name} OF FORM\nENDCLASS\n"
    if role == "queries":
        data = {
            "format": "d64-sql-builder", "version": 8,
            "directory": str(Path(path).parent), "sql": "",
            "tables": [], "connections": [],
            "header_widths": {"relationship": [], "view": {}},
        }
    elif role == "reports":
        data = {
            "format": "d64-report-builder", "version": 5,
            "data_source": "", "page": {"format": "A4"},
            "bands": {}, "elements": [],
        }
    elif role == "labels":
        data = {
            "format": "d64-label-designer", "version": 1,
            "label": {"name": "60 × 40 mm", "width_mm": 60, "height_mm": 40},
            "elements": [], "layout": {},
        }
    elif role == "resources" and Path(path).suffix.casefold() == ".rc":
        return (
            "#define IDS_APP_TITLE 100\n\n"
            "LANGUAGE LANG_GERMAN, SUBLANG_GERMAN\n\n"
            "STRINGTABLE\nBEGIN\n"
            '    IDS_APP_TITLE "Anwendung"\n'
            "END\n"
        )
    else:
        raise ValueError(f"Für {role!r} kann kein leeres Dokument erzeugt werden.")
    return json.dumps(data, ensure_ascii=False, indent=2) + "\n"


def create_dbase_project_file(path: Path, role: str, *, table_writer=None) -> Path:
    """Erzeugt *nur bei Nichtvorhandensein* eine neue, lesbare Datei."""
    path = Path(path)
    if path.exists():
        raise FileExistsError(f"Datei existiert bereits: {path}")
    if role == "archives":
        # Leeres, gültiges ar-Archiv (auch für spätere COFF-Objekte).
        # Weder ein Textdokument mit .a-Endung noch ein externes Tool.
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as handle:
            handle.write(b"!<arch>\n")
    elif role == "tables":
        if table_writer is None:
            raise ValueError("DBF-Writer fehlt")
        table_writer(path)
    else:
        data = new_dbase_file_content(role, path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(data)
    return path


def can_open_dbase_project_file(path: Path) -> bool:
    """Prueft reale Lese-/Schreibzugriffe ohne die Datei zu veraendern.

    Rechtepruefung per tatsaechlichem Dateizugriff statt nur os.access(),
    das besonders unter Windows nicht alle ACL-Sonderfaelle abbildet.
    """
    path = Path(path)
    try:
        if not path.is_file():
            return False
        with path.open("rb"):
            pass
        with path.open("r+b"):
            pass
        return True
    except (OSError, ValueError):
        return False
