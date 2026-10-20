"""Stage 418: lossless compact STA update streams and per-profile project setting."""
import ast
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from c64basic.compiler import _BasicCompiler, compile_basic_to_assembly
from test_stage395_vice_context import make_namespace
import test_stage405_packer_decimal as cpu_model

ROOT = Path(__file__).resolve().parent


def decode(data):
    """Independent Python reference for the 6502 table stream."""
    i = 0
    result = []
    while True:
        marker = data[i]
        i += 1
        if marker == 0:
            assert i == len(data), ('trailing bytes', len(data), i)
            return result
        address = data[i] | (data[i + 1] << 8)
        i += 2
        if marker & 0x80:
            count = 256 - marker
            result.extend((address + j, data[i]) for j in range(count))
            i += 1
        else:
            result.extend((address + j, data[i+j]) for j in range(marker))
            i += marker


class Stage418ReducerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = make_namespace()
        cls.ns['ast'] = ast
        cpu_model.ops = {opcode: (name, mode) for (name, mode), opcode in cls.ns['_assembler_opcode_map']().items()}

    @staticmethod
    def source():
        return '\n'.join((
            '10 LOAD SPRITE "sprites.spr"',
            '20 SCREEN ON',
            '30 SPRITE SOFTWARE ON',
            '40 SPRITE DRAW 0,100,80',
            '45 SCREEN WAIT',
            '50 SPRITE ERASE 0',
            '60 SCREEN OFF',
            '70 END',
        ))

    def test_encoding_roundtrip_run_literal_page_crossings_and_gaps(self):
        modifications = []
        modifications.extend((0x6c7c + i, 0x05) for i in range(180))
        modifications.extend((0x7400 + i, (i * 7) & 0xff) for i in range(132))
        modifications.extend((0xD800 + i*3, (i + 1) & 15) for i in range(50))
        packed = _BasicCompiler._sta_reducer_encode(modifications)
        self.assertEqual(decode(packed), modifications)
        self.assertLess(len(packed), len(modifications) * 3)
        self.assertIn(256-127, packed)

    def test_off_keeps_stage417_direct_sta(self):
        asm = compile_basic_to_assembly(self.source(), filename=str(ROOT/'sample.bas'),sta_reducer=False).assembly
        self.assertIn('Software-Sprite:', asm)
        self.assertNotIn('__basic_sta_reducer_apply:', asm)
        self.assertNotIn('sta_reducer_table_', asm)
        self.assertIn('sta $', asm)

    def test_on_uses_table_assembles_and_reduces_prg(self):
        src = self.source()
        normal = compile_basic_to_assembly(src, filename=str(ROOT/'sample.bas'),sta_reducer=False).assembly
        packed = compile_basic_to_assembly(src, filename=str(ROOT/'sample.bas'),sta_reducer=True).assembly
        self.assertIn('__basic_sta_reducer_apply:', packed)
        self.assertIn('sta_reducer_table_', packed)
        self.assertIn('jsr __basic_sta_reducer_apply', packed)
        basic_prg = self.ns['assemble_mos6510_source'](normal)
        reduced_prg = self.ns['assemble_mos6510_source'](packed)
        self.assertLess(len(reduced_prg.prg), len(basic_prg.prg))
        self.assertEqual(reduced_prg.prg[:2], b'\x01\x08')
        self.assertLess(reduced_prg.symbols['__basic_cbss_end'], 0x3000)

        # Exercise the assembled 6510 table interpreter, not just Python codec.
        # The generated routine uses no ROM calls; it must write precisely the
        # same VIC bitmap/screen/colour addresses as legacy inline STA.
        compiler = _BasicCompiler('', str(ROOT/'sample.bas'),sta_reducer=True)
        class FakeScene:
            def __init__(self, mod): self.mod = mod
            def commit(self, _planes): return self.mod
        changes = [(0x6CF8+i, 5) for i in range(145)] + [(0xD800+i, i & 15) for i in range(30)]
        compiler.soft_scene = FakeScene(changes)
        compiler._soft_emit_deltas(None)
        self.assertEqual(len(compiler.sta_reducer_tables), 1)
        name, table = compiler.sta_reducer_tables[0]
        self.assertEqual(decode(table), changes)
        # The compiler's full assembly includes all the runtime and table data.
        asm_lines = ['.org $080D', '.entry TEST', 'TEST:',
                     'lda #<'+name, 'ldy #>'+name,
                     'jsr __basic_sta_reducer_apply', 'rts']
        compiler.lines = asm_lines
        compiler.emit_sta_reducer_runtime()
        compiler.emit_storage()
        compiler.emit('end')
        program = self.ns['assemble_mos6510_source']('\n'.join(compiler.lines))
        cpu = cpu_model.CPU(program.prg, program.symbols['test'])
        # Seed target locations with different data, except program RAM.
        for address, _ in changes:
            cpu.ram[address] = 0xa5
        for _ in range(100000):
            if cpu.pc == program.symbols['test'] + 7: # RTS after LDA# / LDY# / JSR = 2+2+3
                break
            cpu.step()
        else:
            self.fail('6510 reducer did not return')
        self.assertEqual([cpu.ram[a] for a, _ in changes], [v for _,v in changes])
        self.assertEqual(cpu.ram[changes[0][0]-1], 0)
        self.assertEqual(cpu.ram[changes[-1][0]+1], 0)

    def test_gui_checkbox_project_roundtrip_sources(self):
        text = (ROOT/'d64_dism.py').read_text(encoding='utf-8')
        for bit in ('STA reducer', 'c64_sta_reducer_checkbox', 'STAReducer',
                    'set_project_c64_sta_reducer', 'set_c64_sta_reducer',
                    'sta_reducer=self._project_c64_sta_reducer_configuration()',
                    'sta_reducer_key'):
            self.assertIn(bit, text)
        self.assertEqual(text.count('"sta_reducer_key":'), 4)


if __name__ == '__main__':
    unittest.main()
