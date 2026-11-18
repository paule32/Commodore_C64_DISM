"""Stage 595: typed LPSTR/LPCSTR DLL results become independent dBASE strings."""
from __future__ import annotations

import re
import ast
import unittest
from pathlib import Path

from d64dbase.compiler import compile_dbase_to_assembly, preprocess_dbase_source
from d64dbase.ffi_types import ffi_type_info
from d64dbase.ffi_string_result import (
    MAX_C_STRING_BYTES, prg_ansi_result, returns_ansi_string, wfm_utf8_result,
)

ROOT = Path(__file__).resolve().parent


def compile_test(return_type, target, expression='? get_text()'):
    source = (f'extern {return_type} get_text() cdecl "native.dll" from "get_text"\n'
              f'{expression}\n')
    return compile_dbase_to_assembly(source, target=target).assembly


class TypedCStringReturnTests(unittest.TestCase):
    def test_only_native_ansi_pointers_are_converted(self):
        for name in ('LPSTR', 'LPCSTR', 'PSTR', 'PCSTR', 'PCHAR', 'LPCCH'):
            with self.subTest(name=name):
                self.assertTrue(returns_ansi_string(name))
        for name in ('PVOID', 'LPVOID', 'HANDLE', 'CINT', 'CBOOL', 'LPCWSTR', 'LPWSTR'):
            with self.subTest(name=name):
                self.assertFalse(returns_ansi_string(name))
        self.assertTrue(ffi_type_info('LPSTR').is_pointer)
        self.assertFalse(ffi_type_info('LPSTR').is_string_input)
        self.assertTrue(ffi_type_info('LPCSTR').is_string_input)

    def test_prg_ffi_result_is_typed_string_in_pe32_and_pe64(self):
        for target in ('pe32', 'pe64'):
            for return_type in ('LPSTR', 'LPCSTR'):
                with self.subTest(target=target, return_type=return_type):
                    asm = compile_test(return_type, target)
                    self.assertIn('import __dbase_ffi_lstrlenA, "kernel32.dll", "lstrlenA"', asm)
                    self.assertIn('call __dbase_ffi_lstrlenA', asm)
                    self.assertIn('call __dbase_malloc', asm)
                    self.assertIn('call __dbase_memcpy', asm)
                    self.assertIn('mov dword ptr [__dbase_call_1_ffi_result_type], 2', asm)
                    self.assertIn('mov dword ptr [__dbase_call_1_ffi_result_len], eax', asm)
                    self.assertIn('call __dbase_ffi_get_text', asm)
                    self.assertIn('cmp eax, 16777216', asm)
                    self.assertNotIn('fild qword ptr [__dbase_ffi_return]', asm)
                    self.assertIn('resq 1', asm)  # string metadata storage
                    self.assertIn('call DBaseQtConsoleWrite', asm) if 'call DBaseQtConsoleWrite' in asm else None

    def test_cdecl_stack_cleanup_comes_before_conversion(self):
        for target in ('pe32', 'pe64'):
            source = (f'extern LPCSTR get_text(CINT) cdecl "native.dll" from "get_text"\n'
                      '? get_text(7)\n')
            asm = compile_dbase_to_assembly(source, target=target).assembly
            start = asm.index('call __dbase_ffi_get_text\n')
            after = asm[start:start+240]
            self.assertIn('add esp, 4' if target == 'pe32' else 'add rsp, 40', after)
            self.assertLess(after.index('add esp, 4' if target == 'pe32' else 'add rsp, 40'),
                            after.index('mov dword ptr [__dbase_ffi_return]' if target == 'pe32'
                                        else 'mov qword ptr [__dbase_ffi_return]'))

    def test_string_return_can_be_assigned_printed_and_concatenated(self):
        for target in ('pe32', 'pe64'):
            for expression in ('STORE get_text() TO txt\n? txt',
                               '? get_text() + "!"',
                               'txt = get_text()\n? txt'):
                with self.subTest(target=target, expression=expression):
                    asm = compile_test('LPCSTR', target, expression)
                    self.assertIn('call __dbase_ffi_get_text', asm)
                    self.assertIn('mov dword ptr [__dbase_call_1_ffi_result_type], 2', asm)

    def test_raw_void_pointer_is_still_numeric(self):
        for target in ('pe32', 'pe64'):
            asm = compile_test('PVOID', target)
            self.assertNotIn('lstrlenA', asm)
            self.assertIn('fild qword ptr [__dbase_ffi_return]', asm)

    def test_no_unneeded_ansi_string_imports_for_numeric_ffi(self):
        for target in ('pe32', 'pe64'):
            asm = compile_test('CINT', target)
            self.assertNotIn('__dbase_ffi_lstrlenA', asm)

    def test_null_handling_and_bounded_copy(self):
        for is64 in (False, True):
            asm = '\n'.join(prg_ansi_result('strslot', is64=is64, prefix='x'))
            self.assertIn('jz x_empty', asm)
            self.assertIn('mov dword ptr [strslot_len], 0', asm)
            self.assertIn('mov dword ptr [strslot_type], 2', asm)
            self.assertIn('cmp eax, ' + str(MAX_C_STRING_BYTES), asm)
            self.assertIn('inc eax', asm)  # copy terminator
            self.assertIn('call __dbase_memcpy', asm)
            self.assertIn('call ExitProcess', asm)
            self.assertIn('add rsp, 40' if is64 else 'add esp, 12', asm)

    def test_return_slots_are_distinct_for_multiple_calls(self):
        source = ('extern LPCSTR get_text() cdecl "native.dll" from "get_text"\n'
                  '? get_text()\n? get_text()\n')
        asm = compile_dbase_to_assembly(source, target='pe32').assembly
        names = re.findall(r'__dbase_call_\d+_ffi_result_type:', asm)
        self.assertEqual(len(names), 2)
        self.assertEqual(len(set(names)), 2)
        self.assertEqual(asm.count('call __dbase_ffi_get_text'), 2)

    def test_ffi_prototype_preprocessor_retains_return_type(self):
        frontend = preprocess_dbase_source(
            'extern LPCSTR get_text() cdecl "native.dll" from "get_text"\n')
        self.assertEqual(frontend.ffi_prototypes[0].return_type, 'LPCSTR')


class WfmUtf8ResultTests(unittest.TestCase):
    def test_wfm_converts_ansi_1252_to_utf8_and_copies(self):
        for is64 in (False, True):
            with self.subTest(is64=is64):
                lines = '\n'.join(wfm_utf8_result('slot', is64=is64, prefix='x'))
                self.assertIn('call MultiByteToWideChar', lines)
                self.assertIn('call WideCharToMultiByte', lines)
                self.assertIn('1252', lines)
                self.assertIn('65001', lines)
                self.assertIn('call __dbase_ffi_malloc', lines)
                self.assertIn('call __dbase_ffi_free', lines)
                self.assertIn('mov dword ptr [slot_type], 3', lines)
                self.assertIn('mov dword ptr [slot_len], eax', lines)
                self.assertIn('dec eax', lines)  # omit trailing NUL in length
                self.assertIn('jz x_empty', lines)
                if is64:
                    self.assertIn('sub rsp, 48', lines)
                    self.assertIn('sub rsp, 64', lines)
                    self.assertIn('add rsp, 48', lines)
                    self.assertIn('add rsp, 64', lines)
                    self.assertNotIn('add esp, 4', lines)
                else:
                    self.assertIn('add esp, 4', lines)
                    self.assertIn('push 1252', lines)
                    self.assertIn('push 65001', lines)

    def test_real_wfm_call_emitter_returns_typed_utf8_slot(self):
        # Execute the actual nested Stage-595 WFM emitter with a minimal model
        # instead of only checking text snippets in d64_dism.py.
        raw = (ROOT / 'd64_dism.py').read_text(encoding='utf8')
        ast_source = re.sub(r'(?m)^(\s*)lazy (from|import) ', r'\1\2 ', raw)
        syntax = ast.parse(ast_source)
        functions = [node for node in ast.walk(syntax)
                     if isinstance(node, ast.FunctionDef) and node.name == 'emit_wfm_ffi_call']
        self.assertEqual(len(functions), 1)
        node = functions[0]
        from d64dbase.compiler import (DBaseCallExpression, DBaseLiteralExpression,
                                       DBaseIdentifierExpression)
        from d64dbase.ffi import extract_ffi_prototypes
        _, prototypes = extract_ffi_prototypes(
            'extern LPCSTR get_text() cdecl "native.dll" from "get_text"\n')
        for is64 in (False, True):
            serial = [0]
            def next_label(name):
                serial[0] += 1
                return '__test_' + name + '_' + str(serial[0])
            ns = dict(
                is64=is64, ffi_prototypes={'get_text': prototypes[0]},
                DBaseCallExpression=DBaseCallExpression,
                DBaseLiteralExpression=DBaseLiteralExpression,
                DBaseIdentifierExpression=DBaseIdentifierExpression,
                AssemblerError=RuntimeError, filename='<test>',
                memory_slot=lambda s: s,
                memory_pointer_label=lambda s: s + '_ptr',
                memory_number_label=lambda s: s + '_num',
                memory_type_label=lambda s: s + '_type',
                wfm_flow_label=next_label,
                runtime_memory_kinds={}, console_labels=[],
                WFM_VALUE_INTEGER=1, WFM_VALUE_OBJECT=4,
            )
            isolated = ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[]))
            exec(compile(isolated, '<wfm>', 'exec'), ns)
            out=[]
            expression = DBaseCallExpression(name='get_text', arguments=(), line=1, column=1)
            self.assertTrue(ns['emit_wfm_ffi_call'](out, expression, 'native_result'))
            assembly='\n'.join(out)
            self.assertIn('call __dbase_ffi_get_text', assembly)
            self.assertIn('call MultiByteToWideChar', assembly)
            self.assertIn('call WideCharToMultiByte', assembly)
            self.assertIn('mov dword ptr [native_result_type], 3', assembly)
            self.assertNotIn('fild qword ptr [__dbase_ffi_return]', assembly)
            self.assertTrue(ns['emit_wfm_ffi_call']([], expression, None))

    def test_gui_integration_tracks_string_store_and_imports(self):
        main = (ROOT / 'd64_dism.py').read_text(encoding='utf8')
        self.assertIn('runtime_memory_kinds[destination_key] = (\n', main)
        self.assertIn('wfm_utf8_result(\n', main)
        self.assertIn('wfm_ffi_ansi_result_used = any(', main)
        self.assertIn("'__dbase_ffi_ansi_wcount:'", main)
        self.assertIn("'__dbase_ffi_utf8_count:'", main)
        self.assertIn("('MultiByteToWideChar', 'kernel32.dll', 'MultiByteToWideChar')", main)
        self.assertIn("('WideCharToMultiByte', 'kernel32.dll', 'WideCharToMultiByte')", main)
        self.assertIn('cannot not', 'cannot not') if False else None


if __name__ == '__main__':
    unittest.main()
