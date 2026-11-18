"""Stage 609: actual peephole opcode, safety, settings and COFF checks."""
from __future__ import annotations

import ast
import re
import unittest
from pathlib import Path

from windows_peephole import normalize_peephole_options, optimize_windows_assembly
from d64dbase import compile_dbase_to_assembly

BASE = Path(__file__).parent
SOURCE = (BASE / 'd64_dism.py').read_text('utf8')
PROGRAM = (BASE / 'runtime/dbase/src/System.Objects.prg').read_text('utf8')
ALL = {'register_width': True, 'processor_flags': True, 'stack_state': True}


class Stage609Tests(unittest.TestCase):
    def test_default_off_legacy_code_untouched(self):
        text = 'section .text\nentry:\n    mov eax, 0\n    ret\n'
        self.assertEqual(optimize_windows_assembly(text).assembly, text)
        self.assertEqual(normalize_peephole_options({'processor_flags': 'false'})['processor_flags'], False)

    def test_32bit_mov_zero_to_xor_only_when_flags_checked(self):
        src = 'section .text\nentry:\n mov eax, 0\n ret 12\n'
        self.assertIn('xor eax, eax', optimize_windows_assembly(src, options=ALL).assembly)
        self.assertIn('mov eax, 0', optimize_windows_assembly(src, options={'register_width': True}).assembly)
        self.assertIn('mov eax, 0', optimize_windows_assembly(src, options={'processor_flags': True}).assembly)

    def test_flags_liveness_and_branches(self):
        cases = ('jnz done', 'adc edx, 1', 'setnz al', 'call extern_foo', 'jmp done', 'done:')
        for case in cases:
            with self.subTest(case=case):
                asm = f'section .text\nentry:\n mov eax, 0\n {case}\n ret\n'
                self.assertIn('mov eax, 0', optimize_windows_assembly(asm, options=ALL).assembly)
        asm = 'section .text\nentry:\n mov eax, 0\n mov ecx, 4\n cmp ecx, 0\n jnz end\nend:\n ret\n'
        self.assertIn('xor eax, eax', optimize_windows_assembly(asm, options=ALL).assembly)

    def test_stack_rewrite_requires_return_proof(self):
        src = 'section .text\nentry:\n mov eax, 1\n ret 12\n'
        out = optimize_windows_assembly(src, options={'register_width': True,'stack_state': True})
        self.assertIn('push 1\n pop eax\n ret 12', out.assembly)
        self.assertEqual(out.byte_savings, 2)
        src2 = src.replace('ret 12', 'add eax, 5\n ret 12')
        self.assertIn('mov eax, 1', optimize_windows_assembly(src2, options={'register_width': True,'stack_state': True}).assembly)

    def test_64bit_always_pop_rax_and_zero_extend(self):
        src = 'section .text\nentry:\n mov eax, 1\n ret\n'
        out = optimize_windows_assembly(src, target='pe64', options=ALL).assembly
        self.assertIn('push 1\n pop rax\n',out)
        self.assertNotIn('pop eax',out)
        src2 = 'section .text\nentry:\n mov rax, 0\n ret\n'
        self.assertIn('xor eax, eax',optimize_windows_assembly(src2,target='pe64',options=ALL).assembly)
        self.assertEqual(optimize_windows_assembly(src2,target='pe32',options=ALL).assembly,src2)

    def test_no_data_or_declarations_modified(self):
        src = ('import imp, "kernel32.dll", "ExitProcess"\n'
               'section .data\na: dd 0\n mov eax, 0\n'
               'section .text\nentry:\n mov eax, 0\n ret\n')
        out = optimize_windows_assembly(src,options=ALL).assembly
        self.assertEqual(out.count('mov eax, 0'),1)
        self.assertIn('import imp,',out)

    def test_pascal_source_map_preserved_with_expansion(self):
        src = 'section .text\nentry:\n mov eax, 1\n ret\n'
        opts={'register_width':True,'processor_flags':True}
        out=optimize_windows_assembly(src,options=opts,source_map={3:88,4:89})
        self.assertIn('xor eax, eax\n inc eax',out.assembly)
        self.assertEqual(out.source_map[3],88)
        self.assertEqual(out.source_map[4],88)
        self.assertEqual(out.source_map[5],89)

    def test_real_dbase_library_output_changes(self):
        for target in ('pe32','pe64'):
            with self.subTest(target=target):
                original=compile_dbase_to_assembly(PROGRAM,target=target,source_kind='library')
                optimized=compile_dbase_to_assembly(PROGRAM,target=target,source_kind='library',peephole_options=ALL)
                self.assertIn('mov eax, 1',original.assembly)
                self.assertIn('push 1',optimized.assembly)
                self.assertIn('pop rax' if target=='pe64' else 'pop eax',optimized.assembly)
                self.assertIn('__dbase_vmt_tobject:',optimized.assembly)
                self.assertIn('import __dbase_',optimized.assembly)

    def test_dbase_and_pascal_compiler_hooks(self):
        dbase=(BASE/'d64dbase/compiler.py').read_text('utf8')
        pascal=(BASE/'c64pascal/compiler.py').read_text('utf8')
        self.assertIn('peephole_options=None',dbase)
        self.assertIn('_stage609_dbase_peephole(library_result, target, peephole_options)',dbase)
        self.assertIn('peephole_options=None',pascal)
        self.assertIn('def _stage609_pascal_peephole(',pascal)
        self.assertIn('compiler_kwargs["peephole_options"]',SOURCE)
        self.assertIn('peephole_options=self.project_windows_dbase_peephole',SOURCE)

    def test_dbase_overview_and_original_children(self):
        self.assertIn('"compiler.dbase": (',SOURCE)
        self.assertIn('("Optimierung", self.dbase_optimization_page)',SOURCE)
        for key in ('input','output'):
            self.assertIn(f'self.language_directory_items[("dbase", "{key}")]', SOURCE)
        self.assertIn('"compiler.dbase.optimization"',SOURCE)
        self.assertIn('"dBASE Optimierung", self.dbase_optimization_page',SOURCE)

    def test_three_options_and_abi_separation(self):
        for tag in ('32','64'):
            self.assertIn(f'__windows_pe{tag}_dbase_peephole_register_width__',SOURCE)
            self.assertIn(f'__windows_pe{tag}_dbase_peephole_processor_flags__',SOURCE)
            self.assertIn(f'__windows_pe{tag}_dbase_peephole_stack_state__',SOURCE)
        for text in ('"Peephole Optimierung"','"Registerbreite"','"Prozessorflags"','"Stackzustand"'):
            self.assertIn(text,SOURCE)
        self.assertIn('self.project_windows_dbase_peephole.get(document.build_target',SOURCE)

    def test_roundtrip_config_keys_and_compile_link_protection(self):
        for name in ('RegisterWidth','ProcessorFlags','StackState'):
            self.assertIn(f'"Peephole{name}"',SOURCE)
        self.assertIn('Peephole-Einstellungen geaendert',SOURCE)
        self.assertIn('document.peephole_compile_snapshot',SOURCE)
        self.assertIn('PEEPHOLE LINK',SOURCE)
        self.assertIn('if _at_compile is not None and _at_compile != _now:',SOURCE)
        normalized = re.sub(r'(?m)^(\s*)lazy (from|import)\b',r'\1\2',SOURCE)
        ast.parse(normalized)

if __name__=='__main__':
    unittest.main()
