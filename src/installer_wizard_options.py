"""Stabile, Qt-unabhaengige Auswahlwerte fuer den Software-Installer-Wizard.

Die Labels sind deutsch, die Sprachkennungen folgen BCP 47 (Windows-Locale).
Die Windows-Ziele sind Auswahlvorgaben, keine Behauptung einer getesteten
Binaerkompatibilitaet fuer eine konkrete Setup-Engine.
"""
from __future__ import annotations

import json

# (Deutsche Anzeige, BCP-47-Sprachkennung). Der Umfang ist bewusst
# projektunabhaengig; installierte Windows-Sprachpakete koennen abweichen.
WINDOWS_LANGUAGES = tuple(sorted((
    ("Afrikaans", "af-ZA"),
    ("Albanisch", "sq-AL"),
    ("Arabisch", "ar-SA"),
    ("Armenisch", "hy-AM"),
    ("Aserbaidschanisch", "az-Latn-AZ"),
    ("Baskisch", "eu-ES"),
    ("Bengalisch", "bn-BD"),
    ("Bosnisch", "bs-Latn-BA"),
    ("Bulgarisch", "bg-BG"),
    ("Chinesisch (vereinfacht)", "zh-CN"),
    ("Chinesisch (traditionell)", "zh-TW"),
    ("Dänisch", "da-DK"),
    ("Deutsch", "de-DE"),
    ("Englisch", "en-US"),
    ("Englisch (Großbritannien)", "en-GB"),
    ("Estnisch", "et-EE"),
    ("Finnisch", "fi-FI"),
    ("Französisch", "fr-FR"),
    ("Galicisch", "gl-ES"),
    ("Georgisch", "ka-GE"),
    ("Griechisch", "el-GR"),
    ("Hebräisch", "he-IL"),
    ("Hindi", "hi-IN"),
    ("Indonesisch", "id-ID"),
    ("Irisch", "ga-IE"),
    ("Isländisch", "is-IS"),
    ("Italienisch", "it-IT"),
    ("Japanisch", "ja-JP"),
    ("Kasachisch", "kk-KZ"),
    ("Katalanisch", "ca-ES"),
    ("Koreanisch", "ko-KR"),
    ("Kroatisch", "hr-HR"),
    ("Lettisch", "lv-LV"),
    ("Litauisch", "lt-LT"),
    ("Malaiisch", "ms-MY"),
    ("Niederländisch", "nl-NL"),
    ("Norwegisch (Bokmål)", "nb-NO"),
    ("Persisch", "fa-IR"),
    ("Polnisch", "pl-PL"),
    ("Portugiesisch (Brasilien)", "pt-BR"),
    ("Portugiesisch (Portugal)", "pt-PT"),
    ("Rumänisch", "ro-RO"),
    ("Russisch", "ru-RU"),
    ("Schwedisch", "sv-SE"),
    ("Serbisch (Lateinisch)", "sr-Latn-RS"),
    ("Slowakisch", "sk-SK"),
    ("Slowenisch", "sl-SI"),
    ("Spanisch", "es-ES"),
    ("Spanisch (Mexiko)", "es-MX"),
    ("Thailändisch", "th-TH"),
    ("Tschechisch", "cs-CZ"),
    ("Türkisch", "tr-TR"),
    ("Ukrainisch", "uk-UA"),
    ("Ungarisch", "hu-HU"),
    ("Urdu", "ur-PK"),
    ("Vietnamesisch", "vi-VN"),
), key=lambda option: option[0].casefold()))

DEFAULT_LANGUAGES = ("de-DE", "en-US")
DEFAULT_LANGUAGE = "de-DE"

# (Maschinenlesbare Kennung, sichtbarer Titel, Unterknoten).
# Nur Blaetter sind einzeln adressierbare Kompatibilitaetsziele.
WINDOWS_VERSION_TREE = (
    ("windows-desktop", "Windows (Desktop)", (
        ("windows-legacy", "Ältere Windows-Versionen", (
            ("win-xp", "Windows XP", ()),
            ("win-vista", "Windows Vista", ()),
            ("win-7", "Windows 7", ()),
            ("win-8", "Windows 8", ()),
            ("win-81", "Windows 8.1", ()),
        )),
        ("windows-modern", "Windows 10 / 11", (
            ("win-10", "Windows 10", ()),
            ("win-11", "Windows 11", ()),
        )),
    )),
    ("windows-server", "Windows Server", (
        ("windows-server-legacy", "Ältere Server-Versionen", (
            ("win-server-2008-r2", "Windows Server 2008 R2", ()),
            ("win-server-2012", "Windows Server 2012", ()),
            ("win-server-2012-r2", "Windows Server 2012 R2", ()),
        )),
        ("windows-server-modern", "Neuere Server-Versionen", (
            ("win-server-2016", "Windows Server 2016", ()),
            ("win-server-2019", "Windows Server 2019", ()),
            ("win-server-2022", "Windows Server 2022", ()),
            ("win-server-2025", "Windows Server 2025", ()),
        )),
    )),
)
DEFAULT_WINDOWS_VERSIONS = ("win-10", "win-11")


def windows_leaf_ids(nodes=WINDOWS_VERSION_TREE) -> tuple[str, ...]:
    """Gibt alle selektierbaren Windows-Blatt-IDs in Baumreihenfolge zurueck."""
    leaves = []
    for identifier, _label, children in nodes:
        if children:
            leaves.extend(windows_leaf_ids(children))
        else:
            leaves.append(identifier)
    return tuple(leaves)


def decode_selection(raw, allowed, default=()) -> list[str]:
    """Liest eine JSON-Liste aus dem bestehenden general[str, str]-Schema.

    Bei unbekannten IDs, defekten Daten und Duplikaten werden ausschliesslich
    gueltige eindeutige Werte in der vorgegebenen UI-Reihenfolge uebernommen.
    Eine absichtlich gespeicherte leere Liste bleibt leer.
    """
    if raw is None:
        data = list(default)
    elif isinstance(raw, (list, tuple)):
        data = list(raw)
    else:
        try:
            data = json.loads(str(raw))
        except (ValueError, TypeError):
            data = list(default)
    if not isinstance(data, list):
        data = list(default)
    selected = {item for item in data if isinstance(item, str)}
    return [code for code in allowed if code in selected]


def encode_selection(selected) -> str:
    """Speichert eine Liste ohne aenderung der bestehenden Projektdatei-Version."""
    return json.dumps(list(selected), ensure_ascii=False, separators=(",", ":"))


def normalized_default_language(selected, requested=DEFAULT_LANGUAGE):
    """Standard-Sprache muss in der angehakten Sprachmenge liegen."""
    selected = list(selected)
    if requested in selected:
        return requested
    if DEFAULT_LANGUAGE in selected:
        return DEFAULT_LANGUAGE
    return selected[0] if selected else ""
