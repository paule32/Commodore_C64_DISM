from __future__ import annotations

import importlib.util
import sys
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "d64_dism.py").read_text(encoding="utf-8")


def load_d64():
    name = "d64_stage78_test_module"
    if name in sys.modules:
        return sys.modules[name]
    sys.modules.setdefault("flags_rc", types.ModuleType("flags_rc"))
    spec = importlib.util.spec_from_file_location(name, ROOT / "d64_dism.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class Stage78C64DisassemblyBorderFillTests(unittest.TestCase):
    def test_top_resize_border_has_two_pixel_radius_only_at_top(self):
        window = SOURCE[SOURCE.index("class ExplorerWindow(QMainWindow)"):]
        self.assertIn("FRAMELESS_TOP_CORNER_RADIUS = 2", window)
        start = window.index("def paintEvent(self, event) -> None:", window.index("def _sync_green_beige_menu_objects"))
        end = window.index("def nativeEvent", start)
        block = window[start:end]
        self.assertIn("frame_path.quadTo(left, top, left + radius, top)", block)
        self.assertIn("frame_path.quadTo(right, top, right, top + radius)", block)
        self.assertNotIn("drawRoundedRect", block)
        self.assertIn("frame_path.lineTo(right, bottom)", block)
        self.assertIn("frame_path.lineTo(left, bottom)", block)
        self.assertIn("def _update_frameless_corner_mask", window)
        self.assertIn("QRegion.Ellipse", window)
        self.assertIn("self.setMask(region)", window)

    def test_prg_disassembly_uses_header_load_address_and_documents_jsr_e544(self):
        d64 = load_d64()
        payload = bytes((0x01, 0x08, 0x20, 0x44, 0xE5, 0x60))
        text, load = d64.format_c64_program_disassembly(
            payload,
            suffix=".prg",
            source_name="demo.prg",
        )
        self.assertEqual(load, 0x0801)
        self.assertIn(".org $0801", text)
        self.assertIn("JSR $E544", text)
        self.assertIn("; Bildschirm löschen", text)

        instruction_lines = [
            line for line in text.splitlines()
            if line.startswith("    ") and ";" in line
        ]
        columns = {line.index(";") for line in instruction_lines}
        self.assertEqual(len(columns), 1)
        jsr = next(line for line in instruction_lines if "JSR $E544" in line)
        code = jsr.split(";", 1)[0].rstrip()
        self.assertEqual(jsr.index(";") - len(code), 8)

    def test_raw_bin_uses_0801_default(self):
        d64 = load_d64()
        text, load = d64.format_c64_program_disassembly(
            bytes((0xEA, 0x60)),
            suffix=".bin",
            source_name="raw.bin",
        )
        self.assertEqual(load, 0x0801)
        self.assertIn("Standard fuer rohe .bin-Datei", text)
        self.assertIn("NOP", text)
        self.assertIn("RTS", text)

    def test_basic_sys_stub_is_preserved_as_data_before_machine_code(self):
        d64 = load_d64()
        program = d64.assemble_mos6510_source(
            ".org $080D\n.entry $080D\nLDA #$00\nRTS\n"
        )
        text, load = d64.format_c64_program_disassembly(
            program.prg,
            suffix=".prg",
            source_name="stub.prg",
        )
        self.assertEqual(load, 0x0801)
        self.assertIn("BASIC SYS-Startstub", text)
        self.assertIn(".org $080D", text)
        self.assertIn("LDA #$00", text)

    def test_open_document_routes_prg_and_bin_to_disassembly_raw_tab(self):
        start = SOURCE.index("def open_document(self, path: Path)")
        end = SOURCE.index("def show_character_editor", start)
        block = SOURCE[start:end]
        self.assertIn('path.suffix.casefold() in {".prg", ".bin"}', block)
        self.assertIn("format_c64_program_disassembly(", block)
        self.assertIn("binary_disassembly_mode=binary_disassembly_mode", block)
        self.assertIn("C64-Disassembly im Rohdaten-Tab", block)

        doc_start = SOURCE.index("class DocumentEditor(QWidget)")
        doc_end = SOURCE.index("class ProjectOpenFileDialog", doc_start)
        doc = SOURCE[doc_start:doc_end]
        self.assertIn("if self.binary_disassembly_mode:", doc)
        self.assertIn("self.views.setCurrentWidget(self.source_page)", doc)
        self.assertIn("Kommentare duerfen deshalb niemals in den Hex-Puffer", doc)

    def test_documented_binary_ctrl_s_cannot_overwrite_original_prg(self):
        start = SOURCE.index("def _save_document(")
        end = SOURCE.index("def _assembler_output_path", start)
        block = SOURCE[start:end]
        self.assertIn("save_disassembly_source", block)
        self.assertIn("if save_disassembly_source and not save_as:", block)
        self.assertIn("save_as = True", block)
        self.assertIn('document.path.with_suffix(".asm")', SOURCE)

    def test_fill_screen_example_assembles_and_uses_exact_1000_byte_range(self):
        d64 = load_d64()
        example = ROOT / "examples" / "assembler" / "c64_fill_screen_stage78.asm"
        source = example.read_text(encoding="utf-8")
        program = d64.assemble_mos6510_source(source)
        self.assertTrue(program.prg)
        self.assertIn("LDA #<1000", source)
        self.assertIn("LDA #>1000", source)
        self.assertIn("FillRange:", source)
        self.assertIn("FillLine:", source)
        self.assertIn("FillScreen:", source)
        self.assertIn("$0400-$07E7", source)


if __name__ == "__main__":
    unittest.main()
