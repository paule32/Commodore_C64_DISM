"""Stage 603: target-dependent platform macros for dBASE and Pascal."""
from __future__ import annotations

from pathlib import Path
import ast
import re
import unittest
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional, Union, Iterable

from d64dbase import preprocess_dbase_source, compile_dbase_to_assembly, DBaseCompilerError
from d64dbase.compiler import _preprocess_dbase_macros
ROOT = Path(__file__).parent

# The bundled ANTLR lexer was generated with 4.13.2, whereas the local test
# environment has the 4.9.3 runtime.  Load the *real* Pascal preprocessor
# definitions from compiler.py without importing the incompatible lexer.
source_path = ROOT / 'c64pascal' / 'compiler.py'
compiler_source = source_path.read_text(encoding='utf-8')
compiler_tree = ast.parse(compiler_source, filename=str(source_path))
preprocessor_names = {
    'C64PascalError', '_pascal_code_mask', 'PascalPreprocessResult',
    'PascalPreprocessorDiagnostic', '_expand_pascal_macros',
    '_condition_identifiers', '_evaluate_preprocessor_ast',
    '_evaluate_pascal_condition', '_pascal_target_macros',
    'PascalPreprocessor', 'preprocess_pascal_source',
}
selected_nodes = [node for node in compiler_tree.body
                  if isinstance(node, (ast.FunctionDef, ast.ClassDef))
                  and node.name in preprocessor_names]
namespace = dict(ast=ast, re=re, Path=Path, dataclass=dataclass,
                 Dict=Dict, List=List, Tuple=Tuple, Optional=Optional,
                 Union=Union, Iterable=Iterable)
extracted = ast.Module(body=selected_nodes, type_ignores=[])
exec(compile(ast.fix_missing_locations(extracted), str(source_path), 'exec'), namespace)
_pascal_target_macros = namespace['_pascal_target_macros']
preprocess_pascal_source = namespace['preprocess_pascal_source']

DBASE_SOURCE = '''#ifdef WIN32
? "win32"
#endif
#ifdef WINDOWS
? "windows"
#endif
#if WIN32 == 1
? "win32-value"
#endif
#ifdef WIN64
? "win64"
#endif
#ifdef LINUX
? "linux"
#endif
#if LINUX == 0
? "not-linux"
#endif
'''
PASCAL_SOURCE = '''{$IFDEF WINDOWS}
WIN_RESULT
{$ELSE}
NOT_WINDOWS
{$ENDIF}
{$IFDEF WIN32}
WIN32_RESULT
{$ENDIF}
{$IFDEF WIN64}
WIN64_RESULT
{$ENDIF}
{$IFDEF LINUX}
LINUX_RESULT
{$ENDIF}
'''


class Stage603PlatformMacros(unittest.TestCase):
    def test_dbase_pe32_macros(self):
        result = preprocess_dbase_source(DBASE_SOURCE, target='pe32')
        names = {macro.name.upper(): macro.body for macro in result.macros}
        self.assertEqual(names['WIN32'], '1')
        self.assertEqual(names['WINDOWS'], '1')
        self.assertNotIn('WIN64', names)
        self.assertNotIn('LINUX', names)
        for word in ('"win32"', '"windows"', '"win32-value"', '"not-linux"'):
            self.assertIn(word, result.preprocessed_source)
        self.assertNotIn('"linux"', result.preprocessed_source)
        self.assertNotIn('"win64"', result.preprocessed_source)

    def test_dbase_pe64_macros(self):
        result = preprocess_dbase_source(DBASE_SOURCE, target='pe64')
        self.assertIn('"win64"', result.preprocessed_source)
        self.assertNotIn('"linux"', result.preprocessed_source)
        names = {macro.name.upper() for macro in result.macros}
        self.assertEqual(names & {'WIN32','WINDOWS','WIN64','LINUX'}, {'WIN32','WINDOWS','WIN64'})

    def test_dbase_linux_preprocess_only(self):
        # dBASE backend currently accepts PE32/PE64 only; check internal PP logic
        text = '#ifdef LINUX\n? "linux"\n#endif\n#ifdef WINDOWS\n? "win"\n#endif\n'
        cleaned, macros, _, _, _ = _preprocess_dbase_macros(text, filename='<linux-test>', target='linux')
        self.assertIn('"linux"', cleaned)
        self.assertNotIn('"win"', cleaned)
        self.assertEqual({m.name.upper() for m in macros}, {'LINUX'})
        with self.assertRaises(DBaseCompilerError):
            preprocess_dbase_source(text, target='linux')

    def test_dbase_explicit_undef_and_define_still_work(self):
        text = '#undef WIN32\n#ifdef WIN32\n? "wrong"\n#else\n? "ok"\n#endif\n#define WIN32 2\n#if WIN32 == 2\n? "two"\n#endif\n'
        processed = preprocess_dbase_source(text, target='pe32').preprocessed_source
        self.assertNotIn('"wrong"', processed)
        self.assertIn('"ok"', processed)
        self.assertIn('"two"', processed)

    def test_dbase_real_assembly_both_targets(self):
        code = '#ifdef WINDOWS\n? "OK"\n#else\n? "wrong"\n#endif\n'
        for target in ('pe32', 'pe64'):
            with self.subTest(target=target):
                result = compile_dbase_to_assembly(code, target=target)
                self.assertIn('? "OK"', result.frontend.preprocessed_source)
                self.assertNotIn('wrong', result.frontend.preprocessed_source)
                self.assertIn('db 79, 75', result.assembly)

    def test_pascal_core_targets(self):
        cases = {
            'pe32': {'WINDOWS', 'WIN32'},
            'pe64': {'WINDOWS', 'WIN32', 'WIN64'},
            'linux': {'LINUX'},
            'elf64': {'LINUX'},
            'c64': set(),
            'amiga': set(),
        }
        for target, expected in cases.items():
            with self.subTest(target=target):
                result = preprocess_pascal_source(PASCAL_SOURCE, target=target)
                defined = {name.upper() for name in result.macros}
                self.assertEqual(defined & {'WINDOWS', 'WIN32', 'WIN64', 'LINUX'}, expected)
                active = result.source
                self.assertEqual('WIN_RESULT' in active, 'WINDOWS' in expected)
                self.assertEqual('WIN32_RESULT' in active, 'WIN32' in expected)
                self.assertEqual('WIN64_RESULT' in active, 'WIN64' in expected)
                self.assertEqual('LINUX_RESULT' in active, 'LINUX' in expected)

    def test_pascal_core_no_inactive_zero_macros(self):
        result = preprocess_pascal_source('{$IFDEF LINUX}bad{$ELSE}ok{$ENDIF}', target='pe32')
        self.assertIn('ok', result.source)
        self.assertNotIn('bad', result.source)
        # Caller-supplied stale symbols must not select the wrong ABI.
        macros = _pascal_target_macros({'LINUX': 0, 'WIN64': 1}, 'pe32')
        self.assertEqual({k.upper() for k in macros if k.upper() in ('WINDOWS','WIN32','WIN64','LINUX')}, {'WINDOWS','WIN32'})

    def test_pascal_core_undef_and_value(self):
        source = '{$IF WINDOWS = 1}WIN{$ELSE}NO{$ENDIF}\n{$UNDEF WINDOWS}\n{$IFDEF WINDOWS}BAD{$ELSE}GOOD{$ENDIF}'
        result = preprocess_pascal_source(source, target='pe32')
        self.assertIn('WIN', result.source)
        self.assertIn('GOOD', result.source)
        self.assertNotIn('BAD', result.source)

    def test_pascal_ide_matches_compiler(self):
        # Execute only this helper: importing d64_dism.py needs PyQt5 and Python 3.15.
        source = (ROOT / 'd64_dism.py').read_text(encoding='utf-8')
        start = source.index('def _pascal_ide_target_macros(')
        end = source.index('\ndef preprocess_pascal_source(', start)
        block = source[start:end]
        ns = {'Optional': __import__('typing').Optional, 'Dict': dict}
        exec(compile(block, '<stage603_ide_macros>', 'exec'), ns)
        ide = ns['_pascal_ide_target_macros']
        for target in ('pe32', 'pe64', 'linux', 'elf64', 'c64', 'amiga'):
            with self.subTest(target=target):
                first = {k.upper() for k in ide({}, target)}
                second = {k.upper() for k in _pascal_target_macros({}, target)}
                self.assertEqual(first, second)

    def test_pascal_ide_actual_preprocessor(self):
        # Run real IDE conditional processing without importing the giant Qt GUI.
        source = (ROOT / 'd64_dism.py').read_text(encoding='utf-8')
        start = source.index('class PascalPreprocessorError(')
        end = source.index('\nfrom flags_rc', start)
        import datetime as dt
        ns = dict(__name__=__name__, re=re, Path=Path, dt=dt,
                  dataclass=dataclass, Dict=Dict, List=List, Tuple=Tuple,
                  Optional=Optional, Iterable=Iterable)
        exec(compile(source[start:end], '<stage603_ide_pascal>', 'exec'), ns)
        gui_preprocess = ns['preprocess_pascal_source']
        for target in ('pe32', 'pe64', 'linux', 'c64'):
            with self.subTest(target=target):
                ide = gui_preprocess(PASCAL_SOURCE, target=target)
                compiler = preprocess_pascal_source(PASCAL_SOURCE, target=target)
                self.assertEqual(ide.source, compiler.source)
                self.assertEqual({x.upper() for x in ide.macros},
                                 {x.upper() for x in compiler.macros})

    def test_pascal_ide_preserves_none_target_callers(self):
        source = (ROOT / 'd64_dism.py').read_text(encoding='utf-8')
        start = source.index('def _pascal_ide_target_macros(')
        end = source.index('\ndef preprocess_pascal_source(', start)
        ns = {'Optional': __import__('typing').Optional, 'Dict': dict}
        exec(source[start:end], ns)
        self.assertEqual(ns['_pascal_ide_target_macros']({'MY_DEFINE': '42'}, None), {'MY_DEFINE':'42'})

    def test_parallel_worker_target_propagated(self):
        source = (ROOT / 'pascal_parallel_build.py').read_text(encoding='utf-8')
        self.assertRegex(source, r'prepared\s*=\s*preprocess_pascal_source\([\s\S]{0,160}target=target\)')

    def test_directives_case_insensitive(self):
        self.assertIn('ok', preprocess_dbase_source('#ifdef windows\n? "ok"\n#endif\n', target='pe32').preprocessed_source)
        self.assertIn('ok', preprocess_pascal_source('{$ifdef windows}ok{$endif}', target='pe64').source)


if __name__ == '__main__':
    unittest.main()
