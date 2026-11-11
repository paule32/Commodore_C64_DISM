"""Installer-Sicherheit: Serial-Nummern und optionaler Gültigkeitsbereich.

Die Einstellungen sind Projektkonfiguration. Eine künftige Setup-Runtime muss
Registry-Speicherung, Serienprüfung und Ablaufbedingungen separat implementieren.
Alte Stage-566/567-Daten mit bloßen Serial-Strings bleiben lesbar.
"""
from __future__ import annotations

from datetime import date
import json
import uuid

SECURITY_SECTION = "Sicherheit"
SECURITY_VERSION = 1   # optionale neue Felder sind zu v1 abwärtskompatibel
SECURITY_DEFAULTS = {"serial_lists": []}
SERIAL_CONFIGURATIONS = ("Standard",)
MAX_REG_COUNT = 2_147_483_647

VALIDITY_DEFAULTS = {
    "expiry_enabled": False,
    "expiry_mode": "absolute",            # absolute, after_creation, after_first_start
    "absolute_date": "",                  # ISO 8601; leer bis zur ersten Einstellung
    "days_after_creation": 30,
    "days_after_first_start": 30,
    "expiry_abort_on_registry_error": False,
    "show_remaining_days": False,
    "counter_enabled": False,
    "counter_mode": "system",             # system oder user
    "max_system_installations": 2,
    "max_user_installations": 1,
    "counter_abort_on_registry_error": False,
    "show_remaining_count": False,
    "product_id": "",
    "show_contact_info": False,
    "contact_name": "%CompanyName%",
    "contact_website": "%CompanyURL%",
    "contact_email": "",
    "contact_phone": "",
}


def default_validity_settings():
    return dict(VALIDITY_DEFAULTS)


def validate_validity_settings(value):
    """Nur bekannte Feldtypen und Werte; keine Registry-Aktion beim Speichern."""
    if not isinstance(value, dict) or set(value) != set(VALIDITY_DEFAULTS):
        raise ValueError("Ungültiger Gültigkeits-Bereich")
    result = dict(value)
    for field in (
        "expiry_enabled", "expiry_abort_on_registry_error", "show_remaining_days",
        "counter_enabled", "counter_abort_on_registry_error", "show_remaining_count",
        "show_contact_info",
    ):
        if type(result[field]) is not bool:
            raise ValueError("Ungültige Checkbox-Einstellung: " + field)
    if result["expiry_mode"] not in ("absolute", "after_creation", "after_first_start"):
        raise ValueError("Ungültiger Gültigkeitsmodus")
    if result["counter_mode"] not in ("system", "user"):
        raise ValueError("Ungültiger Zählermodus")
    for field in ("days_after_creation", "days_after_first_start",
                  "max_system_installations", "max_user_installations"):
        if type(result[field]) is not int or not 1 <= result[field] <= 100000:
            raise ValueError("Ungültiger Zahlenwert: " + field)
    absolute = result["absolute_date"]
    if not isinstance(absolute, str):
        raise ValueError("Ungültiges absolutes Datum")
    if absolute:
        try:
            if date.fromisoformat(absolute).isoformat() != absolute:
                raise ValueError
        except ValueError as error:
            raise ValueError("Ungültiges absolutes Datum (JJJJ-MM-TT)") from error
    product_id = result["product_id"]
    if not isinstance(product_id, str):
        raise ValueError("Ungültige Produkt-Identifikation")
    if product_id:
        try:
            value_uuid = uuid.UUID(product_id)
        except (ValueError, AttributeError) as error:
            raise ValueError("Produkt-Identifikation muss eine UUID sein") from error
        result["product_id"] = str(value_uuid)
    for field in ("contact_name", "contact_website", "contact_email", "contact_phone"):
        text = result[field]
        if (not isinstance(text, str) or len(text) > 1024
                or any(c in text for c in "\x00\r\n")):
            raise ValueError("Ungültige Kontaktangabe: " + field)
    return result


def validate_serial_list(value):
    """Pro Liste optionaler Belegt-/Registrierungszähler je Serial-Nummer."""
    if (not isinstance(value, dict)
            or not {"name", "configurations", "serial_numbers"}.issubset(value)
            or set(value) - {"name", "configurations", "serial_numbers", "serial_details"}):
        raise ValueError("Ungültige Serial-Nummer-Liste")

    name = value["name"]
    if not isinstance(name, str) or not name.strip() or len(name) > 120:
        raise ValueError("Bitte einen gültigen Listennamen angeben (max. 120 Zeichen)")
    if any(ch in name for ch in "\x00\r\n"):
        raise ValueError("Ungültige Zeichen im Listennamen")

    configurations = value["configurations"]
    if not isinstance(configurations, list) or any(
        not isinstance(entry, str) or entry not in SERIAL_CONFIGURATIONS
        for entry in configurations
    ) or len(configurations) != len(set(configurations)):
        raise ValueError("Ungültige Konfigurationen der Serial-Nummer-Liste")

    numbers = value["serial_numbers"]
    if not isinstance(numbers, list) or len(numbers) > 100000:
        raise ValueError("Ungültige Anzahl von Serial-Nummern")
    clean_numbers = []
    for item in numbers:
        if (not isinstance(item, str) or not item.strip() or len(item) > 512
                or any(ch in item for ch in "\x00\r\n")):
            raise ValueError("Ungültige Serial-Nummer in Liste " + name)
        clean_numbers.append(item.strip())
    if len({item.casefold() for item in clean_numbers}) != len(clean_numbers):
        raise ValueError("Doppelte Serial-Nummern in Liste " + name)
    result = {"name": name.strip(), "configurations": list(configurations),
              "serial_numbers": clean_numbers}

    if "serial_details" in value:
        details = value["serial_details"]
        if not isinstance(details, dict):
            raise ValueError("Ungültige Serial-Nummer-Metadaten")
        lookup = {item.casefold(): item for item in clean_numbers}
        cleaned = {}
        for key, flags in details.items():
            if not isinstance(key, str) or key.casefold() not in lookup:
                raise ValueError("Metadaten für unbekannte Serial-Nummer")
            if (not isinstance(flags, dict)
                    or set(flags) != {"occupied", "reg_count"}
                    or type(flags["occupied"]) is not bool
                    or type(flags["reg_count"]) is not int
                    or not 0 <= flags["reg_count"] <= MAX_REG_COUNT):
                raise ValueError("Ungültige Belegt-/Reg.-Count-Angabe")
            canonical = lookup[key.casefold()]
            if canonical in cleaned:
                raise ValueError("Doppelte Serial-Nummer-Metadaten")
            cleaned[canonical] = {"occupied": flags["occupied"],
                                  "reg_count": flags["reg_count"]}
        result["serial_details"] = cleaned
    return result


def validate_security_settings(values):
    if (not isinstance(values, dict) or "serial_lists" not in values
            or set(values) - {"serial_lists", "validity"}):
        raise ValueError("Ungültige Sicherheits-Einstellungen")
    serial_lists = values["serial_lists"]
    if not isinstance(serial_lists, list) or len(serial_lists) > 500:
        raise ValueError("Ungültige Anzahl von Serial-Nummer-Listen")
    cleaned = [validate_serial_list(item) for item in serial_lists]
    names = [item["name"].casefold() for item in cleaned]
    if len(set(names)) != len(names):
        raise ValueError("Jeder Listenname darf nur einmal vorkommen")
    result = {"serial_lists": cleaned}
    if "validity" in values:
        result["validity"] = validate_validity_settings(values["validity"])
    return result


def parse_security_settings(raw):
    if not raw or not raw.strip():
        return validate_security_settings({"serial_lists": []})
    try:
        document = json.loads(raw)
    except (ValueError, TypeError) as error:
        raise ValueError("Ungültiger JSON-Abschnitt 'Sicherheit'") from error
    if not isinstance(document, dict) or document.get("version") != SECURITY_VERSION:
        raise ValueError("Unbekanntes Sicherheitsformat")
    return validate_security_settings(document.get("settings"))


def encode_security_settings(values):
    return json.dumps({"version": SECURITY_VERSION,
                       "settings": validate_security_settings(values)},
                      ensure_ascii=False, indent=2)
