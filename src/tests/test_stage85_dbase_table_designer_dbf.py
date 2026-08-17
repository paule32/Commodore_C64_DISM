from __future__ import annotations

import importlib.util
import sys
import tempfile
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "d64_dism.py").read_text(encoding="utf-8")


def load_d64():
    name = "d64_stage85_test_module"
    if name in sys.modules:
        return sys.modules[name]
    sys.modules.setdefault("flags_rc", types.ModuleType("flags_rc"))
    spec = importlib.util.spec_from_file_location(name, ROOT / "d64_dism.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class Stage85DBaseTableDesignerTests(unittest.TestCase):
    def test_dbf_writer_reader_roundtrip_preserves_structure_data_and_index_metadata(self):
        d64 = load_d64()
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "kunden.dbf"
            fields = [
                d64.DBaseDBFField("NAME", "C", 30, 0, True),
                d64.DBaseDBFField("UMSATZ", "N", 12, 2, False),
                d64.DBaseDBFField("AKTIV", "L", 1, 0, False),
            ]
            records = [
                (False, {"NAME": "Müller", "UMSATZ": "123.45", "AKTIV": "T"})
            ]
            d64.write_dbase_dbf(path, fields, records)
            table = d64.read_dbase_dbf(path)

            self.assertEqual(path.read_bytes()[:1], b"\x03")
            self.assertEqual(
                [(f.name, f.field_type, f.length, f.decimals) for f in table.fields],
                [("NAME", "C", 30, 0), ("UMSATZ", "N", 12, 2), ("AKTIV", "L", 1, 0)],
            )
            self.assertTrue(table.fields[0].indexed)
            self.assertEqual(table.records[0][1]["NAME"], "Müller")
            self.assertEqual(table.records[0][1]["UMSATZ"], "123.45")
            self.assertTrue(path.with_suffix(".dbf.d64meta.json").is_file())

    def test_dbf_field_validation_rejects_duplicate_and_invalid_names(self):
        d64 = load_d64()
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "bad.dbf"
            with self.assertRaises(ValueError):
                d64.write_dbase_dbf(
                    path,
                    [d64.DBaseDBFField("A", "C", 10), d64.DBaseDBFField("a", "N", 5)],
                )
            with self.assertRaises(ValueError):
                d64.write_dbase_dbf(path, [d64.DBaseDBFField("11INVALID", "C", 10)])

    def test_dbase_new_menu_exposes_table_designer(self):
        menu_block = SOURCE[
            SOURCE.index("def _populate_new_document_menu"):
            SOURCE.index("def resource_dialog", SOURCE.index("def _populate_new_document_menu"))
        ]
        self.assertIn('submenu.addAction(actions["form"])', menu_block)
        self.assertIn('submenu.addAction(actions["table"])', menu_block)
        self.assertIn('"Tabelle"', SOURCE)
        self.assertIn("self.show_dbase_table_designer", SOURCE)
        self.assertIn('QDockWidget("dBase Tabelle - Designer"', SOURCE)

    def test_table_grid_has_headers_editors_and_numbered_vertical_header(self):
        block = SOURCE[
            SOURCE.index("class DBaseTableFieldGrid"):
            SOURCE.index("class DBaseTablePage", SOURCE.index("class DBaseTableFieldGrid"))
        ]
        for heading in ("Feldname", "Feldtyp", "Länge", "Anzahl nach Komma", "Index"):
            self.assertIn(f'"{heading}"', block)
        self.assertIn("QComboBox", block)
        self.assertIn("QSpinBox", block)
        self.assertIn("QCheckBox", block)
        self.assertIn("self.verticalHeader().setVisible(True)", block)
        self.assertIn("header.setText(str(row + 1))", block)

    def test_context_menu_supports_requested_row_operations(self):
        block = SOURCE[
            SOURCE.index("def _show_context_menu", SOURCE.index("class DBaseTableFieldGrid")):
            SOURCE.index("class DBaseTablePage", SOURCE.index("class DBaseTableFieldGrid"))
        ]
        for action in ("Hinzufügen", "Kopieren", "Ausschneiden", "Einfügen", "Löschen"):
            self.assertIn(f'addAction("{action}")', block)
        self.assertIn("self.copy_row()", block)
        self.assertIn("self.cut_row()", block)
        self.assertIn("self.paste_row()", block)
        self.assertIn("self.delete_row()", block)
        self.assertIn("self._recalculate_vertical_headers()", SOURCE)

    def test_parent_table_tabs_inner_fields_tab_and_file_buttons_exist(self):
        block = SOURCE[
            SOURCE.index("class DBaseTablePage"):
            SOURCE.index("class DockTitleBar", SOURCE.index("class DBaseTablePage"))
        ]
        self.assertIn('self.inner_tabs.addTab(fields_page, "Felder")', block)
        self.assertIn('QPushButton("Speichern"', block)
        self.assertIn('QPushButton("Speichern unter ..."', block)
        self.assertIn('QPushButton("Laden"', block)
        self.assertIn("class DBaseTableDesignerWidget", block)
        self.assertIn("self.table_tabs = QTabWidget", block)
        self.assertIn("self.table_tabs.addTab(page, page.display_name())", block)
        self.assertIn("write_dbase_dbf(", block)
        self.assertIn("read_dbase_dbf(", block)


if __name__ == "__main__":
    unittest.main()
