#!/usr/bin/env python3
"""Execute and render the generated C64 multicolor graphics demo."""

from pathlib import Path
from PIL import Image
import d64_dism

# Assemble the checked-in complete graphics demo.
full = Path("examples/graphics/graphics_demo.generated.asm").read_text(encoding="utf-8")
prog = d64_dism.assemble_mos6510_source(full)

C,Z,I,D,B,U,V,N = 1,2,4,8,16,32,64,128
ops = d64_dism._D64INFO_MODULE.MOS6510_OPCODES

class CPU:
    def __init__(self):
        self.m=bytearray(65536)
        load=prog.load_address
        self.m[load:load+len(prog.prg)-2]=prog.prg[2:]
        self.m[0xFFD2]=0x60 # KERNAL CHROUT stub: RTS
        self.a=self.x=self.y=0
        self.sp=0xFF
        self.p=U
        self.pc=prog.entry_address
        self.steps=0
    def rd(self,a): return self.m[a&0xffff]
    def wr(self,a,v):
        a &=0xffff; v &=0xff
        if 0xD800 <= a <= 0xDBFF: v &= 0x0f
        self.m[a]=v
    def push(self,v): self.wr(0x100+self.sp,v); self.sp=(self.sp-1)&0xff
    def pull(self): self.sp=(self.sp+1)&0xff; return self.rd(0x100+self.sp)
    def set_nz(self,v):
        v &=255
        self.p = (self.p & ~(N|Z)) | (N if v&0x80 else 0) | (Z if v==0 else 0)
        return v
    def flag(self,f): return 1 if self.p&f else 0
    def fetch8(self): v=self.rd(self.pc); self.pc=(self.pc+1)&0xffff; return v
    def fetch16(self): lo=self.fetch8(); hi=self.fetch8(); return lo|(hi<<8)
    def addr(self,mode):
        if mode=='zp': return self.fetch8()
        if mode=='zpx': return (self.fetch8()+self.x)&255
        if mode=='zpy': return (self.fetch8()+self.y)&255
        if mode=='abs': return self.fetch16()
        if mode=='absx': return (self.fetch16()+self.x)&0xffff
        if mode=='absy': return (self.fetch16()+self.y)&0xffff
        if mode=='izx':
            z=(self.fetch8()+self.x)&255; return self.rd(z)|(self.rd((z+1)&255)<<8)
        if mode=='izy':
            z=self.fetch8(); return ((self.rd(z)|(self.rd((z+1)&255)<<8))+self.y)&0xffff
        if mode=='ind':
            p=self.fetch16(); return self.rd(p)|(self.rd((p&0xff00)|((p+1)&255))<<8)
        raise RuntimeError(mode)
    def val(self,mode):
        if mode=='imm': return self.fetch8()
        return self.rd(self.addr(mode))
    def branch(self,cond):
        off=self.fetch8(); off=off-256 if off&128 else off
        if cond: self.pc=(self.pc+off)&0xffff
    def compare(self,r,v):
        q=(r-v)&0x1ff
        self.p=(self.p&~C)|(C if r>=v else 0)
        self.set_nz(q&255)
    def step(self):
        pc0=self.pc; op=self.fetch8()
        if op not in ops: raise RuntimeError(f'illegal {op:02x} at {pc0:04x}')
        mn,mode=ops[op]
        self.steps+=1
        if mn=='LDA': self.a=self.set_nz(self.val(mode))
        elif mn=='LDX': self.x=self.set_nz(self.val(mode))
        elif mn=='LDY': self.y=self.set_nz(self.val(mode))
        elif mn=='STA': self.wr(self.addr(mode),self.a)
        elif mn=='STX': self.wr(self.addr(mode),self.x)
        elif mn=='STY': self.wr(self.addr(mode),self.y)
        elif mn=='TAX': self.x=self.set_nz(self.a)
        elif mn=='TAY': self.y=self.set_nz(self.a)
        elif mn=='TXA': self.a=self.set_nz(self.x)
        elif mn=='TYA': self.a=self.set_nz(self.y)
        elif mn=='TSX': self.x=self.set_nz(self.sp)
        elif mn=='TXS': self.sp=self.x
        elif mn=='PHA': self.push(self.a)
        elif mn=='PHP': self.push(self.p|B|U)
        elif mn=='PLA': self.a=self.set_nz(self.pull())
        elif mn=='PLP': self.p=(self.pull()|U)&~B
        elif mn=='AND': self.a=self.set_nz(self.a & self.val(mode))
        elif mn=='ORA': self.a=self.set_nz(self.a | self.val(mode))
        elif mn=='EOR': self.a=self.set_nz(self.a ^ self.val(mode))
        elif mn=='ADC':
            v=self.val(mode); total=self.a+v+self.flag(C); r=total&255
            self.p=(self.p&~(C|V))|(C if total>255 else 0)|(V if (~(self.a^v)&(self.a^r)&0x80) else 0)
            self.a=self.set_nz(r)
        elif mn=='SBC':
            v=self.val(mode); total=self.a+(v^255)+self.flag(C); r=total&255
            self.p=(self.p&~(C|V))|(C if total>255 else 0)|(V if ((self.a^r)&(self.a^v)&0x80) else 0)
            self.a=self.set_nz(r)
        elif mn=='CMP': self.compare(self.a,self.val(mode))
        elif mn=='CPX': self.compare(self.x,self.val(mode))
        elif mn=='CPY': self.compare(self.y,self.val(mode))
        elif mn=='BIT':
            v=self.val(mode); self.p=(self.p&~(N|V|Z))|(v&(N|V))|(Z if (self.a&v)==0 else 0)
        elif mn in ('ASL','LSR','ROL','ROR'):
            if mode=='acc': old=self.a
            else: ad=self.addr(mode); old=self.rd(ad)
            cin=self.flag(C)
            if mn=='ASL': new=(old<<1)&255; cout=old>>7
            elif mn=='LSR': new=old>>1; cout=old&1
            elif mn=='ROL': new=((old<<1)&255)|cin; cout=old>>7
            else: new=(old>>1)|(cin<<7); cout=old&1
            self.p=(self.p&~C)|(C if cout else 0); new=self.set_nz(new)
            if mode=='acc': self.a=new
            else: self.wr(ad,new)
        elif mn in ('INC','DEC'):
            ad=self.addr(mode); v=(self.rd(ad)+(1 if mn=='INC' else -1))&255; self.wr(ad,v); self.set_nz(v)
        elif mn=='INX': self.x=self.set_nz((self.x+1)&255)
        elif mn=='INY': self.y=self.set_nz((self.y+1)&255)
        elif mn=='DEX': self.x=self.set_nz((self.x-1)&255)
        elif mn=='DEY': self.y=self.set_nz((self.y-1)&255)
        elif mn=='CLC': self.p &= ~C
        elif mn=='SEC': self.p |= C
        elif mn=='CLI': self.p &= ~I
        elif mn=='SEI': self.p |= I
        elif mn=='CLV': self.p &= ~V
        elif mn=='CLD': self.p &= ~D
        elif mn=='SED': self.p |= D
        elif mn=='JMP': self.pc=self.addr(mode)
        elif mn=='JSR':
            ad=self.fetch16(); ret=(self.pc-1)&0xffff; self.push(ret>>8); self.push(ret&255); self.pc=ad
        elif mn=='RTS': self.pc=((self.pull()|(self.pull()<<8))+1)&0xffff
        elif mn=='RTI': self.p=(self.pull()|U)&~B; self.pc=self.pull()|(self.pull()<<8)
        elif mn=='BCC': self.branch(not self.p&C)
        elif mn=='BCS': self.branch(bool(self.p&C))
        elif mn=='BEQ': self.branch(bool(self.p&Z))
        elif mn=='BNE': self.branch(not self.p&Z)
        elif mn=='BMI': self.branch(bool(self.p&N))
        elif mn=='BPL': self.branch(not self.p&N)
        elif mn=='BVC': self.branch(not self.p&V)
        elif mn=='BVS': self.branch(bool(self.p&V))
        elif mn=='NOP': pass
        elif mn=='BRK': raise RuntimeError(f'BRK at {pc0:04x}')
        else: raise RuntimeError(f'unimplemented {mn}/{mode} at {pc0:04x}')

cpu=CPU(); end=prog.symbols['__c_program_end']; same=0
for i in range(12_000_000):
    if cpu.pc==end:
        same +=1
        if same>=2: break
    else: same=0
    cpu.step()
else: raise RuntimeError('timeout')
assert cpu.sp == 0xFF, hex(cpu.sp)
assert cpu.a == 5, hex(cpu.a)
assert cpu.m[0xD016] & 0x18 == 0x18, hex(cpu.m[0xD016])
assert cpu.m[prog.symbols["__gfx_palette_overflow"]] == 0

# Render VIC-II multicolor bitmap to 320x200 using a common C64 palette.
palette=[
(0,0,0),(255,255,255),(136,0,0),(170,255,238),
(204,68,204),(0,204,85),(0,0,170),(238,238,119),
(221,136,85),(102,68,0),(255,119,119),(51,51,51),
(119,119,119),(170,255,102),(0,136,255),(187,187,187)]
img=Image.new('RGB',(320,200),palette[cpu.m[0xD021]&15]); pix=img.load()
for y in range(200):
    cellrow=y>>3; row=y&7
    for cx in range(40):
        cell=cellrow*40+cx
        b=cpu.m[0xA000 + cell*8 + row]
        scr=cpu.m[0x8C00+cell]
        cols=[cpu.m[0xD021]&15,(scr>>4)&15,scr&15,cpu.m[0xD800+cell]&15]
        for q in range(4):
            code=(b>>(6-2*q))&3
            c=palette[cols[code]]
            x=cx*8+q*2
            pix[x,y]=c; pix[x+1,y]=c
output = Path("examples/graphics/graphics_demo.expected.c64.png")
img.save(output)
expected = {
    (10, 10): palette[2],
    (150, 30): palette[3],
    (105, 130): palette[4],
    (165, 130): palette[5],
    (200, 130): palette[1],
    (270, 95): palette[6],
    (260, 150): palette[7],
}
for point, colour in expected.items():
    assert img.getpixel(point) == colour, (point, img.getpixel(point), colour)
print(
    f"OK: {cpu.steps} instructions, stack=${cpu.sp:02X}, "
    f"center={cpu.a}, palette_overflow=0, image={output}"
)
