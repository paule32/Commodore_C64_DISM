"""Real internal COFF/PE32/PE64 smoke links for Stage 605 without PyQt5.

The application module imports Qt GUI services at top level. For a portable
regression, load only its PE assembler/linker declarations into an isolated
namespace. The linked outputs are inspected via the actual PE parser.
"""
from __future__ import annotations

import ast
import io
import json
import os
import re
import struct
import sys
import types
import unittest
import zlib
import hashlib
from pathlib import Path
from dataclasses import dataclass, field, replace
from typing import *
from collections import defaultdict
from tempfile import TemporaryDirectory

from debug_options import DebugOptions
from windows_asm_macros import (
    WindowsAsmMacroError, preprocess_windows_asm,
    externalize_windows_imports, externalize_windows_wfm_payload,
)
from d64dbase import compile_dbase_to_assembly
from pascal_console_dependencies import inspect_pe

ROOT = Path(__file__).resolve().parent
OBJECTS = ROOT / 'runtime/dbase/src/System.Objects.prg'


def _load_pe_linker():
    source = (ROOT / 'd64_dism.py').read_text(encoding='utf-8')
    source = re.sub(r'(?m)^(\s*)lazy (from|import)\b', r'\1\2', source)
    tree = ast.parse(source)
    beginning = next(node.lineno for node in tree.body if isinstance(node, ast.ClassDef)
                     and node.name == 'PE32AssemblerError') - 60
    # PE assembler, COFF, linker, and debug-option definitions. Ends before
    # the main PyQt5 application and its GUI-only state.
    ending = next(node.lineno for node in tree.body if isinstance(node, ast.FunctionDef)
                  and node.name == '_project_document_output_path') if any(
        isinstance(node, ast.FunctionDef) and node.name == '_project_document_output_path'
        for node in tree.body) else 47000
    ending = min(ending, 47000)
    included = [node for node in tree.body if beginning <= getattr(node, 'lineno', 0) < ending
                and isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.Assign, ast.AnnAssign))]
    namespace_name = '_stage605_pe_linker_smoketest'
    module = types.ModuleType(namespace_name)
    sys.modules[namespace_name] = module
    ns = module.__dict__
    ns.update(globals())
    ns['__name__'] = namespace_name
    ns['__file__'] = str(ROOT / 'd64_dism.py')
    import __future__
    exec(compile(ast.fix_missing_locations(ast.Module(body=included, type_ignores=[])),
                 'stage605_reduced_linker', 'exec', flags=__future__.annotations.compiler_flag), ns)
    return ns


class Stage605CoffLinks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.linker = _load_pe_linker()
        cls.source = OBJECTS.read_text('utf-8')

    def test_real_pe32_pe64_class_dlls(self):
        for target, machine in (('pe32', 0x14c), ('pe64', 0x8664)):
            with self.subTest(target=target):
                result = compile_dbase_to_assembly(
                    self.source, filename=str(OBJECTS), target=target,
                    source_kind='library')
                linker = self.linker
                if target == 'pe32':
                    obj = linker['assemble_pe32_object_source'](
                        result.assembly, filename=str(OBJECTS))
                    binary = linker['write_coff32_object'](obj)
                    dll = linker['link_coff32_objects'](
                        (binary,), entry_symbol='__d64_dll_entry',
                        dll=True, dll_name='RuntimeDB.dll')
                else:
                    obj = linker['assemble_pe64_object_source'](
                        result.assembly, filename=str(OBJECTS))
                    binary = linker['write_coff64_object'](obj)
                    dll = linker['link_coff64_objects'](
                        (binary,), entry_symbol='__d64_dll_entry',
                        dll=True, dll_name='RuntimeDB.dll')
                with TemporaryDirectory() as directory:
                    path = Path(directory) / 'RuntimeDB.dll'
                    path.write_bytes(dll.executable)
                    actual_machine, imports, exports = inspect_pe(path)
                self.assertEqual(actual_machine, machine)
                self.assertIn('libd64_runtime.dll', {key.lower() for key in imports})
                self.assertIn('__dbase_cls_tobject_create', exports)
                self.assertIn('__dbase_cls_tobject_vmt', exports)
                self.assertIn('__dbase_cls_tobject_classname', exports)
                self.assertIn('__dbase_cls_tobject_free', exports)
                self.assertNotIn('__dbase_vmt_tobject', exports)


if __name__ == '__main__':
    unittest.main()
