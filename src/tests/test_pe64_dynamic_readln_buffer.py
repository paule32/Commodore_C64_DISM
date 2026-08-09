from __future__ import annotations

import struct
import unittest
from pathlib import Path

import d64_dism as mod


class PE64DynamicReadLnBufferTests(unittest.TestCase):
    def test_virtualalloc_is_known_pe64_import_with_four_arguments(self):
        self.assertEqual(
            mod.PE32_DEFAULT_IMPORTS["virtualalloc"],
            ("kernel32.dll", "VirtualAlloc"),
        )
        self.assertEqual(mod.PE64_IMPORT_SIGNATURES["virtualalloc"], (4, False))

    def test_dynamic_buffer_can_be_assembled_and_linked(self):
        source = r'''
bits 64
section .text
global _start
entry _start
extern VirtualAlloc
extern ExitProcess
_start:
    push 4
    push 12288
    push 4096
    push 0
    call VirtualAlloc
    mov qword ptr [input_buffer], rax
    push 0
    call ExitProcess
section .data
align 8
input_buffer:
    dq 0
'''
        raw = mod.assemble_pe64_coff_object(source, filename="dynamic_readln.asm")
        self.assertEqual(struct.unpack_from("<H", raw, 0)[0], 0x8664)
        parsed = mod.parse_coff64_object(raw)
        self.assertEqual(len(parsed.data), 8)
        image = mod.link_coff64_objects((raw,), entry_symbol="_start").executable
        self.assertIn(b"VirtualAlloc\0", image)
        self.assertIn(b"ExitProcess\0", image)

    def test_pascal_pe64_readln_uses_pointer_not_embedded_4k_buffer(self):
        compiler = (
            Path(__file__).resolve().parents[1] / "c64pascal" / "compiler.py"
        ).read_text(encoding="utf-8")
        start = compiler.index("class _PE64CodeGenerator")
        end = compiler.index("class _AmigaCodeGenerator", start)
        pe64 = compiler[start:end]
        self.assertIn('call VirtualAlloc', pe64)
        self.assertIn('push 4096', pe64)
        self.assertIn('push 4095', pe64)
        self.assertIn('_input_buffer: resq 1', pe64)
        self.assertNotIn('_input_buffer: db "+", ".join(["0"]*1024)', pe64)


if __name__ == "__main__":
    unittest.main()
