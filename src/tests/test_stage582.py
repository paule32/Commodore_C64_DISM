"""Stage 582: source-relative console runtime deployment and diagnostics.

These tests are synthetic PE fixtures; a real Windows execution is not assumed.
"""
from pathlib import Path
import tempfile
import textwrap
import unittest

from pascal_console_dependencies import (
    MACHINE_AMD64, MACHINE_I386, console_library_candidates,
)
from test_stage552 import synthetic_pe

ROOT = Path(__file__).resolve().parent


def deployment_method():
    source = (ROOT / 'd64_dism.py').read_text('utf-8')
    start = source.index('        def _stage551_deploy_pascal_console(')
    end = source.index('        def assemble_generated_document(', start)
    namespace = {
        'Path': Path,
        'IMAGE_FILE_MACHINE_I386': MACHINE_I386,
        'IMAGE_FILE_MACHINE_AMD64': MACHINE_AMD64,
        '__file__': str(ROOT / 'd64_dism.py'),
    }
    exec(textwrap.dedent(source[start:end]), namespace)
    return namespace['_stage551_deploy_pascal_console']


class FakeUI:
    def __init__(self, current_directory):
        self.current_directory = current_directory
        self.current_project_path = None
        self.logs = []

    def log(self, text):
        self.logs.append(text)


class Stage582ConsoleTests(unittest.TestCase):
    def test_paths_include_source_specific_target_folder(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            src = root / 'myproj' / 'src' / 'app.pas'
            exe = root / 'myproj' / 'build' / 'app.exe'
            paths = console_library_candidates(exe, 'pe32', source_path=src)
            self.assertEqual(paths[0], exe.parent / 'libd64_console.dll')
            self.assertIn(src.parent / 'pe32' / 'libd64_console.dll', paths)
            self.assertNotIn(src.parent / 'pe64' / 'libd64_console.dll', paths)
            self.assertEqual(len(paths), len(set(paths)))

    def test_deployment_copies_from_source_pe32_to_different_exe_folder(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            src = root / 'src' / 'app.pas'
            src.parent.mkdir()
            dll = src.parent / 'pe32' / 'libd64_console.dll'
            dll.parent.mkdir()
            dll.write_bytes(synthetic_pe(exported='d64_console_init'))
            exe = root / 'output' / 'app.exe'
            exe.parent.mkdir()
            ui = FakeUI(root)
            self.assertTrue(deployment_method()(ui, exe, 'pe32',
                                                {'d64_console_init'}, source_path=src))
            self.assertEqual((exe.parent / dll.name).read_bytes(), dll.read_bytes())
            self.assertIn('PASCAL CONSOLE RUNTIME OK', '\n'.join(ui.logs))

    def test_invalid_adjacent_dll_replaced_with_valid_source_dll(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            src = root / 'src' / 'app.pas'
            src.parent.mkdir()
            dll = src.parent / 'pe32' / 'libd64_console.dll'
            dll.parent.mkdir()
            dll.write_bytes(synthetic_pe(exported='d64_console_init'))
            exe = root / 'bin' / 'app.exe'
            exe.parent.mkdir()
            target_dll = exe.parent / dll.name
            target_dll.write_bytes(synthetic_pe(machine=MACHINE_AMD64))
            ui = FakeUI(root)
            self.assertTrue(deployment_method()(ui, exe, 'pe32',
                                                {'d64_console_init'}, source_path=src))
            self.assertEqual(target_dll.read_bytes(), dll.read_bytes())

    def test_wrong_architecture_is_rejected_and_diagnosed(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            src = root / 'src' / 'app.pas'
            dll = src.parent / 'pe32' / 'libd64_console.dll'
            dll.parent.mkdir(parents=True)
            dll.write_bytes(synthetic_pe(machine=MACHINE_AMD64))
            exe = root / 'build' / 'app.exe'
            exe.parent.mkdir()
            ui = FakeUI(root)
            self.assertFalse(deployment_method()(ui, exe, 'pe32',
                                                 {'d64_console_init'}, source_path=src))
            self.assertIn('Architektur', ui._stage551_pascal_console_last_error)
            self.assertIn(str(dll), ui._stage551_pascal_console_last_error)
            self.assertFalse((exe.parent / dll.name).exists())

    def test_missing_exports_are_not_silently_accepted(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            src = root / 'src' / 'app.pas'
            dll = src.parent / 'pe32' / 'libd64_console.dll'
            dll.parent.mkdir(parents=True)
            dll.write_bytes(synthetic_pe(exported='d64_console_init'))
            exe = root / 'build' / 'app.exe'
            exe.parent.mkdir()
            ui = FakeUI(root)
            self.assertFalse(deployment_method()(ui, exe, 'pe32',
                                                 {'d64_console_restore'}, source_path=src))
            self.assertIn('fehlende Exporte: d64_console_restore',
                          ui._stage551_pascal_console_last_error)

    def test_pe64_does_not_use_pe32_sibling_dll(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            src = root / 'src' / 'app.pas'
            dll = src.parent / 'pe32' / 'libd64_console.dll'
            dll.parent.mkdir(parents=True)
            dll.write_bytes(synthetic_pe(machine=MACHINE_I386))
            exe = root / 'build' / 'app.exe'
            exe.parent.mkdir()
            ui = FakeUI(root)
            self.assertFalse(deployment_method()(ui, exe, 'pe64',
                                                 {'d64_console_init'}, source_path=src))
            self.assertNotIn(str(dll), ui._stage551_pascal_console_last_error)
            self.assertIn(str(src.parent / 'pe64' / 'libd64_console.dll'),
                          ui._stage551_pascal_console_last_error)

    def test_assembler_passes_source_path_to_deployment(self):
        data = (ROOT / 'd64_dism.py').read_text(encoding='utf-8')
        part = data[data.index('if console_exports and not self._stage551_deploy_pascal_console('):]
        self.assertIn('source_path=document.path', part[:240])


if __name__ == '__main__':
    unittest.main()
