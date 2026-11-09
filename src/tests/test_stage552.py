"""Stage 552: prevent success of PE32 builds with missing console DLL.

Tests use synthetic PE binaries and mocks.  No Windows execution is assumed.
"""
import json
import struct
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest.mock import patch

from pascal_console_dependencies import (
    CONSOLE_DLL, MACHINE_I386, MACHINE_AMD64, PEInspectionError,
    inspect_pe, manifest_dlls_and_console_symbols,
    required_console_exports, validate_console_library, diagnose_package,
)

ROOT = Path(__file__).resolve().parent


def synthetic_pe(machine=MACHINE_I386, imported='libd64_console.dll',
                 member='d64_console_newline', exported='d64_console_init'):
    """Minimal PE32 containing a standard import and export descriptor."""
    data = bytearray(0x600)
    data[:2] = b'MZ'
    struct.pack_into('<I', data, 0x3c, 0x80)
    data[0x80:0x84] = b'PE\0\0'
    struct.pack_into('<H', data, 0x84, machine)
    struct.pack_into('<H', data, 0x86, 2)
    pe64 = machine == MACHINE_AMD64
    optional_size = 0xf0 if pe64 else 0xe0
    struct.pack_into('<H', data, 0x94, optional_size)
    opt = 0x98
    struct.pack_into('<H', data, opt, 0x20b if pe64 else 0x10b)
    dirs = opt + (112 if pe64 else 96)
    struct.pack_into('<II', data, dirs, 0x2000, 0x100) # export dir
    struct.pack_into('<II', data, dirs + 8, 0x1000, 0x100) # import dir
    sect = opt + optional_size
    data[sect:sect + 8] = b'.idata\0\0'
    struct.pack_into('<IIII', data, sect + 8, 0x200, 0x1000, 0x200, 0x200)
    sect += 40
    data[sect:sect + 8] = b'.edata\0\0'
    struct.pack_into('<IIII', data, sect + 8, 0x200, 0x2000, 0x200, 0x400)
    # Import directory; terminator at file offset 0x214.
    struct.pack_into('<IIIII', data, 0x200, 0x1040, 0, 0, 0x1080, 0x1040)
    if pe64:
        struct.pack_into('<QQ', data, 0x240, 0x10a0, 0)
    else:
        struct.pack_into('<II', data, 0x240, 0x10a0, 0)
    data[0x280:0x280 + len(imported) + 1] = imported.encode() + b'\0'
    data[0x2a2:0x2a2 + len(member) + 1] = member.encode() + b'\0'
    # Export directory, one named export.
    struct.pack_into('<II', data, 0x400 + 24, 1, 1)
    struct.pack_into('<I', data, 0x400 + 32, 0x2060)
    struct.pack_into('<I', data, 0x460, 0x2080)
    data[0x480:0x480 + len(exported) + 1] = exported.encode() + b'\0'
    return bytes(data)


class Stage552Tests(unittest.TestCase):
    def test_pe_reader_imports_exports_architecture(self):
        with tempfile.TemporaryDirectory() as tmp:
            pe = Path(tmp) / 'example.dll'
            pe.write_bytes(synthetic_pe())
            machine, imports, exports = inspect_pe(pe)
            self.assertEqual(machine, MACHINE_I386)
            self.assertEqual(imports[CONSOLE_DLL], {'d64_console_newline'})
            self.assertEqual(exports, {'d64_console_init'})

    def test_pe64_reader_imports_exports_architecture(self):
        with tempfile.TemporaryDirectory() as tmp:
            pe = Path(tmp) / 'example64.dll'
            pe.write_bytes(synthetic_pe(machine=MACHINE_AMD64))
            machine, imports, exports = inspect_pe(pe)
            self.assertEqual(machine, MACHINE_AMD64)
            self.assertEqual(imports[CONSOLE_DLL], {'d64_console_newline'})
            self.assertEqual(exports, {'d64_console_init'})

    def test_pe_reader_rejects_truncated_pe(self):
        with tempfile.TemporaryDirectory() as tmp:
            pe = Path(tmp) / 'bad.dll'
            pe.write_bytes(b'Not a PE')
            with self.assertRaises(PEInspectionError):
                inspect_pe(pe)

    def test_manifest_includes_externalized_console_imports(self):
        manifest = {'imports': [
            {'dll': CONSOLE_DLL, 'member': 'd64_console_init'},
            {'dll': 'Runtime.dll', 'member': 'TApplication_new_Create'}]}
        dlls, symbols = manifest_dlls_and_console_symbols(manifest)
        self.assertIn(CONSOLE_DLL, dlls)
        self.assertEqual(symbols, {'d64_console_init'})
        with tempfile.TemporaryDirectory() as tmp:
            exe = Path(tmp) / 'program.exe'
            exe.write_bytes(b'compressed loader')
            self.assertEqual(required_console_exports(exe, manifest), {'d64_console_init'})

    def test_transitive_import_from_runtime_dll(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            dll = out / 'Runtime.dll'
            dll.write_bytes(synthetic_pe())
            self.assertEqual(required_console_exports(
                out / 'program.exe',
                {'imports': [{'dll': 'Runtime.dll', 'member': 'TApplication_new_Create'}]}
            ), {'d64_console_newline'})

    def test_console_export_name_and_architecture_validation(self):
        with tempfile.TemporaryDirectory() as tmp:
            dll = Path(tmp) / CONSOLE_DLL
            dll.write_bytes(synthetic_pe())
            self.assertIsNone(validate_console_library(dll, MACHINE_I386, {'d64_console_init'}))
            self.assertIn('Architektur', validate_console_library(dll, MACHINE_AMD64, {'d64_console_init'}))
            self.assertIn('fehlende Exporte', validate_console_library(dll, MACHINE_I386, {'d64_console_restore'}))

    def test_package_audit_reports_missing_console(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            (directory / 'test_raise.exe').write_bytes(b'packed binary')
            (directory / 'Runtime.dll').write_bytes(synthetic_pe())
            (directory / 'test_raise.exe.imports.json').write_text(json.dumps({
                'target': 'pe32',
                'imports': [{'dll': 'Runtime.dll', 'member': 'TApplication_new_Create'}],
            }), encoding='utf-8')
            warnings = diagnose_package(directory)
            self.assertEqual(len(warnings), 1)
            self.assertIn(CONSOLE_DLL, warnings[0])
            self.assertIn('d64_console_newline', warnings[0])

    def test_ide_uses_manifest_and_verifies_before_success(self):
        text = (ROOT / 'd64_dism.py').read_text(encoding='utf-8')
        start = text.index('        def assemble_generated_document(')
        end = text.index('        @staticmethod\n        def _c_source_has_main_definition(', start)
        part = text[start:end]
        self.assertIn('required_console_exports(', part)
        self.assertIn('getattr(program, "import_manifest", None)', part)
        self.assertIn('source_includes_console=has_asm_console', part)
        self.assertIn('self._stage551_deploy_pascal_console(', part)
        self.assertLess(part.index('self._stage551_deploy_pascal_console('),
                        part.index('ASM-Tab erfolgreich assembliert'))
        self.assertNotIn('and "libd64_console.dll" in assembly_source.casefold()', part)

    def test_deploy_copies_valid_dll_and_checks_exports(self):
        text = (ROOT / 'd64_dism.py').read_text(encoding='utf-8')
        start = text.index('        def _stage551_deploy_pascal_console(')
        end = text.index('        def assemble_generated_document(', start)
        namespace = {'Path': Path,
                     'IMAGE_FILE_MACHINE_I386': MACHINE_I386,
                     'IMAGE_FILE_MACHINE_AMD64': MACHINE_AMD64,
                     '__file__': str(ROOT / 'd64_dism.py')}
        exec(textwrap.dedent(text[start:end]), namespace)
        fn = namespace['_stage551_deploy_pascal_console']
        class FakeUI:
            def __init__(self, current_directory):
                self.current_directory = current_directory
                self.current_project_path = None
                self.logs = []
            def log(self, text):
                self.logs.append(text)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            built = root / 'runtime' / 'compiler' / 'win32' / CONSOLE_DLL
            built.parent.mkdir(parents=True)
            built.write_bytes(synthetic_pe())
            output = root / 'bin' / 'app.exe'
            output.parent.mkdir()
            ui = FakeUI(root)
            self.assertTrue(fn(ui, output, 'pe32', {'d64_console_init'}))
            self.assertEqual((output.parent / CONSOLE_DLL).read_bytes(), built.read_bytes())
            self.assertFalse(fn(ui, output, 'pe32', {'d64_console_restore'}))


if __name__ == '__main__':
    unittest.main(verbosity=2)
