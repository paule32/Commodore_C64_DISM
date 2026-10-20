"""Stage 420: Reachability-Optimizer, project GUI persistence and assembly tests."""
from pathlib import Path
import ast
import unittest

from c64basic.call_reducer import reduce_runtime_calls
from c64basic.compiler import compile_basic_to_assembly
from test_stage395_vice_context import make_namespace

ROOT = Path(__file__).resolve().parent


class Stage420CallReducerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = make_namespace()
        cls.ns['ast'] = ast

    def assemble(self, source, *, call_reducer=False, sta_reducer=False, filename='<memory>'):
        result = compile_basic_to_assembly(
            source, call_reducer=call_reducer, sta_reducer=sta_reducer,
            filename=filename)
        assembled = self.ns['assemble_mos6510_source'](result.assembly)
        return result, assembled

    def test_unused_runtime_routines_are_removed(self):
        off, old = self.assemble('10 END', call_reducer=False)
        on, new = self.assemble('10 END', call_reducer=True)
        self.assertIn('__basic_print_float:', off.assembly)
        self.assertNotIn('__basic_print_float:', on.assembly)
        self.assertNotIn('__basic_string_append:', on.assembly)
        self.assertIn('__basic_init_cbss:', on.assembly)
        self.assertIn('__basic_program_end:', on.assembly)
        self.assertLess(len(new.prg), len(old.prg))
        self.assertIn('CALL reducer: aktiv;', ' '.join(on.notes))

    def test_print_and_numeric_dependencies_stay_linked(self):
        source = '10 A=27\n20 PRINT A\n30 PRINT "HELLO"\n40 END'
        off, old = self.assemble(source, call_reducer=False)
        on, new = self.assemble(source, call_reducer=True)
        self.assertIn('__basic_print_float:', on.assembly)
        self.assertIn('__basic_print_z:', on.assembly)
        self.assertIn('__basic_init_cbss:', on.assembly)
        self.assertLess(len(new.prg), len(old.prg))
        # The visible output and load address remain unaffected.
        self.assertEqual(new.prg[:2], old.prg[:2])

    def test_branch_and_jsr_graph_and_address_taken(self):
        code = ['jsr __basic_alive', 'rts', '__basic_alive:', 'beq __basic_alive_skip', 'jsr __basic_helper',
                '__basic_alive_skip:', 'rts', '__basic_dead:', 'jsr __basic_dead_helper', 'rts',
                '__basic_helper:', 'rts', '__basic_dead_helper:', 'rts']
        reduced = reduce_runtime_calls(code, 2, len(code))
        joined = '\n'.join(reduced.lines)
        self.assertIn('__basic_helper:', joined)
        self.assertIn('__basic_alive_skip:', joined)
        self.assertNotIn('__basic_dead_helper:', joined)
        self.assertNotIn('__basic_dead:', joined)
        self.assertGreater(reduced.removed_instructions, 0)
        # Address passed through an operand may be a later indirect call.
        code2 = ['lda #<__basic_helper', 'rts', '__basic_helper:', 'rts', '__basic_unused:', 'rts']
        result = reduce_runtime_calls(code2, 2, len(code2))
        self.assertIn('__basic_helper:', '\n'.join(result.lines))
        self.assertNotIn('__basic_unused:', '\n'.join(result.lines))

    def test_indirect_jumps_and_inline_data_are_conservative(self):
        code = ['jsr __basic_alive', '__basic_alive:', 'jmp ($FB)', '__basic_unseen:', 'rts']
        reduced = reduce_runtime_calls(code, 1, len(code))
        self.assertNotIn('__basic_unseen:', '\n'.join(reduced.lines))
        code2 = ['jsr __basic_alive', '__basic_alive:', '.word __basic_unseen', '__basic_unseen:', 'rts']
        result = reduce_runtime_calls(code2, 1, len(code2))
        self.assertTrue(result.skipped)
        self.assertEqual(list(result.lines), code2)

    def test_mixed_sprite_reducers_compiles_and_keeps_table(self):
        path = ROOT / 'sample.bas'
        source = '\n'.join([
            '10 LOAD SPRITE "sprites.spr"', '20 SCREEN ON',
            '30 SPRITE SOFTWARE ON', '40 SPRITE DRAW 0,100,80',
            '45 SCREEN WAIT', '50 SPRITE ERASE 0',
            '60 SCREEN OFF', '70 END'])
        off, old = self.assemble(source,filename=str(path),sta_reducer=True)
        on, new = self.assemble(source,filename=str(path),sta_reducer=True,call_reducer=True)
        self.assertIn('__basic_sta_reducer_apply:', on.assembly)
        self.assertIn('__basic_soft_screen_on:', on.assembly)
        self.assertIn('__basic_soft_zero_pages:', on.assembly)
        self.assertIn('__basic_sprite_copy:', on.assembly)
        self.assertLess(len(new.prg), len(old.prg))

    def test_setting_wired_to_all_four_profiles_and_compile(self):
        text = (ROOT / 'd64_dism.py').read_text(encoding='utf-8')
        for token in ('CALL reducer', 'c64_call_reducer_checkbox',
                      '"CALLReducer"', '"call_reducer_key"',
                      'set_project_c64_call_reducer',
                      'call_reducer=self._project_c64_call_reducer_configuration()',
                      'set_c64_call_reducer(', 'project_c64_call_reducer',
                      'call_reducer_enabled'):
            self.assertIn(token, text)
        self.assertEqual(text.count('"call_reducer_key":'), 4)
        self.assertIn('STAReducer', text)
        self.assertEqual(text.count('"sta_reducer_key":'), 4)


if __name__ == '__main__':
    unittest.main()
