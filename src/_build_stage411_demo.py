"""Build reproducible Stage-411 output from user's uploaded BASIC and sprite."""
from pathlib import Path
import ast
import zipfile

from c64basic.compiler import compile_basic_to_assembly
from c64_d64_disk import build_1541_d64, _offset
from c64_vice_assets import c64_vice_sprite_program
from test_stage395_vice_context import make_namespace

root=Path('/mnt/data')
src=(root/'Sprite_A(1).bas').read_text(encoding='utf-8-sig')
spr=c64_vice_sprite_program((root/'sprites(2).spr').read_bytes())
result=compile_basic_to_assembly(src,filename='Sprite_A.bas')
ns=make_namespace();ns['ast']=ast
assembled=ns['assemble_mos6510_source'](result.assembly,filename='Sprite_A.generated.asm')
prg=assembled.prg
setnam=prg.index(b'\x20\xbd\xff')
ptr=prg[setnam-3] | (prg[setnam-1]<<8)
literal=prg.index(b'\x0bSPRITES.SPR')
real_address=assembled.load_address+literal-1
assert ptr==real_address,(hex(ptr),hex(real_address))
assert prg[literal+1:literal+12] == b'SPRITES.SPR'
d64=build_1541_d64([('SPRITE_A',prg),('sprites.spr',spr)])
o=_offset(18,1)+32
assert d64[o+5:o+16]==b'SPRITES.SPR'
folder=root/'stage411_demo';folder.mkdir(exist_ok=True)
(folder/'Sprite_A.bas').write_text(src,encoding='utf-8')
(folder/'Sprite_A.generated.asm').write_text(result.assembly,encoding='utf-8')
(folder/'Sprite_A.prg').write_bytes(prg)
(folder/'sprites.spr').write_bytes(spr)
(folder/'Sprite_A_411.d64').write_bytes(d64)
(folder/'STAGE411_Diagnose.txt').write_text(
    'SETNAM-Diagnose (aus dem zusammengestellten MOS6510-Programm):\n'
    f'BASIC-Dateiname: sprites.spr\n'
    f'PETSCII-Dateiname: SPRITES.SPR (53 50 52 49 54 45 53 2E 53 50 52)\n'
    f'Datenadresse des Dateinamens: ${real_address:04X}\n'
    f'SETNAM-Register: X=${prg[setnam-3]:02X}, Y=${prg[setnam-1]:02X}\n'
    f'SETNAM-Zeiger: ${ptr:04X}\n'
    f'D64-Dateiname: SPRITES.SPR\n'
    f'D64-Dateigroesse: {len(d64)} Bytes\n'
    'VICE: Sprite_A_411.d64 an Geraet 8 einlegen, SPRITE_A starten.\n'
    'Hinweis: keine Verifikation der tatsaechlichen VICE-Ausfuehrung.\n', encoding='utf-8'
)
with zipfile.ZipFile(root/'Sprite_A_411_Test.zip','w',zipfile.ZIP_DEFLATED) as z:
    for p in sorted(folder.iterdir()):z.write(p,p.name)
print('Sprite PRG',len(spr),'Bytes; Sprite_A PRG',len(prg),'Bytes; D64',len(d64),'Bytes; literal address',hex(real_address),'SETNAM pointer',hex(ptr))
