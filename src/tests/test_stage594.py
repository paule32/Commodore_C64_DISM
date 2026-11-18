"""Stage 594: dBASE orange directives/FFI types and external C procedures."""
import re
import textwrap
import types
import unittest
from pathlib import Path

from d64dbase.ffi import extract_ffi_prototypes
from d64dbase.compiler import compile_dbase_to_assembly, preprocess_dbase_source

ROOT = Path(__file__).resolve().parent


def _load_highlighter_without_pyqt5():
    """Execute only the unmodified highlighter class with a stand-in Qt base."""
    text = (ROOT / 'd64_dism.py').read_text(encoding='utf-8')
    start = text.index('    class AssemblerSyntaxHighlighter(QSyntaxHighlighter):')
    end = text.index('\n    class ', start + 10)
    namespace = {'re': re, 'QSyntaxHighlighter': type('QSyntaxHighlighter', (), {})}
    exec(textwrap.dedent(text[start:end]), namespace)
    return namespace['AssemblerSyntaxHighlighter']


def highlight_line(text, previous_state=0):
    highlighter_class = _load_highlighter_without_pyqt5()
    highlighter = highlighter_class.__new__(highlighter_class)
    colors = [None] * len(text)
    highlighter.pascal_keyword_format = 'keyword'
    highlighter.pascal_number_format = 'number'
    highlighter.pascal_string_format = 'string'
    highlighter.comment_format = 'comment'
    highlighter.dbase_ffi_orange_format = 'orange'
    highlighter.setFormat = lambda start, length, fmt: colors.__setitem__(slice(start, start + length), [fmt] * length)
    highlighter.previousBlockState = lambda: previous_state
    highlighter.setCurrentBlockState = lambda value: setattr(highlighter, '_state', value)
    highlighter._highlight_dbase_block(text)
    return colors, highlighter._state


class Stage594Tests(unittest.TestCase):
    def test_external_procedure_syntax_all_aliases(self):
        source = '''extern CVOID log_a(LPCSTR) cdecl "log.dll" from "log_a"
extern VOID log_b(CINT) stdcall "log.dll" from "log_b"
extern PROC log_c() cdecl "log.dll" from "log_c"
extern PROCEDURE log_d(PVOID) cdecl "log.dll" from "log_d"
extern log_e(CINT, INT64) cdecl "log.dll" from "log_e"
'''
        rest, protos = extract_ffi_prototypes(source)
        self.assertEqual(rest.count('\n'), source.count('\n'))
        self.assertEqual(len(protos), 5)
        self.assertEqual({p.return_type for p in protos}, {'CVOID'})
        self.assertEqual([p.name for p in protos], ['log_a', 'log_b', 'log_c', 'log_d', 'log_e'])

    def test_cdecl_procedure_uses_caller_stack_cleanup_pe32(self):
        source = ('extern print_status(CINT, INT64) cdecl "status.dll" from "print_status"\n'
                  'print_status(5, 1024)\n')
        asm = compile_dbase_to_assembly(source, target='pe32').assembly
        self.assertIn('import __dbase_ffi_print_status, "status.dll", "print_status"', asm)
        self.assertRegex(asm, r'call __dbase_ffi_print_status\n    add esp, 12\n')

    def test_stdcall_procedure_no_caller_cleanup_pe32(self):
        asm = compile_dbase_to_assembly(
            'extern PROCEDURE notify(CINT) stdcall "notify.dll" from "notify"\nnotify(9)\n',
            target='pe32').assembly
        self.assertNotIn('add esp, 4\n', asm.split('call __dbase_ffi_notify\n', 1)[1][:60])

    def test_void_procedure_as_value_rejected(self):
        with self.assertRaisesRegex(Exception, 'keinen Wert|liefert CVOID'):
            compile_dbase_to_assembly('extern run() cdecl "run.dll" from "run"\nx = run()\n')

    def test_pe64_procedure_unified_call_convention(self):
        asm = compile_dbase_to_assembly(
            'extern PROCEDURE set_flag(CINT) cdecl "flag.dll" from "set_flag"\nset_flag(2)\n',
            target='pe64').assembly
        self.assertRegex(asm, r'call __dbase_ffi_set_flag\n    add rsp, 40\n')

    def test_user_macro_example_preprocesses(self):
        source = '''#ifndef RUNTIME_DLL
#define RUNTIME_DLL "libd64_runtime.dll"
#else
#undef RUNTiME_DLL
#define RUNTIME_DLL "libd64_runtime.dll"
#endif
extern PVOID jit_object_instance_new(PVOID); cdecl; RUNTIME_DLL; from "jit_object_instance_new"
result = jit_object_instance_new(0)
'''
        frontend = preprocess_dbase_source(source)
        self.assertEqual(len(frontend.ffi_prototypes), 1)
        self.assertEqual(frontend.ffi_prototypes[0].dll, 'libd64_runtime.dll')
        self.assertEqual(frontend.ffi_prototypes[0].calling_convention, 'cdecl')
        self.assertEqual(frontend.ffi_prototypes[0].return_type, 'PVOID')

    def test_orange_preprocessor_directives_only(self):
        for line, token in [('#ifndef RUNTIME_DLL', '#ifndef'),
                            ('#define RUNTIME_DLL "libd64_runtime.dll"', '#define'),
                            ('#else', '#else'),
                            ('#undef RUNTiME_DLL', '#undef'),
                            ('#endif', '#endif'),
                            ('   #iNcLuDe "foo.h"', '#iNcLuDe')]:
            with self.subTest(line=line):
                colors, _ = highlight_line(line)
                pos = line.index('#')
                self.assertTrue(all(color == 'orange' for color in colors[pos:pos + len(token)]), colors)
                self.assertTrue(all(color != 'orange' for color in colors[pos + len(token):]), colors)

    def test_orange_ffi_types_but_strings_and_comments_override(self):
        line = 'extern PVOID init(PVOID, CINT, LPCSTR) cdecl "PVOID" // CINT'
        colors, _ = highlight_line(line)
        for token in ('PVOID', 'CINT', 'LPCSTR'):
            idx = line.index(token)
            self.assertEqual(colors[idx:idx + len(token)], ['orange'] * len(token))
        quoted = line.index('"PVOID"')
        self.assertEqual(colors[quoted:quoted + 7], ['string'] * 7)
        comment = line.index('//')
        self.assertEqual(colors[comment:], ['comment'] * (len(line) - comment))

    def test_orange_not_on_substrings_of_identifiers(self):
        colors, _ = highlight_line('PVOID_VALUE = 4')
        self.assertTrue(all(color != 'orange' for color in colors[:11]))

    def test_multiline_comments_remain_comments(self):
        _, state = highlight_line('/* open')
        colors, _ = highlight_line('PVOID CINT */', state)
        self.assertTrue(all(color == 'comment' for color in colors))


if __name__ == '__main__':
    unittest.main()
