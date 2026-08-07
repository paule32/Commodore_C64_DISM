from __future__ import annotations

import struct
import unittest
import inspect

from pathlib import Path

from amiga500 import (
    ADF_SIZE,
    BOOT_BLOCK_SIZE,
    BOOT_PAYLOAD_ADDRESS,
    BOOT_PAYLOAD_OFFSET,
    HUNK_CODE,
    HUNK_END,
    HUNK_HEADER,
    AmigaAssemblerError,
    assemble_amiga_boot_source,
    assemble_amiga_source,
)
from c64c import C64CError, compile_c_to_assembly
from c64pascal import C64PascalError, compile_pascal_to_assembly


ROOT = Path(__file__).resolve().parents[1]


class Amiga500TargetTests(unittest.TestCase):
    @staticmethod
    def _end_around_sum(data: bytes) -> int:
        total = 0
        for (value,) in struct.iter_unpack(">I", data):
            previous = total
            total = (total + value) & 0xFFFFFFFF
            if total < previous:
                total = (total + 1) & 0xFFFFFFFF
        return total

    def test_minimal_hunk_is_big_endian_and_executable(self) -> None:
        program = assemble_amiga_source(
            "section code,code\n"
            "xdef _start\n"
            "_start:\n"
            "    moveq #0,d0\n"
            "    rts\n"
        )
        self.assertEqual(program.code, bytes.fromhex("70004e75"))
        longs = struct.unpack(
            ">10I",
            program.executable,
        )
        self.assertEqual(longs[0], HUNK_HEADER)
        self.assertEqual(longs[6], HUNK_CODE)
        self.assertEqual(longs[-1], HUNK_END)

    def test_pascal_advanced_types_generate_68000(self) -> None:
        source = (
            ROOT / "examples" / "c64pascal" / "advanced_types.pas"
        ).read_text(encoding="utf-8")
        generated = compile_pascal_to_assembly(
            source,
            filename="advanced_types.pas",
            target="amiga",
        )
        self.assertIn("Motorola-68000", generated.assembly)
        self.assertIn("Counter", source)
        self.assertIn("bsr __pas_method_tcounter_getvalue", generated.assembly)
        self.assertIn(".bootable", generated.assembly)
        program = assemble_amiga_boot_source(generated.assembly)
        self.assertEqual(len(program.adf), ADF_SIZE)
        self.assertGreater(program.instruction_count, 50)

    def test_pascal_compiler_public_api_accepts_target(self) -> None:
        parameters = inspect.signature(
            compile_pascal_to_assembly
        ).parameters
        self.assertIn("target", parameters)
        self.assertEqual(parameters["target"].default, "c64")

    def test_c_printf_generates_68000(self) -> None:
        source = (
            '#include <stdio.h>\n'
            'int main(void) {\n'
            '  int counter = 5;\n'
            '  printf("Counter = %d\\n", counter);\n'
            '  return 0;\n'
            '}\n'
        )
        generated = compile_c_to_assembly(
            source,
            filename="hello_amiga.c",
            include_paths=[ROOT / "examples" / "c64c" / "include"],
            target="amiga",
        )
        self.assertIn("Von C erzeugter Motorola-68000-Assembler", generated.assembly)
        self.assertIn("__c_print_int16", generated.assembly)
        self.assertIn(".bootable", generated.assembly)
        program = assemble_amiga_boot_source(generated.assembly)
        self.assertEqual(len(program.adf), ADF_SIZE)

    def test_c64_target_remains_default(self) -> None:
        generated = compile_pascal_to_assembly(
            "program DefaultTarget; begin WriteLn('OK'); end.",
            filename="default_target.pas",
        )
        self.assertIn("MOS-6510", generated.assembly)
        self.assertIn(".basic", generated.assembly)
        self.assertNotIn(".bootable", generated.assembly)
        self.assertNotIn("$00DFF000", generated.assembly)

    def test_undefined_m68k_label_reports_source_line(self) -> None:
        with self.assertRaises(AmigaAssemblerError) as context:
            assemble_amiga_source(
                "_start:\n"
                "    bra missing\n"
            )
        self.assertEqual(context.exception.line, 2)

    def test_standalone_blitter_example_is_bootable_adf(self) -> None:
        source = (
            ROOT / "examples" / "amiga" / "blitter_green.m68k"
        ).read_text(encoding="utf-8")
        program = assemble_amiga_boot_source(source)

        self.assertEqual(len(program.adf), ADF_SIZE)
        self.assertEqual(len(program.boot_block), BOOT_BLOCK_SIZE)
        self.assertEqual(program.boot_block[:4], b"DOS\0")
        self.assertEqual(self._end_around_sum(program.boot_block), 0xFFFFFFFF)
        self.assertEqual(program.entry_offset, BOOT_PAYLOAD_ADDRESS)
        self.assertEqual(
            program.adf[
                BOOT_PAYLOAD_OFFSET:BOOT_PAYLOAD_OFFSET + len(program.code)
            ],
            program.code,
        )

        self.assertIn("$180(a5)", source)
        self.assertIn("#$00F0", source)
        self.assertIn("#$0100", source)
        self.assertIn("#$8240", source)
        self.assertIn("#$0041", source)
        self.assertIn("#$4000", source)

    def test_trackloader_accepts_payload_larger_than_bootblock(self) -> None:
        source = (
            ".bootable\n"
            "_start:\n"
            ".forever:\n"
            "    bra .forever\n"
            "    ds.b 2048\n"
        )
        program = assemble_amiga_boot_source(source)
        self.assertGreater(len(program.code), BOOT_BLOCK_SIZE)
        self.assertEqual(program.entry_offset, BOOT_PAYLOAD_ADDRESS)
        self.assertEqual(
            program.adf[
                BOOT_PAYLOAD_OFFSET:BOOT_PAYLOAD_OFFSET + len(program.code)
            ],
            program.code,
        )

    def test_pascal_writeln_uses_bitmap_font_and_direct_ocs(self) -> None:
        source = (
            ROOT / "examples" / "amiga" / "bitmap_text_pascal.pas"
        ).read_text(encoding="utf-8")
        generated = compile_pascal_to_assembly(
            source,
            filename="bitmap_text_pascal.pas",
            target="amiga",
        )
        assembly = generated.assembly
        self.assertIn("__pas_font_8x8:", assembly)
        self.assertIn("bsr __pas_print_string", assembly)
        self.assertIn("bsr __pas_set_text_color", assembly)
        self.assertIn("move.l #$01001200,(a1)+", assembly)
        self.assertIn("move.w d0,$0182(a0)", assembly)
        self.assertNotIn("dos.library", assembly)
        self.assertNotIn("jsr -48(a6)", assembly)
        program = assemble_amiga_boot_source(assembly)
        self.assertGreater(len(program.code), BOOT_BLOCK_SIZE)

    def test_c_printf_uses_separate_amiga_bitmap_runtime(self) -> None:
        source = (
            ROOT / "examples" / "amiga" / "bitmap_text_c.c"
        ).read_text(encoding="utf-8")
        generated = compile_c_to_assembly(
            source,
            filename=str(ROOT / "examples" / "amiga" / "bitmap_text_c.c"),
            target="amiga",
        )
        assembly = generated.assembly
        self.assertIn("__c_font_8x8:", assembly)
        self.assertIn("bsr __c_print_string", assembly)
        self.assertIn("bsr __c_set_text_color", assembly)
        self.assertNotIn("__pas_", assembly)
        self.assertNotIn("$FFD2", assembly)
        self.assertNotIn("dos.library", assembly)
        program = assemble_amiga_boot_source(assembly)
        self.assertEqual(len(program.adf), ADF_SIZE)

    def test_amiga_color_api_is_not_emitted_for_c64(self) -> None:
        with self.assertRaises(C64PascalError) as pascal_error:
            compile_pascal_to_assembly(
                "program P; begin SetTextColor($0F0, $000) end.",
                filename="separate_runtime.pas",
                target="c64",
            )
        self.assertIn("System.Graphics", str(pascal_error.exception))

        with self.assertRaises(C64CError) as c_error:
            compile_c_to_assembly(
                "#include <amiga.h>\n"
                "int main(void) {\n"
                "  amiga_set_text_color(AMIGA_GREEN, AMIGA_BLACK);\n"
                "  return 0;\n"
                "}\n",
                filename="separate_runtime.c",
                target="c64",
            )
        self.assertIn("Amiga-spezifische", str(c_error.exception))


if __name__ == "__main__":
    unittest.main()
