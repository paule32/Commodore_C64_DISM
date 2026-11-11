"""Stage 568: Serial-Status, Gültigkeits-Bereich, UUID und ältere Projekte."""
from __future__ import annotations

import ast
import json
from pathlib import Path
import tempfile
import unittest
import uuid

from installer_security_settings import (
    SECURITY_SECTION, MAX_REG_COUNT, VALIDITY_DEFAULTS,
    default_validity_settings, validate_validity_settings,
    validate_serial_list, parse_security_settings, encode_security_settings,
)
from software_installer_model import InstallerProject

ROOT = Path(__file__).resolve().parent
SRC = (ROOT / "software_installer_dialogs.py").read_text(encoding="utf8")
TREE = ast.parse(SRC)


def gui_method(cls_name, func):
    cls = next(node for node in TREE.body if isinstance(node, ast.ClassDef)
               and node.name == cls_name)
    fn = next(node for node in cls.body if isinstance(node, ast.FunctionDef)
              and node.name == func)
    return ast.get_source_segment(SRC, fn)


class Stage568ModelTests(unittest.TestCase):
    def test_old_serial_project_parses_unchanged(self):
        old = {"serial_lists": [{"name": "Stage 567", "configurations": ["Standard"],
                                 "serial_numbers": ["AAA-BBB", "CCC-DDD"]}]}
        self.assertEqual(parse_security_settings(encode_security_settings(old)), old)
        self.assertNotIn("validity", parse_security_settings(encode_security_settings(old)))

    def test_serial_metadata_roundtrip_and_case_normalization(self):
        serial = {
            "name": "Produkt", "configurations": ["Standard"],
            "serial_numbers": ["AA-BB", "CC-DD"],
            "serial_details": {"aa-bb": {"occupied": True, "reg_count": 7},
                               "CC-DD": {"occupied": False, "reg_count": 0}},
        }
        checked = validate_serial_list(serial)
        self.assertEqual(checked["serial_details"]["AA-BB"]["reg_count"], 7)
        self.assertIs(checked["serial_details"]["AA-BB"]["occupied"], True)
        data = {"serial_lists": [serial], "validity": default_validity_settings()}
        self.assertEqual(parse_security_settings(encode_security_settings(data))["serial_lists"][0],
                         checked)

    def test_invalid_serial_usage_rejected(self):
        base = {"name": "A", "configurations": [], "serial_numbers": ["ABC"]}
        for value in ({"occupied": 1, "reg_count": 0},
                      {"occupied": False, "reg_count": -1},
                      {"occupied": True, "reg_count": 1.5},
                      {"occupied": True, "reg_count": MAX_REG_COUNT + 1},
                      {"occupied": False},
                      {"occupied": False, "reg_count": 3, "other": 5}):
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate_serial_list({**base, "serial_details": {"ABC": value}})
        with self.assertRaisesRegex(ValueError, "unbekannte"):
            validate_serial_list({**base,
                "serial_details": {"OTHER": {"occupied": False, "reg_count": 0}}})

    def test_defaults_are_independent_and_complete(self):
        a = default_validity_settings()
        b = default_validity_settings()
        a["contact_name"] = "X"
        self.assertEqual(b, VALIDITY_DEFAULTS)
        self.assertEqual(b["days_after_creation"], 30)
        self.assertEqual(b["days_after_first_start"], 30)
        self.assertEqual(b["max_system_installations"], 2)
        self.assertEqual(b["max_user_installations"], 1)
        self.assertEqual(b["contact_name"], "%CompanyName%")
        self.assertEqual(b["contact_website"], "%CompanyURL%")

    def test_uuid_and_date_values(self):
        values = default_validity_settings()
        values["expiry_enabled"] = True
        values["expiry_mode"] = "after_first_start"
        values["absolute_date"] = "2027-02-28"
        values["product_id"] = str(uuid.uuid4())
        values["counter_enabled"] = True
        values["show_contact_info"] = True
        checked = validate_validity_settings(values)
        self.assertEqual(checked, values)
        full = {"serial_lists": [], "validity": values}
        self.assertEqual(parse_security_settings(encode_security_settings(full)), full)

    def test_validate_bad_dates_uuid_and_ranges(self):
        changes = (
            ("absolute_date", "2027-02-30"), ("absolute_date", "07.11.2026"),
            ("product_id", "not-uuid"), ("counter_mode", "per-user"),
            ("expiry_mode", "unknown"), ("counter_enabled", 1),
            ("max_system_installations", 0),
            ("max_user_installations", -2),
            ("days_after_first_start", True),
            ("show_remaining_days", "yes"),
            ("contact_email", "bad\nline"),
        )
        for field, value in changes:
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                validate_validity_settings({**default_validity_settings(), field: value})

    def test_project_json_preserves_other_sections(self):
        value = default_validity_settings()
        value["product_id"] = str(uuid.uuid4())
        raw = encode_security_settings({"serial_lists": [], "validity": value})
        project = InstallerProject(name="Test", sections={SECURITY_SECTION: raw,
            "Log-Datei": "unchanged", "Systemanforderungen": "unchanged"})
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "sample.installer.json"
            project.save(str(path))
            loaded = InstallerProject.load(str(path))
        self.assertEqual(parse_security_settings(loaded.sections[SECURITY_SECTION])["validity"],
                         value)
        self.assertEqual(loaded.sections["Log-Datei"], "unchanged")


class Stage568SourceTests(unittest.TestCase):
    def test_serial_table_columns_and_metadata(self):
        child = gui_method("InstallerSerialListPropertiesDialog", "__init__")
        self.assertIn('QTableWidget(0, 3, self)', child)
        self.assertIn('"Serial Nummer", "Belegt", "Reg. Count"', child)
        self.assertIn('QHeaderView.Interactive', child)
        self.assertIn('_style_installer_serial_header(', child)
        self.assertIn('_installer_serial_font()', child)
        self.assertIn('Qt.ItemIsUserCheckable', gui_method(
            "InstallerSerialListPropertiesDialog", "_set_rows"))
        self.assertIn('"serial_details": details', gui_method(
            "InstallerSerialListPropertiesDialog", "_accept_changes"))
        for meth in ("_undo", "_redo", "_serial_item_changed"):
            self.assertIn("_row_records", gui_method("InstallerSerialListPropertiesDialog", meth))

    def test_three_groups_pickers_and_tab(self):
        parent = gui_method("InstallerSecurityDialog", "__init__")
        self.assertIn('"Gültigkeits-Bereich"', parent)
        self.assertIn('self._build_validity_tab()', parent)
        body = gui_method("InstallerSecurityDialog", "_build_validity_tab")
        for element in ('QGroupBox("Gültigkeit Datum"', 'QGroupBox("Zerfall - Zähler"',
                        'QGroupBox("Einstellungen"', '"Datum des Auslaufen"',
                        '"Absolutes Datum"', '"Tage nach Erstellung"',
                        '"Tage nach ersten Start"', '"Zeige Rest-Tage an"',
                        '"Installationen auf System"', '"Benutzer-Installationen"',
                        '"Nummer bis Limit anzeigen"', '"Produkt Identifikation"',
                        '"Kontaktinfos anzeigen"', '"Kontakt-Name:"',
                        '"Webseite"', '"Kontakt E-Mail"', '"Kontakt Telefon"',
                        'setCalendarPopup(True)', 'setWidgetResizable(True)',
                        '"Erstellen"'):
            with self.subTest(element=element):
                self.assertIn(element, body)
        self.assertIn('setFixedSize(WIZARD_SIZE[0] - 140, WIZARD_SIZE[1] - 40)', parent)
        self.assertIn('gradient_title=True', parent)
        self.assertIn('("OK", "Abbrechen", "Hilfe")', parent)

    def test_uuid_generation_and_existing_save_transaction(self):
        self.assertIn('uuid.uuid4()', gui_method("InstallerSecurityDialog", "_generate_product_id"))
        accepting = gui_method("InstallerSecurityDialog", "_accept_changes")
        self.assertIn('self._collect_validity_settings()', accepting)
        self.assertIn('encode_security_settings(', accepting)
        self.assertIn('self.accept()', accepting)
        init = gui_method("InstallerSecurityDialog", "__init__")
        self.assertIn('self.reject', init)
        self.assertIn('self._help', init)
        self.assertNotIn('winreg', SRC)  # Entwurfsdaten, keine Registry-Änderung

    def test_help_docs_updated(self):
        text = (ROOT / "help/software_installer/sicherheit.html").read_text('utf8')
        for word in ("Gültigkeits-Bereich", "Reg. Count", "UUID v4",
                     "Registry-Schreiboperation", "%CompanyURL%"):
            self.assertIn(word, text)


if __name__ == '__main__':
    unittest.main()
