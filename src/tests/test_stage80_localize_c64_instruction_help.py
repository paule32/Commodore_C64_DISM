from __future__ import annotations

import importlib.util
import sys
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "d64_dism.py").read_text(encoding="utf-8")


def load_d64():
    name = "d64_stage80_test_module"
    if name in sys.modules:
        return sys.modules[name]
    sys.modules.setdefault("flags_rc", types.ModuleType("flags_rc"))
    spec = importlib.util.spec_from_file_location(name, ROOT / "d64_dism.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class Stage80LocalizeAndC64InstructionHelpTests(unittest.TestCase):
    def test_localize_dock_uses_complete_free_work_area(self):
        window = SOURCE[SOURCE.index("class ExplorerWindow(QMainWindow)"):]
        init = window[window.index("def __init__"):window.index("def _create_green_beige_window_chrome")]
        self.assertIn("self._localize_replaced_central_widget = False", init)

        start = window.index("def _localize_dock_visibility_changed")
        end = window.index("def _ensure_localize_dock", start)
        block = window[start:end]
        self.assertIn("central = self.centralWidget()", block)
        self.assertIn("central.hide()", block)
        self.assertIn("central.show()", block)
        self.assertIn("self.resizeDocks([dock], [100000], Qt.Horizontal)", block)
        self.assertIn("self.resizeDocks([dock], [100000], Qt.Vertical)", block)

    def test_jsr_e544_disassembly_keeps_description_and_bytecode(self):
        d64 = load_d64()
        text, load = d64.format_c64_program_disassembly(
            bytes((0x01, 0x08, 0x20, 0x44, 0xE5, 0x60)),
            suffix=".prg",
            source_name="demo.prg",
        )
        self.assertEqual(load, 0x0801)
        jsr = next(line for line in text.splitlines() if "JSR $E544" in line)
        self.assertIn("; Bildschirm löschen", jsr)
        self.assertIn("$0801: 20 44 E5", jsr)
        self.assertEqual(jsr.index(";") - len(jsr.split(";", 1)[0].rstrip()), 8)

    def test_jsr_hash_e544_is_supported_as_documentation_alias(self):
        d64 = load_d64()
        self.assertEqual(
            d64.c64_assembler_call_description("JSR", "#E544"),
            "Bildschirm löschen",
        )
        self.assertEqual(
            d64.c64_assembler_call_description("JSR", "#$E544"),
            "Bildschirm löschen",
        )
        self.assertEqual(
            d64.c64_assembler_call_description("JSR", "$E544"),
            "Bildschirm löschen",
        )

    def test_assembler_highlighter_has_yellow_opcode_and_white_operand(self):
        highlighter = SOURCE[
            SOURCE.index("class AssemblerSyntaxHighlighter"):
            SOURCE.index("class LineNumberArea", SOURCE.index("class AssemblerSyntaxHighlighter"))
        ]
        self.assertIn('QColor("#FFD84D")', highlighter)
        self.assertIn('QColor("#FFFFFF")', highlighter)
        self.assertIn("self.operand_format = QTextCharFormat()", highlighter)
        self.assertIn("self.setFormat(start, end - start, self.operand_format)", highlighter)
        self.assertIn("ASSEMBLER_STATEMENT_PATTERN", highlighter)

    def test_assembler_instruction_description_is_live_for_typing_and_click(self):
        editor = SOURCE[
            SOURCE.index("class SourceTextEdit(QPlainTextEdit)"):
            SOURCE.index("class SourceEditorWithMiniMap", SOURCE.index("class SourceTextEdit(QPlainTextEdit)"))
        ]
        self.assertIn('"assembler_instruction_help_frame"', editor)
        self.assertIn("self.textChanged.connect(self._schedule_instruction_help_update)", editor)
        self.assertIn("self.cursorPositionChanged.connect(", editor)
        self.assertIn("self._schedule_instruction_help_update", editor)
        self.assertIn("def _assembler_instruction_info_at_cursor", editor)
        self.assertIn("c64_assembler_call_description(mnemonic, operand)", editor)
        self.assertIn('description += f"\\nZielbeschreibung: {semantic}"', editor)
        self.assertIn("QTimer.singleShot(0, self._update_instruction_help)", editor)

    def test_instruction_help_tracks_scroll_and_resize(self):
        editor = SOURCE[
            SOURCE.index("class SourceTextEdit(QPlainTextEdit)"):
            SOURCE.index("class SourceEditorWithMiniMap", SOURCE.index("class SourceTextEdit(QPlainTextEdit)"))
        ]
        self.assertGreaterEqual(editor.count("self._position_instruction_help_frame()"), 3)
        self.assertIn("self.instruction_help_frame.hide()", editor)


if __name__ == "__main__":
    unittest.main()
