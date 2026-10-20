"""Stage 402 - file-based tests (no VICE/PyQt required)."""
import ast
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from c64_vice_assets import (
    c64_basic_sprite_load_names,
    c64_vice_sprite_program,
    prepare_c64_vice_sprite_drive,
    c64_vice_drive8_command_options,
)

ROOT = Path(__file__).parent


class SpriteDriveTests(unittest.TestCase):
    def test_find_executable_load_only(self):
        source = '\n'.join([
            '10 REM LOAD "comment.spr",8,1',
            '20 PRINT "LOAD \\"ignore.spr\\",8,1"',
            '30 LOAD "sprites.spr",8,1',
            '40 LOAD "SECOND.SPR",8,1',
            '50 LOAD SCREEN "abc.spr"',
            '60 LOAD "tape.spr",1,1',
            '70 LOAD "old.spr",8,0',
        ])
        self.assertEqual(c64_basic_sprite_load_names(source), ('sprites.spr', 'SECOND.SPR'))

    def test_no_deps_no_side_effect(self):
        with tempfile.TemporaryDirectory() as temp:
            stage = Path(temp) / 'staging'
            self.assertIsNone(prepare_c64_vice_sprite_drive('10 PRINT "HI"', None, stage_root=stage))
            self.assertFalse(stage.exists())

    def test_64_byte_image(self):
        image = c64_vice_sprite_program(bytes([3] * 64))
        self.assertEqual(len(image), 66)
        self.assertEqual(image[:2], b'\x00\x30')
        self.assertEqual(image[2:], bytes([3] * 64))

    def test_63_byte_image_padded(self):
        image = c64_vice_sprite_program(bytes([3] * 63 * 2))
        self.assertEqual(len(image), 130)
        self.assertEqual(image[2 + 63], 0)
        self.assertEqual(image[2 + 127], 0)
        self.assertEqual(image[2 + 64], 3)

    def test_converts_file_to_vice_visible_name(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            (base / 'SPRITES.SPR').write_bytes(bytes(range(64)))
            stage = base / 'emulated_drive'
            prepared = prepare_c64_vice_sprite_drive(
                '50 LOAD "sprites.spr",8,1', base / 'program.bas', stage_root=stage
            )
            self.assertEqual(prepared, stage)
            self.assertEqual((stage / 'sprites.spr').read_bytes(), b'\x00\x30' + bytes(range(64)))
            self.assertFalse((base / 'sprites.spr').exists())  # original unchanged

    def test_missing_is_explicit_error(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(FileNotFoundError, 'nicht gefunden'):
                prepare_c64_vice_sprite_drive('LOAD "sprites.spr",8,1', Path(temp)/'a.bas')

    def test_file_format_validation(self):
        with self.assertRaisesRegex(ValueError, 'Dateigröße'):
            c64_vice_sprite_program(b'12345')
        with self.assertRaisesRegex(ValueError, 'Adressraum'):
            c64_vice_sprite_program(bytes(64), 0xFFF0)

    def test_launch_options(self):
        self.assertEqual(c64_vice_drive8_command_options(None), [])
        args = c64_vice_drive8_command_options(Path('/tmp/dir'))
        self.assertEqual(args[0], '-fs8')
        self.assertIn('-devicebackend8', args)
        self.assertIn('-trapdevice8', args)
        self.assertIn('+drive8truedrive', args)

    def test_resource_set_wire_protocol(self):
        import ast
        import struct
        source = (ROOT/'d64_dism.py').read_text(encoding='utf-8')
        tree = ast.parse(source)
        node = next(item for item in ast.walk(tree)
                    if isinstance(item, ast.ClassDef) and item.name == 'ViceBinaryMonitorClient')
        node.body = [member for member in node.body
                     if isinstance(member, ast.FunctionDef) and
                     member.name in ('set_vice_resource', 'configure_virtual_drive8')]
        ns = {'Path': Path, 'struct': struct,
              'VICE_BINARY_MONITOR_RESOURCE_SET': 0x52,
              'ViceBinaryMonitorError': ValueError}
        exec(compile(ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[])),
                     str(ROOT/'d64_dism.py'),'exec'), ns)
        client = ns['ViceBinaryMonitorClient']()
        calls = []
        client.command = lambda code, data: calls.append((code, data))
        client.set_vice_resource('FileSystemDevice8', 1)
        self.assertEqual(calls[-1], (0x52, b'\x01\x11FileSystemDevice8\x04\x01\x00\x00\x00'))
        client.set_vice_resource('FSDevice8Dir', 'C:/temp')
        self.assertEqual(calls[-1], (0x52, b'\x00\x0cFSDevice8Dir\x07C:/temp'))
        with self.assertRaises(ValueError):
            client.set_vice_resource('FSDevice8Dir', 'A'*256)

    def test_main_window_wiring_source(self):
        code = (ROOT/'d64_dism.py').read_text(encoding='utf-8')
        self.assertIn('sprite_drive = self._stage_c64_basic_sprite_dependencies(document)', code)
        self.assertIn('c64_vice_d64_command_options(sprite_disk)', code)
        self.assertIn('sprite_drive = self._stage_c64_basic_sprite_dependencies(', code)
        self.assertIn('document, extra_directory=output_path.parent', code)
        self.assertIn('VICE_BINARY_MONITOR_RESOURCE_SET = 0x52',code)


if __name__ == '__main__':
    unittest.main()
