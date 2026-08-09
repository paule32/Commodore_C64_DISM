from __future__ import annotations

import struct
import tempfile
import unittest
from pathlib import Path

import d64_dism as mod


class PE64InternalToolchainTests(unittest.TestCase):
    def _pe(self, image: bytes):
        self.assertEqual(image[:2], b"MZ")
        peoff = struct.unpack_from("<I", image, 0x3C)[0]
        self.assertEqual(image[peoff:peoff + 4], b"PE\0\0")
        return peoff, peoff + 24

    def test_target_macros_do_not_mix_pe32_and_pe64(self):
        macros = mod.windows_application_predefined_macros("Direct3D", "pe64")
        self.assertIn("__D64_TARGET_PE64__", macros)
        self.assertNotIn("__D64_TARGET_PE32__", macros)
        self.assertIn("__D64_GRAPHICS_DIRECT3D__", macros)

    def test_amd64_coff_and_pe32_plus_exe(self):
        src = r'''
bits 64
import ExitProcess, "kernel32.dll", "ExitProcess"
global _start
entry _start
extern ExitProcess
_start:
    push 0
    call ExitProcess
'''
        raw = mod.assemble_pe64_coff_object(src, filename="hello64.asm")
        self.assertEqual(struct.unpack_from("<H", raw, 0)[0], 0x8664)
        parsed = mod.parse_coff64_object(raw)
        self.assertIn("_start", parsed.symbols)
        image = mod.link_coff64_objects((raw,), entry_symbol="_start").executable
        peoff, optional = self._pe(image)
        self.assertEqual(struct.unpack_from("<H", image, peoff + 4)[0], 0x8664)
        self.assertEqual(struct.unpack_from("<H", image, optional)[0], 0x20B)
        self.assertEqual(struct.unpack_from("<H", image, optional + 68)[0], 3)
        import_rva, import_size = struct.unpack_from("<II", image, optional + 112 + 8)
        self.assertNotEqual(import_rva, 0)
        self.assertNotEqual(import_size, 0)

    def test_import_adapter_and_dir64_relocation(self):
        src = r'''
bits 64
import MessageBoxA, "user32.dll", "MessageBoxA"
import ExitProcess, "kernel32.dll", "ExitProcess"
global _start
entry _start
extern __d64_argc4__MessageBoxA
extern ExitProcess
_start:
    push 0
    push text
    push text
    push 0
    call __d64_argc4__MessageBoxA
    push 0
    call ExitProcess
text:
    db "PE64",0
text_pointer:
    dq text
'''
        raw = mod.assemble_pe64_coff_object(src)
        image = mod.link_coff64_objects((raw,), entry_symbol="_start", gui=True).executable
        _peoff, optional = self._pe(image)
        self.assertEqual(struct.unpack_from("<H", image, optional + 68)[0], 2)
        reloc_rva, reloc_size = struct.unpack_from("<II", image, optional + 112 + 5 * 8)
        self.assertNotEqual(reloc_rva, 0)
        self.assertNotEqual(reloc_size, 0)
        self.assertIn(b"user32.dll\0", image)
        self.assertIn(b"MessageBoxA\0", image)

    def test_coff64_archive_cross_object_link(self):
        main = mod.assemble_pe64_coff_object(
            "bits 64\nglobal _start\nentry _start\nextern Foo\nextern ExitProcess\n"
            "_start:\n call Foo\n push 0\n call ExitProcess\n"
        )
        member = mod.assemble_pe64_coff_object(
            "bits 64\nglobal Foo\nFoo:\n mov eax,42\n ret\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            main_path = root / "main.o"
            archive_path = root / "libfoo.a"
            main_path.write_bytes(main)
            archive_path.write_bytes(mod.create_coff64_archive((("foo.o", member),)))
            linked = mod.link_coff64_inputs((main_path, archive_path), entry_symbol="_start")
        self.assertTrue(linked.executable.startswith(b"MZ"))
        self.assertIn("foo", linked.symbols)

    def test_pe64_dll_export_directory(self):
        raw = mod.assemble_pe64_coff_object(r'''
bits 64
dllname "demo64.dll"
global __d64_dll_entry
global Foo
entry __d64_dll_entry
export Foo, Foo
__d64_dll_entry:
    mov eax,1
    ret
Foo:
    mov eax,42
    ret
''')
        image = mod.link_coff64_objects(
            (raw,), entry_symbol="__d64_dll_entry", dll=True, dll_name="demo64.dll"
        ).executable
        peoff, optional = self._pe(image)
        characteristics = struct.unpack_from("<H", image, peoff + 22)[0]
        self.assertTrue(characteristics & 0x2000)
        export_rva, export_size = struct.unpack_from("<II", image, optional + 112)
        self.assertNotEqual(export_rva, 0)
        self.assertNotEqual(export_size, 0)
        self.assertIn(b"demo64.dll\0", image)
        self.assertIn(b"Foo\0", image)

    def test_pascal_and_c_frontends_have_pe64_backends(self):
        root = Path(__file__).resolve().parents[1]
        pas = (root / "c64pascal" / "compiler.py").read_text(encoding="utf-8")
        csrc = (root / "c64c" / "compiler.py").read_text(encoding="utf-8")
        self.assertIn("class _PE64CodeGenerator", pas)
        self.assertIn('generator_class = _PE64CodeGenerator', pas)
        self.assertIn('"pe64"', pas)
        self.assertIn("bits 64", pas)
        self.assertIn("class _PE64CCodeGenerator", csrc)
        self.assertIn("_PE64CCodeGenerator", csrc)
        self.assertIn('"pe64"', csrc)
        self.assertIn("bits 64", csrc)


    def test_indirect_call_and_jump_registers_are_not_coff_symbols(self):
        src = r'''
bits 64
global _start
entry _start
_start:
    call rdx
    jmp rdx
indirect_high:
    jmp r11
'''
        obj = mod.assemble_pe64_object_source(src, filename="indirect64.asm")
        self.assertEqual(obj.relocations, ())
        self.assertNotIn("rdx", obj.externals)
        self.assertNotIn("r11", obj.externals)
        raw = mod.write_coff64_object(obj)
        self.assertEqual(struct.unpack_from("<H", raw, 0)[0], 0x8664)
        # CALL RDX = FF D2; JMP RDX = FF E2; JMP R11 = 41 FF E3
        self.assertIn(b"\xFF\xD2", obj.code)
        self.assertIn(b"\xFF\xE2", obj.code)
        self.assertIn(b"\x41\xFF\xE3", obj.code)

    def test_all_amd64_register_names_are_excluded_from_symbol_recognition(self):
        registers = set(mod._X64_REG_CODE) | set(mod._X64_REG16) | set(mod._X64_REG8) | {"rip"}
        for register in registers:
            with self.subTest(register=register):
                self.assertFalse(mod._x64_is_symbol(register))
        self.assertTrue(mod._x64_is_symbol("MyProcedure"))

    def test_target_combo_contains_pe64(self):
        source = (Path(__file__).resolve().parents[1] / "d64_dism.py").read_text(encoding="utf-8")
        self.assertIn(
            'self.build_target_combo.addItems(("C= 64", "Amiga", "Windows PE32", "Windows PE64"))',
            source,
        )
        self.assertIn('"pe64": "Windows PE64"', source)
        self.assertIn('self.coff_object_button.setText("COFF64 .o")', source)


if __name__ == "__main__":
    unittest.main()

class PE64ConsoleAndSectionRegressionTests(unittest.TestCase):
    def _sections(self, image: bytes):
        peoff = struct.unpack_from("<I", image, 0x3C)[0]
        count = struct.unpack_from("<H", image, peoff + 6)[0]
        optional = peoff + 24
        optional_size = struct.unpack_from("<H", image, peoff + 20)[0]
        section_table = optional + optional_size
        result = {}
        for index in range(count):
            off = section_table + index * 40
            name = image[off:off + 8].rstrip(b"\0").decode("ascii")
            chars = struct.unpack_from("<I", image, off + 0x24)[0]
            result[name] = chars
        return result

    def test_pe64_has_rx_text_and_rw_data(self):
        source = r'''
bits 64
section .text
global _start
entry _start
extern ExitProcess
_start:
    mov rax, message
    mov rcx, qword ptr [counter]
    push 0
    call ExitProcess
section .data
align 8
counter:
    dq 123
message:
    db "hello",0
message_ptr:
    dq message
'''
        raw = mod.assemble_pe64_coff_object(source)
        parsed = mod.parse_coff64_object(raw)
        self.assertGreater(len(parsed.code), 0)
        self.assertGreater(len(parsed.data), 0)
        self.assertEqual(parsed.symbol_sections["_start"], ".text")
        self.assertEqual(parsed.symbol_sections["message"], ".data")
        self.assertTrue(any(r.section == ".text" for r in parsed.relocations))
        self.assertTrue(any(r.section == ".data" for r in parsed.relocations))

        image = mod.link_coff64_objects((raw,), entry_symbol="_start").executable
        sections = self._sections(image)
        self.assertIn(".text", sections)
        self.assertIn(".data", sections)
        # IMAGE_SCN_MEM_EXECUTE / READ / WRITE
        self.assertTrue(sections[".text"] & 0x20000000)
        self.assertTrue(sections[".text"] & 0x40000000)
        self.assertFalse(sections[".text"] & 0x80000000)
        self.assertFalse(sections[".data"] & 0x20000000)
        self.assertTrue(sections[".data"] & 0x40000000)
        self.assertTrue(sections[".data"] & 0x80000000)

    def test_pe64_rejects_machine_code_in_data_section(self):
        source = "bits 64\nsection .data\nvalue: dq 1\nmov rax, rbx\n"
        with self.assertRaises(mod.PE64AssemblerError):
            mod.assemble_pe64_object_source(source)

    def test_pe64_compiler_emits_explicit_data_section_and_launcher_new_console(self):
        root = Path(__file__).resolve().parents[1]
        pascal = (root / "c64pascal" / "compiler.py").read_text(encoding="utf-8")
        gui = (root / "d64_dism.py").read_text(encoding="utf-8")
        self.assertIn('self.emitter.emit("section .data")', pascal)
        self.assertIn('lines.append("section .text")', pascal)
        self.assertIn('subprocess.CREATE_NEW_CONSOLE', gui)
