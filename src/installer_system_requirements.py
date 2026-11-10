"""Persistente Systemanforderungen des Software-Installers (Stage 564)."""
from __future__ import annotations
import json
from installer_wizard_options import (
    DEFAULT_WINDOWS_VERSIONS, windows_leaf_ids, decode_selection, encode_selection,
)

SYSTEM_REQUIREMENTS_SECTION = "Systemanforderungen"
SYSTEM_REQUIREMENTS_VERSION = 1
SYSTEM_REQUIREMENTS_DEFAULTS = {
    "windows_versions": list(DEFAULT_WINDOWS_VERSIONS),
    "ram_mb": 0,
    "screen_width_px": 0,
    "screen_height_px": 0,
    "color_depth_bpp": 0,
    "require_admin": False,
    "notification": "warn_continue",
}


def validate_system_requirements(values):
    if not isinstance(values, dict):
        raise ValueError("Ungültige Systemanforderungen")
    extras = set(values) - set(SYSTEM_REQUIREMENTS_DEFAULTS)
    if extras:
        raise ValueError("Unbekannte Systemanforderungen: " + ", ".join(sorted(extras)))
    result = dict(SYSTEM_REQUIREMENTS_DEFAULTS)
    result.update(values)
    versions = result["windows_versions"]
    if not isinstance(versions, list) or any(not isinstance(v, str) for v in versions):
        raise ValueError("Windows-Versionen müssen eine Liste sein")
    if any(v not in windows_leaf_ids() for v in versions):
        raise ValueError("Unbekannte Windows-Version")
    result["windows_versions"] = decode_selection(versions, windows_leaf_ids(), ())
    for key in ("ram_mb", "screen_width_px", "screen_height_px", "color_depth_bpp"):
        value = result[key]
        if type(value) is not int or not 0 <= value <= 2147483647:
            raise ValueError("Ungültiger Zahlenwert: " + key)
    if type(result["require_admin"]) is not bool:
        raise ValueError("Ungültiger Administrator-Status")
    if result["notification"] not in ("warn_continue", "abort_setup"):
        raise ValueError("Ungültiger Benachrichtigungsmodus")
    return result


def parse_system_requirements(raw):
    if not raw or not raw.strip():
        return validate_system_requirements({})
    obj = json.loads(raw)
    if not isinstance(obj, dict) or obj.get("version") != SYSTEM_REQUIREMENTS_VERSION:
        raise ValueError("Unbekanntes Systemanforderungsformat")
    return validate_system_requirements(obj.get("settings"))


def encode_system_requirements(settings):
    return json.dumps({"version": SYSTEM_REQUIREMENTS_VERSION,
                       "settings": validate_system_requirements(settings)},
                      ensure_ascii=False, indent=2)
