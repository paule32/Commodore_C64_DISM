from __future__ import annotations

import unittest
from pathlib import Path

from d64_dism import AssemblerError, assemble_mos6510_source

ROOT = Path(__file__).resolve().parents[1]
ASM_PATH = ROOT / "runtime" / "graphics" / "c64" / "graphics_c64.asm"
HEADER_PATH = ROOT / "c64c" / "include" / "graphics.h"
PASCAL_WRAPPER = ROOT / "c64pascal" / "units" / "System" / "Graphics.c64.c"


class C64MulticolorGraphicsTargetTests(unittest.TestCase):
    def test_c64_header_links_separate_asm_target(self) -> None:
        source = HEADER_PATH.read_text(encoding="utf-8")
        c64_block = source.split(
            "#if defined(__D64_TARGET_C64__)", 1
        )[1].split("#endif", 1)[0]

        self.assertIn("graphics/c64/graphics_c64.asm", c64_block)
        self.assertNotIn("graphics/common/graphics_api.c", c64_block)
        self.assertNotIn("graphics_target.c", c64_block)

    def test_pascal_wrapper_uses_same_c64_asm_target(self) -> None:
        source = PASCAL_WRAPPER.read_text(encoding="utf-8")
        self.assertIn("graphics/c64/graphics_c64.asm", source)
        self.assertNotIn("graphics/common/graphics_api.c", source)
        self.assertNotIn("graphics_target.c", source)

    def test_target_assembles_inside_bank2_runtime_window(self) -> None:
        source = ".nostub\n" + ASM_PATH.read_text(encoding="utf-8")
        program = assemble_mos6510_source(source)

        self.assertEqual(program.load_address, 0x4000)
        self.assertGreaterEqual(program.symbols["initgraphics"], 0x4000)
        self.assertGreaterEqual(program.symbols["setpixel"], 0x4000)
        self.assertLess(program.end_address, 0x8000)

    def test_linked_layout_keeps_bank2_free(self) -> None:
        module = ASM_PATH.read_text(encoding="utf-8")
        source = """.org $080D
.entry start
.basic
start:
    jsr InitGraphics
hang:
    jmp hang
""" + module
        program = assemble_mos6510_source(source)

        self.assertEqual(program.entry_address, 0x080D)
        self.assertEqual(
            program.symbols["__d64_graphics_reserve_start"],
            0x8000,
        )
        self.assertEqual(
            program.symbols["__d64_graphics_reserve_end"],
            0xBFFF,
        )
        self.assertGreaterEqual(program.symbols["initgraphics"], 0x4000)
        self.assertLess(program.symbols["initgraphics"], 0x8000)

    def test_reserved_vic_bank_overlap_is_rejected(self) -> None:
        source = """.org $080D
.entry start
.nostub
__d64_graphics_reserve_start = $8000
__d64_graphics_reserve_end = $BFFF
start:
    rts
.org $8000
    .byte $AA
"""
        with self.assertRaisesRegex(
            AssemblerError,
            "reservierten C64-Grafikspeicher",
        ):
            assemble_mos6510_source(source)

    def test_application_and_direct_runtime_use_separate_windows(self) -> None:
        module = ASM_PATH.read_text(encoding="utf-8")
        source = """.org $080D
.entry start
.basic
start:
    jsr InitGraphics
    jmp start
.org $3FFF
    .byte $AA
""" + module
        program = assemble_mos6510_source(source)

        self.assertEqual(program.symbols["__d64_graphics_reserve_start"], 0x8000)
        self.assertEqual(program.symbols["__d64_graphics_runtime_start"], 0x4000)
        self.assertGreaterEqual(program.symbols["initgraphics"], 0x4000)
        self.assertLess(program.symbols["initgraphics"], 0x8000)

    def test_init_clears_before_enabling_bitmap_display(self) -> None:
        source = ASM_PATH.read_text(encoding="utf-8")
        init = source.split("InitGraphics:", 1)[1].split(
            "; ---------------------------------------------------------------------------\n; DoneGraphics",
            1,
        )[0]
        self.assertLess(
            init.index("jsr __gfx_clear_graphics"),
            init.index("ora #$38"),
        )

    def test_multicolor_palette_has_three_local_slots(self) -> None:
        source = ASM_PATH.read_text(encoding="utf-8")
        self.assertIn("GFX_PALETTE_BASE = $8800", source)
        self.assertIn("GFX_COLOR_BASE   = $D800", source)
        self.assertIn("__gfx_allocate_slot1:", source)
        self.assertIn("__gfx_allocate_slot2:", source)
        self.assertIn("__gfx_allocate_slot3:", source)
        self.assertIn("__gfx_code_patterns:", source)

    def test_vic_multicolor_bit_is_enabled(self) -> None:
        source = ASM_PATH.read_text(encoding="utf-8")
        init = source.split("InitGraphics:", 1)[1].split(
            "; ---------------------------------------------------------------------------\n; DoneGraphics",
            1,
        )[0]
        self.assertIn("and #$E7", init)
        self.assertIn("ora #$18", init)
        self.assertIn("sta $D016", init)


    def test_vic_screen_matrix_avoids_bank2_character_rom_shadow(self) -> None:
        source = ASM_PATH.read_text(encoding="utf-8")
        self.assertIn("GFX_PALETTE_BASE = $8800", source)
        self.assertIn("GFX_SCREEN_BASE = $8C00", source)
        self.assertIn("lda #$38", source)
        self.assertNotIn("GFX_SCREEN_BASE = $9C00", source)

    def test_all_1000_palette_screen_and_color_bytes_are_cleared(self) -> None:
        source = ASM_PATH.read_text(encoding="utf-8")
        self.assertIn("sta $8B00,x", source)
        self.assertIn("sta $8F00,x", source)
        self.assertIn("sta $DB00,x", source)
        self.assertIn("cpx #$E8", source)
        self.assertNotIn("ldx #$E7\n__gfx_clear_palette_tail", source)
        self.assertNotIn("ldx #$E7\n__gfx_clear_screen_tail", source)

    def test_graphics_linked_c_program_uses_persistent_end_loop(self) -> None:
        source = (ROOT / "c64c" / "compiler.py").read_text(encoding="utf-8")
        self.assertIn(
            'Path(filename).name.casefold() == "graphics_c64.asm"',
            source,
        )
        self.assertIn(
            'self.emitter.emit("    jmp __c_program_end", source_line)',
            source,
        )


    def test_bitmap_ram_is_visible_to_cpu_during_graphics(self) -> None:
        source = ASM_PATH.read_text(encoding="utf-8")
        init = source.split("InitGraphics:", 1)[1].split(
            "; ---------------------------------------------------------------------------\n; DoneGraphics",
            1,
        )[0]

        # $A000-$BFFF normally reads BASIC ROM.  LORAM must be cleared before
        # any bitmap read/modify/write operation can occur.
        self.assertIn("sta __gfx_saved_cpu_port", init)
        self.assertIn("and #$FE", init)
        self.assertIn("sta $01", init)
        self.assertLess(init.index("and #$FE"), init.index("jsr __gfx_clear_graphics"))

    def test_done_graphics_restores_cpu_memory_mapping(self) -> None:
        source = ASM_PATH.read_text(encoding="utf-8")
        done = source.split("DoneGraphics:", 1)[1].split(
            "; ---------------------------------------------------------------------------\n; SetPixel",
            1,
        )[0]
        self.assertIn("lda __gfx_saved_cpu_port", done)
        self.assertIn("sta $01", done)

    def test_setpixel_reads_bitmap_ram_not_basic_rom_contract(self) -> None:
        source = ASM_PATH.read_text(encoding="utf-8")
        self.assertEqual(
            source.count("__gfx_saved_cpu_port:.byte $37"),
            1,
        )
        self.assertIn("lda (GFX_BITMAP_LO),y", source)
        self.assertIn("GFX_BITMAP_BASE = $A000", source)

    def test_end_directive_is_accepted_as_noop(self) -> None:
        program = assemble_mos6510_source(
            ".org $080D\n.entry start\n.nostub\nstart:\n    rts\nend\n"
        )
        self.assertEqual(program.entry_address, 0x080D)


if __name__ == "__main__":
    unittest.main()
