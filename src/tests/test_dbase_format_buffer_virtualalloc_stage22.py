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


def load_d64():
    sys.modules.setdefault("flags_rc", types.ModuleType("flags_rc"))
    name = "_d64_dbase_stage22_test"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, ROOT / "d64_dism.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class DBaseFormatBufferVirtualAllocStage22Tests(unittest.TestCase):
    SOURCE = '''
x = 12.5
? x
s = "value=" + x
? s
'''

    def compile(self, target: str):
        return compile_dbase_to_assembly(
            self.SOURCE,
            filename="format_buffer_stage22.dbase",
            target=target,
            windows_application_mode="GUI",
        )

    def test_pe32_buffer_is_pointer_slot_not_96_zero_bytes(self):
        asm = self.compile("pe32").assembly
        self.assertIn('import VirtualAlloc, "kernel32.dll", "VirtualAlloc"', asm)
        self.assertIn('import VirtualFree, "kernel32.dll", "VirtualFree"', asm)
        self.assertIn("call VirtualAlloc", asm)
        self.assertIn("mov dword ptr [__dbase_format_buffer], eax", asm)
        self.assertIn("push dword ptr [__dbase_format_buffer]", asm)
        self.assertIn("mov ecx, dword ptr [__dbase_format_buffer]", asm)
        self.assertIn("call VirtualFree", asm)
        self.assertIn("__dbase_format_buffer:\n    dd 0", asm)
        self.assertNotIn("__dbase_format_buffer:\n    db ", asm)

    def test_pe64_buffer_is_pointer_slot_not_96_zero_bytes(self):
        asm = self.compile("pe64").assembly
        self.assertIn("call VirtualAlloc", asm)
        self.assertIn("mov qword ptr [__dbase_format_buffer], rax", asm)
        self.assertIn("mov r8, qword ptr [__dbase_format_buffer]", asm)
        self.assertIn("mov rcx, qword ptr [__dbase_format_buffer]", asm)
        self.assertIn("call VirtualFree", asm)
        self.assertIn("__dbase_format_buffer:\n    dd 0, 0", asm)
        self.assertNotIn("__dbase_format_buffer:\n    db ", asm)

    def test_virtualalloc_uses_96_bytes_commit_reserve_readwrite(self):
        asm32 = self.compile("pe32").assembly
        self.assertIn("push 4\n    push 12288\n    push 96\n    push 0\n    call VirtualAlloc", asm32)

        asm64 = self.compile("pe64").assembly
        self.assertIn("xor ecx, ecx", asm64)
        self.assertIn("mov edx, 96", asm64)
        self.assertIn("mov r8d, 12288", asm64)
        self.assertIn("mov r9d, 4", asm64)

    def test_virtualfree_uses_mem_release(self):
        asm32 = self.compile("pe32").assembly
        self.assertIn("push 32768", asm32)
        self.assertIn("call VirtualFree", asm32)
        asm64 = self.compile("pe64").assembly
        self.assertIn("mov r8d, 32768", asm64)
        self.assertIn("call VirtualFree", asm64)

    def test_pe32_pe64_internal_link(self):
        d64 = load_d64()
        for target, magic in (("pe32", 0x10B), ("pe64", 0x20B)):
            result = self.compile(target)
            program = (
                d64.assemble_pe32_source(result.assembly, filename="format22_32.asm", gui=True)
                if target == "pe32"
                else d64.assemble_pe64_source(result.assembly, filename="format22_64.asm", gui=True)
            )
            pe = struct.unpack_from("<I", program.executable, 0x3C)[0]
            self.assertEqual(struct.unpack_from("<H", program.executable, pe + 24)[0], magic)
            self.assertEqual(struct.unpack_from("<H", program.executable, pe + 24 + 68)[0], 2)


if __name__ == "__main__":
    unittest.main()
