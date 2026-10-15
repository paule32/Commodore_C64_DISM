from pathlib import Path
import zipfile, ast, sys
BASE=Path('/mnt/data')
sys.path.insert(0,str(BASE/'stage410_work'))
from c64basic.compiler import compile_basic_to_assembly
from c64_d64_disk import build_1541_d64, _offset
from c64_vice_assets import c64_vice_sprite_program
from test_stage395_vice_context import make_namespace
source=(BASE/'Sprite_A(1).bas').read_text(encoding='utf-8')
r=compile_basic_to_assembly(source,filename='Sprite_A.bas')
ns=make_namespace();ns['ast']=ast
assembled=ns['assemble_mos6510_source'](r.assembly,filename='Sprite_A.generated.asm')
prg=assembled.prg
assert b'\x0bSPRITES.SPR' in prg and b'\x0bsprites.spr' not in prg
spr=c64_vice_sprite_program((BASE/'sprites(2).spr').read_bytes())
assert len(spr)==130 and spr[:2]==b'\x00\x30'
d64=build_1541_d64([('SPRITE_A',prg),('sprites.spr',spr)])
dir_offset=_offset(18,1)
assert d64[dir_offset+32+5:dir_offset+32+16]==b'SPRITES.SPR'
assert len(d64)==174848
p=BASE/'stage410_demo';p.mkdir(exist_ok=True)
(p/'Sprite_A.bas').write_text(source,encoding='utf-8')
(p/'Sprite_A.generated.asm').write_text(r.assembly,encoding='utf-8')
(p/'Sprite_A.prg').write_bytes(prg)
(p/'sprites.spr').write_bytes(spr)
(p/'Sprite_A_410.d64').write_bytes(d64)
(p/'README.txt').write_text('Stage 410 PETSCII-Test: ein D64 mit SPRITE_A PRG und SPRITES.SPR PRG.\n'
                          'Dateiname im Code und im Disk-Verzeichnis: 53 50 52 49 54 45 53 2E 53 50 52.\n'
                          'VICE x64sc: Sprite_A_410.d64 in Laufwerk 8 einlegen, PRG SPRITE_A starten.\n'
                          'C64-Sprite-Daten werden per LOAD an $3000 geladen.\n'
                          'PRG aus Stage 409 ist veraltet; Stage 410 benutzen.\n',encoding='utf-8')
with zipfile.ZipFile(BASE/'Sprite_A_410_PETSCII_Test.zip','w',zipfile.ZIP_DEFLATED) as z:
 for f in sorted(p.iterdir()):z.write(f,f.name)
print('PRG:',len(prg),'bytes; D64:',len(d64),'bytes; Sprite:',len(spr),'bytes')
print('ASM literal: ',next(line for line in r.assembly.splitlines() if ' .byte $0B, $53, $50, $52' in line))
