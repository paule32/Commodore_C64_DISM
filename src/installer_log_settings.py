"""Projekt-Einstellungen für den Installer-Dialog „Log-Datei" (Stage 565).

Dies speichert zunächst nur die Konfiguration. Die spätere Setup-Laufzeit
interpretiert die Platzhalter und entscheidet über das Schreiben der Logdatei.
"""
from __future__ import annotations

import json

LOG_FILE_SECTION = "Log-Datei"
LOG_FILE_VERSION = 1
LOG_FILE_DEFAULTS = {
    "enabled": False,
    "filename": r"%TempFolder%\%ProductName% Setup Log.txt",
    "write_mode": "append",
}


def validate_log_settings(values):
    """Validiert und ergänzt ein vollständiges Einstellungs-Dictionary."""
    if not isinstance(values, dict):
        raise ValueError("Ungültige Log-Datei-Einstellungen")
    extras = set(values) - set(LOG_FILE_DEFAULTS)
    if extras:
        raise ValueError("Unbekannte Log-Datei-Einstellungen: " + ", ".join(sorted(extras)))
    result = dict(LOG_FILE_DEFAULTS)
    result.update(values)
    if type(result["enabled"]) is not bool:
        raise ValueError("'Log-Datei anlegen' muss ein Wahrheitswert sein")
    filename = result["filename"]
    if not isinstance(filename, str):
        raise ValueError("Der Dateiname muss Text sein")
    if (len(filename) > 4096 or "\x00" in filename or "\n" in filename or "\r" in filename):
        raise ValueError("Ungültiger Log-Dateiname")
    result["filename"] = filename.strip()
    if result["enabled"] and not result["filename"]:
        raise ValueError("Bitte einen Dateinamen für die Log-Datei angeben")
    if result["write_mode"] not in ("append", "overwrite"):
        raise ValueError("Ungültiger Schreibmodus; erlaubt sind Anhängen und Überschreiben")
    return result


def parse_log_settings(raw):
    """Leerer Projektabschnitt nutzt Standardwerte; beschädigte Daten melden Fehler."""
    if not raw or not raw.strip():
        return validate_log_settings({})
    document = json.loads(raw)
    if not isinstance(document, dict) or document.get("version") != LOG_FILE_VERSION:
        raise ValueError("Unbekanntes Log-Datei-Format")
    return validate_log_settings(document.get("settings"))


def encode_log_settings(values):
    return json.dumps({"version": LOG_FILE_VERSION,
                       "settings": validate_log_settings(values)},
                      ensure_ascii=False, indent=2)
