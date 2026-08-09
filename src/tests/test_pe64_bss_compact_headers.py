from __future__ import annotations

import struct
import unittest
from pathlib import Path

import d64_dism as mod


class PE64BssAndCompactHeaderTests(unittest.TestCase):
    def _headers(self, image: bytes):
        peoff = struct.unpack_from('<I', image, 0x3C)[0]
        self.assertEqual(peoff, 0x40)
        self.assertEqual(image[peoff:peoff+4], b'PE\0\0')
        optional_size = struct.unpack_from('<H', image, peoff + 20)[0]
        optional = peoff + 24
        count = struct.unpack_from('<H', image, peoff + 6)[0]
        section_table = optional + optional_size
        return peoff, optional, optional_size, count, section_table

    def test_bss_has_virtual_size_but_no_raw_bytes(self):
        source = r'''
bits 64
global _start
entry _start
section .text
_start:
    mov rax, huge_buffer
    ret
section .bss
align 16
huge_buffer:
    resb 10000
'''
        obj = mod.assemble_pe64_object_source(source)
        self.assertEqual(obj.bss_size, 10000)
        raw = mod.write_coff64_object(obj)
        parsed = mod.parse_coff64_object(raw)
        self.assertEqual(parsed.bss_size, 10000)
        self.assertEqual(parsed.symbol_sections['huge_buffer'], '.bss')

        image = mod.link_coff64_objects((raw,), entry_symbol='_start').executable
        _pe, optional, optional_size, count, section_table = self._headers(image)
        self.assertEqual(optional_size, 0xF0)
        self.assertEqual(struct.unpack_from('<I', image, optional + 0x3C)[0], 0x200)
        self.assertEqual(struct.unpack_from('<I', image, optional + 0x0C)[0], 10000)

        sections = {}
        for i in range(count):
            off = section_table + i * 40
            name = image[off:off+8].rstrip(b'\0').decode('ascii')
            sections[name] = {
                'virtual': struct.unpack_from('<I', image, off+8)[0],
                'raw_size': struct.unpack_from('<I', image, off+16)[0],
                'raw_ptr': struct.unpack_from('<I', image, off+20)[0],
                'chars': struct.unpack_from('<I', image, off+36)[0],
            }
        self.assertEqual(sections['.text']['raw_ptr'], 0x200)
        self.assertEqual(sections['.bss']['virtual'], 10000)
        self.assertEqual(sections['.bss']['raw_size'], 0)
        self.assertEqual(sections['.bss']['raw_ptr'], 0)
        self.assertFalse(sections['.bss']['chars'] & 0x20000000)
        self.assertTrue(sections['.bss']['chars'] & 0x80000000)
        # 10 KB BSS must not make the file 10 KB larger.
        self.assertLess(len(image), 4096)

    def test_standard_optional_header_and_first_code_at_0x200(self):
        source = r'''
bits 64
import ExitProcess, "kernel32.dll", "ExitProcess"
global _start
entry _start
extern ExitProcess
section .text
_start:
    mov rax, scratch
    push 0
    call ExitProcess
section .data
value: dq 123
section .bss
scratch: resb 4096
'''
        raw = mod.assemble_pe64_coff_object(source)
        image = mod.link_coff64_objects((raw,), entry_symbol='_start').executable
        _pe, optional, optional_size, count, section_table = self._headers(image)
        self.assertEqual(optional_size, 0xF0)
        self.assertEqual(struct.unpack_from('<I', image, optional + 0x6C)[0], 16)
        self.assertEqual(struct.unpack_from('<I', image, optional + 0x3C)[0], 0x200)
        self.assertLessEqual(count, 4)
        first_raw = None
        for i in range(count):
            off = section_table + i * 40
            name = image[off:off+8].rstrip(b'\0')
            raw_ptr = struct.unpack_from('<I', image, off+20)[0]
            if name == b'.text':
                first_raw = raw_ptr
        self.assertEqual(first_raw, 0x200)

    def test_pascal_pe64_emits_real_bss(self):
        compiler = (Path(__file__).resolve().parents[1] / 'c64pascal' / 'compiler.py').read_text(encoding='utf-8')
        start = compiler.index('class _PE64CodeGenerator')
        end = compiler.index('class _AmigaCodeGenerator', start)
        pe64 = compiler[start:end]
        self.assertIn('section .bss', pe64)
        self.assertIn('_input_buffer: resq 1', pe64)
        self.assertIn('_format_buffer: resb 32', pe64)
        self.assertIn('resb {size}', pe64)


if __name__ == '__main__':
    unittest.main()
