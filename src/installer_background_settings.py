"""Qt-unabhängige Konfiguration für den Installer-Dialog 'Hintergrund Fenster'.

Die Einstellungen werden als JSON im bestehenden InstallerProject.sections-Feld
'Hintergrund Fenster' abgelegt. Der Dialog arbeitet mit einer separaten Kopie,
sodass Abbrechen keine Projektänderung erzeugt.
"""
from __future__ import annotations

import json
import re

BACKGROUND_SECTION = "Hintergrund Fenster"
BACKGROUND_SCHEMA = 1

BACKGROUND_MODES = ("standard", "framed", "kiosk")
BACKGROUND_APPEARANCES = ("static", "gradient", "image")
BACKGROUND_ALIGNMENTS = ("left", "center", "right")

BACKGROUND_DEFAULTS = {
    "enabled": False,
    "mode": "standard",
    "appearance": "static",
    "static_color": "#20385f",
    "gradient_start": "#2f72d6",
    "gradient_end": "#ffffff",
    "image_path": "",
    "title_text": "%ProductName%",
    "title_font": "",
    "title_color": "#ffffff",
    "title_align": "center",
    "version_text": "%ProductVersion%",
    "version_font": "",
    "version_color": "#ffffff",
    "version_align": "center",
    "footer_text": "%Copyright% Alle Rechte vorbehalten.",
    "footer_font": "",
    "footer_color": "#ffffff",
}

_COLOR = re.compile(r"#[0-9a-fA-F]{6}\Z")


def validate_background_settings(settings: dict) -> dict:
    """Validiert Daten vor der Serialisierung bzw. nach dem Laden.

    Fehlende Schlüssel erhalten die dokumentierten Vorgaben. Zusätzliche
    Schlüssel sind für die Vorwärtskompatibilität nicht zulässig.
    """
    if not isinstance(settings, dict):
        raise ValueError("Ungültige Hintergrund-Fenster-Einstellungen")
    unknown = set(settings).difference(BACKGROUND_DEFAULTS)
    if unknown:
        raise ValueError("Unbekannte Hintergrund-Fenster-Einstellungen: " + ", ".join(sorted(unknown)))
    result = dict(BACKGROUND_DEFAULTS)
    result.update(settings)
    if not isinstance(result["enabled"], bool):
        raise ValueError("'Hintergrund Fenster anzeigen' muss ein Wahrheitswert sein")
    for field, options in (
        ("mode", BACKGROUND_MODES),
        ("appearance", BACKGROUND_APPEARANCES),
        ("title_align", BACKGROUND_ALIGNMENTS),
        ("version_align", BACKGROUND_ALIGNMENTS),
    ):
        if result[field] not in options:
            raise ValueError("Ungültige Auswahl für " + field)
    for field in ("static_color", "gradient_start", "gradient_end",
                  "title_color", "version_color", "footer_color"):
        color = result[field]
        if not isinstance(color, str) or not _COLOR.fullmatch(color):
            raise ValueError("Ungültige Farbe für " + field)
        result[field] = color.lower()
    for field in ("image_path", "title_text", "title_font", "version_text",
                  "version_font", "footer_text", "footer_font"):
        if not isinstance(result[field], str):
            raise ValueError("Ungültiger Text für " + field)
    return result


def parse_background_settings(source: str | None) -> dict:
    if not source or not source.strip():
        return dict(BACKGROUND_DEFAULTS)
    document = json.loads(source)
    if not isinstance(document, dict) or document.get("version") != BACKGROUND_SCHEMA:
        raise ValueError("Unbekanntes Hintergrund-Fenster-Format")
    settings = document.get("settings")
    return validate_background_settings(settings)


def encode_background_settings(settings: dict) -> str:
    return json.dumps({"version": BACKGROUND_SCHEMA,
                       "settings": validate_background_settings(settings)},
                      ensure_ascii=False, indent=2)
