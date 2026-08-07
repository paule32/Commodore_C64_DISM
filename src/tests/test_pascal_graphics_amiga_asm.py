from __future__ import annotations

import json
import unittest

from pathlib import Path

from amiga500 import assemble_amiga_boot_source


ROOT = Path(__file__).resolve().parents[1]
GRAPHICS_DIR = ROOT / "c64pascal" / "units" / "System"


class PascalGraphicsAmigaAssemblyTests(unittest.TestCase):
    def test_all_pui_routines_have_assembly_exports(self) -> None:
        pui = json.loads(
            (GRAPHICS_DIR / "Graphics.pui").read_text(encoding="utf-8")
        )
        assembly = (
            GRAPHICS_DIR / "Graphics.amiga.asm"
        ).read_text(encoding="utf-8")

        routines = pui["interface"]["routines"]
        self.assertEqual(len(routines), 15)

        for routine in routines:
            symbol = routine["symbol"]
            self.assertIn(f"xdef {symbol}", assembly)
            self.assertIn(f"{symbol}:", assembly)

    def test_amiga_graphics_module_assembles_with_boot_program(self) -> None:
        module = (
            GRAPHICS_DIR / "Graphics.amiga.asm"
        ).read_text(encoding="utf-8").rstrip().splitlines()
        if module and module[-1].strip().casefold() == "end":
            module.pop()

        source = (
            ".bootable\n"
            "section code,code\n"
            "xdef _start\n"
            "_start:\n"
            "    move.l #$0007FFFC,sp\n"
            "    bsr __pas_System_Graphics_InitGraphics\n"
            "    move.w #$000A,-(sp)\n"
            "    move.w #$0014,-(sp)\n"
            "    move.w #$0002,-(sp)\n"
            "    bsr __pas_System_Graphics_SetPixel\n"
            "    addq.l #6,sp\n"
            "    move.w #$000A,-(sp)\n"
            "    move.w #$0014,-(sp)\n"
            "    bsr __pas_System_Graphics_GetPixel\n"
            "    addq.l #4,sp\n"
            "    move.w #$0001,-(sp)\n"
            "    bsr __pas_System_Graphics_DoneGraphics\n"
            "    addq.l #2,sp\n"
            ".loop:\n"
            "    bra .loop\n"
            + "\n".join(module)
            + "\nend\n"
        )

        assembled = assemble_amiga_boot_source(
            source,
            filename="graphics_amiga_smoke.asm",
        )
        self.assertEqual(len(assembled.adf), 901120)
        self.assertGreater(assembled.instruction_count, 1000)

    def test_copper_reloads_bitplane_pointers_each_frame(self) -> None:
        assembly = (
            GRAPHICS_DIR / "Graphics.amiga.asm"
        ).read_text(encoding="utf-8")

        self.assertIn("__gfx_install_graphics_copper:", assembly)
        self.assertIn("move.l #$00010000,d0", assembly)
        self.assertIn("move.l d0,$0080(a0)", assembly)
        self.assertIn("move.w #$0000,$0088(a0)", assembly)
        self.assertIn("move.w #$8380,$0096(a0)", assembly)
        self.assertIn("move.l #$00E00002,(a1)+", assembly)
        self.assertIn("move.l #$00E20000,(a1)+", assembly)
        self.assertIn("move.l #$00EC0002,(a1)+", assembly)
        self.assertIn("move.l #$00EE6000,(a1)+", assembly)
        self.assertNotIn("move.w #$8300,$0096(a0)", assembly)

    def test_pascal_text_runtime_uses_copper(self) -> None:
        compiler_source = (
            ROOT / "c64pascal" / "compiler.py"
        ).read_text(encoding="utf-8")

        self.assertIn("install_text_copper", compiler_source)
        self.assertIn("#$8380,$0096(a0)", compiler_source)
        self.assertIn("#$0001002E", compiler_source)
        self.assertIn("#$00010032", compiler_source)


if __name__ == "__main__":
    unittest.main()
