"""Stage 407 regression: preserve user VICE config/FSDevice8Dir."""
import ast
import tempfile
import unittest
from pathlib import Path

from c64_vice_assets import (
    c64_vice_configuration_command_options,
    c64_vice_ini_drive8_directory,
    prepare_c64_vice_sprite_drive,
)

ROOT=Path(__file__).resolve().parent


class TestStage407ViceSettings(unittest.TestCase):
    def test_vice_ini_reads_explicit_c64_fsdevice8dir(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)
            folder=p/'settings'
            folder.mkdir()
            cfg=p/'vice.ini'
            cfg.write_text('[C64]\nFSDevice8Dir="' + str(folder) + '"\n', encoding='utf8')
            self.assertEqual(c64_vice_ini_drive8_directory(cfg),folder.resolve())
            self.assertEqual(c64_vice_configuration_command_options(cfg), ['-config', str(cfg.resolve())])

    def test_config_missing_is_not_silently_ignored(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'missing.ini'
            with self.assertRaises(FileNotFoundError):
                c64_vice_configuration_command_options(p)

    def test_default_staging_is_near_source_not_temp(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)
            (p/'sprites.spr').write_bytes(bytes([0x55])*64)
            drive=prepare_c64_vice_sprite_drive('50 LOAD "sprites.spr",8,1',p/'game.bas')
            self.assertEqual(drive, (p/'.d64_dism'/'vice_drive8').resolve())
            self.assertEqual((drive/'sprites.spr').read_bytes(), b'\x00\x30'+bytes([0x55])*64)

    def test_user_selected_drive_is_respected(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)
            source=p/'sources'
            source.mkdir()
            (source/'sprites.spr').write_bytes(bytes([0xAA])*64)
            target=p/'configured_vice_drive8'
            target.mkdir()
            result=prepare_c64_vice_sprite_drive('LOAD "sprites.spr",8,1',source/'program.bas',stage_root=target)
            self.assertEqual(result, target.resolve())
            self.assertEqual((target/'sprites.spr').read_bytes()[:2], b'\x00\x30')

    def test_existing_raw_sprite_never_overwritten(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)
            source=p/'sprites.spr'
            original=bytes(range(64))
            source.write_bytes(original)
            with self.assertRaisesRegex(FileExistsError, 'Keine Quelldatei'):
                prepare_c64_vice_sprite_drive('LOAD "sprites.spr",8,1',p/'program.bas',stage_root=p)
            self.assertEqual(source.read_bytes(),original)

    def test_existing_staged_file_is_idempotent(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)
            (p/'sprites.spr').write_bytes(bytes(range(64)))
            drive=p/'drive'
            for _ in range(2):
                self.assertEqual(prepare_c64_vice_sprite_drive('LOAD "sprites.spr",8,1',p/'game.bas',stage_root=drive),drive.resolve())

    def test_updated_sprite_refreshes_own_staged_copy(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)
            raw=p/'sprites.spr'
            drive=p/'drive'
            raw.write_bytes(bytes([0x55])*64)
            prepare_c64_vice_sprite_drive('LOAD "sprites.spr",8,1', p/'game.bas', stage_root=drive)
            raw.write_bytes(bytes([0xAA])*64)
            prepare_c64_vice_sprite_drive('LOAD "sprites.spr",8,1', p/'game.bas', stage_root=drive)
            self.assertEqual((drive/'sprites.spr').read_bytes(), b'\x00\x30'+bytes([0xAA])*64)

    def test_modified_generated_file_is_not_silently_overwritten(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)
            raw=p/'sprites.spr'
            raw.write_bytes(bytes([0x55])*64)
            drive=p/'drive'
            prepare_c64_vice_sprite_drive('LOAD "sprites.spr",8,1', p/'game.bas', stage_root=drive)
            (drive/'sprites.spr').write_bytes(b'USER CHANGED')
            raw.write_bytes(bytes([0xAA])*64)
            with self.assertRaises(FileExistsError):
                prepare_c64_vice_sprite_drive('LOAD "sprites.spr",8,1', p/'game.bas', stage_root=drive)
            self.assertEqual((drive/'sprites.spr').read_bytes(),b'USER CHANGED')

    def test_vice_ui_menu_persists_settings(self):
        src=(ROOT/'d64_dism.py').read_text(encoding='utf8')
        ast.parse(src)
        for name in ('dism/vice_settings_path','dism/vice_drive8_path','choose_dism_vice_settings', 'choose_dism_vice_drive8'):
            self.assertIn(name,src)
        self.assertIn('stage_root=self._vice_sprite_stage_directory()',src)
        self.assertIn('str(vice_path), *vice_config_args,',src)
        self.assertGreaterEqual(src.count('str(vice_path), *self._vice_launch_config_options()'),2)
        self.assertNotIn("Path(tempfile.gettempdir()) / 'd64_dism_vice_drive8'",(ROOT/'c64_vice_assets.py').read_text())

    def test_uploaded_sprite_stage(self):
        original=Path('/mnt/data/sprites.spr')
        if not original.exists():
            self.skipTest('uploaded sprite missing')
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)
            (p/'sprites.spr').write_bytes(original.read_bytes())
            target=p/'drive'
            converted=prepare_c64_vice_sprite_drive('LOAD "sprites.spr",8,1',p/'Sprite_A.bas',stage_root=target)
            data=(converted/'sprites.spr').read_bytes()
            self.assertEqual(data[:2],b'\x00\x30')
            self.assertEqual(len(data),130)


if __name__ == '__main__':
    unittest.main()
