"""Stage 414: reproduzierbarer GUI-Editor/Compiler-Fehlerbericht und Parser-Kontext."""
from pathlib import Path
import unittest
from tempfile import TemporaryDirectory

from c64basic.compiler import compile_basic_to_assembly, C64BasicError
from c64basic.editor_model import (
    split_numbered_basic_source, wrap_basic_lines,
    reconcile_basic_line_numbering, serialize_numbered_basic_source,
)


USER_SOURCE = '''REM LOAD "figur.spr",8,1\tLAEDT DIE ANGEGEBENE DATEI VOM EINGELEGTEN D64-IMAGE
REM AUF LAUFWERK 8.

REM LOAD SPRITE "figur.spr"\tLIEST DIE SPRITE-DATEI VOM WINDOWS-HOST
REM UND STELLT IHRE DATEN AB $3000 BEREIT.

REM LOAD SPRITE "figur.spr",$3040\tVERWENDET DIE ALTERNATIVE ZIELADRESSE $3040.

LOAD SPRITE "sprites.spr"

POKE  2040,192
POKE 53248,120
POKE 53249,100
POKE 53264,0
POKE 53276,0
POKE 53287,1
POKE 53269,1

END'''


class Stage414GuiCompileDiagnostics(unittest.TestCase):
    def _source_path(self, parent):
        path = Path(parent) / 'Sprite_Test_1.bas'
        path.write_text(USER_SOURCE, encoding='utf-8')
        (Path(parent) / 'sprites.spr').write_bytes(bytes([255])*64)
        return path

    def test_entire_user_source(self):
        with TemporaryDirectory() as directory:
            path = self._source_path(directory)
            asm = compile_basic_to_assembly(path.read_text('utf-8'),filename=str(path)).assembly
            self.assertIn('__basic_sprite_resource_', asm)

    def test_c64_editor_wrapped_and_gutter_numbered_source(self):
        with TemporaryDirectory() as directory:
            path = self._source_path(directory)
            lines, numbers = split_numbered_basic_source(USER_SOURCE)
            lines, numbers = wrap_basic_lines(lines, numbers, max_columns=80)
            lines, numbers, _ = reconcile_basic_line_numbering(lines,numbers,max_columns=80)
            numbered=serialize_numbered_basic_source(lines,numbers)
            self.assertIn('LOAD SPRITE "sprites.spr"',numbered)
            asm = compile_basic_to_assembly(numbered,filename=str(path)).assembly
            self.assertIn('__basic_sprite_resource_', asm)

    def test_manual_line_98_supported(self):
        with TemporaryDirectory() as directory:
            path=self._source_path(directory)
            asm=compile_basic_to_assembly('98 LOAD SPRITE "sprites.spr"\n106 POKE 2040,192\n170 END',filename=str(path)).assembly
            self.assertIn('__basic_line_98:',asm)

    def test_parser_error_preserves_actual_statement(self):
        with TemporaryDirectory() as directory:
            path=self._source_path(directory)
            with self.assertRaises(C64BasicError) as ctx:
                compile_basic_to_assembly('98 XYZ=\n100 END',filename=str(path))
            self.assertEqual(getattr(ctx.exception,'source_statement',None),'XYZ=')
            self.assertEqual(ctx.exception.line,98)

    def test_gui_logs_loaded_compiler_and_actual_source(self):
        gui=(Path(__file__).parent/'d64_dism.py').read_text(encoding='utf-8')
        self.assertIn('C64 BASIC COMPILER:',gui)
        self.assertIn('C64 BASIC EINGABE:',gui)
        self.assertIn('C64 BASIC PARSERFEHLER:',gui)
        self.assertIn('Quelltext im Compiler:',gui)


if __name__=='__main__':
    unittest.main()
