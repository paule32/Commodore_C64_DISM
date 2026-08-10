from __future__ import annotations

import importlib.util
import struct
import sys
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from d64dbase import compile_dbase_to_assembly


def load_d64_dism():
    sys.modules.setdefault("flags_rc", types.ModuleType("flags_rc"))
    name = "_d64_dism_dbase_numeric_variable_fix_test"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, ROOT / "d64_dism.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("d64_dism.py konnte nicht geladen werden")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class DBaseNumericVariableRuntimeFixTests(unittest.TestCase):
    def test_exact_user_case_is_14(self):
        source = 'X = 2 + 3 * 4\n? "Wert von X = " + X\n'
        for target in ("pe32", "pe64"):
            result = compile_dbase_to_assembly(source, target=target)
            self.assertEqual(result.transcript, "Wert von X = 14\r\n")
            self.assertIn("fmulp", result.assembly)
            self.assertIn("faddp", result.assembly)
            self.assertIn("fstp qword ptr [__dbase_var_x_num]", result.assembly)
            self.assertIn("fld qword ptr [__dbase_var_x_num]", result.assembly)

    def test_pe32_gcvt_uses_distinct_high_dword_label(self):
        result = compile_dbase_to_assembly('X=14\n? X\n', target="pe32")
        self.assertIn("push dword ptr [__dbase_temp_number_hi]", result.assembly)
        self.assertIn("__dbase_temp_number_hi:", result.assembly)
        self.assertNotIn("[__dbase_temp_number+4]", result.assembly)

    def test_pe32_symbol_plus_displacement_relocation_keeps_addend(self):
        d64 = load_d64_dism()
        asm = """bits 32
section .text
global _start
entry _start
_start:
    mov eax, dword ptr [value+4]
    push 0
    call ExitProcess
section .data
value:
    dd 0x11111111, 0x22222222
import ExitProcess, "kernel32.dll", "ExitProcess"
"""
        obj = d64.assemble_pe32_object_source(asm, filename="disp32.asm")
        # MOV EAX, [disp32] => A1 imm32 in this assembler path or 8B /r disp32.
        # Locate the DIR32 relocation and verify that its encoded addend is 4.
        dirs = [r for r in obj.relocations if r.symbol == "value" and r.relocation_type == d64.IMAGE_REL_I386_DIR32]
        self.assertEqual(len(dirs), 1)
        reloc = dirs[0]
        self.assertEqual(struct.unpack_from("<i", obj.code, reloc.offset)[0], 4)

        program = d64.assemble_pe32_source(asm, filename="disp32.asm", gui=False)
        patched = struct.unpack_from("<I", program.code, reloc.offset)[0]
        expected = d64.PE32_IMAGE_BASE + d64.PE32_SECTION_RVA + obj.symbols["value"] + 4
        self.assertEqual(patched, expected)

    def test_user_case_links_pe32_and_pe64(self):
        d64 = load_d64_dism()
        source = 'X = 2 + 3 * 4\n? "Wert von X = " + X\n'
        for target, magic in (("pe32", 0x10B), ("pe64", 0x20B)):
            result = compile_dbase_to_assembly(source, target=target)
            program = (
                d64.assemble_pe32_source(result.assembly, filename="x14_32.asm", gui=False)
                if target == "pe32"
                else d64.assemble_pe64_source(result.assembly, filename="x14_64.asm", gui=False)
            )
            self.assertTrue(program.executable.startswith(b"MZ"))
            pe = struct.unpack_from("<I", program.executable, 0x3C)[0]
            self.assertEqual(struct.unpack_from("<H", program.executable, pe + 24)[0], magic)


if __name__ == "__main__":
    unittest.main()
