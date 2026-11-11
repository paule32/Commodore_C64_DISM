"""Stage 567: GUI-Quelltextchecks ohne PyQt5-Abhängigkeit."""
from __future__ import annotations

import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE = (ROOT / "software_installer_dialogs.py").read_text(encoding="utf-8")
TREE = ast.parse(SOURCE)


def method_in(class_name, method_name):
    cls = next(node for node in TREE.body if isinstance(node, ast.ClassDef)
               and node.name == class_name)
    node = next(node for node in cls.body if isinstance(node, ast.FunctionDef)
                and node.name == method_name)
    return ast.get_source_segment(SOURCE, node)


def function(name):
    node = next(node for node in TREE.body if isinstance(node, ast.FunctionDef)
                and node.name == name)
    return ast.get_source_segment(SOURCE, node)


class InstallerStage567Checks(unittest.TestCase):
    def test_header_has_separate_dark_and_light_colors(self):
        helper = function("_style_installer_serial_header")
        self.assertIn('"#343b48"', helper)
        self.assertIn('"#e4e9ef"', helper)
        self.assertIn('"#f1f2f4"', helper)
        self.assertIn('"#20242b"', helper)
        self.assertIn("header.setStyleSheet(", helper)
        self.assertIn("QHeaderView::section", helper)
        self.assertIn("QHeaderView::section:hover", helper)
        self.assertIn("header.setHighlightSections(False)", helper)

    def test_both_tables_get_header_theme_and_live_theme_updates(self):
        parent = method_in("InstallerSecurityDialog", "__init__")
        child = method_in("InstallerSerialListPropertiesDialog", "__init__")
        theme = method_in("InstallerThemedDialog", "apply_theme")
        self.assertIn("_style_installer_serial_header(self.lists_table, self._dark_mode)", parent)
        self.assertIn("_style_installer_serial_header(self.serial_table, self._dark_mode)", child)
        self.assertIn('"installerSerialListsTable"', theme)
        self.assertIn('"installerSerialNumbersTable"', theme)
        self.assertIn("_style_installer_serial_header(table, self._dark_mode)", theme)
        self.assertIn("QHeaderView.Interactive", parent)  # weiter mit Maus resizable
        self.assertIn('self.lists_table.verticalHeader().setVisible(False)', parent)

    def test_monospace_font_family_with_fallbacks(self):
        font = function("_installer_serial_font")
        self.assertIn('"Consolas", "Courier New", "Courier"', font)
        self.assertIn('font.setStyleHint(QFont.TypeWriter)', font)
        init = method_in("InstallerSerialListPropertiesDialog", "__init__")
        self.assertIn("self.serial_font = _installer_serial_font()", init)
        self.assertIn("self.serial_table.setFont(self.serial_font)", init)
        table = method_in("InstallerSerialListPropertiesDialog", "_set_rows")
        self.assertIn("item.setFont(self.serial_font)", table)

    def test_print_first_previews_with_same_document(self):
        preview = method_in("InstallerSerialListPropertiesDialog", "_print")
        document = method_in("InstallerSerialListPropertiesDialog", "_serial_print_document")
        self.assertIn("QPrintPreviewDialog", preview)
        self.assertNotIn("QPrintDialog(", preview)  # Vorschau macht dies selbst beim Drucken
        self.assertIn("QPrinter(QPrinter.HighResolution)", preview)
        self.assertIn("preview.paintRequested.connect(document.print_)", preview)
        self.assertIn("preview.exec_()", preview)
        self.assertIn("document.setDefaultFont(self.serial_font)", document)
        self.assertIn("escape(value)", document)  # keine HTML-Injektion aus Nummern
        self.assertIn("document.setHtml(content)", document)

    def test_existing_menu_and_transaction_unchanged(self):
        actions = method_in("InstallerSerialListPropertiesDialog", "_create_commands")
        self.assertIn('("Drucken", None, self._print)', actions)
        parent_ok = method_in("InstallerSecurityDialog", "_accept_changes")
        self.assertIn("encode_security_settings(", parent_ok)
        child_ok = method_in("InstallerSerialListPropertiesDialog", "_accept_changes")
        self.assertIn("validate_serial_list(", child_ok)
        self.assertIn("self.accept()", child_ok)


if __name__ == "__main__":
    unittest.main()
