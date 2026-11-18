"""Stage 624: SET BACKGROUND TO compiler + Turbo-Vision integration tests.

Pure-Python integration checks; a real MinGW32/Qt GUI build still requires Windows.
"""
from pathlib import Path
import unittest

from d64dbase.compiler import (
    DBaseCompilerError, DBaseSetBackgroundStatement,
    compile_dbase_to_assembly, parse_dbase_statements,
)

ROOT = Path(__file__).resolve().parents[1]
BRIDGE = (ROOT / 'd64qt5/d64qt5_bridge.cpp').read_text(encoding='utf-8')
HEADER = (ROOT / 'd64qt5/d64_turbo_output.hpp').read_text(encoding='utf-8')
DEFS = (ROOT / 'd64qt5/d64qt5_bridge.def').read_text(encoding='utf-8')


class Stage624Test(unittest.TestCase):
    def compile(self, source, target='pe32'):
        result = compile_dbase_to_assembly(source, target=target)
        self.assertIn('call DBaseQtFillBackground', result.assembly)
        self.assertIn('import DBaseQtFillBackground, "libd64_qt5.dll", "DBaseQtFillBackground"', result.assembly)
        return result.assembly

    def test_parser_single(self):
        stmts = parse_dbase_statements('SET BACKGROUND TO 176')
        self.assertIsInstance(stmts[0], DBaseSetBackgroundStatement)
        self.assertEqual(len(stmts[0].arguments), 1)

    def test_parser_triple(self):
        stmts = parse_dbase_statements('set background to 1,14,177')
        self.assertEqual(len(stmts[0].arguments), 3)

    def test_pe32_single(self):
        asm = self.compile('SET BACKGROUND TO 176')
        self.assertIn('    push -1', asm)
        self.assertIn('    add esp, 12', asm)

    def test_pe64_single(self):
        asm = self.compile('SET BACKGROUND TO 177', 'pe64')
        self.assertIn('    mov edx, -1', asm)
        self.assertIn('    mov ecx, -1', asm)

    def test_pe32_three_params(self):
        asm = self.compile('SET BACKGROUND TO 1, 14, 219')
        self.assertIn('    call DBaseQtFillBackground', asm)
        self.assertIn('    push dword ptr [__dbase_background_arg_', asm)

    def test_pe64_three_params(self):
        asm = self.compile('SET BACKGROUND TO 1, 14, 219', 'pe64')
        for reg in ('ecx', 'edx', 'r8d'):
            self.assertIn('    mov '+reg+', dword ptr [__dbase_background_arg_', asm)

    def test_variables(self):
        self.compile('bg=2\nfg=15\nchar=35\nSET BACKGROUND TO bg,fg,char')

    def test_arithmetic(self):
        self.compile('SET BACKGROUND TO (1+2), 7*2, 160+16')

    def test_macro(self):
        self.compile('#define BG 2\n#define FG 15\n#define CH 176\nSET BACKGROUND TO BG,FG,CH')

    def test_function(self):
        self.compile('FUNCTION Zeichen()\n RETURN 65\nSET BACKGROUND TO Zeichen()')

    def test_function_three_params(self):
        self.compile('FUNCTION Farbe()\n RETURN 1\nSET BACKGROUND TO Farbe(), 14, 176')

    def test_hex(self):
        self.compile('SET BACKGROUND TO 0x01, 0x0F, 0xB0')

    def test_class_properties(self):
        for target in ('pe32', 'pe64'):
            self.compile('''CLASS TColor OF TObject
 PROPERTY Bg = 1
 PROPERTY Fg = 14
 PROPERTY Glyph = 176
 PROCEDURE Show()
  SET BACKGROUND TO self.Bg, self.Fg, self.Glyph
  RETURN
ENDCLASS''', target)

    def test_class_function_and_math(self):
        for target in ('pe32', 'pe64'):
            self.compile('''CLASS TColor OF TObject
 PROPERTY Bg = 1
 FUNCTION Glyph()
  RETURN 176
 PROCEDURE Show()
  SET BACKGROUND TO self.Bg+1, 14, Glyph()
  RETURN
ENDCLASS''', target)

    def test_invalid_counts(self):
        for source in ('SET BACKGROUND TO 1,2', 'SET BACKGROUND TO 1,2,3,4'):
            with self.assertRaises(DBaseCompilerError):
                compile_dbase_to_assembly(source)

    def test_invalid_ranges(self):
        for source in ('SET BACKGROUND TO 256',
                       'SET BACKGROUND TO -1',
                       'SET BACKGROUND TO 16,15,176',
                       'SET BACKGROUND TO 0, 16, 176',
                       'SET BACKGROUND TO 1,2,256',
                       'SET BACKGROUND TO 1.5,2,3'):
            with self.subTest(source=source), self.assertRaises(DBaseCompilerError):
                compile_dbase_to_assembly(source)

    def test_invalid_type(self):
        for source in ('SET BACKGROUND TO "W"', 'SET BACKGROUND TO 1,2,"A"'):
            with self.assertRaises(DBaseCompilerError):
                compile_dbase_to_assembly(source)

    def test_runtime_cpp_export(self):
        self.assertIn('int DBaseQtFillBackground(int bg, int fg, int code)', BRIDGE)
        self.assertIn('DBaseQtFillBackground @1016', DEFS)
        # Stage 625: the background belongs to the main QPlainTextEdit.
        self.assertIn('render_console_character_pattern(code, foreground, background)', BRIDGE)
        self.assertNotIn('g_turbo_output->fillBackground(bg, fg, code)', BRIDGE)

    def test_turbo_raster_and_cp437(self):
        self.assertIn('fillBackground(int background, int foreground, int character)', HEADER)
        self.assertIn('const ushort codePoints[256]', HEADER)
        for item in ('0x2591', '0x2592', '0x2593', '0x2588'):
            self.assertIn(item, HEADER)
        self.assertIn('const int ncols = qBound(1, columns_, 500)', HEADER)
        self.assertIn('const int nrows = qBound(1, rows_, 500)', HEADER)

    def test_turbo_overwrite_and_zoom(self):
        self.assertIn('overlayText_ += text;', HEADER)
        self.assertIn('lines[currentRow][currentColumn] = letter;', HEADER)
        self.assertIn('refreshBackgroundFill();', HEADER)
        self.assertIn('if (maximized_)\n            fitMaximizedToViewport();', HEADER)


if __name__ == '__main__':
    unittest.main()
