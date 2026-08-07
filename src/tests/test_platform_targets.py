import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('d64_platform_module', ROOT / 'd64_dism.py')
mod = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = mod
SPEC.loader.exec_module(mod)


class PlatformProfileTests(unittest.TestCase):
    def test_exact_amiga_cpu_models(self):
        self.assertEqual(mod.AMIGA_CPU_MODELS, (
            'mk68000','mk68010','mk68020','mk68030','mk68040','mk68060'
        ))

    def test_exact_amiga_fpu_models(self):
        self.assertEqual(mod.AMIGA_FPU_MODELS, (
            'FPU: None','FPU: 68881','FPU: 68882'
        ))

    def test_rtd_requires_68010(self):
        src = 'section code,code\nxdef _start\n_start:\n rtd #4\n'
        with self.assertRaises(mod.AmigaAssemblerError):
            mod.assemble_amiga_source(src, cpu_model='mk68000')
        p = mod.assemble_amiga_source(src, cpu_model='mk68010')
        self.assertEqual(p.code, bytes.fromhex('4e740004'))

    def test_long_branch_requires_68020(self):
        src = 'section code,code\nxdef _start\n_start:\n bra.l _start\n'
        with self.assertRaises(mod.AmigaAssemblerError):
            mod.assemble_amiga_source(src, cpu_model='mk68010')
        p = mod.assemble_amiga_source(src, cpu_model='mk68020')
        self.assertEqual(p.code, bytes.fromhex('60fffffffffe'))

    def test_movec_profiles_and_link_long(self):
        p10 = mod.assemble_amiga_source(
            'section code,code\nxdef _start\n_start:\n movec vbr,d0\n',
            cpu_model='mk68010',
        )
        self.assertEqual(p10.code, bytes.fromhex('4e7a0801'))
        p20 = mod.assemble_amiga_source(
            'section code,code\nxdef _start\n_start:\n link.l a6,#-16\n',
            cpu_model='mk68020',
        )
        self.assertEqual(p20.code, bytes.fromhex('480efffffff0'))
        p40 = mod.assemble_amiga_source(
            'section code,code\nxdef _start\n_start:\n movec tc,d1\n',
            cpu_model='mk68040',
        )
        self.assertEqual(p40.code, bytes.fromhex('4e7a1003'))
        with self.assertRaises(mod.AmigaAssemblerError):
            mod.assemble_amiga_source(
                'section code,code\nxdef _start\n_start:\n movec pcr,d0\n',
                cpu_model='mk68040',
            )
        p60 = mod.assemble_amiga_source(
            'section code,code\nxdef _start\n_start:\n movec pcr,d0\n',
            cpu_model='mk68060',
        )
        self.assertEqual(p60.code, bytes.fromhex('4e7a0808'))

    def test_fpu_register_arithmetic(self):
        src = (
            'section code,code\nxdef _start\n_start:\n'
            ' fmove fp0,fp1\n fadd fp1,fp2\n fmul fp2,fp3\n'
            ' fcmp fp3,fp4\n ftst fp4\n rts\n'
        )
        with self.assertRaises(mod.AmigaAssemblerError):
            mod.assemble_amiga_source(src, fpu_model='FPU: None')
        p = mod.assemble_amiga_source(src, fpu_model='FPU: 68882')
        self.assertTrue(p.code.startswith(bytes.fromhex('f2000080f2000522')))
        self.assertTrue(p.code.endswith(bytes.fromhex('4e75')))

    def test_fnop_requires_fpu(self):
        src = 'section code,code\nxdef _start\n_start:\n fnop\n'
        with self.assertRaises(mod.AmigaAssemblerError):
            mod.assemble_amiga_source(src, fpu_model='FPU: None')
        p = mod.assemble_amiga_source(src, fpu_model='FPU: 68881')
        self.assertEqual(p.code, bytes.fromhex('f2800000'))


class PE32Tests(unittest.TestCase):
    def test_direct_pe32(self):
        src = '.entry _start\n_start:\n mov eax, 42\n ret\n'
        p = mod.assemble_pe32_source(src)
        self.assertTrue(p.executable.startswith(b'MZ'))
        peoff = int.from_bytes(p.executable[0x3c:0x40], 'little')
        self.assertEqual(p.executable[peoff:peoff+4], b'PE\0\0')

    def test_coff_roundtrip(self):
        src = '.entry _start\n_start:\n mov eax, 42\n ret\n'
        raw = mod.assemble_pe32_coff_object(src)
        obj = mod.parse_coff32_object(raw)
        self.assertIn('_start', obj.symbols)
        self.assertEqual(obj.code[:5], bytes.fromhex('b82a000000'))

    def test_cross_object_and_archive_link(self):
        a = mod.assemble_pe32_coff_object('.entry _start\nextern foo\n_start:\n call foo\n ret\n')
        b = mod.assemble_pe32_coff_object('global foo\nfoo:\n mov eax, 42\n ret\n')
        archive = mod.create_coff32_archive((('a.o', a), ('b.o', b)))
        self.assertEqual(len(mod.parse_coff32_archive(archive)), 2)
        with tempfile.TemporaryDirectory() as tmp:
            ap = Path(tmp) / 'test.a'
            ap.write_bytes(archive)
            p = mod.link_coff32_inputs((ap,))
            self.assertTrue(p.executable.startswith(b'MZ'))
            self.assertIn('foo', p.symbols)

    def test_pe32_without_imports(self):
        p = mod.assemble_pe32_source(
            'bits 32\nglobal _start\nentry _start\n_start:\n mov eax, 7\n ret\n'
        )
        self.assertTrue(p.executable.startswith(b'MZ'))
        peoff = int.from_bytes(p.executable[0x3c:0x40], 'little')
        optional = peoff + 24
        self.assertEqual(
            int.from_bytes(
                p.executable[optional + 0x1c:optional + 0x20], 'little'
            ),
            0x00400000,
        )

    def test_stackframe_memory_addressing(self):
        src = """
.entry _start
extern ExitProcess
_start:
 push ebp
 mov ebp, esp
 sub esp, 16
 mov dword ptr [ebp-4], 42
 mov eax, [ebp-4]
 mov [ebp-8], eax
 lea ecx, [ebp-8]
 movzx edx, byte ptr [ebp-4]
 cmp eax, [ebp-8]
 sete al
 imul eax, [ebp-4]
 cdq
 idiv dword ptr [ebp-8]
 add dword ptr [ebp-4], 1
 shl dword ptr [ebp-4], 2
 push 0
 call ExitProcess
 leave
 ret
"""
        p = mod.assemble_pe32_source(src)
        self.assertTrue(p.executable.startswith(b'MZ'))
        self.assertIn(bytes.fromhex('c745fc2a000000'), p.code)
        self.assertIn(bytes.fromhex('8b45fc'), p.code)
        self.assertIn(bytes.fromhex('0f94c0'), p.code)

    def test_coff_import_metadata_roundtrip(self):
        src = (
            'bits 32\n'
            'import CustomCall, "custom.dll", "RealCall"\n'
            'extern CustomCall\n'
            'global _start\nentry _start\n'
            '_start:\n call CustomCall\n ret\n'
        )
        raw = mod.assemble_pe32_coff_object(src)
        obj = mod.parse_coff32_object(raw)
        self.assertEqual(
            obj.imports['customcall'], ('custom.dll', 'RealCall')
        )
        linked = mod.link_coff32_objects((raw,))
        self.assertIn(b'custom.dll\0', linked.executable)
        self.assertIn(b'RealCall\0', linked.executable)

    def test_internal_dll_export_directory(self):
        src = (
            'bits 32\n'
            'dllname "demo.dll"\n'
            'global __d64_dll_entry\n'
            'entry __d64_dll_entry\n'
            'export Add, add_impl\n'
            '__d64_dll_entry:\n mov eax, 1\n ret 12\n'
            'add_impl:\n mov eax, 42\n ret\n'
        )
        raw = mod.assemble_pe32_coff_object(src)
        parsed = mod.parse_coff32_object(raw)
        self.assertEqual(parsed.exports, {'Add': 'add_impl'})
        self.assertEqual(parsed.dll_name, 'demo.dll')
        dll = mod.link_coff32_objects(
            (raw,), entry_symbol='__d64_dll_entry', dll=True
        ).executable
        peoff = int.from_bytes(dll[0x3c:0x40], 'little')
        characteristics = int.from_bytes(
            dll[peoff + 22:peoff + 24], 'little'
        )
        self.assertTrue(characteristics & 0x2000)
        optional = peoff + 24
        export_rva = int.from_bytes(dll[optional + 0x60:optional + 0x64], 'little')
        self.assertNotEqual(export_rva, 0)
        self.assertIn(b'demo.dll\0', dll)
        self.assertIn(b'Add\0', dll)

    def test_dll_can_import_and_export_via_archive(self):
        src = (
            'bits 32\n'
            'dllname "bridge.dll"\n'
            'import GetTickCount, "kernel32.dll", "GetTickCount"\n'
            'extern GetTickCount\n'
            'global __d64_dll_entry\nentry __d64_dll_entry\n'
            'export Tick, tick_impl\n'
            '__d64_dll_entry:\n mov eax, 1\n ret 12\n'
            'tick_impl:\n call GetTickCount\n ret\n'
        )
        raw = mod.assemble_pe32_coff_object(src)
        archive = mod.create_coff32_archive((('bridge.o', raw),))
        with tempfile.TemporaryDirectory() as tmp:
            ap = Path(tmp) / 'bridge.a'
            ap.write_bytes(archive)
            linked = mod.link_coff32_inputs(
                (ap,), entry_symbol='__d64_dll_entry', dll=True
            )
        image = linked.executable
        self.assertIn(b'bridge.dll\0', image)
        self.assertIn(b'Tick\0', image)
        self.assertIn(b'kernel32.dll\0', image)
        self.assertIn(b'GetTickCount\0', image)
        peoff = int.from_bytes(image[0x3c:0x40], 'little')
        optional = peoff + 24
        self.assertEqual(
            int.from_bytes(image[optional + 0x1c:optional + 0x20], 'little'),
            0x10000000,
        )
        reloc_rva = int.from_bytes(
            image[optional + 0x88:optional + 0x8c], 'little'
        )
        self.assertNotEqual(reloc_rva, 0)

    def test_dll_base_relocations_for_dir32(self):
        src = (
            'bits 32\n'
            'dllname "relocdemo.dll"\n'
            'global __d64_dll_entry\nentry __d64_dll_entry\n'
            'export GetValue, get_value\n'
            '__d64_dll_entry:\n mov eax,1\n ret 12\n'
            'get_value:\n mov eax, [global_value]\n ret\n'
            'global_value:\n dd 42\n'
        )
        raw = mod.assemble_pe32_coff_object(src)
        image = mod.link_coff32_objects(
            (raw,), entry_symbol='__d64_dll_entry', dll=True
        ).executable
        peoff = int.from_bytes(image[0x3c:0x40], 'little')
        optional = peoff + 24
        self.assertEqual(
            int.from_bytes(image[optional + 0x1c:optional + 0x20], 'little'),
            0x10000000,
        )
        self.assertNotEqual(
            int.from_bytes(image[optional + 0x88:optional + 0x8c], 'little'),
            0,
        )
        self.assertIn(b'.reloc', image)

    def test_import_table_exitprocess(self):
        src = '.entry _start\nextern ExitProcess\n_start:\n push 0\n call ExitProcess\n ret\n'
        p = mod.assemble_pe32_source(src)
        self.assertTrue(p.executable.startswith(b'MZ'))
        self.assertIn('exitprocess', p.symbols)
        self.assertIn(b'kernel32.dll\0', p.executable)
        self.assertIn(b'ExitProcess\0', p.executable)
        self.assertIn(b'\xff\x25', p.code)

    def test_windows_graphics_runtime(self):
        self.assertIn('Direct2D', mod.WINDOWS_GRAPHICS_BACKENDS)
        self.assertIn('Direct3D', mod.WINDOWS_GRAPHICS_BACKENDS)
        self.assertIn('D2D1CreateFactory', mod.WINDOWS_GRAPHICS_RUNTIME_CPP)
        self.assertIn('Direct3DCreate9', mod.WINDOWS_GRAPHICS_RUNTIME_CPP)
        self.assertIn('320', mod.WINDOWS_GRAPHICS_RUNTIME_CPP)
        self.assertIn('200', mod.WINDOWS_GRAPHICS_RUNTIME_CPP)

    def test_gui_source_contains_platform_controls(self):
        source = (ROOT / 'd64_dism.py').read_text(encoding='utf-8')
        for token in (
            'Windows PE32', 'amiga_cpu_combo', 'amiga_fpu_combo',
            'COFF32 .o', 'Windows PE32 Linker', 'Direct2D/Direct3D'
        ):
            self.assertIn(token, source)


if __name__ == '__main__':
    unittest.main()
