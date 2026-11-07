"""Stage 535: Windows-Pascal codegen section placement tests (no GUI required).

Run: python test_stage535.py
The generated assembler is tested, not the execution of a native Windows EXE.
"""
import unittest
from test_stage532 import _compiler


class TestStage535Sections(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c = _compiler()
        cls.loc = cls.c.SourcePosition(1, 1)

    def generate(self, bits, mode="program", with_cookie=False):
        c, loc = self.c, self.loc
        prog = c.PascalProgram("SectionCheck", (), (), c.CompoundStatement(loc, ()))
        cls = c._PE32CodeGenerator if bits == 32 else c._PE64CodeGenerator
        opts = {"console_mode": False, "stack_protector": with_cookie}
        if mode == "unit":
            opts["unit_name"] = "SectionCheckUnit"
        elif mode == "library":
            opts["library_name"] = "SectionCheckLib"
        gen = cls(prog, **opts)
        gen._allocate_variable("Msg", c._PascalType("TMsg", 28, kind="record"),
                               loc, internal=True, label_prefix="local_global_runmessageloop")
        gen._allocate_variable("WinClass", c._PascalType("TWndClassA", 40, kind="record"),
                               loc, internal=True, label_prefix="local_twindow_create")
        gen._allocate_variable("ZeroCounter", c._PascalType("Integer", 4), loc,
                               label_prefix="var")
        variable = gen._allocate_variable("Initialized", c._PascalType("Integer", 4),
                                          loc, label_prefix="var")
        variable.c_initial_value = 42
        gen.strings[b"Hello"] = "__test_const_hello"
        return gen.generate().assembly

    def test_separate_initialized_and_zeroed_storage(self):
        for bits in (32, 64):
            with self.subTest(bits=bits):
                asm = self.generate(bits)
                self.assertIn("section .data", asm)
                self.assertIn("section .bss", asm)
                text, data = asm.split("section .data", 1)
                data, bss = data.split("section .bss", 1)
                self.assertIn("_start:", text)
                self.assertNotIn("_start:", data)
                self.assertNotIn("_start:", bss)
                self.assertIn("__test_const_hello: db", data)
                self.assertIn("__pas_var_initialized_3: dd 42", data)
                self.assertNotIn("__pas_var_initialized_3:", bss)
                self.assertIn("__pas_local_global_runmessageloop_msg_0: resb 28", bss)
                self.assertIn("__pas_local_twindow_create_winclass_1: resb 40", bss)
                self.assertIn("__pas_var_zerocounter_2: resb 4", bss)
                self.assertNotIn("__pas_local_global_runmessageloop_msg_0: db", asm)

    def test_unit_and_library_target_sections(self):
        for bits in (32, 64):
            for mode in ("unit", "library"):
                with self.subTest(bits=bits, mode=mode):
                    asm = self.generate(bits, mode)
                    self.assertIn("section .data", asm)
                    self.assertIn("section .bss", asm)
                    data, bss = asm.split("section .data", 1)[1].split("section .bss", 1)
                    self.assertIn("initialized_3: dd 42", data)
                    self.assertIn("winclass_1: resb 40", bss)

    def test_stack_cookie_is_still_bss(self):
        for bits in (32, 64):
            with self.subTest(bits=bits):
                asm = self.generate(bits, with_cookie=True)
                bss = asm.split("section .bss", 1)[1]
                self.assertIn("_cookie_secret: res", bss)
                self.assertIn("winclass_1: resb 40", bss)
                self.assertIn("BCryptGenRandom", asm)


if __name__ == "__main__":
    unittest.main(verbosity=2)
