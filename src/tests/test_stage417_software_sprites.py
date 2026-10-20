"""Stage 417: software sprites, bitmap VIC-II and compile/assemble regression."""
import ast
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from c64_bitmap_sprite import encode_bitmap_sprites, TRANSPARENT
from c64_software_sprite import (load_software_sprite_sheet, SoftwareSpriteScene,
                                 BITMAP_ADDR, SCREEN_ADDR, COLOR_ADDR)
from c64basic import compile_basic_to_assembly, C64BasicError
from test_stage395_vice_context import make_namespace

ROOT = Path(__file__).parent


class Stage417Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ns = make_namespace()
        ns['ast'] = ast
        cls.assemble = staticmethod(ns['assemble_mos6510_source'])

    def test_hardware_spr_decode(self):
        with TemporaryDirectory() as d:
            f = Path(d)/'sprites.spr'
            f.write_bytes(bytes([0x80, 0, 0]*21 + [0]) + bytes(64))
            sheet = load_software_sprite_sheet(f)
            self.assertEqual((sheet.width, sheet.height, len(sheet.sprites)), (24,21,2))
            self.assertEqual(sheet.sprites[0][0], 1)
            self.assertEqual(sheet.sprites[0][1], TRANSPARENT)
            self.assertTrue(all(x==TRANSPARENT for x in sheet.sprites[1]))

    def test_bitmap_16_palette_indices_across_cells(self):
        with TemporaryDirectory() as d:
            f = Path(d)/'figur.bmsprite'
            pix = bytearray([TRANSPARENT]* (24*24))
            for y in range(24):
                for x in range(24):
                    pix[y*24+x] = 1+ (x//4 + (y//8)*6) % 15
            f.write_bytes(encode_bitmap_sprites([pix],24,24))
            sheet = load_software_sprite_sheet(f)
            self.assertEqual(sheet.sprites[0], bytes(pix))
            scene = SoftwareSpriteScene();scene.sheet=sheet
            bmp, scr, col = scene.move(0, 100, 80)
            self.assertEqual(len(bmp),8000)
            self.assertTrue(any(bmp))
            self.assertIn(15, set(scr) | set(col) | {b>>4 for b in scr})

    def test_overlap_erase_restores_second_sprite(self):
        with TemporaryDirectory() as d:
            f=Path(d)/'figuren.bmsprite'
            one=bytearray([TRANSPARENT]*64);two=bytearray([TRANSPARENT]*64)
            for i in range(64):one[i]=2;two[i]=5
            f.write_bytes(encode_bitmap_sprites([one,two],8,8))
            scene=SoftwareSpriteScene();scene.sheet=load_software_sprite_sheet(f)
            scene.move(0,100,80);a=scene.move(1,104,80)
            scene.commit(a)
            b=scene.erase(0)
            changes=scene.commit(b)
            self.assertTrue(any(base<=addr<base+size for addr,_ in changes for base,size in [(BITMAP_ADDR,8000),(SCREEN_ADDR,1000),(COLOR_ADDR,1000)]))
            self.assertIn(1,scene.visible)
            self.assertNotIn(0,scene.visible)
            single=SoftwareSpriteScene();single.sheet=scene.sheet
            self.assertEqual(b,single.move(1,104,80))

    def test_reject_4_non_background_colors_in_cell(self):
        with TemporaryDirectory() as d:
            f=Path(d)/'busy.bmsprite'
            f.write_bytes(encode_bitmap_sprites([[1,2,3,4]],4,1))
            scene=SoftwareSpriteScene();scene.sheet=load_software_sprite_sheet(f)
            with self.assertRaisesRegex(ValueError,'Farbgrenze'):
                scene.move(0,0,0)
            self.assertFalse(scene.visible)

    def test_compile_and_assemble_original_user_commands(self):
        with TemporaryDirectory() as d:
            d=Path(d); (d/'figuren.spr').write_bytes((ROOT/'sprites.spr').read_bytes())
            source='''10 LOAD SPRITE "figuren.spr"
20 SCREEN ON
30 SPRITE SOFTWARE ON
40 SPRITE DRAW 0,100,80
50 SPRITE DRAW 1,140,80
60 SPRITE ERASE 0
70 SCREEN OFF
80 END'''
            asm=compile_basic_to_assembly(source,filename=str(d/'test.bas')).assembly
            for code in ('jsr __basic_soft_screen_on','jsr __basic_soft_screen_off',
                         '__basic_soft_save_colour:', '__basic_soft_restore_colour:',
                         'sta $DD00','sta $D018','sta $D011','sta $D016','sta $D021',
                         'sta $6000,x','sta $4400,x','sta $D800,x'):
                self.assertIn(code,asm)
            prg=self.assemble(asm)
            self.assertEqual(prg.prg[:2], b'\x01\x08')
            self.assertLess(prg.symbols['__basic_cbss_end'],0x3000)
            self.assertLess(prg.symbols['__basic_image_end'],0x3000)

    def test_compile_bitmap_sheet(self):
        with TemporaryDirectory() as d:
            d=Path(d)
            img=bytes([12]* 16*16)
            (d/'girl.bmsprite').write_bytes(encode_bitmap_sprites([img],16,16))
            asm=compile_basic_to_assembly('10 LOAD SPRITE "girl.bmsprite"\n20 SCREEN ON\n30 SPRITE SOFTWARE ON\n40 SPRITE DRAW 0,20,30\n50 SPRITE ERASE 0\n60 SCREEN OFF\n70 END', filename=str(d/'a.bas')).assembly
            self.assertIn('Software-Sprites vorbereitet',asm)
            self.assertNotIn('jsr __basic_sprite_copy',asm)
            self.assemble(asm)

    def test_errors_and_control_flow_guard(self):
        with TemporaryDirectory() as d:
            d=Path(d)
            (d/'g.bmsprite').write_bytes(encode_bitmap_sprites([[1]*64],8,8))
            prefix='10 LOAD SPRITE "g.bmsprite"\n20 SCREEN ON\n30 SPRITE SOFTWARE ON\n'
            for stmt in ('SPRITE DRAW 0,101,80', 'SPRITE DRAW 1,100,80',
                         'SPRITE DRAW 0,A,80', 'SPRITE DRAW 0,100,200',
                         'SPRITE ERASE 1'):
                with self.subTest(stmt=stmt),self.assertRaises(C64BasicError):
                    compile_basic_to_assembly(prefix+'40 '+stmt,filename=str(d/'x.bas'))
            with self.assertRaisesRegex(C64BasicError,'lineare BASIC'):
                compile_basic_to_assembly(prefix+'40 SPRITE DRAW 0,100,80\n50 GOTO 40',filename=str(d/'x.bas'))

    def test_gui_rejects_direct_basic_v2_for_software_sprite(self):
        gui=(ROOT/'d64_dism.py').read_text()
        self.assertIn('VICE BASIC Debug - Bitmap Software-Sprites',gui)
        self.assertIn('"c64_software_sprite"', (ROOT/'d64_dism.spec').read_text())


if __name__=='__main__':
    unittest.main()
