"""Stage 415: TABs in C64 BASIC direct-debug keyboard feed + host origin log.

Run: python -m unittest -v test_stage415_vice_basic_tabs_sprite_origin
"""
import ast
from pathlib import Path
import unittest

from test_stage395_vice_context import extract, SOURCE


class Stage415ViceBasicTabsAndOriginTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fn = extract('c64_basic_text_to_petscii')
        class ViceBinaryMonitorError(RuntimeError):
            pass
        ns = {'ViceBinaryMonitorError': ViceBinaryMonitorError}
        exec(compile(ast.fix_missing_locations(ast.Module(body=[fn], type_ignores=[])),
                     str(SOURCE), 'exec'), ns)
        cls.encode = staticmethod(ns['c64_basic_text_to_petscii'])
        cls.exception = ViceBinaryMonitorError

    def test_rem_with_tab_from_user_example(self):
        line = '20 REM LOAD "figur.spr",8,1\tLAEDT DIE DATEI VOM D64-IMAGE\r'
        self.assertEqual(self.encode(line),
                         b'20 REM LOAD "FIGUR.SPR",8,1 LAEDT DIE DATEI VOM D64-IMAGE\r')

    def test_multiple_tabs_in_rem_and_no_unprintable_bytes(self):
        line = '10 REM A\tB\tC\r'
        self.assertEqual(self.encode(line), b'10 REM A B C\r')
        self.assertNotIn(b'\x09', self.encode(line))

    def test_no_tab_no_change_and_filename_case(self):
        self.assertEqual(self.encode('98 LOAD SPRITE "sprites.spr"\r'),
                         b'98 LOAD SPRITE "SPRITES.SPR"\r')
        self.assertEqual(self.encode('50 LOAD "sprites.spr",8,1\r'),
                         b'50 LOAD "SPRITES.SPR",8,1\r')

    def test_tab_in_string_documented_debug_fallback_to_space(self):
        self.assertEqual(self.encode('PRINT "A\tB"\r'), b'PRINT "A B"\r')

    def test_editor_petscii_private_bytes_unchanged(self):
        self.assertEqual(self.encode('REM \ue073\tZ\r'), b'REM s Z\r')

    def test_unsupported_characters_remain_explicit_errors(self):
        with self.assertRaisesRegex(self.exception, r'U\+20AC'):
            self.encode('PRINT "€"\r')

    def test_host_vs_disk_origin_in_debug_path(self):
        source = Path(__file__).with_name('d64_dism.py').read_text(encoding='utf-8')
        self.assertIn('client.load_sprite_resource(sprite_resource.address, sprite_resource.data)', source)
        self.assertIn('VICE LOAD SPRITE: HOST/WINDOWS -> VICE BINARY MONITOR:', source)
        self.assertIn('VICE D64 ATTACH: -8 ', source)
        self.assertIn("client.feed_basic_line(f'{line_number} REM LOAD SPRITE HOST')", source)


if __name__ == '__main__':
    unittest.main()
