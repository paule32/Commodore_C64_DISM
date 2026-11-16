"""Stage 590: ESP-slots tooltip and PE DLL MSZIP linker integration."""
import ast
import re
import unittest
from pathlib import Path

from asm_stack_frame_tooltips import esp_stack_slot_tooltip
from test_stage586 import extract_editor_stack_methods, fake_document

ROOT = Path(__file__).resolve().parent
GROUP = [
    '    mov dword ptr [esp+0], ebx',
    '    mov dword ptr [esp+4], esi',
    '    mov dword ptr [esp+8], edi',
    '    mov dword ptr [esp+12], ebp',
    '    mov dword ptr [esp+16], esp',
]


class StackSlotTests(unittest.TestCase):
    def test_all_five_movs_are_group_help(self):
        lines = ['sub esp, 20', '; register block'] + GROUP
        for ix in range(2, 7):
            tip = esp_stack_slot_tooltip(lines, ix)
            self.assertIsNotNone(tip)
            self.assertIn('fünf 32-Bit', tip.title)
            self.assertIn('20 Byte', tip.description)
            self.assertIn('MOV', tip.instructions)
            self.assertIn('nicht automatisch die fünf Pascal-Parameter', tip.description)
            self.assertIn('nicht eine Kopie des Stacks', tip.description)

    def test_individual_movs_without_prolog(self):
        for ix, line in enumerate(GROUP):
            tip = esp_stack_slot_tooltip([line], 0)
            self.assertIsNotNone(tip)
            self.assertIn(f'ESP+{ix * 4}', tip.instructions)
            self.assertIn('ESP bleibt durch MOV unverändert', tip.description)
        self.assertIn('aktuelle numerische', esp_stack_slot_tooltip([GROUP[4]],0).description)

    def test_case_comments_no_false_match(self):
        tip = esp_stack_slot_tooltip(['  MOV DWORD PTR [ESP+0X10], ESP ; comment'], 0)
        self.assertIsNotNone(tip)
        self.assertIsNone(esp_stack_slot_tooltip(['; ' + GROUP[0]], 0))
        self.assertIsNone(esp_stack_slot_tooltip(['something ' + GROUP[0]], 0))
        self.assertIsNone(esp_stack_slot_tooltip(['mov dword ptr [esp+0], eax+2'], 0))
        self.assertIsNone(esp_stack_slot_tooltip([GROUP[0]], 0, 'pe64'))
        self.assertIsNone(esp_stack_slot_tooltip([GROUP[0]], 0, 'c64'))

    def test_interrupted_group_becomes_individual(self):
        data = GROUP[:2] + ['nop'] + GROUP[2:]
        for ix in (0, 1, 3, 4, 5):
            tip = esp_stack_slot_tooltip(data, ix)
            self.assertIsNotNone(tip)
            self.assertNotIn('fünf 32-Bit', tip.title)

    def test_editor_integration_individual_and_group(self):
        obj = extract_editor_stack_methods()()
        obj._assembler_target = 'pe32'
        blocks = fake_document(['sub esp, 20', '; save regs'] + GROUP)
        for i in range(2, 7):
            tip = obj._stack_frame_tooltip_for_block(blocks[i])
            self.assertIsNotNone(tip)
            self.assertIn('fünf 32-Bit', tip.title)
        obj._assembler_target = 'c64'
        self.assertIsNone(obj._stack_frame_tooltip_for_block(blocks[2]))


class PackingLinkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        text = (ROOT / 'd64_dism.py').read_text('utf-8')
        cls.tree = ast.parse(re.sub(r'(?m)^(\s*)lazy (from|import) ', r'\1\2 ', text))

    def function(self, name):
        funcs = [n for n in self.tree.body if isinstance(n, ast.FunctionDef) and n.name == name]
        self.assertTrue(funcs, name)
        return funcs[-1]

    def test_link_functions_propagate_pack_flag(self):
        for fn in ('link_coff32_objects', 'link_coff32_inputs',
                   'link_coff64_objects', 'link_coff64_inputs'):
            node = self.function(fn)
            argnames = [a.arg for a in node.args.args + node.args.kwonlyargs]
            self.assertIn('pack_dll', argnames, fn)
        for name in ('link_coff32_objects', 'link_coff64_objects'):
            node = self.function(name)
            self.assertTrue(any(isinstance(n, ast.Name) and n.id == 'pack_dll'
                                for n in ast.walk(node)), name)

    def test_dll_packing_only_with_library_and_checkbox(self):
        node = self.function('_stage590_should_pack_dll')
        ns = {'_pe_packing_enabled': lambda target: True}
        exec(compile(ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[])),
                     '<stage590>', 'exec'), ns)
        fn = ns['_stage590_should_pack_dll']
        self.assertFalse(fn('pe32', False))  # EXE remains on separate path
        self.assertFalse(fn('pe32', True, False))  # explicit project OFF beats global ON
        self.assertTrue(fn('pe32', True, True))
        self.assertTrue(fn('pe64', True, True))
        self.assertTrue(fn('pe64', True, None))

    def test_library_path_reaches_linker_with_dll_true(self):
        text = (ROOT / 'd64_dism.py').read_text('utf-8')
        self.assertIn('is_library = source_kind == "library"', text)
        self.assertIn('dll=is_library', text)
        self.assertIn('pack_this_dll = _stage590_should_pack_dll', text)
        self.assertIn('if pack_this_dll:', text)

    def test_real_pe32_pe64_container_layout_with_mocked_imports(self):
        # Windows Cabinet/MSZIP is unavailable here; this test validates the
        # PE section, import/export-directory and relocation layout only.
        import zlib
        from unittest.mock import patch
        from d64dbase import pe_dll_payload as mod
        samples = (
            ROOT / 'runtime/win32/libd64_runtime.dll',
            ROOT / 'examples/dbase/build/bin/pe64/d64_dbase_console.dll',
        )
        for path in samples:
            before = path.read_bytes()
            base = mod.parse_pe(before)
            fake_imports = {
                spec: 0x2000 + i * 8
                for i, spec in enumerate(mod.DLL_LOADER_IMPORTS.values())
            }
            with self.subTest(path=path), patch.object(mod, 'import_iats', return_value=fake_imports):
                after = mod.pack_pe_dll(before, compressor=lambda b: zlib.compress(b, 9))
                packed = mod.parse_pe(after)
                self.assertEqual(packed['machine'], base['machine'])
                self.assertNotEqual(packed['entry'], base['entry'])
                self.assertEqual(before[base['dd']:base['dd']+8], after[packed['dd']:packed['dd']+8])
                self.assertIn(b'.loader', [s['name'] for s in packed['secs']])
                self.assertIn(b'.ztext', [s['name'] for s in packed['secs']])
                self.assertEqual(len(after), len(mod.pack_pe_dll(after, compressor=lambda b: zlib.compress(b,9))))

    def test_dll_bootstrap_and_export_pe_structure(self):
        from d64dbase.pe_dll_payload import (DLL_LOADER_IMPORTS, D64Z, _x86_stub, _x64_stub)
        self.assertGreaterEqual(len(DLL_LOADER_IMPORTS), 5)
        self.assertEqual(D64Z.size, 32)
        for target, factory in [('pe32', _x86_stub), ('pe64', _x64_stub)]:
            imp = {name: 0x4000 + i*8 for i, (_symbol, (_dll, name))
                   in enumerate(DLL_LOADER_IMPORTS.items())}
            stub = factory(0x5000, 0x1000, 4096, 0x7000, 100, 0x7200,
                           0, 0x1010, 0x400000 if target=='pe32' else 0x140000000, imp)
            self.assertTrue(stub)
            self.assertNotIn(b'CES:', stub)


if __name__ == '__main__':
    unittest.main()
