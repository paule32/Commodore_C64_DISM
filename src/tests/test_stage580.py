"""Stage 580 – PE32 System.Strings imports through the real IDE preprocessor.

The installed ANTLR runtime may be older than the generated parser.  These
checks use the actual IDE preprocessing code, the Unit interface scanner, and
real PE32 code generation without requiring Windows, NASM, or a GUI.

Run: python -m unittest -v test_stage580
"""
from pathlib import Path
import unittest
from test_stage546 import IDE_PREPROCESS, D64, C

ROOT = Path(__file__).resolve().parent
SOURCE = (ROOT / 'runtime/pascal/system/System.Strings.pas').read_text('utf-8')

class Stage580Tests(unittest.TestCase):
    def test_gui_pe32_unit_is_import_only(self):
        processed = IDE_PREPROCESS(SOURCE, filename='System.Strings.pas', target='pe32')
        self.assertNotIn('result := jit_dynstring_from_cstr', processed.source)
        self.assertNotIn('result := _StrToInt', processed.source)
        self.assertNotIn('function _IntToStr', processed.source)
        self.assertNotIn('function _StrToInt', processed.source)
        self.assertEqual(processed.link_files, ())
        self.assertIn("external 'libd64_runtime.dll' name 'jit_pas_inttostr'", processed.source)
        self.assertIn("external 'libd64_runtime.dll' name 'jit_pas_strtoint'", processed.source)
        transformed, name, _iu, _mu, interface, implementation = C._unit_program_source(
            processed.source, filename='System.Strings.pas'
        )
        self.assertEqual(name, 'System.Strings')
        self.assertNotIn('function IntToStr', implementation)
        self.assertNotIn('function StrToInt', implementation)
        _parser_src, routines = C._pui_routine_information(name, interface)
        self.assertEqual({r['name'] for r in routines}, {'IntToStr', 'StrToInt'})
        self.assertTrue(all(r['is_external'] for r in routines))
        imports = C._pui_interface_external_declarations(name, routines)
        self.assertEqual({x.import_name for x in imports},
                         {'jit_pas_inttostr','jit_pas_strtoint'})
        self.assertTrue(all(x.library_reference == 'libd64_runtime.dll' for x in imports))

    def test_real_source_unit_imports_produce_no_wrappers(self):
        processed = IDE_PREPROCESS(SOURCE, filename='System.Strings.pas', target='pe32')
        _, name, _, _, interface, implementation = C._unit_program_source(
            processed.source, filename='System.Strings.pas')
        self.assertFalse(implementation.strip().replace('end;', '').strip())
        _, routines = C._pui_routine_information(name, interface)
        imports = C._pui_interface_external_declarations(name, routines)
        pos = C.SourcePosition(1, 1)
        statements = (
            C.CallStatement(pos, C.DesignatorExpression(pos, 'IntToStr', ()),
                            (C.LiteralExpression(pos, 42),)),
            C.CallStatement(pos, C.DesignatorExpression(pos, 'StrToInt', ()),
                            (C.LiteralExpression(pos, '42'),)),
        )
        program = C.PascalProgram('UseSystemStrings', (), (),
            C.CompoundStatement(pos, statements), external_routines=imports)
        asm = C._PE32CodeGenerator(program, stack_protector=True).generate().assembly
        for unwanted in ('__pas_global_inttostr:', '__pas_global_strtoint:',
                         'call _jit_dynstring_from_cstr', 'call __IntToStr',
                         'call __StrToInt'):
            self.assertNotIn(unwanted, asm)
        self.assertIn('import _IntToStr, "libd64_runtime.dll", "jit_pas_inttostr"', asm)
        self.assertIn('import _StrToInt, "libd64_runtime.dll", "jit_pas_strtoint"', asm)
        self.assertIn('call _IntToStr', asm)
        self.assertIn('call _StrToInt', asm)

    def test_ide_pe64_and_other_targets_preserve_legacy(self):
        for target in ('pe64', 'c64'):
            with self.subTest(target=target):
                processed = IDE_PREPROCESS(SOURCE, filename='System.Strings.pas', target=target)
                self.assertIn('result := jit_dynstring_from_cstr', processed.source)
                self.assertIn('result := _StrToInt', processed.source)
                self.assertNotIn("external 'libd64_runtime.dll' name 'jit_pas_inttostr'", processed.source)
                self.assertEqual([Path(x).name for x in processed.link_files],
                                 ['inttostr.o','strtoint.o'])

    def test_target_flags_cannot_be_spoofed_by_application_macros(self):
        result32 = IDE_PREPROCESS(SOURCE, filename='System.Strings.pas', target='pe32',
            predefined_macros={'__D64_TARGET_PE64__':'1'})
        self.assertIn('jit_pas_inttostr', result32.source)
        self.assertNotIn('result := jit_dynstring_from_cstr', result32.source)
        result64 = IDE_PREPROCESS(SOURCE, filename='System.Strings.pas', target='pe64',
            predefined_macros={'__D64_TARGET_PE32__':'1'})
        self.assertNotIn('jit_pas_inttostr', result64.source)
        self.assertIn('result := jit_dynstring_from_cstr', result64.source)

    def test_parallel_preprocessing_also_selects_correct_branch(self):
        macros = C._pascal_target_macros({}, 'pe32')
        pre = C.preprocess_pascal_source(SOURCE,
            filename='System.Strings.pas', predefined_macros=macros)
        self.assertIn('jit_pas_inttostr', pre.source)
        self.assertNotIn('result := jit_dynstring_from_cstr', pre.source)
        self.assertIn('predefined_macros=_pascal_target_macros(macros, target)', D64)

    def test_all_ide_paths_supply_compiler_target(self):
        self.assertIn('target=document.build_target,\n                )\n                if "predefined_macros"', D64)
        self.assertIn('target=target,\n        )\n        kwargs["predefined_macros"]', D64)
        self.assertIn('def _pascal_ide_target_macros(', D64)

    def test_stale_unit_pui_invalidates_previously_built_coff(self):
        # When a prior Unit build chose the legacy branch, both its PUI
        # contract and compiled object may exist even after source update.
        # A metadata mismatch must force a source compilation instead of
        # silently re-linking that cached object into the consumer EXE.
        import inspect
        resolver_source = inspect.getsource(C._PascalUnitResolver.resolve)
        self.assertIn('source_contract_changed = True', resolver_source)
        self.assertIn('not source_contract_changed', resolver_source)

    def test_obsolete_test_raise_asm_not_packaged_as_current_output(self):
        self.assertFalse((ROOT/'runtime/pascal/test/test_raise.generated.pe32.asm').exists())

if __name__ == '__main__':
    unittest.main()
