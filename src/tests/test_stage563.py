"""Stage 563: statische Layout-Regression fuer 'Hintergrund Fenster'."""
from __future__ import annotations

import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parent
SOURCE = (ROOT / "software_installer_dialogs.py").read_text(encoding="utf-8")


class Stage563LayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        tree = ast.parse(SOURCE)
        cls.dialog = next(node for node in tree.body
                          if isinstance(node, ast.ClassDef)
                          and node.name == "InstallerBackgroundWindowDialog")
        cls.init = next(node for node in cls.dialog.body
                        if isinstance(node, ast.FunctionDef) and node.name == "__init__")
        cls.calls = [node for node in ast.walk(cls.init) if isinstance(node, ast.Call)]

    @staticmethod
    def invokes(node, receiver, method):
        fn = node.func
        return (isinstance(fn, ast.Attribute) and fn.attr == method
                and isinstance(fn.value, ast.Name) and fn.value.id == receiver)

    @classmethod
    def find_call(cls, receiver, method):
        return [node for node in cls.calls if cls.invokes(node, receiver, method)]

    def test_left_and_right_column_top_edges_match(self):
        # Eine zusaetzliche 9px-Marge hatte die linke Spalte nach unten verschoben.
        margins = self.find_call("left_column", "setContentsMargins")
        self.assertEqual(len(margins), 1)
        self.assertEqual([arg.value for arg in margins[0].args], [0, 0, 0, 0])
        left_adds = self.find_call("body_layout", "addWidget")
        left = [call for call in left_adds if isinstance(call.args[0], ast.Name)
                and call.args[0].id == "left_widget"]
        self.assertEqual(len(left), 1)
        self.assertEqual(len(left[0].args), 2)  # kein Qt.AlignTop
        self.assertFalse(self.find_call("left_column", "addStretch"))
        # Die untere linke GroupBox nutzt die restliche Spaltenhoehe.
        self.assertTrue(any(len(call.args) == 2
                            and isinstance(call.args[0], ast.Attribute)
                            and call.args[0].attr == "appearance_group"
                            and isinstance(call.args[1], ast.Constant)
                            and call.args[1].value == 1
                            for call in self.find_call("left_column", "addWidget")))

    def test_full_width_text_inputs_and_separate_options(self):
        self.assertFalse(self.find_call("input_row", "addWidget"))
        self.assertFalse(self.find_call("edit", "setMinimumWidth"))
        text_adds = self.find_call("text_layout", "addWidget")
        self.assertTrue(any(isinstance(call.args[0], ast.Name)
                            and call.args[0].id == "edit" for call in text_adds))
        self.assertFalse(self.find_call("font_button", "setFixedWidth"))
        self.assertFalse(self.find_call("color", "setFixedWidth"))
        self.assertTrue(self.find_call("font_button", "setMinimumWidth"))
        self.assertTrue(self.find_call("color", "setMinimumWidth"))
        options = self.find_call("options_row", "addWidget")
        self.assertEqual(len(options), 2)
        self.assertEqual({call.args[0].id for call in options}, {"font_button", "color"})
        self.assertTrue(self.find_call("text_layout", "addLayout"))

    def test_existing_interactions_and_serialization_retained(self):
        for key in ("title", "version", "footer"):
            self.assertIn(f'"{key}", ', SOURCE)
        self.assertIn('lambda _checked=False, which=key: self._choose_font(which)', SOURCE)
        self.assertIn('self._fonts[which] = QFont(selected)', SOURCE)
        self.assertIn('settings[key + "_color"] = self.text_colors[key].color()', SOURCE)
        self.assertIn('self.serialized = encode_background_settings(self.settings())', SOURCE)
        self.assertIn('self.image_browse.clicked.connect(self._browse_image)', SOURCE)
        self.assertIn('self.help_callback("Hintergrund Fenster")', SOURCE)


if __name__ == "__main__":
    unittest.main()
