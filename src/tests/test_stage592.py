"""Stage 592: dBASE typed external DLL imports with PE32 cdecl/stdcall."""
import re
import unittest
from pathlib import Path

from d64dbase.ffi import extract_ffi_prototypes, ffi_stack_argument_bytes
from d64dbase.compiler import compile_dbase_to_assembly, preprocess_dbase_source

ROOT = Path(__file__).resolve().parent


def assemble(source, target='pe32'):
    return compile_dbase_to_assembly(source, target=target).assembly


class Stage592FFITests(unittest.TestCase):
    def test_default_stdcall_legacy_headers(self):
        source = '''extern CINT old_call(CINT) "user32.dll" from "MessageBoxA"\n'''
        rest, (proto,) = extract_ffi_prototypes(source)
        self.assertEqual(rest, '\n')
        self.assertEqual(proto.calling_convention, 'stdcall')
        self.assertEqual(proto.entry, 'MessageBoxA')

    def test_multiline_cdecl_and_import_name(self):
        source = ('extern PVOID jit_object_instance_new(PVOID) ;\n'
                  '   cdecl ;\n'
                  '   "libd64_runtime.dll" ;\n'
                  '   from "jit_object_instance_new"\n'
                  'result = jit_object_instance_new(0)\n')
        rest, (proto,) = extract_ffi_prototypes(source)
        self.assertEqual(rest.count('\n'), source.count('\n'))
        self.assertEqual(rest.splitlines()[-1], 'result = jit_object_instance_new(0)')
        self.assertEqual(proto.calling_convention, 'cdecl')
        self.assertEqual(proto.argument_types, ('PVOID',))
        self.assertEqual(proto.import_line,
                         'import __dbase_ffi_jit_object_instance_new, "libd64_runtime.dll", "jit_object_instance_new"')

    def test_case_insensitive_explicit_stdcall_and_cdecl(self):
        source = ('ExTeRn CINT fnA(CINT) CDeCl "a.dll" from "fnA"\n'
                  'extern CINT fnB(CINT) STDcall "b.dll" from "fnB"\n')
        _, protos = extract_ffi_prototypes(source)
        self.assertEqual([p.calling_convention for p in protos], ['cdecl', 'stdcall'])

    def test_reject_unimplemented_fastcall(self):
        with self.assertRaisesRegex(ValueError, 'Ungueltige extern'):
            extract_ffi_prototypes('extern CINT fn(CINT) fastcall "a.dll" from "fn"')

    def test_stack_bytes_include_64bit_two_slots(self):
        self.assertEqual(ffi_stack_argument_bytes(('PVOID', 'INT64', 'DWORD', 'UINT64')), 24)
        self.assertEqual(ffi_stack_argument_bytes(()), 0)
        self.assertEqual(ffi_stack_argument_bytes(('PVOID', 'INT64'), target='pe64'), 0)

    def test_pe32_cdecl_pointer_return_caller_cleanup(self):
        source = ('extern PVOID jit_object_instance_new(PVOID) cdecl '
                  '"libd64_runtime.dll" from "jit_object_instance_new"\n'
                  'result = jit_object_instance_new(4096)\n')
        asm = assemble(source)
        self.assertIn('import __dbase_ffi_jit_object_instance_new, "libd64_runtime.dll", "jit_object_instance_new"',asm)
        self.assertRegex(asm, r'call __dbase_ffi_jit_object_instance_new\n    add esp, 4\n    mov dword ptr \[__dbase_ffi_return\], eax')

    def test_pe32_cdecl_64bit_arguments_bytes_correct(self):
        source=('extern CINT sum64(INT64, UINT64, CINT) cdecl "example.dll" from "sum64"\n'
                'value = sum64(12, 14, 99)\n')
        asm=assemble(source)
        self.assertRegex(asm, r'call __dbase_ffi_sum64\n    add esp, 20\n')

    def test_pe32_stdcall_and_legacy_no_cleanup(self):
        for prefix in ('stdcall ', ''):
            with self.subTest(prefix=prefix):
                asm=assemble('extern CINT fn(CINT, PVOID) '+prefix+'"library.dll" from "fn"\n'
                             'result = fn(2, 3)\n')
                part=asm.split('call __dbase_ffi_fn\n',1)[1]
                self.assertFalse(part.startswith('    add esp,'), part[:100])

    def test_pe32_nullary_cdecl_doesnt_overcorrect(self):
        asm=assemble('extern DWORD test() cdecl "library.dll" from "test"\n'
                     'x = test()\n')
        part=asm.split('call __dbase_ffi_test\n',1)[1]
        self.assertFalse(part.startswith('    add esp,'),part[:100])

    def test_pe64_both_conventions_win64_abi(self):
        for convention in ('cdecl','stdcall'):
            with self.subTest(convention=convention):
                asm=assemble('extern PVOID fn(PVOID) '+convention+' "library.dll" from "fn"\n'
                             'result = fn(4096)\n', 'pe64')
                self.assertRegex(asm, r'call __dbase_ffi_fn\n    add rsp, 40\n')
                self.assertNotIn('add esp,', asm)

    def test_legacy_shellapi_header_retains_default_stdcall(self):
        header = (ROOT/'examples/dbase/shellapi32.h').read_text(encoding='utf-8')
        declarations = preprocess_dbase_source(header, filename=str(ROOT/'examples/dbase/shellapi32.h')).ffi_prototypes
        self.assertGreater(len(declarations), 2)
        self.assertTrue(all(d.calling_convention=='stdcall' for d in declarations))

    def test_wfm_path_respects_ffi_calling_convention(self):
        source=(ROOT/'d64_dism.py').read_text(encoding='utf-8')
        block=source.split('            def emit_wfm_ffi_call(',1)[1].split('            def emit_wfm_condition_true(',1)[0]
        self.assertIn("if ffi.calling_convention == 'cdecl':",block)
        self.assertIn('ffi_stack_argument_bytes(ffi.argument_types',block)
        self.assertIn("out.append(f'    add esp, {cleanup}')",block)
        self.assertIn("f'    add rsp, {size}'",block)


if __name__=='__main__':
    unittest.main()
