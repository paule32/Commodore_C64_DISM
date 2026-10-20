"""Stage 405: D64PACK hat vor ADC den Decimal-Modus zu deaktivieren.

Regression mit einer kleinen 6510-CPU-Simulation; kein PyQt5/VICE nötig.
"""
import ast
import dataclasses
import re
import struct
import sys
import unittest
from pathlib import Path
from typing import *
from test_stage395_vice_context import make_namespace, TREE, SOURCE
from c64basic.compiler import compile_basic_to_assembly


def packer_namespace():
    ns = make_namespace()
    ns.update(ast=ast, dataclass=dataclasses.dataclass, Mapping=Mapping, Callable=Callable)
    nodes = []
    names = {
        'normalize_packer_mode', 'normalize_search_mode',
        '_serialize_tokens', '_compress_rle', '_candidate_limit',
        '_best_lz_matches', '_lz_tokens_greedy', '_lz_tokens_maximum',
        '_compress_lz', 'decompress_stream_for_test',
        '_return_stub_bytes', '_choose_return_stub_address', '_hex16',
        '_decrunch_source', '_byte_lines', '_bootstrap_source',
        '_inspection_source', '_safe_assemble', '_assemble_payload_bytes',
        '_make_candidate', 'pack_c64_program'
    }
    classes = {'C64PackerError', 'C64PackerStats', '_C64PackToken'}
    for node in TREE.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            value = node.targets[0] if isinstance(node, ast.Assign) else node.target
            if isinstance(value, ast.Name) and value.id.startswith(
                    ('_ZP_', '_RETURN_', '_HIGH_', '_END_MARKER',
                     '_MAX_', 'PACKER_')):
                nodes.append(node)
        elif isinstance(node, ast.ClassDef) and node.name in classes:
            nodes.append(node)
        elif isinstance(node, ast.FunctionDef) and node.name in names:
            nodes.append(node)
    exec(compile(ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[])),
                 str(SOURCE), 'exec'), ns)
    return ns

class CPU:
  def __init__(self,prg,start,decimal=False):
    self.ram=bytearray(65536)
    addr=prg[0]|prg[1]<<8
    self.ram[addr:addr+len(prg)-2]=prg[2:]
    self.ram[1]=0x37
    self.pc=start;self.sp=0xfd; self.a=0;self.x=0;self.y=0;self.p=0x24 | (8 if decimal else 0)
    self.cycles=0
  def get(self,a):return self.ram[a&65535]
  def put(self,a,v):self.ram[a&65535]=v&255
  def fetch(self): b=self.get(self.pc);self.pc=(self.pc+1)&65535;return b
  def push(self,v):self.put(0x100+self.sp,v);self.sp=(self.sp-1)&255
  def pop(self):self.sp=(self.sp+1)&255;return self.get(0x100+self.sp)
  def zn(self,v):v&=255;self.p=(self.p & ~0x82)|(0x02 if v==0 else 0)|(v&0x80)
  def flag(self,flag,v):self.p=(self.p|flag) if v else (self.p & ~flag)
  def address(self,mode):
    if mode=='imp' or mode=='acc':return None
    if mode=='imm':a=self.pc;self.pc=(self.pc+1)&65535;return a
    if mode in ('zp','zpx','zpy','izx','izy'):
      z=self.fetch()
      if mode=='zp':return z
      if mode=='zpx':return (z+self.x)&255
      if mode=='zpy':return (z+self.y)&255
      if mode=='izx':z=(z+self.x)&255
      if mode in ('izx','izy'):
        addr=self.get(z)|self.get((z+1)&255)<<8
        if mode=='izy':addr=(addr+self.y)&65535
        return addr
    if mode=='rel':return self.fetch()
    lo=self.fetch();hi=self.fetch();addr=lo|(hi<<8)
    if mode=='abs':return addr
    if mode=='abx':return (addr+self.x)&65535
    if mode=='aby':return (addr+self.y)&65535
    if mode=='ind':return self.get(addr)|(self.get((addr&0xff00)|((addr+1)&0xff))<<8)
    raise RuntimeError(('mode',mode))
  def step(self):
    pc=self.pc; op=self.fetch()
    if op not in ops:raise RuntimeError(f'unknown opcode {op:02x} at {pc:04X}')
    m,mode=ops[op]
    a=self.address(mode)
    def v():return self.get(a)
    def register(r,b): setattr(self,r,b&255);self.zn(b)
    if m in ('LDA','LDX','LDY'):register({'LDA':'a','LDX':'x','LDY':'y'}[m],v())
    elif m in ('STA','STX','STY'):self.put(a,{'STA':self.a,'STX':self.x,'STY':self.y}[m])
    elif m in ('TAX','TAY','TXA','TYA','TSX','TXS'):
      dest={'TAX':'x','TAY':'y','TXA':'a','TYA':'a','TSX':'x','TXS':'sp'}[m]
      src={'TAX':'a','TAY':'a','TXA':'x','TYA':'y','TSX':'sp','TXS':'x'}[m]
      setattr(self,dest,getattr(self,src))
      if m != 'TXS':self.zn(getattr(self,dest))
    elif m in ('PHA','PHP'):self.push(self.a if m=='PHA' else (self.p|0x30))
    elif m in ('PLA','PLP'):
      value=self.pop()
      if m=='PLA':register('a',value)
      else:self.p=(value|0x20)&0xef
    elif m=='JMP':self.pc=a
    elif m=='JSR':
      ret=(self.pc-1)&65535
      self.push(ret>>8);self.push(ret&255);self.pc=a
    elif m=='RTS':self.pc=((self.pop()|self.pop()<<8)+1)&65535
    elif m in ('CLC','SEC','SEI','CLI','CLD','SED','CLV'):
      b={'CLC':1,'SEC':1,'SEI':4,'CLI':4,'CLD':8,'SED':8,'CLV':0x40}[m]
      self.flag(b,m in ('SEC','SEI','SED'))
    elif m in ('DEC','INC','DEX','INX','DEY','INY'):
      increment=m in ('INC','INX','INY')
      num={'DEC':v,'INC':v,'DEX':lambda:self.x,'INX':lambda:self.x,'DEY':lambda:self.y,'INY':lambda:self.y}[m]()
      out=(num+(1 if increment else -1))&255
      if m in ('DEC','INC'):self.put(a,out);self.zn(out)
      else:register('x' if m in ('DEX','INX') else 'y',out)
    elif m in ('CMP','CPX','CPY'):
      left={'CMP':self.a,'CPX':self.x,'CPY':self.y}[m]
      right=v();self.zn(left-right);self.flag(1,left>=right)
    elif m in ('ORA','AND','EOR'):
      func={'ORA':lambda x,y:x|y,'AND':lambda x,y:x&y,'EOR':lambda x,y:x^y}[m]
      register('a',func(self.a,v()))
    elif m in ('ADC','SBC'):
      lhs=self.a;rhs=v()
      if m=='SBC':rhs ^= 255
      out=lhs+rhs+(self.p&1)
      if self.p&8 and m=="ADC":
        low=(lhs&15)+(rhs&15)+(self.p&1)
        carry=low>9
        if carry:low+=6
        high=(lhs>>4)+(rhs>>4)+(1 if carry else 0)
        if high>9:high+=6
        out=((high<<4)|(low&15))
      self.flag(1,out>255)
      self.flag(0x40,(~(lhs ^ rhs)&(lhs^out)&0x80)!=0)
      register('a',out)
    elif m in ('BNE','BEQ','BCS','BCC','BPL','BMI','BVS','BVC'):
      mask={'BNE':2,'BEQ':2,'BCS':1,'BCC':1,'BPL':0x80,'BMI':0x80,'BVS':0x40,'BVC':0x40}[m]
      expect=m in ('BEQ','BCS','BMI','BVS')
      if bool(self.p&mask)==expect:self.pc=(self.pc+(a if a<0x80 else a-256))&65535
    elif m=='NOP':pass
    else:raise RuntimeError((pc,m,mode))
    self.cycles+=1
    return pc,m



class Stage405PackerDecimalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = packer_namespace()
        global ops
        ops = {number: (name, mode) for (name, mode), number in cls.ns['_assembler_opcode_map']().items()}

    def check_wrapper(self, asm_text, mode):
        ns = self.ns
        original = ns['assemble_mos6510_source'](asm_text)
        wrapper, stats = ns['pack_c64_program'](
            original, assemble_func=ns['assemble_mos6510_source'], mode=mode)
        self.assertEqual(stats.selected_mode, mode)
        self.assertTrue(wrapper.has_basic_stub)
        self.assertEqual(wrapper.prg[2:14], b'\x0b\x08\x0a\x00\x9e2061\x00\x00\x00')
        # Real RAM image, as VICE would load the PRG before SYS 2061.
        # Test explicitly with D=1 (BCD) and non-trivial A, X, Y registers.
        cpu = CPU(wrapper.prg, wrapper.entry_address, decimal=True)
        cpu.a = 0x27
        cpu.x = 0x33
        cpu.y = 0x5A
        original_registers = (cpu.a, cpu.x, cpu.y, cpu.p, cpu.sp, cpu.get(1))
        for _ in range(1_000_000):
            cpu.step()
            if cpu.pc == original.entry_address:
                break
        else:
            self.fail(f'{mode}: Entpacker erreichte den Programmeinstieg nicht')
        loaded = original.prg[0] | original.prg[1] << 8
        self.assertEqual(bytes(cpu.ram[loaded: loaded + len(original.prg)-2]),
                         original.prg[2:])
        self.assertEqual((cpu.a, cpu.x, cpu.y, cpu.p, cpu.sp, cpu.get(1)),
                         original_registers)
        self.assertEqual(wrapper.entry_address, 0x080D)
        self.assertIn('    cld\n', stats.asm_source)

    def test_lz_compile_basic_with_decimal_flag_set(self):
        text = '10 REM SPRITE TEST\n20 PRINT "HALLO"\n30 END'
        asm = compile_basic_to_assembly(text).assembly
        self.check_wrapper(asm, 'lz')

    def test_rle_compile_basic_with_decimal_flag_set(self):
        text = '10 REM SPRITE TEST\n20 PRINT "HALLO"\n30 END'
        asm = compile_basic_to_assembly(text).assembly
        self.check_wrapper(asm, 'rle')

    def test_rle_bcd_sensitive_run_length(self):
        asm = '.org $080D\n.entry START\nSTART:\n.fill 11,$55\n    rts\n'
        self.check_wrapper(asm, 'rle')

    def test_lz_bcd_sensitive_match_length(self):
        asm = '.org $080D\n.entry START\nSTART:\n.fill 90,$55\n    rts\n'
        self.check_wrapper(asm, 'lz')


if __name__ == '__main__':
    unittest.main()
