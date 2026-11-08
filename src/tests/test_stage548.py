"""Stage 548: project-root-relative PE outputs and consistent Pascal DLL lookup.

The real d64_dism.py functions are extracted from their AST. This avoids Qt
and the Python-3.15 lazy import statement under Python 3.13 for targeted tests.
"""
from __future__ import annotations
import ast
import os
from pathlib import Path
import re
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from typing import List, Tuple, Optional

from pascal_library_contract import read_contract, write_contract, validate_contract_exports
from pascal_class_exports import validate_class_dll_references


def load_real_paths():
    path = Path(__file__).with_name('d64_dism.py')
    source = re.sub(r'(?m)^(\s*)lazy from ', r'\1from ', path.read_text(encoding='utf-8'))
    module = ast.parse(source, filename=str(path))
    explorer = next(n for n in ast.walk(module)
                    if isinstance(n, ast.ClassDef) and n.name == 'ExplorerWindow')
    names = {
        '_project_windows_base_directory', '_project_windows_absolute_directory',
        '_project_windows_output_path', '_project_windows_link_search_paths',
        '_project_windows_pascal_library_search_paths', '_document_windows_output_path',
        '_document_windows_pascal_unit_output_path', '_project_generated_object_path',
        '_resolve_project_link_input',
    }
    selected = [n for n in explorer.body if isinstance(n, ast.FunctionDef) and n.name in names]
    assert {n.name for n in selected} == names, names - {n.name for n in selected}
    standalone = next(n for n in module.body if isinstance(n, ast.FunctionDef)
                      and n.name == '_project_document_output_path')
    class_def = ast.ClassDef(name='ActualPaths', bases=[], keywords=[], body=selected, decorator_list=[])
    synthetic = ast.Module(body=[ast.ImportFrom(module='__future__', names=[ast.alias(name='annotations')], level=0),
                                 standalone, class_def], type_ignores=[])
    ast.fix_missing_locations(synthetic)
    namespace = {'Path':Path, 'os':os, 'Tuple':Tuple, 'List':List, 'Optional':Optional,
                 'AssemblerError':ValueError}
    exec(compile(synthetic, str(path), 'exec'), namespace)
    return namespace['ActualPaths'], namespace['_project_document_output_path'], source


ActualPaths, OUTPUT_PATH, MAIN_SOURCE = load_real_paths()


class Host(ActualPaths):
    def __init__(self, root):
        self.current_project_path = root / 'pascal.pro'
        self.current_directory = root
        self.project_windows_output_directories = {
            'pe32': r'runtime/pascal/test/pe32',
            'pe64': r'runtime/pascal/test/pe64',
        }
        self.project_windows_assembler_cache = {
            'pe32': r'runtime/pascal/test/tmp',
            'pe64': r'runtime/pascal/test/tmp64',
        }
        self.project_windows_pascal_unit_output_directories = {
            'pe32': r'runtime/pascal/test/x32',
            'pe64': r'runtime/pascal/test/x64',
        }
        self.project_windows_relative_paths = {
            'pe32': {'input': True, 'output': True},
            'pe64': {'input': True, 'output': True},
        }
        self.project_windows_search_paths = {
            'pe32': ['runtime/pascal/test/include32'],
            'pe64': ['runtime/pascal/test/include64'],
        }

    def _project_windows_target_key(self, target):
        return str(target).casefold()


class PathTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.host = Host(self.root)
        self.source_dir = self.root/'runtime'/'pascal'/'test'
        self.source_dir.mkdir(parents=True)
        self.source = self.source_dir/'test_raise.pas'
        self.source.write_text('program test_raise; begin end.',encoding='utf-8')

    def document(self, target='pe32'):
        return SimpleNamespace(path=self.source, build_target=target,
                               window=lambda: self.host)

    def test_paths_are_project_root_relative_not_source_relative(self):
        for target in ('pe32','pe64'):
            with self.subTest(target=target):
                doc = self.document(target)
                final = self.root/'runtime'/'pascal'/'test'/target
                unit = self.root/'runtime'/'pascal'/'test'/('x32' if target == 'pe32' else 'x64')
                tmp = self.root/'runtime'/'pascal'/'test'/('tmp' if target == 'pe32' else 'tmp64')
                self.assertEqual(OUTPUT_PATH(doc,'test_raise.exe'),final/'test_raise.exe')
                self.assertEqual(OUTPUT_PATH(doc,'Runtime.dll'),final/'Runtime.dll')
                self.assertEqual(OUTPUT_PATH(doc,'test_raise.asm'),tmp/'test_raise.asm')
                self.assertEqual(OUTPUT_PATH(doc,'UnitA.o'),unit/'UnitA.o')
                self.assertEqual(OUTPUT_PATH(doc,'UnitA.pui'),unit/'UnitA.pui')
                self.assertEqual(self.host._document_windows_output_path(doc),final)
                self.assertEqual(self.host._document_windows_pascal_unit_output_path(doc),unit)
                self.assertEqual(self.host._project_generated_object_path(self.source,target),unit/'test_raise.o')
                self.assertNotIn('runtime/pascal/test/runtime/pascal/test',
                                 str(OUTPUT_PATH(doc,'Runtime.dll')))

    def test_cached_absolute_paths_and_unchecked_relative_mode(self):
        self.host.project_windows_output_directories['pe32'] = str(self.root/'runtime'/'pascal'/'test'/'pe32')
        for mode in (True,False):
            self.host.project_windows_relative_paths['pe32']['output'] = mode
            doc = self.document()
            self.assertEqual(OUTPUT_PATH(doc,'Runtime.dll'),
                             self.source_dir/'pe32'/'Runtime.dll')
            self.assertEqual(self.host._document_windows_output_path(doc),self.source_dir/'pe32')

    def test_target_specific_library_search_and_manifest(self):
        from test_stage546 import IDE_PREPROCESS
        for target in ('pe32','pe64'):
            with self.subTest(target=target):
                doc = self.document(target)
                output = self.host._document_windows_output_path(doc)
                output.mkdir(parents=True,exist_ok=True)
                dll = output/'Runtime.dll'
                dll.write_bytes(b'PE-STUB-FOR-LOOKUP')
                contract_file = write_contract(output,'Runtime',target,{},'')
                self.assertEqual(contract_file,output/'Runtime.paslib.json')
                search = self.host._project_windows_pascal_library_search_paths(doc)
                self.assertEqual(search[0],output)
                self.assertIn(self.host._document_windows_pascal_unit_output_path(doc),search)
                self.assertIn(self.root,search)
                self.assertIn(self.source_dir/('include32' if target=='pe32' else 'include64'),search)
                prepared=IDE_PREPROCESS('program x; {$L Runtime.dll} begin end.',
                                      filename=str(self.source),link_search_paths=search)
                self.assertEqual(prepared.link_dlls,(str(dll.resolve()),))
                self.assertIsNotNone(read_contract('Runtime.dll',target,search))
                with patch('pascal_class_exports._pe_exports',return_value={'TFoo_Bar'}):
                    classes=[{'name':'TFoo','methods':[{'name':'Bar','kind':'procedure'}],
                              'fields':[],'properties':[]}]
                    paths=validate_class_dll_references(prepared.link_dlls,classes,
                                target=target,filename=str(self.source),
                                output_directory=self.host._document_windows_pascal_unit_output_path(doc),
                                link_search_paths=search)
                    self.assertEqual(paths,(str(dll.resolve()),))
                with patch('pascal_class_exports._pe_exports',return_value=set()):
                    self.assertEqual(validate_contract_exports(read_contract('Runtime.dll',target,search),
                                     'Runtime.dll',target,search),str(dll.resolve()))

    def test_output_dll_preferred_over_stale_source_copy(self):
        from test_stage546 import IDE_PREPROCESS, C
        output = self.source_dir/'pe32'
        output.mkdir(exist_ok=True)
        wanted = output/'Runtime.dll'
        wanted.write_bytes(b'NEW-OUTPUT')
        (self.source_dir/'Runtime.dll').write_bytes(b'OLD-SOURCE')
        search = self.host._project_windows_pascal_library_search_paths(self.document())
        result = IDE_PREPROCESS('{$L Runtime.dll}', filename=str(self.source),
                                link_search_paths=search)
        self.assertEqual(result.link_dlls,(str(wanted.resolve()),))
        pre = C.PascalPreprocessor(link_search_paths=search)
        other = pre.process('{$L Runtime.dll}',filename=str(self.source))
        self.assertEqual(other.link_dlls,(str(wanted.resolve()),))

    def test_link_inputs_use_unit_directory_and_executable_directory(self):
        unit=self.source_dir/'x32'
        unit.mkdir(exist_ok=True)
        obj=unit/'helper.o'
        obj.write_bytes(b'OBJ')
        dll=self.source_dir/'pe32'/'Runtime.dll'
        dll.parent.mkdir(exist_ok=True)
        dll.write_bytes(b'DLL')
        self.assertEqual(self.host._resolve_project_link_input('helper.o',source_path=self.source,
                                                                target='pe32'),obj)
        self.assertEqual(self.host._resolve_project_link_input('Runtime.dll',source_path=self.source,
                                                                target='pe32'),dll)

    def test_other_architecture_not_considered(self):
        only32=self.source_dir/'pe32'
        only32.mkdir(exist_ok=True)
        (only32/'Runtime.dll').write_bytes(b'32')
        search=self.host._project_windows_pascal_library_search_paths(self.document('pe64'))
        self.assertNotIn(only32,search)
        with patch('pascal_class_exports._pe_exports',return_value=set()):
            with self.assertRaisesRegex(ValueError,'nicht gefunden'):
                validate_class_dll_references(('Runtime.dll',),[{'name':'TFoo','methods':[],
                   'fields':[],'properties':[]}],target='pe64', filename=str(self.source),
                   output_directory=self.source_dir/'x64',link_search_paths=search)

    def test_build_paths_feed_compiler_and_parallel_worker(self):
        self.assertIn('self._project_windows_pascal_library_search_paths(document)',MAIN_SOURCE)
        self.assertIn('"link_search_paths": [str(x) for x in\n                            self._project_windows_pascal_library_search_paths(document)]', MAIN_SOURCE)


if __name__ == '__main__':
    unittest.main()
