"""Stage 541 import manager: manifest, cache, ABI isolation and project wiring.

Run: python -m unittest -v test_stage541
No native Windows/Qt/ANTLR runtime is required for these structural tests.
"""
import ast
import configparser
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace
import json
import re
import tempfile
import unittest

from pascal_import_manager import (
    analyze_assembly, cache_root, clear_cache, externalize_declarations,
    link_manifest_from_parsed_objects, process_assembly, write_manifest,
)

ROOT = Path(__file__).resolve().parent


class Stage541Tests(unittest.TestCase):
    EXAMPLE = (
        'bits 32\nextern ExitProcess\n'
        'import _IsWindow@4, "user32.dll", "IsWindow"\n'
        'import _Used@4, "user32.dll", "Used"\n'
        'import _Unused, "unused.dll", "unused"\n'
        '_start:\n    push 1\n    call _Used@4\n    call ExitProcess\n'
    )

    def test_pruning_and_line_number_stability(self):
        code, manifest = process_assembly(self.EXAMPLE, 'pe32', cache_enabled=False)
        self.assertEqual(manifest['declared'], 4)
        self.assertEqual(manifest['used'], 2)
        self.assertEqual(manifest['unused'], 2)
        self.assertEqual(len(code.splitlines()), len(self.EXAMPLE.splitlines()))
        self.assertIn('import _Used@4, "user32.dll", "Used"', code)
        self.assertIn('extern ExitProcess', code)
        self.assertNotIn('import _Unused,', code)
        self.assertIn('_start:', code)

    def test_mixed_object_dependencies_leave_declarations_intact(self):
        code, manifest = process_assembly(
            self.EXAMPLE, 'pe32', conservative=True, cache_enabled=False)
        self.assertEqual(code, self.EXAMPLE)
        self.assertEqual(manifest['unused'], 0)

    def test_cache_key_and_separate_cpu_targets(self):
        with tempfile.TemporaryDirectory() as directory:
            c1, a1 = process_assembly(self.EXAMPLE, 'pe32',
                                      explicit_cache_root=directory,
                                      source_text='foo')
            c2, a2 = process_assembly(self.EXAMPLE, 'pe32',
                                      explicit_cache_root=directory,
                                      source_text='foo')
            c3, a3 = process_assembly(self.EXAMPLE, 'pe64',
                                      explicit_cache_root=directory,
                                      source_text='foo')
            _, a4 = process_assembly(self.EXAMPLE + '\n; changed', 'pe32',
                                      explicit_cache_root=directory,
                                      source_text='foo')
            _, a5 = process_assembly(self.EXAMPLE, 'pe32',
                                      explicit_cache_root=directory,
                                      source_text='bar')
            self.assertFalse(a1['cache_hit'])
            self.assertTrue(a2['cache_hit'])
            self.assertEqual(c1, c2)
            self.assertNotEqual(a1['cache_key'], a3['cache_key'])
            self.assertNotEqual(a1['cache_key'], a4['cache_key'])
            self.assertNotEqual(a1['cache_key'], a5['cache_key'])
            self.assertEqual(clear_cache(directory, 'pe32'), 3)
            self.assertTrue(Path(a3['cache_file']).is_file())
            self.assertFalse(Path(a1['cache_file']).exists())

    def test_parallel_cache_writes_are_always_json(self):
        with tempfile.TemporaryDirectory() as directory:
            def job(_):
                return process_assembly(self.EXAMPLE, 'pe32',
                    explicit_cache_root=directory, source_text='same')[1]
            with ThreadPoolExecutor(max_workers=8) as pool:
                results = list(pool.map(job, range(30)))
            self.assertEqual(len({r['cache_key'] for r in results}), 1)
            self.assertEqual(results[0]['used'], 2)
            path = Path(results[0]['cache_file'])
            data = json.loads(path.read_text(encoding='utf-8'))
            self.assertEqual(data['manifest']['unused'], 2)

    def test_dll_change_invalidates_cache(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            dll = root / 'libd64_runtime.dll'
            dll.write_bytes(b'old')
            asm = 'import _jit_free, "libd64_runtime.dll", "_jit_free"\ncall _jit_free\n'
            _, a = process_assembly(asm, 'pe32', output_directory=root,
                                    source_text='same')
            dll.write_bytes(b'new')
            _, b = process_assembly(asm, 'pe32', output_directory=root,
                                    source_text='same')
            self.assertNotEqual(a['cache_key'], b['cache_key'])

    def test_externalize_asm_imports(self):
        with tempfile.TemporaryDirectory() as directory:
            asm_path = Path(directory) / 'foo.generated.pe32.asm'
            asm, name, contents = externalize_declarations(self.EXAMPLE, asm_path)
            self.assertEqual(len(asm.splitlines()), len(self.EXAMPLE.splitlines()))
            self.assertIn('%include "foo.generated.pe32.asm.imports.inc"', asm)
            self.assertIn('import _Used@4,', contents)
            self.assertTrue(str(name).endswith('.imports.inc'))
            self.assertEqual(len(contents.splitlines()), 4)

    def test_link_manifest_only_selected_imports(self):
        objects = [SimpleNamespace(imports={'_used@4': ('user32.dll','Used'),
                                            '_dead': ('unused.dll','dead')}),
                   SimpleNamespace(imports={'_other': ('kernel32.dll','Other')})]
        linked = link_manifest_from_parsed_objects(objects, 'pe32',
            {'_used@4': ('user32.dll','Used'), '_other': ('kernel32.dll','Other')})
        self.assertEqual(linked['used'], 2)
        self.assertEqual(linked['unused_declared'], ['_dead'])
        with tempfile.TemporaryDirectory() as directory:
            dest = write_manifest(Path(directory) / 'out.exe.imports.json', linked)
            self.assertEqual(json.loads(dest.read_text())['used'], 2)
        with self.assertRaisesRegex(ValueError, 'Widersprüchliche'):
            link_manifest_from_parsed_objects(
                [SimpleNamespace(imports={'f': ('a.dll','x')}),
                 SimpleNamespace(imports={'f': ('b.dll','x')})], 'pe32', {})

    def test_conflicting_import_declarations(self):
        with self.assertRaisesRegex(ValueError, 'Widersprüchliche'):
            analyze_assembly('import f, "a.dll", "x"\nimport f, "b.dll", "x"\n', 'pe32')

    def test_gui_wiring(self):
        gui = (ROOT / 'd64_dism.py').read_text(encoding='utf-8')
        worker = (ROOT / 'pascal_parallel_build.py').read_text(encoding='utf-8')
        compiler = (ROOT / 'c64pascal/compiler.py').read_text(encoding='utf-8')
        for required in (
            '"compiler.pascal.imports"', 'Import-Cache verwenden',
            'Nicht verwendete Imports entfernen', 'Cache für dieses Ziel löschen',
            'Import-Deklarationen in .inc auslagern',
            'Settings.Windows.{_suffix}.Compiler.Pascal.Imports',
            '"import_cache_directory"', '"import_cache_enabled"',
            '"import_prune_unused"', '"import_externalize"',
            'link_manifest_from_parsed_objects',
            'program.import_manifest',
        ):
            self.assertIn(required, gui)
        for required in ('import_cache_directory', 'import_prune_unused',
                         'import_cache_enabled', 'import_externalize',
                         'generated.import_manifest'):
            self.assertIn(required, worker)
        self.assertIn('def _stage541_process_pascal_imports(', compiler)
        self.assertIn('import_manifest: Optional[dict]', compiler)

    def test_ini_separate_target_roundtrip(self):
        source = (ROOT / 'd64_dism.py').read_text(encoding='utf-8')
        parseable = re.sub(r'(?m)^(\s*)lazy (from|import) ', r'\1\2 ', source)
        ast.parse(parseable)
        default = {"cache_enabled": True, "prune_unused": True, "externalize": False}
        keys = {"pe32": "i32", "pe64": "i64"}
        def norm(d=None):
            d = d or {}
            def cast(v, default):
                return str(v).strip().lower() in {'1','true','yes'}
            return {k: cast(d.get(k, v), v) for k,v in default.items()}
        env = {'PROJECT_WINDOWS_PASCAL_IMPORT_KEYS': keys,
               'stage541_import_options': norm}
        tree = ast.parse(parseable)
        def loop(name, extra):
            f = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name==name)
            matched = [n for n in f.body if isinstance(n, ast.For) and
                       'Settings.Windows.{_suffix}.Compiler.Pascal.Imports' in ast.get_source_segment(parseable,n)]
            self.assertEqual(len(matched),1)
            exec(compile(ast.fix_missing_locations(ast.Module(body=matched, type_ignores=[])),
                         '<stage541>', 'exec'), dict(env, **extra))
        parser = configparser.ConfigParser(interpolation=None)
        parser.optionxform = str
        loop('format_project_ini', {'parser': parser, 'entries': {
            'i32': [{'cache_enabled': True, 'prune_unused': False, 'externalize': True}],
            'i64': [{'cache_enabled': False, 'prune_unused': True, 'externalize': False}]}})
        self.assertEqual(parser.get('Settings.Windows.32Bit.Compiler.Pascal.Imports','Externalize'), 'true')
        self.assertEqual(parser.get('Settings.Windows.64Bit.Compiler.Pascal.Imports','CacheEnabled'), 'false')
        restored = {}
        loop('parse_project_ini', {'parser': parser, 'entries': restored})
        self.assertTrue(restored['i32'][0]['externalize'])
        self.assertFalse(restored['i32'][0]['prune_unused'])
        self.assertFalse(restored['i64'][0]['cache_enabled'])
        self.assertTrue(restored['i64'][0]['prune_unused'])

    def test_compiler_bridge_preserves_required_imports_for_both_targets(self):
        from test_stage532 import _compiler
        c = _compiler()
        pos = c.SourcePosition(1, 1)
        body = c.CompoundStatement(pos, (
            c.CallStatement(pos, 'writeln', (c.LiteralExpression(pos, 'Hallo'),)),
        ))
        program = c.PascalProgram('ImportProbe', (), (), body)
        for target, implementation in (("pe32", c._PE32CodeGenerator),
                                       ("pe64", c._PE64CodeGenerator)):
            raw = implementation(program, stack_protector=True).generate()
            processed = c._stage541_process_pascal_imports(
                raw, source='program ImportProbe;', filename='<inline>', target=target,
                output_directory=None, import_cache_enabled=False,
                import_prune_unused=True, import_cache_directory=None,
                import_runtime_version='libd64_runtime', optimization_level=0,
                stack_protector=True, no_stack_frames=False)
            self.assertGreater(processed.import_manifest['used'], 0)
            self.assertIn('BCryptGenRandom', processed.assembly)
            self.assertIn('call __pas_print_string', processed.assembly)
            self.assertEqual(len(processed.assembly.splitlines()),
                             len(raw.assembly.splitlines()))

    def test_real_stage540_asm_analysis(self):
        asm_path = ROOT / 'runtime/pascal/test/test_raise.generated.pe32.asm'
        if not asm_path.exists():
            self.skipTest('Generated sample not included')
        original = asm_path.read_text(encoding='utf-8')
        clean, manifest = process_assembly(original, 'pe32', cache_enabled=False)
        self.assertLessEqual(manifest['unused'], manifest['declared'])
        self.assertIn('__pas_method_tfoo_create:', clean)
        self.assertIn('import _jit_object_free,', clean)
        self.assertIn('call _jit_object_free', clean)


if __name__ == '__main__':
    unittest.main()
