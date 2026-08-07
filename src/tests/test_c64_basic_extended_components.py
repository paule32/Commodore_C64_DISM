from __future__ import annotations

import unittest

from c64basic import C64BasicError, compile_basic_to_assembly
from d64_dism import assemble_mos6510_source


class C64BasicExtendedComponentTests(unittest.TestCase):
    def assemble(self, source: str, name: str = "extended.bas"):
        result = compile_basic_to_assembly(source, filename=name)
        program = assemble_mos6510_source(
            result.assembly,
            filename=name.rsplit(".", 1)[0] + ".generated.asm",
        )
        self.assertEqual(program.load_address, 0x0801)
        self.assertEqual(program.entry_address, 0x080D)
        self.assertLess(program.end_address, 0xA000)
        return result, program

    def test_float_literals_variables_and_rom_arithmetic(self) -> None:
        result, _program = self.assemble(
            """10 A=1.5
20 B=2.25
30 C=A*B/0.5
40 PRINT C
50 END
""",
            "float.bas",
        )
        self.assertIn("jsr __basic_mul", result.assembly)
        self.assertIn("jsr __basic_div", result.assembly)
        self.assertIn("__basic_var_A: .fill 5, $00", result.assembly)
        self.assertIn(".byte $81, $40, $00, $00, $00", result.assembly)  # 1.5
        self.assertIn(".byte $82, $10, $00, $00, $00", result.assembly)  # 2.25
        self.assertIn("jsr $BDDD", result.assembly)  # FOUT

    def test_string_variables_concatenation_and_comparison(self) -> None:
        result, _program = self.assemble(
            """10 A$="HELLO"
20 B$=A$+" WORLD"
30 IF B$<>"HELLO WORLD" THEN 60
40 PRINT B$
50 END
60 STOP
""",
            "strings.bas",
        )
        self.assertIn("__basic_str_A_: .fill 256, $00", result.assembly)
        self.assertIn("jsr __basic_string_append", result.assembly)
        self.assertIn("jsr __basic_string_compare", result.assembly)
        self.assertIn("__basic_string_expr: .fill 256, $00", result.assembly)

    def test_numeric_integer_and_string_arrays(self) -> None:
        result, _program = self.assemble(
            """10 DIM F(3),I%(2,2),S$(2)
20 F(1)=3.5
30 I%(1,2)=42
40 S$(1)="ARRAY"
50 PRINT F(1),I%(1,2),S$(1)
60 END
""",
            "arrays.bas",
        )
        self.assertIn("__basic_array_F: .fill 20, $00", result.assembly)
        self.assertIn("__basic_array_I_: .fill 18, $00", result.assembly)
        self.assertIn("__basic_array_S_: .fill 768, $00", result.assembly)
        self.assertIn("jsr __basic_u16_mul", result.assembly)
        self.assertIn("jsr __basic_bad_subscript", result.assembly)

    def test_data_read_and_restore(self) -> None:
        result, _program = self.assemble(
            """10 DATA 3.14,"TEXT",7
20 READ A,B$,I%
30 RESTORE 10
40 READ C
50 PRINT A,B$,I%,C
60 END
""",
            "data.bas",
        )
        self.assertIn("__basic_data_line_10:", result.assembly)
        self.assertIn("jsr __basic_data_read_field", result.assembly)
        self.assertIn("lda #<__basic_data_line_10", result.assembly)
        self.assertIn("$04, $33, $2E, $31, $34", result.assembly)
        self.assertIn("$04, $54, $45, $58, $54", result.assembly)

    def test_input_get_and_string_numeric_conversion(self) -> None:
        result, _program = self.assemble(
            """10 INPUT "NAME";N$
20 INPUT "VALUE";A
30 GET K$
40 GET C%
50 PRINT N$,A,K$,C%
60 END
""",
            "input.bas",
        )
        self.assertIn("jsr __basic_read_line", result.assembly)
        self.assertIn("jsr __basic_input_next_field", result.assembly)
        self.assertIn("jsr __basic_field_to_float", result.assembly)
        self.assertIn("jsr $FFE4", result.assembly)
        self.assertIn("$B7B5", result.assembly)

    def test_kernal_file_and_device_channels(self) -> None:
        result, _program = self.assemble(
            """10 OPEN 2,8,2,"TEST,S,W"
20 PRINT#2,"VALUE";12.5
30 CLOSE 2
40 OPEN 2,8,2,"TEST,S,R"
50 INPUT#2,A$,B
60 GET#2,C$
70 CLOSE 2
80 OPEN 15,8,15
90 CMD 15
100 PRINT "I"
110 CLOSE 15
120 END
""",
            "channels.bas",
        )
        for address in ("$FFBA", "$FFBD", "$FFC0", "$FFC3", "$FFC6", "$FFC9", "$FFCC", "$FFCF"):
            self.assertIn(address, result.assembly)
        self.assertIn("__basic_lfn", result.assembly)
        self.assertIn("__basic_device", result.assembly)
        self.assertIn("__basic_secondary", result.assembly)

    def test_extended_numeric_functions(self) -> None:
        result, _program = self.assemble(
            """10 A=ABS(-1.5)
20 B=INT(2.9)
30 C=SGN(-4)
40 D=PEEK(53280)
50 S$="123.5"
60 E=VAL(S$)
70 F=LEN(S$)
80 G=ASC("A")
90 H$=CHR$(65)+STR$(E)
100 PRINT A,B,C,D,E,F,G,H$
110 END
""",
            "functions.bas",
        )
        self.assertIn("jsr $BC58", result.assembly)
        self.assertIn("jsr $BCCC", result.assembly)
        self.assertIn("jsr $BC39", result.assembly)
        self.assertIn("jsr __basic_float_to_string_term", result.assembly)

    def test_string_append_preserves_16bit_base_pointer(self) -> None:
        result, _program = self.assemble(
            """10 A$="A"
20 A$=A$+"B"
30 PRINT A$
40 END
""",
            "string_page.bas",
        )
        self.assertIn("__basic_string_base_ptr: .word $0000", result.assembly)
        self.assertIn("sta __basic_string_base_ptr+1", result.assembly)
        self.assertIn("lda __basic_string_base_ptr+1", result.assembly)
        self.assertNotIn("sbc __basic_string_dest_length", result.assembly)

    def test_auto_dim_and_static_memory_guard(self) -> None:
        result, _program = self.assemble(
            "10 A(2)=7\n20 PRINT A(2)\n30 END\n",
            "autodim.bas",
        )
        self.assertTrue(any("automatisch" in warning for warning in result.warnings))
        with self.assertRaises(C64BasicError):
            compile_basic_to_assembly("10 DIM S$(200)\n20 END\n")
        with self.assertRaises(C64BasicError):
            compile_basic_to_assembly("10 DIM A(2,2,2)\n20 END\n")


if __name__ == "__main__":
    unittest.main()
