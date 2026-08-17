from __future__ import annotations

import importlib.util
import sys
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_d64():
    name = "d64_stage82_test_module"
    if name in sys.modules:
        return sys.modules[name]
    sys.modules.setdefault("flags_rc", types.ModuleType("flags_rc"))
    spec = importlib.util.spec_from_file_location(name, ROOT / "d64_dism.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class Stage82C64InternalRomRoutineTests(unittest.TestCase):
    def test_basic_internal_table_contains_core_entries(self):
        d64 = load_d64()
        table = {address: (name, description) for address, name, description in d64.C64_BASIC_INTERNAL_JSR_ROUTINES}
        self.assertIn(0xA474, table)
        self.assertEqual(table[0xA474][0], "RESTART")
        self.assertIn(0xA613, table)
        self.assertEqual(table[0xA613][0], "CRUNCH")
        self.assertIn(0xAD1E, table)
        self.assertEqual(table[0xAD1E][0], "NEXT")
        self.assertIn(0xE37B, table)
        self.assertEqual(table[0xE37B][0], "PANIC")
        self.assertIn(0xE394, table)
        self.assertEqual(table[0xE394][0], "INIT")

    def test_kernal_internal_table_keeps_clear_screen_and_irq_entries(self):
        d64 = load_d64()
        table = {address: (name, description) for address, name, description in d64.C64_KERNAL_INTERNAL_JSR_ROUTINES}
        self.assertEqual(table[0xE544], ("CLSR", "Bildschirm löschen"))
        self.assertEqual(table[0xE566][0], "NXTD")
        self.assertEqual(table[0xEA31][0], "IRQ")
        self.assertEqual(table[0xEA81][0], "IRQRTI")

    def test_compatibility_internal_table_is_combined(self):
        d64 = load_d64()
        self.assertEqual(
            len(d64.C64_INTERNAL_JSR_ROUTINES),
            len(d64.C64_BASIC_INTERNAL_JSR_ROUTINES)
            + len(d64.C64_KERNAL_INTERNAL_JSR_ROUTINES),
        )

    def test_stability_distinguishes_api_basic_and_kernal_internal(self):
        d64 = load_d64()
        self.assertEqual(
            d64.c64_assembler_call_stability("JSR", "$FFD2"),
            "KERNAL-API",
        )
        self.assertEqual(
            d64.c64_assembler_call_stability("JSR", "$A474"),
            "INTERN BASIC - nicht API-stabil",
        )
        self.assertEqual(
            d64.c64_assembler_call_stability("JSR", "$E544"),
            "INTERN KERNAL - nicht API-stabil",
        )

    def test_textual_lookup_keeps_plain_description(self):
        d64 = load_d64()
        self.assertEqual(
            d64.c64_assembler_call_description("JSR", "$A474"),
            "BASIC-Eingabeschleife neu starten",
        )
        self.assertEqual(
            d64.c64_assembler_call_description("JSR", "#A474"),
            "BASIC-Eingabeschleife neu starten",
        )
        self.assertEqual(
            d64.c64_assembler_call_description("JSR", "$E544"),
            "Bildschirm löschen",
        )

    def test_disassembly_marks_internal_basic_and_kernal(self):
        d64 = load_d64()
        payload = bytes((
            0x01, 0x08,
            0x20, 0x74, 0xA4,  # JSR $A474
            0x20, 0x44, 0xE5,  # JSR $E544
            0x20, 0xD2, 0xFF,  # JSR $FFD2 - official API
            0x60,
        ))
        text, load = d64.format_c64_program_disassembly(
            payload,
            suffix=".prg",
            source_name="stage82_internal.prg",
        )
        self.assertEqual(load, 0x0801)
        self.assertIn("JSR $A474", text)
        self.assertIn("[INTERN BASIC RESTART]", text)
        self.assertIn("JSR $E544", text)
        self.assertIn("[INTERN KERNAL CLSR]", text)
        self.assertIn("JSR $FFD2", text)
        self.assertIn("CHROUT:", text)
        self.assertNotIn("[INTERN KERNAL CHROUT]", text)

    def test_live_help_contains_internal_rom_warning_source(self):
        source = (ROOT / "d64_dism.py").read_text(encoding="utf-8")
        self.assertIn("c64_assembler_call_stability", source)
        self.assertIn("interne ROM-Routine", source)
        self.assertIn("nicht Teil der stabilen KERNAL-Jump-Table", source)


if __name__ == "__main__":
    unittest.main()
