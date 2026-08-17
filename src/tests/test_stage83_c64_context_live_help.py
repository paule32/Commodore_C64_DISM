from __future__ import annotations

import importlib.util
import sys
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "d64_dism.py").read_text(encoding="utf-8")


def load_d64():
    name = "d64_stage83_test_module"
    if name in sys.modules:
        return sys.modules[name]
    sys.modules.setdefault("flags_rc", types.ModuleType("flags_rc"))
    spec = importlib.util.spec_from_file_location(name, ROOT / "d64_dism.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class Stage83C64ContextAndLiveHelpTests(unittest.TestCase):
    def test_lda_screen_code_then_sta_0400_is_context_annotated(self):
        d64 = load_d64()
        text, load = d64.format_c64_program_disassembly(
            bytes((
                0x01, 0x08,
                0xA9, 0x01,       # LDA #$01
                0x8D, 0x00, 0x04, # STA $0400
                0x60,
            )),
            suffix=".prg",
            source_name="screen_a.prg",
        )
        self.assertEqual(load, 0x0801)
        lda = next(line for line in text.splitlines() if "LDA #$01" in line)
        sta = next(line for line in text.splitlines() if "STA $0400" in line)
        self.assertIn('Bildschirmcode für "A"', lda)
        self.assertIn("$0801: A9 01", lda)
        self.assertIn("linke obere Bildschirmposition", sta)
        self.assertIn("$0803: 8D 00 04", sta)

    def test_lda_color_then_sta_d800_is_context_annotated(self):
        d64 = load_d64()
        text, load = d64.format_c64_program_disassembly(
            bytes((
                0x01, 0x08,
                0xA9, 0x01,       # LDA #$01
                0x8D, 0x00, 0xD8, # STA $D800
                0x60,
            )),
            suffix=".prg",
            source_name="color_white.prg",
        )
        self.assertEqual(load, 0x0801)
        lda = next(line for line in text.splitlines() if "LDA #$01" in line)
        sta = next(line for line in text.splitlines() if "STA $D800" in line)
        self.assertIn("Farbe weis", lda)
        self.assertIn("$0801: A9 01", lda)
        self.assertIn("Farbe der linken oberen Position", sta)
        self.assertIn("$0803: 8D 00 D8", sta)

    def test_context_requires_direct_machine_instruction_pair(self):
        d64 = load_d64()
        text, _load = d64.format_c64_program_disassembly(
            bytes((
                0x01, 0x08,
                0xA9, 0x01,       # LDA #$01
                0xEA,             # NOP
                0x8D, 0x00, 0x04, # STA $0400
                0x60,
            )),
            suffix=".prg",
            source_name="not_direct.prg",
        )
        lda = next(line for line in text.splitlines() if "LDA #$01" in line)
        sta = next(line for line in text.splitlines() if "STA $0400" in line)
        self.assertNotIn("Bildschirmcode", lda)
        self.assertNotIn("linke obere Bildschirmposition", sta)
        self.assertIn("$0801: A9 01", lda)
        self.assertIn("$0804: 8D 00 04", sta)

    def test_live_help_current_value_is_separate_green_row(self):
        editor = SOURCE[
            SOURCE.index("class SourceTextEdit(QPlainTextEdit)"):
            SOURCE.index(
                "class SourceEditorWithMiniMap",
                SOURCE.index("class SourceTextEdit(QPlainTextEdit)"),
            )
        ]
        self.assertIn('"assembler_instruction_help_current"', editor)
        self.assertIn('self.instruction_help_current.setText(f"Aktuell: {operand}")', editor)
        self.assertIn("#66FF66", editor)
        self.assertIn("#008000", editor)
        self.assertNotIn('header += f"    Aktuell: {operand}"', editor)

    def test_live_help_wraps_operands_and_warning_has_blank_line(self):
        editor = SOURCE[
            SOURCE.index("class SourceTextEdit(QPlainTextEdit)"):
            SOURCE.index(
                "class SourceEditorWithMiniMap",
                SOURCE.index("class SourceTextEdit(QPlainTextEdit)"),
            )
        ]
        self.assertIn("metrics.horizontalAdvance(one_line) > content_width", editor)
        self.assertIn('header = mnemonic + "\\n" + operands', editor)
        self.assertIn('"\\n\\nHinweis: interne ROM-Routine; "', editor)


if __name__ == "__main__":
    unittest.main()
