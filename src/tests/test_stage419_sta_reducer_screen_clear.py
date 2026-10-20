"""Stage 419: compact STA-reducer bitmap / screen / colour page clears."""
import ast
import unittest

from c64basic.compiler import compile_basic_to_assembly
from test_stage395_vice_context import make_namespace
import test_stage405_packer_decimal as cpu_model

SOURCE = '\n'.join((
    '10 SCREEN ON',
    '20 SPRITE SOFTWARE ON',
    '30 SCREEN OFF',
    '40 END',
))

RANGES = ((0x6000, 0x8000), (0x4400, 0x4800), (0xD800, 0xDC00))
GUARDS = (0x5FFF, 0x8000, 0x43FF, 0x4800, 0xD7FF, 0xDC00)


class Stage419ScreenClearTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = make_namespace()
        cls.ns['ast'] = ast
        cpu_model.ops = {
            code: (name, {'absx': 'abx', 'absy': 'aby'}.get(mode, mode))
            for (name, mode), code in cls.ns['_assembler_opcode_map']().items()
        }

    def assemble(self, reduce):
        assembly = compile_basic_to_assembly(SOURCE, sta_reducer=reduce).assembly
        compiled = self.ns['assemble_mos6510_source'](assembly)
        return assembly, compiled

    def test_legacy_loop_unchanged_when_disabled(self):
        asm, _ = self.assemble(False)
        self.assertIn('    sta $6000,x', asm)
        self.assertIn('    sta $6100,x', asm)
        self.assertIn('    sta $7F00,x', asm)
        self.assertIn('    sta $4400,x', asm)
        self.assertIn('    sta $DB00,x', asm)
        self.assertNotIn('__basic_soft_zero_pages:', asm)

    def test_enabled_reduces_all_three_memory_ranges(self):
        asm, packed = self.assemble(True)
        self.assertIn('__basic_soft_zero_clear:', asm)
        self.assertIn('__basic_soft_zero_pages:', asm)
        self.assertIn('    sta __basic_soft_zero_store+2', asm)
        self.assertIn('    inc __basic_soft_zero_store+2', asm)
        self.assertEqual(asm.count('    sta $6000,x'), 1)
        self.assertNotIn('    sta $6100,x', asm)
        self.assertNotIn('    sta $4400,x', asm)
        clear_asm = asm.split('__basic_soft_zero_clear:')[1].split('__basic_soft_screen_wait:')[0]
        self.assertNotIn('    sta $D800,x', clear_asm)
        for item in ('    lda #$60', '    ldy #$20',
                     '    lda #$44', '    ldy #$04',
                     '    lda #$D8'):
            self.assertIn(item, asm)
        _, normal = self.assemble(False)
        self.assertLess(len(packed.prg), len(normal.prg))
        self.assertEqual(len(normal.prg) - len(packed.prg), 82)

    def test_CPU_clear_exactly_those_pages_and_repeatably(self):
        _, prog = self.assemble(True)
        start = prog.symbols['__basic_soft_zero_clear']
        operand = prog.symbols['__basic_soft_zero_store'] + 2
        cpu = cpu_model.CPU(prog.prg, start)
        self.assertLess(prog.symbols['__basic_cbss_end'], 0x3000)
        # Indirect user data never intersects with the program code.
        for index in range(2):
            for low, end in RANGES:
                cpu.ram[low:end] = bytes([0xA5 + index]) * (end - low)
            for address in GUARDS:
                cpu.ram[address] = 0xE1 + index
            # Fake JSR return address $04FF, so RTS reaches $0500.
            cpu.pc = start
            cpu.sp = 0xFD
            cpu.push(0x04)
            cpu.push(0xFF)
            for _ in range(100000):
                if cpu.pc == 0x0500:
                    break
                cpu.step()
            else:
                self.fail('STA reducer screen clear never returned')
            for low, end in RANGES:
                self.assertEqual(bytes(cpu.ram[low:end]), bytes(end - low),
                                 f'wrong clear in ${low:04X}-${end-1:04X}')
            self.assertEqual([cpu.ram[a] for a in GUARDS], [0xE1 + index]*len(GUARDS))
            # After last page in colour RAM, high byte of the operand is $DC.
            self.assertEqual(cpu.ram[operand], 0xDC)

    def test_does_not_require_new_settings_or_new_call_signature(self):
        # The existing per-profile checkbox controls both optimizations.
        source = compile_basic_to_assembly(SOURCE,sta_reducer=False).assembly
        updated = compile_basic_to_assembly(SOURCE,sta_reducer=True).assembly
        self.assertIn('__basic_soft_zero_pages:', updated)
        self.assertNotIn('__basic_soft_zero_pages:', source)
        self.assertNotIn('__basic_sta_reducer_apply:', updated)


if __name__ == '__main__':
    unittest.main()
