from __future__ import annotations

import unittest

from c64basic import C64BasicError, compile_basic_to_assembly
from d64_dism import assemble_mos6510_source


class C64BasicCompilerTests(unittest.TestCase):
    def test_compiles_core_basic_statements_to_assemblable_6510(self) -> None:
        source = """10 PRINT "HALLO C64"
20 A=2+3*4
30 PRINT A
40 FOR I=1 TO 3
50 PRINT I;
60 NEXT I
70 IF A>=14 THEN 90
80 GOTO 100
90 POKE 53280,0
100 END
"""
        result = compile_basic_to_assembly(source, filename="demo.bas")
        self.assertIn(".org $080D", result.assembly)
        self.assertIn("__basic_line_10:", result.assembly)
        self.assertIn("jsr __basic_print_string", result.assembly)
        self.assertIn("jsr __basic_mul", result.assembly)
        self.assertIn("sta ($FB),y", result.assembly)
        program = assemble_mos6510_source(
            result.assembly, filename="demo.generated.asm"
        )
        self.assertEqual(program.load_address, 0x0801)
        self.assertEqual(program.entry_address, 0x080D)
        self.assertTrue(program.has_basic_stub)
        self.assertGreater(program.instruction_count, 100)

    def test_supports_gosub_return_sys_and_relations(self) -> None:
        source = """10 A=1
20 GOSUB 100
30 IF A<>2 THEN 60
40 SYS 65520
50 END
60 STOP
100 A=A+1
110 RETURN
"""
        result = compile_basic_to_assembly(source, filename="flow.bas")
        self.assertIn("jsr __basic_line_100", result.assembly)
        self.assertIn("jsr $FFF0", result.assembly)
        self.assertIn("jsr __basic_cmp_ne", result.assembly)
        assemble_mos6510_source(result.assembly, filename="flow.asm")

    def test_rem_keeps_colons_inside_comment(self) -> None:
        result = compile_basic_to_assembly(
            '10 REM DIES:BLEIBT:EIN KOMMENTAR\n20 END\n'
        )
        self.assertNotIn("BASIC-Anweisung wird nicht unterstützt", result.assembly)
        assemble_mos6510_source(result.assembly, filename="rem.asm")

    def test_rejects_missing_jump_target(self) -> None:
        with self.assertRaises(C64BasicError) as caught:
            compile_basic_to_assembly("10 GOTO 999\n20 END\n")
        self.assertIn("Sprungziel 999", str(caught.exception))

    def test_rejects_amiga_target(self) -> None:
        with self.assertRaises(C64BasicError):
            compile_basic_to_assembly("10 END\n", target="amiga")


class BasicGuiIntegrationSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        from pathlib import Path
        cls.source = (Path(__file__).resolve().parents[1] / "d64_dism.py").read_text(
            encoding="utf-8"
        )

    def test_basic_is_a_compiled_document(self) -> None:
        self.assertIn("def is_basic_document", self.source)
        self.assertIn("def _compile_basic_document", self.source)
        self.assertIn("from c64basic import C64BasicError", self.source)
        self.assertIn("self._basic_assembly_output_path(document)", self.source)
        self.assertIn("return self._compile_basic_document(document)", self.source)

    def test_new_documents_are_added_and_project_saved(self) -> None:
        self.assertIn("def _ensure_project_for_new_document", self.source)
        self.assertIn("Unbenannt_Projekt_", self.source)
        self.assertIn("return self.create_new_project_item(root)", self.source)
        self.assertIn("if self.current_project_path is not None:\n                self.save_project()", self.source)

    def test_requested_project_context_menu(self) -> None:
        for label in ("Hilfe", "Hinzufügen", "Einträge löschen"):
            self.assertIn(f'menu.addAction("{label}")', self.source)
        self.assertIn("root.takeChildren()", self.source)


if __name__ == "__main__":
    unittest.main()
