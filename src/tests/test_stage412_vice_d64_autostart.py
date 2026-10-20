"""Stage 412: protect D64 autostart from ASCII/PETSCII program name confusion."""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from c64_d64_disk import (_offset, build_1541_d64, prepare_c64_sprite_disk,
                          c64_vice_d64_autostart_options)

ROOT = Path(__file__).parent


class Stage412AutostartTests(unittest.TestCase):
    def test_image_only_autostart_has_no_colon_program_suffix(self):
        with TemporaryDirectory() as td:
            image = Path(td) / 'Sprite_A.d64'
            image.write_bytes(build_1541_d64([('SPRITE-A', b'\x01\x08\x60'),
                                               ('sprites.spr', b'\x00\x30' + bytes(128))]))
            args = c64_vice_d64_autostart_options(image)
            self.assertEqual(args, ['-8', str(image.resolve()), '-autostart', str(image.resolve())])
            self.assertEqual(args[-1], args[1])
            self.assertFalse(args[-1].endswith(':SPRITE-A'))

    def test_first_directory_entry_is_program_second_is_sprite(self):
        with TemporaryDirectory() as td:
            root=Path(td)
            staging=root/'.d64_dism'/'vice_drive8'
            staging.mkdir(parents=True)
            spr=b'\x00\x30'+bytes(range(128))
            (staging/'sprites.spr').write_bytes(spr)
            prg=root/'Sprite_A.prg'; prg.write_bytes(b'\x01\x08'+bytes(range(200)))
            disk,name=prepare_c64_sprite_disk(staging, names=['sprites.spr'], program_path=prg,
                                               program_name='SPRITE-A')
            raw=disk.read_bytes()
            d0=_offset(18,1)
            self.assertEqual(raw[d0+2],0x82)
            self.assertEqual(raw[d0+5:d0+13], b'SPRITE-A')
            self.assertEqual(raw[d0+32+5:d0+32+16], b'SPRITES.SPR')
            # program data is the first sector chain, not just first listing line
            self.assertEqual(tuple(raw[d0+3:d0+5]), (17,0))
            self.assertEqual(tuple(raw[d0+32+3:d0+32+5]), (17,1))

    def test_ide_uses_only_d64_path_for_compiled_autostart(self):
        text=(ROOT/'d64_dism.py').read_text(encoding='utf-8')
        self.assertIn('*c64_vice_d64_autostart_options(sprite_disk)', text)
        self.assertNotIn("'-autostart', str(sprite_disk) + ':' + disk_program_name", text)
        self.assertIn("program_label = _re.sub(r'[^A-Za-z0-9.-]'", text)
        self.assertIn("command.extend(c64_vice_d64_command_options(sprite_disk))",text)

    def test_no_image_is_explicit_error(self):
        with TemporaryDirectory() as td:
            with self.assertRaises(FileNotFoundError):
                c64_vice_d64_autostart_options(Path(td)/'missing.d64')


if __name__ == '__main__':
    unittest.main()
