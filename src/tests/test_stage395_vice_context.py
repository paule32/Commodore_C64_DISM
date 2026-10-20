"""Stage 395: GUI-free tests of VICE transfer, PC register, assembler stepping and menus.

Run: python -m unittest -v test_stage395_vice_context.py
"""
import ast
from dataclasses import dataclass
import re
import struct
from pathlib import Path
from typing import Optional, Tuple, Dict, List, Sequence
from types import SimpleNamespace
import unittest

SOURCE = Path(__file__).with_name('d64_dism.py')
TEXT = SOURCE.read_text(encoding='utf-8')
TREE = ast.parse(TEXT)

def extract(name, *, kind=ast.FunctionDef):
    result = [n for n in ast.walk(TREE) if isinstance(n, kind) and n.name == name]
    if len(result) != 1:
        raise AssertionError((name, len(result)))
    node = result[0]
    if isinstance(node, ast.FunctionDef):
        node.decorator_list = []
    return node

def make_namespace():
    constants = {}
    for node in TREE.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            value = node.targets[0] if isinstance(node, ast.Assign) else node.target
            if isinstance(value, ast.Name) and (value.id.startswith('_ASSEMBLER_') or value.id.startswith('MOS6510_')):
                constants[value.id] = node
    nodes = list(constants.values())
    nodes += [extract(name, kind=ast.ClassDef) for name in (
        'AssemblerError', 'AssemblerStatement', 'AssemblerLayoutItem',
        'AssemblerLayout', 'AssembledProgram', 'ViceBinaryMonitorError', '_AssemblerExpressionParser',
    )]
    # Pure assembler implementation only; GUI imports are deliberately excluded.
    # Assembler-Funktionen anhand stabiler Namen statt Quelltext-Zeilennummern.
    first = next(i for i, n in enumerate(TREE.body)
                 if getattr(n, 'name', '') == '_assembler_opcode_map')
    last = next(i for i, n in enumerate(TREE.body)
                if getattr(n, 'name', '') == 'assemble_mos6510_source')
    nodes += [n for n in TREE.body[first:last + 1]
              if isinstance(n, ast.FunctionDef)]
    nodes += [extract('c64_vice_prg_memory_image'), extract('_assembler_vice_step_plan')]
    ns = dict(dataclass=dataclass, re=re, struct=struct, Optional=Optional,
              Tuple=Tuple, Dict=Dict, List=List, Sequence=Sequence)
    exec(compile(ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[])), str(SOURCE), 'exec'), ns)
    return ns

class StubEditor:
    def __init__(self, first=4, last=None):
        self.first = first
        self.last = last
    def textCursor(self): return self
    def block(self): return self
    def blockNumber(self): return self.first - 1
    def hasSelection(self): return self.last is not None
    def selectionStart(self): return self.first * 100
    def selectionEnd(self): return (self.last or self.first) * 100 + 1
    def document(self): return self
    def findBlock(self, position):
        return SimpleNamespace(blockNumber=lambda: position // 100 - 1)

class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.ns = make_namespace()

    def test_prg_excludes_load_address_and_checks_wrap(self):
        decode = self.ns['c64_vice_prg_memory_image']
        self.assertEqual(decode(b'\x00\x10\xa9\x01\x60',0x1000),
                         (0x1000,b'\xa9\x01\x60',0x1000))
        with self.assertRaises(self.ns['ViceBinaryMonitorError']):
            decode(b'\xff\xff\x01\x02',0xFFFF)
        with self.assertRaises(self.ns['ViceBinaryMonitorError']):
            decode(b'\x00\x10',0x1000)

    def test_assembler_line_maps_to_code_address_in_full_source(self):
        source = '.org $1000\n.nostub\nSTART:\n LDA #$01\n STA $D020\n RTS\n'
        program = self.ns['assemble_mos6510_source'](source)
        self.assertEqual(program.prg,b'\x00\x10\xa9\x01\x8d\x20\xd0\x60')
        func = self.ns['_assembler_vice_step_plan']
        prg, entry, steps = func(source, 'line',StubEditor(4))
        self.assertEqual((prg, entry,steps),(program.prg,0x1000,1))
        prg, entry, steps = func(source, 'selection',StubEditor(4,5))
        self.assertEqual((prg,entry,steps),(program.prg,0x1000,2))

    def test_assembler_non_instruction_rejected_for_step(self):
        with self.assertRaises(self.ns['ViceBinaryMonitorError']):
            self.ns['_assembler_vice_step_plan'](
                '.org $1000\n.nostub\nSTART:\n RTS\n', 'line', StubEditor(3))

    def test_vice_pc_register_resolution_and_request_format(self):
        client_class=extract('ViceBinaryMonitorClient',kind=ast.ClassDef)
        client_class.body=[node for node in client_class.body
            if isinstance(node,ast.FunctionDef) and node.name in ('set_program_counter','advance_instructions')]
        ns = dict(struct=struct, ViceBinaryMonitorError=self.ns['ViceBinaryMonitorError'],
                  VICE_BINARY_MONITOR_REGISTERS_AVAILABLE=0x83,
                  VICE_BINARY_MONITOR_REGISTERS_SET=0x32,
                  VICE_BINARY_MONITOR_REGISTER_INFO=0x31,
                  VICE_BINARY_MONITOR_ADVANCE_INSTRUCTIONS=0x71)
        exec(compile(ast.fix_missing_locations(ast.Module(body=[client_class], type_ignores=[])),str(SOURCE),'exec'),ns)
        client=ns['ViceBinaryMonitorClient']()
        calls=[]
        def command(code,payload,response_type=None):
            calls.append((code,bytes(payload),response_type))
            if code == 0x83:
                return b'\x02\x00' + b'\x04\x08\x10\x01X' + b'\x05\x23\x10\x02PC'
            return b''
        client.command=command
        client.set_program_counter(0x1000)
        self.assertEqual(calls[0],(0x83,b'\x00',None))
        self.assertEqual(calls[1],(0x32,b'\x00\x01\x00\x03\x23\x00\x10',0x31))
        client.advance_instructions(2)
        self.assertEqual(calls[2],(0x71,b'\x01\x02\x00',None))

    def test_signal_menu_wiring(self):
        self.assertIn('self.assembler_vice_requested.emit(self, operation)',TEXT)
        self.assertIn('self._handle_assembler_vice_debug_request',TEXT)
        self.assertIn('"run" if is_asm else "program_run"', TEXT)
        self.assertIn('client.write_memory(load_address, payload)',TEXT)
        self.assertIn('client.set_program_counter(entry_address)',TEXT)
        self.assertIn('client.advance_instructions(step_count)',TEXT)
        self.assertIn('standard_menu = self.createStandardContextMenu()',TEXT)

if __name__ == '__main__':
    unittest.main()
