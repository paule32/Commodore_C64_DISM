"""Stage 403: file not found after Stage 402 VICE sprite staging."""
import ast
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from c64_vice_assets import (
    c64_vice_drive8_command_options,
    prepare_c64_vice_sprite_drive,
    _vice_drive8_trap_option,
)
ROOT = Path(__file__).parent


def resource_client_class():
    code = ast.parse((ROOT / 'd64_dism.py').read_text(encoding='utf-8'))
    node = next(x for x in ast.walk(code) if isinstance(x, ast.ClassDef)
                and x.name == 'ViceBinaryMonitorClient')
    node.body = [x for x in node.body if isinstance(x, ast.FunctionDef)
                 and x.name == 'configure_virtual_drive8']
    ns = {'Path': Path, 'ViceBinaryMonitorError': ValueError}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[])),
                 '<isolated-VICE-configuration>', 'exec'), ns)
    return ns['ViceBinaryMonitorClient']


class ViceLoadErrorFourTests(unittest.TestCase):
    def setUp(self):
        _vice_drive8_trap_option.cache_clear()

    def test_cli_enables_real_trap_and_disables_true_drive(self):
        with tempfile.TemporaryDirectory() as d:
            args = c64_vice_drive8_command_options(Path(d))
            self.assertIn('-trapdevice8', args)
            self.assertIn('+drive8truedrive', args)
            self.assertIn('+fs8hidecbm', args)
            self.assertNotIn('-busdevice8', args)

    def test_older_vice_uses_virtualdev(self):
        with patch('c64_vice_assets.subprocess.run', return_value=SimpleNamespace(stdout=' -virtualdev8\n +virtualdev8 ')):
            args = c64_vice_drive8_command_options(Path('.'), Path('/fake/x64sc'))
        self.assertIn('-virtualdev8', args)
        self.assertNotIn('-trapdevice8', args)

    def test_newer_vice_uses_trapdevice(self):
        with patch('c64_vice_assets.subprocess.run', return_value=SimpleNamespace(stdout=' -trapdevice8 -busdevice8 ')):
            args = c64_vice_drive8_command_options(Path('.'), Path('/fake/x64sc'))
        self.assertIn('-trapdevice8', args)
        self.assertNotIn('-busdevice8', args)

    def test_running_monitor_new_version(self):
        with tempfile.TemporaryDirectory() as d:
            cls = resource_client_class()
            obj = cls()
            calls = []
            obj.set_vice_resource = lambda name, value: calls.append((name, value))
            obj.configure_virtual_drive8(Path(d))
            self.assertIn(('TrapDevice8', 1), calls)
            self.assertIn(('Drive8TrueEmulation', 0), calls)
            self.assertIn(('FSDevice8HideCBMFiles', 0), calls)
            self.assertNotIn(('BusDevice8', 1), calls)

    def test_running_monitor_old_version_fallback(self):
        with tempfile.TemporaryDirectory() as d:
            cls = resource_client_class()
            obj = cls()
            calls = []
            def setter(name, value):
                calls.append((name, value))
                if name == 'TrapDevice8':
                    raise ValueError('Unknown resource')
            obj.set_vice_resource = setter
            obj.configure_virtual_drive8(Path(d))
            self.assertEqual(calls[-1], ('VirtualDevice8', 1))

    def test_running_monitor_reports_missing_trap(self):
        with tempfile.TemporaryDirectory() as d:
            cls = resource_client_class()
            obj = cls()
            def setter(name, value):
                if name in ('TrapDevice8', 'VirtualDevice8'):
                    raise ValueError('Unknown resource')
            obj.set_vice_resource = setter
            with self.assertRaisesRegex(ValueError, 'KERNAL LOAD'):
                obj.configure_virtual_drive8(Path(d))

    def test_staging_is_identical_and_sprite_data_intact(self):
        with tempfile.TemporaryDirectory() as d:
            base = Path(d)
            (base / 'sprites.spr').write_bytes(bytes(range(64)))
            stage = prepare_c64_vice_sprite_drive('50 LOAD "sprites.spr",8,1', base / 'game.bas', stage_root=base / 'drive')
            self.assertEqual((stage / 'sprites.spr').read_bytes(), b'\x00\x30' + bytes(range(64)))


if __name__ == '__main__':
    unittest.main()
