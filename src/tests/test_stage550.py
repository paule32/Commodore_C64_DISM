"""Stage 550: compact import includes and NASM %line source-location mapping.

Run: python -m unittest -v test_stage550
"""
from __future__ import annotations

import ast
import configparser
from pathlib import Path
import re
import sys
import tempfile
import types
import unittest

from pascal_import_manager import externalize_declarations, process_assembly
from windows_asm_line_directives import strip_line_directives, remap_asm_locations

ROOT = Path(__file__).resolve().parent


class Stage550Tests(unittest.TestCase):
    SAMPLE = (
        '; Pascal\n'
        'bits 32\n'
        'global _start\n'
        'entry _start\n'
        'extern ExitProcess\n'
        'import _Used@4, "user32.dll", "Used"\n'
        'import _Unused@4, "user32.dll", "Unused"\n'
        '\n'
        '_start:\n'
        '    call _Used@4\n'
        '    call ExitProcess\n'
    )

    def test_compact_imports_prune_comment_and_restore_original_line(self):
        code, _ = process_assembly(self.SAMPLE, 'pe32', cache_enabled=False)
        with tempfile.TemporaryDirectory() as temp:
            compact, path, includes = externalize_declarations(
                code, Path(temp) / 'test.asm', use_preprocessor_lines=True)
            self.assertEqual(path.name, 'test.asm.imports.inc')
            self.assertIn('import _Used@4', includes)
            self.assertNotIn('import _Unused@4', includes)
            self.assertEqual(compact.count('%include'), 1)
            self.assertNotIn('Stage 541', compact)
            self.assertEqual(compact.count('%line '), 1)
            marker = next(row for row in compact.splitlines() if row.startswith('%line'))
            # The first real line following the original import block is _start.
            self.assertEqual(marker, '%line 9')
            self.assertIn('_start:', compact)
            self.assertLess(len(compact.splitlines()), len(code.splitlines()))
            stripped, positions = strip_line_directives(compact, str(Path(temp) / 'test.asm'))
            self.assertNotIn('%line', stripped)
            physical = compact.splitlines().index('_start:') + 1
            self.assertEqual(positions[physical][1], 9)

    def test_disabled_switch_keeps_old_placeholder_layout(self):
        code, _ = process_assembly(self.SAMPLE, 'pe32', cache_enabled=False)
        legacy, _, _ = externalize_declarations(code, Path('test.asm'))
        self.assertEqual(len(legacy.splitlines()), len(code.splitlines()))
        self.assertNotIn('%line ', legacy)
        self.assertIn('Stage 541:', legacy)

    def test_no_declarations_is_noop(self):
        code = '; hello\n_start:\nret\n'
        result, path, data = externalize_declarations(
            code, 'any.asm', use_preprocessor_lines=True)
        self.assertEqual((result, path, data), (code, None, None))

    def test_do_not_drop_real_comments_or_intervening_code(self):
        asm = ('extern Alpha\n; Keep this explanatory comment\n'
               'call Alpha\nimport Beta, "B.dll", "B"\nret\n')
        compact, _, inc = externalize_declarations(
            asm, 'test.asm', use_preprocessor_lines=True)
        self.assertIn('Keep this explanatory comment', compact)
        self.assertIn('call Alpha', compact)
        self.assertIn('import Beta', inc)
        self.assertEqual(compact.count('%line'), 2)

    def test_import_lines_before_and_after_pruned_markers(self):
        asm = ('bits 32\n; Stage 541: unbenutzte/duplizierte Import-Deklaration\n'
               '\nextern One\n\n; Stage 541: unbenutzte/duplizierte Import-Deklaration\n'
               'import Two, "B.dll", "Two"\n\n_start:\nret\n')
        compact, _, inc = externalize_declarations(
            asm, 'test.asm', use_preprocessor_lines=True)
        self.assertEqual(compact.count('%include'), 1)
        self.assertEqual(compact.count('%line'), 1)
        self.assertIn('%line 9', compact)
        self.assertIn('extern One', inc)
        self.assertNotIn('Stage 541', compact)

    def test_line_reset_and_increment(self):
        source = 'bits 32\n%line 27\nmov eax, 1\n%line 60+2 "origin.asm"\nret\n'
        clean, mapping = strip_line_directives(source, 'generated.asm')
        self.assertNotIn('%line', clean)
        self.assertEqual(len(clean.splitlines()), len(source.splitlines()))
        self.assertEqual(mapping[3], ('generated.asm', 27))
        self.assertEqual(mapping[5], ('origin.asm', 60))

    def test_invalid_directive_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Ungültige %line'):
            strip_line_directives('bits 32\n%line banana\nret\n', 'a.asm')
        with self.assertRaisesRegex(ValueError, 'Ungültige %line'):
            strip_line_directives('%line 0\nret\n', 'a.asm')

    def test_main_file_location_mapping_not_included_file(self):
        clean, mapping = strip_line_directives('%include "a.inc"\n%line 40\nret\n', 'main.asm')
        locs = [('a.inc', 1), ('a.inc', 2), ('main.asm', 1),
                ('main.asm', 2), ('main.asm', 3)]
        remapped = remap_asm_locations(locs, 'main.asm', mapping)
        self.assertEqual(remapped[:2], tuple(locs[:2]))
        self.assertEqual(remapped[-1], ('main.asm', 40))

    def test_internal_assembler_entrypoint_applies_line_map(self):
        source = (ROOT / 'd64_dism.py').read_text(encoding='utf-8')
        parseable = re.sub(r'(?m)^(\s*)lazy (from|import) ', r'\1\2 ', source)
        tree = ast.parse(parseable)
        func = next(n for n in tree.body if isinstance(n, ast.FunctionDef)
                    and n.name == '_preprocess_windows_assembly')
        module = ast.fix_missing_locations(ast.Module(body=[func], type_ignores=[]))
        fake_att = types.ModuleType('windows_asm_att')
        fake_att.contains_att_syntax = lambda text: False
        fake_att.att_to_intel = lambda text: text
        old_att = sys.modules.get('windows_asm_att')
        sys.modules['windows_asm_att'] = fake_att
        try:
            class FakeResult:
                def __init__(self, *, source, locations):
                    self.source, self.locations = source, locations
            class FakeError(Exception):
                pass
            def expand(src, *, filename, include_dirs):
                rows = src.splitlines()
                # Simulate one imported include and the original source map
                return FakeResult(source='extern Func\n' + src,
                                  locations=[('file.inc', 1)] +
                                  [(filename, n) for n in range(1, len(rows)+1)])
            env = {'preprocess_windows_asm': expand,
                   'WindowsAsmMacroError': FakeError}
            exec(compile(module, '<stage550-preprocessor>', 'exec'), env)
            result = env['_preprocess_windows_assembly'](
                '%include "file.inc"\n%line 27\n_start:\nret\n',
                'main.asm', FakeError)
            self.assertEqual(result.locations[0], ('file.inc', 1))
            self.assertEqual(result.locations[3], ('main.asm', 27))
            self.assertEqual(result.locations[4], ('main.asm', 28))
            self.assertNotIn('%line', result.source)
        finally:
            if old_att is None:
                del sys.modules['windows_asm_att']
            else:
                sys.modules['windows_asm_att'] = old_att

    def test_gui_persisted_for_each_architecture(self):
        source = (ROOT / 'd64_dism.py').read_text(encoding='utf-8')
        parseable = re.sub(r'(?m)^(\s*)lazy (from|import) ', r'\1\2 ', source)
        tree = ast.parse(parseable)
        keys = {'pe32': 'i32', 'pe64': 'i64'}
        def norm(options=None):
            options = options or {}
            result = {}
            for key, default in [('cache_enabled',True),('prune_unused',True),
                                 ('externalize',False), ('use_preprocessor_lines',False)]:
                val = options.get(key, default)
                result[key] = val if isinstance(val, bool) else str(val).lower() == 'true'
            return result
        env = {'PROJECT_WINDOWS_PASCAL_IMPORT_KEYS': keys,
               'stage541_import_options': norm}
        def run(name, extra):
            f = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name==name)
            loops = [n for n in f.body if isinstance(n, ast.For)
                     and 'Settings.Windows.{_suffix}.Compiler.Pascal.Imports'
                     in ast.get_source_segment(parseable,n)]
            self.assertEqual(len(loops),1)
            exec(compile(ast.fix_missing_locations(ast.Module(body=loops,
                type_ignores=[])), '<stage550-ini>', 'exec'), dict(env, **extra))
        parser = configparser.ConfigParser(interpolation=None)
        parser.optionxform = str
        run('format_project_ini', {'parser':parser, 'entries': {
            'i32': [{'externalize':True, 'use_preprocessor_lines':True}],
            'i64': [{'externalize':True, 'use_preprocessor_lines':False}]}})
        self.assertEqual(parser.get('Settings.Windows.32Bit.Compiler.Pascal.Imports',
                                    'UsePreprocessorLines'), 'true')
        restored = {}
        run('parse_project_ini', {'parser':parser,'entries':restored})
        self.assertTrue(restored['i32'][0]['use_preprocessor_lines'])
        self.assertFalse(restored['i64'][0]['use_preprocessor_lines'])

    def test_gui_and_parallel_worker_wiring(self):
        source = (ROOT / 'd64_dism.py').read_text(encoding='utf-8')
        worker = (ROOT / 'pascal_parallel_build.py').read_text(encoding='utf-8')
        self.assertIn('Use Pre-processor Lines', source)
        self.assertIn('preprocessor_lines_checkbox', source)
        self.assertIn('import_use_preprocessor_lines', source)
        self.assertIn('use_preprocessor_lines=_import_options', source)
        self.assertIn('use_preprocessor_lines=bool(job.get(', worker)


if __name__ == '__main__':
    unittest.main()
