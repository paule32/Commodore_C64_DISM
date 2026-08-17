from __future__ import annotations

import importlib.util
import sys
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_d64():
    name = "d64_stage81_test_module"
    if name in sys.modules:
        return sys.modules[name]
    sys.modules.setdefault("flags_rc", types.ModuleType("flags_rc"))
    spec = importlib.util.spec_from_file_location(name, ROOT / "d64_dism.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class Stage81C64KernalJsrCommentTests(unittest.TestCase):
    def test_official_kernal_jump_table_has_39_entries(self):
        d64 = load_d64()
        self.assertEqual(len(d64.C64_KERNAL_JSR_ROUTINES), 39)
        self.assertEqual(d64.C64_KERNAL_JSR_ROUTINES[0][:2], (0xFF81, "CINT"))
        self.assertEqual(d64.C64_KERNAL_JSR_ROUTINES[-1][:2], (0xFFF3, "IOBASE"))
        self.assertEqual(
            [addr for addr, _name, _desc in d64.C64_KERNAL_JSR_ROUTINES],
            list(range(0xFF81, 0xFFF4, 3)),
        )

    def test_clear_screen_is_e544_not_5344(self):
        d64 = load_d64()
        self.assertEqual(
            d64.c64_assembler_call_description("JSR", "$E544"),
            "Bildschirm löschen",
        )
        self.assertEqual(
            d64.c64_assembler_call_description("JSR", "#$E544"),
            "Bildschirm löschen",
        )
        self.assertIsNone(d64.c64_assembler_call_description("JSR", "$5344"))

    def test_kernal_jump_table_descriptions_are_available(self):
        d64 = load_d64()
        self.assertEqual(
            d64.c64_assembler_call_description("JSR", "$FFD2"),
            "CHROUT: Zeichen an den aktuellen Ausgabekanal schreiben",
        )
        self.assertEqual(
            d64.c64_assembler_call_description("JSR", "$FFE4"),
            "GETIN: Zeichen aus Eingabepuffer/Kanal holen",
        )
        self.assertEqual(
            d64.c64_assembler_call_description("JSR", "$FFF0"),
            "PLOT: Cursorposition lesen oder setzen",
        )

    def test_disassembly_annotates_e544_and_official_kernal_calls(self):
        d64 = load_d64()
        payload = bytes((
            0x01, 0x08,
            0x20, 0x44, 0xE5,  # JSR $E544
            0x20, 0xD2, 0xFF,  # JSR $FFD2
            0x20, 0xE4, 0xFF,  # JSR $FFE4
            0x60,
        ))
        text, load = d64.format_c64_program_disassembly(
            payload,
            suffix=".prg",
            source_name="kernal_calls.prg",
        )
        self.assertEqual(load, 0x0801)
        self.assertIn("JSR $E544", text)
        self.assertIn("Bildschirm löschen", text)
        self.assertIn("JSR $FFD2", text)
        self.assertIn("CHROUT: Zeichen an den aktuellen Ausgabekanal schreiben", text)
        self.assertIn("JSR $FFE4", text)
        self.assertIn("GETIN: Zeichen aus Eingabepuffer/Kanal holen", text)


if __name__ == "__main__":
    unittest.main()
