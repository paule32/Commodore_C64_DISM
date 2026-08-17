from __future__ import annotations

import importlib.util
import sys
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "d64_dism.py").read_text(encoding="utf-8")


def load_d64():
    name = "d64_stage84_test_module"
    if name in sys.modules:
        return sys.modules[name]
    sys.modules.setdefault("flags_rc", types.ModuleType("flags_rc"))
    spec = importlib.util.spec_from_file_location(name, ROOT / "d64_dism.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class Stage84BinaryBuildMruAndFormDesignerTests(unittest.TestCase):
    def test_binary_disassembly_roundtrips_through_internal_assembler(self):
        d64 = load_d64()
        original = bytes((
            0x01, 0x08,
            0xA9, 0x01,
            0x8D, 0x00, 0x04,
            0x60,
        ))
        source, load_address = d64.format_c64_program_disassembly(
            original,
            suffix=".prg",
            source_name="roundtrip.prg",
        )
        self.assertEqual(load_address, 0x0801)
        program = d64.assemble_mos6510_source(
            source,
            filename="roundtrip.disassembly.asm",
        )
        self.assertEqual(program.prg, original)

    def test_binary_rohdaten_is_a_buildable_assembler_document(self):
        document_block = SOURCE[
            SOURCE.index("class DocumentEditor(QWidget)"):
            SOURCE.index("class DBaseFormDesignerScene", SOURCE.index("class DocumentEditor(QWidget)"))
        ]
        self.assertIn("or is_disassembly", document_block)
        self.assertIn("self.binary_disassembly_mode\n                or self.effective_suffix", document_block)
        self.assertIn("self.start_assembled_button.setVisible(is_assembler_source)", document_block)
        self.assertIn('document.path.stem + ".reassembled.prg"', SOURCE)

    def test_recent_program_menu_keeps_ten_entries_in_settings(self):
        self.assertIn("RECENT_PROGRAM_LIMIT = 10", SOURCE)
        self.assertIn('"files/recent_programs"', SOURCE)
        self.assertIn('"Zuletzt verwendete Programme"', SOURCE)
        self.assertIn("self._remember_recent_program_file(path)", SOURCE)
        self.assertIn("self._remember_recent_program_file(document.path)", SOURCE)

    def test_dbase_new_menu_contains_separator_and_form_action(self):
        menu_block = SOURCE[
            SOURCE.index("def _populate_new_document_menu"):
            SOURCE.index("def resource_dialog", SOURCE.index("def _populate_new_document_menu"))
        ]
        self.assertIn('if profile_key == "dbase":', menu_block)
        self.assertIn("submenu.addSeparator()", menu_block)
        self.assertIn('submenu.addAction(actions["form"])', menu_block)
        self.assertIn('"Formular"', SOURCE)

    def test_form_designer_has_requested_tabs_property_grid_and_pixel_grid(self):
        designer = SOURCE[
            SOURCE.index("class DBaseFormDesignerScene"):
            SOURCE.index("class DockTitleBar", SOURCE.index("class DBaseFormDesignerScene"))
        ]
        self.assertIn("GRID_SPACING = 10", designer)
        self.assertIn('setHorizontalHeaderLabels(("Key", "Value"))', designer)
        for name in ("Top", "Left", "Width", "Height"):
            self.assertIn(f'"{name}"', designer)
        for tab in ("Eigenschaften", "Ereignisse", "Methoden", "Standard", "Erweitert"):
            self.assertIn(f'"{tab}"', designer)
        self.assertIn("QSpinBox", designer)
        self.assertIn("QListView.IconMode", designer)

    def test_form_designer_has_two_buttons_and_eight_resize_handles(self):
        designer = SOURCE[
            SOURCE.index("class DBaseFormResizeHandle"):
            SOURCE.index("class DockTitleBar", SOURCE.index("class DBaseFormResizeHandle"))
        ]
        for role in ("nw", "n", "ne", "e", "se", "s", "sw", "w"):
            self.assertIn(f'"{role}"', designer)
        self.assertIn("Qt.SizeFDiagCursor", designer)
        self.assertIn("Qt.SizeBDiagCursor", designer)
        self.assertIn("Qt.SizeHorCursor", designer)
        self.assertIn("Qt.SizeVerCursor", designer)
        self.assertIn("begin_resize", designer)
        self.assertIn("update_resize", designer)
        self.assertIn("finish_resize", designer)
        self.assertIn('DBaseFormButtonItem("Button 1"', SOURCE)
        self.assertIn('DBaseFormButtonItem("Button 2"', SOURCE)


if __name__ == "__main__":
    unittest.main()
