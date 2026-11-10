"""Qt-unabhaengige Session-Variablen fuer den Software Installer (Stage 559).

Die Wizard-Einstellungen sind Quelle der Systemvorgaben. Nur explizit geaenderte
Werte werden als Overrides gespeichert; damit aktualisieren sich unveraenderte
Defaults bei einer spaeteren Aenderung des Wizard-Projektes.
"""
from __future__ import annotations

from collections import OrderedDict
import json
import re

SESSION_SECTION = "Session Variable"
SESSION_SCHEMA = 1
VARIABLE_NAME_PATTERN = re.compile(r"%[A-Za-z_][A-Za-z0-9_]*%\Z", re.ASCII)


def default_session_groups(general: dict | None = None) -> dict[str, dict[str, str]]:
    """Reihenfolge und Werte fuer beide fest definierten Tabellen."""
    general = general or {}
    def wizard_value(key, fallback):
        return str(general.get(key, "") or fallback)
    product = OrderedDict([
        ("%ProductName%", wizard_value("product", "Ihr Produkt")),
        ("%CompanyName%", wizard_value("company", "Ihre Firma")),
        ("%ProductVersion%", wizard_value("version", "1.0")),
        ("%Copyright%", "Copyright (c) #CURRENTYEAR# %CompanyName%"),
        ("%CompanyURL%", wizard_value("website", "https://www.firma.de")),
        ("%WindowTitle%", "%ProductName% Setup"),
        ("%WindowTitleUninstall%", "%ProductName% Uninstaller"),
    ])
    directories = OrderedDict([
        ("%AppFolder%", "%ProgramFilesFolder%\\%ProductName%"),
        ("%AppShortcutFolderName%", "%ProductName%"),
    ])
    return {"product": product, "directories": directories}


def normalize_variable_name(name: str) -> str:
    """Akzeptiert %Name% sowie Name und speichert immer %Name%."""
    name = str(name).strip()
    if name and not name.startswith("%") and not name.endswith("%"):
        name = "%" + name + "%"
    if not VARIABLE_NAME_PATTERN.fullmatch(name):
        raise ValueError("Der Variablenname muss die Form %VariableName% haben (Buchstaben, Ziffern, _).")
    return name


def check_variable_name(name: str, existing, *, previous: str | None = None) -> str:
    """Kollisionspruefung ohne Beachtung der Gross-/Kleinschreibung."""
    normalized = normalize_variable_name(name)
    old = previous.casefold() if previous else None
    if any(str(item).casefold() == normalized.casefold() and
           (old is None or str(item).casefold() != old) for item in existing):
        raise ValueError("Die Session-Variable '" + normalized + "' ist bereits vorhanden.")
    return normalized


def parse_session_variables(text: str | None, general: dict | None = None) -> dict:
    """Liest Projekt-Overrides; abhaengige Wizard-Vorgaben bleiben aktuell."""
    defaults = default_session_groups(general)
    data = json.loads(text) if text and str(text).strip() else {}
    if not isinstance(data, dict) or data.get("version", SESSION_SCHEMA) != SESSION_SCHEMA:
        raise ValueError("Ungueltiges Format der Session-Variablen")
    overrides = data.get("overrides", {})
    custom = data.get("custom", {})
    if not isinstance(overrides, dict) or not isinstance(custom, dict):
        raise ValueError("Ungueltige Session-Variablen-Daten")
    standard = {key: name for group in defaults.values() for key, name in group.items()}
    normalized_overrides = {}
    for key, value in overrides.items():
        if key not in standard or not isinstance(value, str):
            raise ValueError("Unbekannte oder ungueltige Systemvariable: " + str(key))
        normalized_overrides[key] = value
    normalized_custom = OrderedDict()
    for key, value in custom.items():
        name = check_variable_name(key, (*standard, *normalized_custom))
        if not isinstance(value, str):
            raise ValueError("Ungueltiger Wert fuer " + name)
        normalized_custom[name] = value
    return {"overrides": normalized_overrides, "custom": normalized_custom}


def effective_session_groups(general: dict | None = None, text: str | None = None) -> dict:
    """Zusammenfuehrung in darzustellender Reihenfolge."""
    groups = default_session_groups(general)
    stored = parse_session_variables(text, general)
    for group in groups.values():
        for key in group:
            if key in stored["overrides"]:
                group[key] = stored["overrides"][key]
    groups["custom"] = OrderedDict(stored["custom"])
    return groups


def encode_session_variables(general: dict | None, groups: dict) -> str:
    """Speichert nur echte Ueberschreibungen und benutzerdefinierte Variablen."""
    defaults = default_session_groups(general)
    overrides = OrderedDict()
    all_standard_names = tuple(key for group in defaults.values() for key in group)
    for category in ("product", "directories"):
        values = groups.get(category, {})
        if not isinstance(values, dict):
            raise ValueError("Ungueltige Systemvariablen-Gruppe")
        if set(values) != set(defaults[category]):
            raise ValueError("Systemvariablen duerfen nicht entfernt oder umbenannt werden")
        for name, base_value in defaults[category].items():
            value = str(values[name])
            if value != base_value:
                overrides[name] = value
    custom = groups.get("custom", {})
    if not isinstance(custom, dict):
        raise ValueError("Ungueltige benutzerdefinierte Variablen")
    checked_custom = OrderedDict()
    for name, value in custom.items():
        canonical = check_variable_name(name, (*all_standard_names, *checked_custom))
        checked_custom[canonical] = str(value)
    return json.dumps({"version": SESSION_SCHEMA, "overrides": overrides,
                       "custom": checked_custom}, ensure_ascii=False, indent=2)
