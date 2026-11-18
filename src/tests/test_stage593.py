"""Regressionen fuer die Sprach-/ABI-getrennten Projektverzeichnisse (Stage 593)."""
from __future__ import annotations

import ast
import configparser
import importlib
from pathlib import Path
import re
import textwrap
from types import SimpleNamespace
import unittest

ROOT = Path(__file__).resolve().parent
MAIN = ROOT / 'd64_dism.py'
from project_compiler_directories import LANGUAGES, compiler_language, settings_for


def _ast_main():
    source = MAIN.read_text(encoding='utf-8')
    return ast.parse(re.sub(r'\blazy\s+(?=from |import )', '', source))


def _extract_function(name, ns):
    root = _ast_main()
    found = [node for node in ast.walk(root)
             if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name]
    if len(found) != 1:
        raise AssertionError(f"{name}: {len(found)} definitions")
    node = found[0]
    fn = ast.FunctionDef(name=node.name, args=node.args, body=node.body,
                         decorator_list=[], returns=None, type_comment=None)
    mod = ast.fix_missing_locations(ast.Module(body=[fn], type_ignores=[]))
    exec(compile(mod, str(MAIN), 'exec'), ns)
    return ns[name]


class PathsTests(unittest.TestCase):
    def test_independent_section_names_and_keys(self):
        keys = []
        sections = []
        for target in ('pe32', 'pe64'):
            for language in LANGUAGES:
                settings = settings_for(target, language)
                keys += [settings['input_key'], settings['output_key'],
                         settings['cache_key'], settings['input_relative_key'],
                         settings['output_relative_key']]
                sections += [settings['input_section'], settings['output_section']]
        self.assertEqual(len(keys), len(set(keys)))
        self.assertEqual(len(sections), len(set(sections)))
        self.assertIn('dBASE', settings_for('pe32', 'dbase')['input_section'])

    def test_language_from_document(self):
        for lang in LANGUAGES:
            flags = {'is_' + lang + '_document': True}
            self.assertEqual(compiler_language(SimpleNamespace(**flags)), lang)
        self.assertEqual(compiler_language(SimpleNamespace(source_language=lambda: 'dbase')), 'dbase')
        self.assertEqual(compiler_language(SimpleNamespace(source_language=lambda: 'prolog')), 'prolog')
        self.assertEqual(compiler_language(SimpleNamespace(source_language=lambda: 'pascal')), 'pascal')
        self.assertEqual(compiler_language(SimpleNamespace(source_language=lambda: 'c')), '')

    def test_project_output_resolution_language_and_type(self):
        class AssemblerError(Exception):
            pass
        ns = {'Path': Path, 'AssemblerError': AssemblerError,
              '_project_document_compiler_language': compiler_language}
        resolve = _extract_function('_project_document_output_path', ns)
        base = Path('/mnt/s593/projects').resolve()
        output = {
            'pe32': {lang: str(base / (lang + '-final')) for lang in LANGUAGES},
            'pe64': {lang: str(base / ('64-' + lang)) for lang in LANGUAGES},
        }
        cache = {
            'pe32': {lang: str(base / (lang + '-asm')) for lang in LANGUAGES},
            'pe64': {lang: str(base / ('64-' + lang + '-asm')) for lang in LANGUAGES},
        }
        class Owner:
            project_windows_language_output_directories = output
            project_windows_language_assembler_cache = cache
            project_windows_pascal_unit_output_directories = {
                'pe32': str(base / 'pascal-pui'), 'pe64': str(base / 'pascal64-pui')}
            project_windows_output_directories = {'pe32': str(base / 'old-output')}
            project_windows_assembler_cache = {'pe32': str(base / 'old-cache')}
            def _project_windows_absolute_directory(self, p):
                return str(Path(p).resolve())
        owner = Owner()
        for target in ('pe32', 'pe64'):
            for lang in LANGUAGES:
                flags = {'is_' + lang + '_document': True}
                doc = SimpleNamespace(path=base / f'foo.{lang}',
                                      build_target=target, window=lambda: owner,
                                      project_tree_compile_output_directory=None, **flags)
                self.assertEqual(resolve(doc, 'foo.exe'), Path(output[target][lang]) / 'foo.exe')
                self.assertEqual(resolve(doc, 'foo.dll'), Path(output[target][lang]) / 'foo.dll')
                self.assertEqual(resolve(doc, 'foo.generated.asm'), Path(cache[target][lang]) / 'foo.generated.asm')
                expected_obj = (base / ('pascal-pui' if target == 'pe32' else 'pascal64-pui')) if lang == 'pascal' else Path(output[target][lang])
                self.assertEqual(resolve(doc, 'foo.o'), expected_obj / 'foo.o')

    def test_separate_inputs_and_output_routing(self):
        class Owner:
            project_windows_language_search_paths = {
                'pe32': {lang: [f'/a/{lang}'] for lang in LANGUAGES}}
            project_windows_language_output_directories = {
                'pe32': {lang: f'/b/{lang}' for lang in LANGUAGES}}
            def _project_windows_language(self, lang): return lang
            def _project_windows_target_key(self, target): return target
            def _project_windows_absolute_directory(self, value): return str(value)
        ns = {'Path': Path, 'Tuple': tuple, 'List': list}
        link = _extract_function('_project_windows_link_search_paths', ns)
        asm = _extract_function('_project_windows_asm_include_paths', ns)
        out = _extract_function('_project_windows_language_output_path', ns)
        Owner._project_windows_link_search_paths = link
        Owner._project_windows_asm_include_paths = asm
        Owner._project_windows_language_output_path = out
        owner = Owner()
        for lang in LANGUAGES:
            self.assertEqual(owner._project_windows_link_search_paths('pe32', lang), (Path('/a/' + lang),))
            self.assertEqual(owner._project_windows_asm_include_paths('pe32', lang), (Path('/a/' + lang),))
            self.assertEqual(owner._project_windows_language_output_path('pe32', lang), Path('/b/' + lang))

    def test_parser_code_migration_and_explicit_empty(self):
        """Fuehrt den originalen Stage-593-Importblock mit einem echten .pro-Parser aus."""
        raw = MAIN.read_text(encoding='utf-8')
        start = raw.index('    # Stage 593: getrennte Verzeichnisse lesen;')
        end = raw.index('\n    return entries\n\n\ndef save_project_ini(', start)
        snippet = raw[start:end]
        source = 'def parse_stage593(parser, entries, project_path):\n' + snippet + '\n    return entries\n'
        def loaded(path, project):
            path = Path(path)
            return str(path.resolve()) if path.is_absolute() else str((project.parent / path).resolve())
        ns = {'PROJECT_WINDOWS_TARGET_SETTINGS': {
            'pe32': dict(input_key='legacy_in', output_key='legacy_out',
                         input_relative_key='legacy_in_rel', output_relative_key='legacy_out_rel',
                         asm_cache_key='legacy_cache', pascal_unit_output_key='unit'),
            'pe64': dict(input_key='legacy64_in', output_key='legacy64_out',
                         input_relative_key='legacy64_in_rel', output_relative_key='legacy64_out_rel',
                         asm_cache_key='legacy64_cache', pascal_unit_output_key='unit64'),
        }, 'PROJECT_WINDOWS_COMPILER_LANGUAGES': LANGUAGES,
        '_project_compiler_directory_settings': settings_for,
        '_project_loaded_path': loaded, 'Path': Path,
        '_parse_project_bool': lambda value, default: str(value).lower() in ('true', '1', 'yes')}
        exec(compile(source, str(MAIN), 'exec'), ns)
        legacy = {k: [] for k in ('legacy_in','legacy_out','legacy_cache','unit',
                                  'legacy64_in','legacy64_out','legacy64_cache','unit64')}
        legacy.update({'legacy_in':[{'path':'/old/source'}], 'legacy_out':[{'path':'/old/target'}],
                       'legacy_cache':[{'path':'/old/asm'}],
                       'legacy_in_rel':[{'value':'true'}], 'legacy_out_rel':[{'value':'true'}],
                       'legacy64_in_rel':[{'value':'true'}], 'legacy64_out_rel':[{'value':'true'}]})
        parser = configparser.ConfigParser()
        results = ns['parse_stage593'](parser, legacy, Path('/tmp/app.pro'))
        for language in LANGUAGES:
            ls = settings_for('pe32', language)
            self.assertEqual(results[ls['input_key']], [{'path':'/old/source'}])
            self.assertEqual(results[ls['output_key']], [{'path':'/old/target'}])
        # Explicitly empty new profile means no fallback to the legacy value.
        ls = settings_for('pe32', 'pascal')
        parser[ls['input_section']] = {'RelativePaths': 'false'}
        parser[ls['output_section']] = {'RelativePaths': 'false'}
        results = ns['parse_stage593'](parser, legacy, Path('/tmp/app.pro'))
        self.assertEqual(results[ls['input_key']], [])
        self.assertEqual(results[ls['output_key']], [])
        self.assertEqual(results[ls['input_relative_key']], [{'value':'false'}])


class IntegrationTests(unittest.TestCase):
    def test_editor_tree_nested_language_paths(self):
        s = MAIN.read_text(encoding='utf-8')
        self.assertIn('self.nodes["compiler"].removeChild(self.compiler_input_directories_item)', s)
        self.assertIn('self.language_directory_items[(_language, _kind)] = _item', s)
        self.assertIn('self.language_directory_pages[_language] = _directory_page', s)
        self.assertIn('self._document_windows_output_path(document)', s)
        self.assertIn('self._project_windows_asm_include_paths(document.build_target, "pascal")', s)
        self.assertIn('self._project_windows_asm_include_paths(document.build_target, "dbase")', s)
        self.assertIn('self.project_windows_language_output_directories.get(', s)
        self.assertIn('language=_project_document_compiler_language(document)', s)


if __name__ == '__main__':
    unittest.main()
