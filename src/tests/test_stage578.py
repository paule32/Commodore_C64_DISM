"""Stage 578: native PE32 Pascal IntToStr/StrToInt runtime-ABI regression.

These tests exercise preprocessing, interface metadata extraction and the real
PE32 assembler emitter without a GUI or a native Windows toolchain. Run them
with: python -m unittest -v test_stage578
Native DLL linking and Windows execution must be verified separately.
"""
from __future__ import annotations

import unittest
from pathlib import Path

from test_stage532 import _compiler


ROOT = Path(__file__).resolve().parent
C = _compiler()
UNIT = ROOT / 'runtime' / 'pascal' / 'system' / 'System.Strings.pas'


class Stage578Tests(unittest.TestCase):
    def test_pe32_unit_has_direct_dll_imports_and_no_link_objects(self):
        source = UNIT.read_text(encoding='utf-8')
        parser = C.PascalPreprocessor(C._pascal_target_macros({}, 'pe32'))
        processed = parser.process(source, filename=str(UNIT)).source
        self.assertFalse(parser.link_files)
        self.assertIn("external 'libd64_runtime.dll' name 'jit_pas_inttostr'", processed)
        self.assertIn("external 'libd64_runtime.dll' name 'jit_pas_strtoint'", processed)
        self.assertNotIn('result := jit_dynstring_from_cstr', processed)
        self.assertNotIn('result := _StrToInt', processed)

        # The existing PUI interface scanner must preserve import targets.
        _transformed, unit, _uses_i, _uses_m, public, _impl = C._unit_program_source(
            processed, filename=str(UNIT)
        )
        self.assertEqual(unit, 'System.Strings')
        _blanked, routines = C._pui_routine_information(unit, public)
        self.assertEqual({r['name'] for r in routines}, {'IntToStr', 'StrToInt'})
        self.assertTrue(all(r['is_external'] for r in routines))
        self.assertEqual({r['import_name'] for r in routines},
                         {'jit_pas_inttostr', 'jit_pas_strtoint'})
        self.assertTrue(all(r['library_reference'] == 'libd64_runtime.dll'
                            for r in routines))

    def test_ide_preprocessor_uses_existing_pe32_target_flag(self):
        from test_stage546 import IDE_PREPROCESS
        source = UNIT.read_text(encoding='utf-8')
        generated = IDE_PREPROCESS(
            source, filename=str(UNIT),
            predefined_macros={'__D64_TARGET_PE32__': '1'},
        )
        self.assertIn("external 'libd64_runtime.dll' name 'jit_pas_inttostr'", generated.source)
        self.assertNotIn('result := jit_dynstring_from_cstr', generated.source)
        self.assertFalse(generated.link_files)

    def test_pe64_keeps_previous_unit_behavior(self):
        source = UNIT.read_text(encoding='utf-8')
        parser = C.PascalPreprocessor(C._pascal_target_macros({}, 'pe64'))
        processed = parser.process(source, filename=str(UNIT)).source
        self.assertIn('result := jit_dynstring_from_cstr', processed)
        self.assertIn('result := _StrToInt', processed)
        self.assertNotIn("external 'libd64_runtime.dll' name 'jit_pas_inttostr'", processed)
        self.assertEqual([Path(x).name for x in parser.link_files],
                         ['inttostr.o', 'strtoint.o'])

    def test_compiler_backend_target_flags_are_authoritative(self):
        self.assertIn('__D64_TARGET_PE32__', C._pascal_target_macros({}, 'pe32'))
        self.assertIn('__D64_TARGET_PE64__', C._pascal_target_macros({}, 'pe64'))
        target = C._pascal_target_macros({'__D64_TARGET_PE32__': '1'}, 'pe64')
        self.assertNotIn('__D64_TARGET_PE32__', target)
        self.assertIn('__D64_TARGET_PE64__', target)
        self.assertFalse(any(x.startswith('__D64_TARGET_PE')
                             for x in C._pascal_target_macros({}, 'c64')))

    def test_pe32_emitter_only_imports_and_calls_external_functions(self):
        pos = C.SourcePosition(1, 1)
        int_param = C.ParameterDeclaration(('AValue',), 'integer', 'value', pos)
        str_param = C.ParameterDeclaration(('S',), 'string', 'value', pos)
        externals = (
            C.ExternalRoutineDeclaration('System.Strings', 'function', 'IntToStr',
                (int_param,), 'string', '_IntToStr', 'cdecl',
                'libd64_runtime.dll', 'jit_pas_inttostr'),
            C.ExternalRoutineDeclaration('System.Strings', 'function', 'StrToInt',
                (str_param,), 'integer', '_StrToInt', 'cdecl',
                'libd64_runtime.dll', 'jit_pas_strtoint'),
        )
        statements = (
            C.CallStatement(pos, C.DesignatorExpression(pos, 'IntToStr', ()),
                            (C.LiteralExpression(pos, 12345),)),
            C.CallStatement(pos, C.DesignatorExpression(pos, 'StrToInt', ()),
                            (C.LiteralExpression(pos, '12345'),)),
        )
        program = C.PascalProgram(
            'Probe', (), (), C.CompoundStatement(pos, statements),
            external_routines=externals,
        )
        asm = C._PE32CodeGenerator(program, stack_protector=True).generate().assembly
        self.assertIn('import _IntToStr, "libd64_runtime.dll", "jit_pas_inttostr"', asm)
        self.assertIn('import _StrToInt, "libd64_runtime.dll", "jit_pas_strtoint"', asm)
        self.assertIn('call _IntToStr', asm)
        self.assertIn('call _StrToInt', asm)
        self.assertNotIn('__pas_global_inttostr:', asm)
        self.assertNotIn('__pas_global_strtoint:', asm)
        self.assertNotIn('call _jit_dynstring_from_cstr', asm)

    def test_runtime_exports_and_build_rules(self):
        for directory, source in (
            ('runtime', 'pascal'), ('runtime/compiler', '../pascal')
        ):
            script = (ROOT / directory / 'build.win32.sh').read_text('utf-8')
            self.assertIn(f'{source}/inttostr.asm', script)
            self.assertIn(f'{source}/strtoint.asm', script)
            self.assertIn('pas_inttostr.o', script)
            self.assertIn('pas_strtoint.o', script)
            defs = (ROOT / directory / 'win32/libd64_runtime.def').read_text('utf-8')
            self.assertRegex(defs, r'(?m)^\s+jit_pas_inttostr(?:\s|$)')
            self.assertRegex(defs, r'(?m)^\s+jit_pas_strtoint(?:\s|$)')
        from_int = (ROOT/'runtime/pascal/inttostr.asm').read_text('utf-8')
        from_str = (ROOT/'runtime/pascal/strtoint.asm').read_text('utf-8')
        self.assertIn('_jit_pas_inttostr:', from_int)
        self.assertIn('_jit_pas_strtoint:', from_str)
        self.assertIn('call DYNS_FROM_CSTR', from_int)


if __name__ == '__main__':
    unittest.main()
