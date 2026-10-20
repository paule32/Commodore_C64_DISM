"""Stage 406 regression: compiled BASIC -> independently opened ASM -> VICE."""
import ast
import tempfile
import unittest
from pathlib import Path
from c64_vice_assets import (
    c64_generated_asm_basic_source,
    c64_basic_sprite_load_names,
    prepare_c64_vice_sprite_drive,
    c64_vice_drive8_command_options,
)

ROOT = Path(__file__).resolve().parent
UPLOADED_SOURCE = Path('/mnt/data/Sprite_A.bas')
UPLOADED_ASM = Path('/mnt/data/Sprite_A.generated.asm')
UPLOADED_PRG = Path('/mnt/data/Sprite_A.prg')


class GeneratedBasicSpriteStartTests(unittest.TestCase):
    def test_source_finder_case_insensitive(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root/'SPRITE_A.BAS').write_text('50 LOAD "sprites.spr",8,1\n',encoding='utf8')
            detected = c64_generated_asm_basic_source(root/'Sprite_A.generated.asm')
            self.assertEqual(detected.name, 'SPRITE_A.BAS')

    def test_source_finder_follows_compiler_header(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root/'Different_Name.bas'
            source.write_text('50 LOAD "sprites.spr",8,1\n',encoding='utf8')
            asm = '; C64 BASIC Compiler output: '+str(source)+'\n'
            self.assertEqual(c64_generated_asm_basic_source(root/'Sprite_A.generated.asm',assembly_source=asm),source.resolve())

    def test_rejects_unrelated_assembler_document(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            (root/'game.bas').write_text('LOAD "sprites.spr",8,1',encoding='utf8')
            self.assertIsNone(c64_generated_asm_basic_source(root/'game.asm'))

    def test_compiled_source_stages_sprite_with_3000_header(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            source=root/'Sprite_A.bas'
            source.write_text('50 LOAD "sprites.spr",8,1\n',encoding='utf8')
            (root/'sprites.spr').write_bytes(bytes([0xff])*64)
            asm=root/'Sprite_A.generated.asm'
            asm.write_text('; C64 BASIC Compiler output: '+str(source)+'\n',encoding='utf8')
            match = c64_generated_asm_basic_source(asm, assembly_source=asm.read_text())
            self.assertEqual(match,source.resolve())
            stage=prepare_c64_vice_sprite_drive(match.read_text(),match,stage_root=root/'drive8')
            self.assertEqual((stage/'sprites.spr').read_bytes(),b'\x00\x30'+bytes([0xff])*64)
            self.assertIn('-fs8',c64_vice_drive8_command_options(stage))

    def test_launch_wires_both_document_kinds(self):
        src=(ROOT/'d64_dism.py').read_text(encoding='utf8')
        ast.parse(src)
        self.assertIn('if document.is_basic_document or document.is_assembler_document:',src)
        self.assertIn('self._stage_c64_generated_basic_sprite_dependencies(',src)
        self.assertIn('VICE DRIVE8: virtuelles Sprite-Verzeichnis',src)

    def test_uploaded_source_and_asm_consistent(self):
        if not all(p.is_file() for p in (UPLOADED_SOURCE,UPLOADED_ASM,UPLOADED_PRG)):
            self.skipTest('User-provided example not present in project archive')
        names = c64_basic_sprite_load_names(UPLOADED_SOURCE.read_text(encoding='utf-8'))
        self.assertEqual(names,('sprites.spr',))
        asm=UPLOADED_ASM.read_text(encoding='utf8')
        self.assertIn('.byte $0B, $73, $70, $72, $69, $74, $65, $73, $2E, $73, $70, $72',asm)
        prg=UPLOADED_PRG.read_bytes()
        self.assertEqual(prg[:2],b'\x01\x08')


if __name__ == '__main__':
    unittest.main()
