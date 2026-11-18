"""Stage 602 – dBASE CLASS method bodies and NULL literal."""
from pathlib import Path
import re
import unittest

from d64dbase import (compile_dbase_to_assembly, parse_dbase_statements,
                      preprocess_dbase_source, DBaseCompilerError)

ROOT = Path(__file__).parent
SRC = ROOT / 'runtime/dbase/src/System.Objects.prg'


class Stage602SourceMethods(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SRC.read_text(encoding='utf-8')

    def build(self, suffix='', target='pe32', source=None):
        return compile_dbase_to_assembly(source if source is not None else self.source + suffix,
                                         filename=str(SRC), target=target).assembly

    def method_code(self, asm, name):
        start = '__dbase_cls_tobject_' + name.lower() + ':'
        return asm.split(start, 1)[1].split('__dbase_cls_tobject_' + name.lower() + '_source_end:', 1)[0]

    def test_real_dbase_bodies_are_retained(self):
        classes = parse_dbase_statements(self.source, filename=str(SRC))
        tobj = classes[0]
        self.assertEqual(len(tobj.methods), 10)
        for member in ('Free', 'FreeInstance', 'ClassType', 'ClassParent',
                       'ClassNameAddress', 'ClassName', 'InstanceSize', 'InheritsFrom'):
            meth = next(m for m in tobj.methods if m.name == member)
            self.assertTrue(meth.body, member)
            self.assertTrue(any('return' in s.lower() for _,s in meth.body))

    def test_source_ffi_symbols_not_precompiled_wrappers(self):
        for target in ('pe32', 'pe64'):
            with self.subTest(target=target):
                asm = self.build(target=target)
                for name in ('jit_object_free', 'jit_object_instance_free',
                             'jit_object_class_type', 'jit_class_parent',
                             'jit_class_name', 'jit_class_instance_size',
                             'jit_inherits_from_object'):
                    self.assertIn('call __dbase_ffi_' + name, asm)
                self.assertNotIn('jit_dynstring_from_cstr', self.method_code(asm, 'ClassName'))

    def test_source_drives_generated_calls(self):
        # Explicitly prove codegen is driven by the user-supplied body.
        original = self.build()
        modified = self.source.replace('jit_object_free(Self)', 'jit_object_instance_free(Self)')
        asm = self.build(source=modified)
        self.assertIn('call __dbase_ffi_jit_object_free', self.method_code(original, 'Free'))
        self.assertNotIn('call __dbase_ffi_jit_object_free', self.method_code(asm, 'Free'))
        self.assertIn('call __dbase_ffi_jit_object_instance_free', self.method_code(asm, 'Free'))

    def test_null_literal_and_not_nil(self):
        from d64dbase import evaluate_dbase_statements
        result = evaluate_dbase_statements(parse_dbase_statements('STORE NULL TO p\n? p\n'))
        self.assertEqual(result, '0\r\n')
        for target in ('pe32', 'pe64'):
            with self.subTest(target=target):
                asm = self.build('\n? NULL\n', target=target)
                self.assertIn('__dbase_vmt_tobject', asm)
        bad = self.source.replace('Self <> NULL', 'Self <> NIL')
        with self.assertRaisesRegex(DBaseCompilerError, 'NIL'):
            self.build(source=bad)

    def test_x86_cdecl_and_native_pointer_self(self):
        asm = self.build()
        free = self.method_code(asm, 'Free')
        self.assertIn('mov eax, dword ptr [ebp+8]', free)
        self.assertRegex(free, r'call __dbase_ffi_jit_object_free\n\s+add esp, 4')
        size = self.method_code(asm, 'InstanceSize')
        self.assertIn('call __dbase_ffi_jit_object_class_type', size)
        self.assertIn('call __dbase_ffi_jit_class_instance_size', size)
        self.assertNotIn('fild', size)
        inherits = self.method_code(asm, 'InheritsFrom')
        self.assertRegex(inherits, r'call __dbase_ffi_jit_inherits_from_object\n\s+add esp, 8')
        self.assertIn('setne al', inherits)

    def test_win64_self_and_shadow_space(self):
        asm = self.build(target='pe64')
        free = self.method_code(asm, 'Free')
        self.assertIn('mov qword ptr [rbp-8], rcx', free)
        self.assertIn('mov rax, qword ptr [rbp-8]', free)
        self.assertIn('call __dbase_ffi_jit_object_free', free)
        self.assertIn('add rsp, 48', free)
        inherits = self.method_code(asm, 'InheritsFrom')
        self.assertIn('mov rdx, qword ptr [rsp+48]', inherits)
        self.assertIn('add rsp, 56', inherits)
        self.assertNotIn('fild', inherits)

    def test_internal_method_call_receives_self(self):
        for t in ('pe32', 'pe64'):
            asm = self.build(target=t)
            cname = self.method_code(asm, 'ClassName')
            self.assertIn('call __dbase_cls_tobject_classnameaddress', cname)
            self.assertIn('call __dbase_ffi_jit_class_name', self.method_code(asm, 'ClassNameAddress'))

    def test_ffi_unknown_is_compile_error(self):
        text = self.source.replace('jit_object_free(Self)', 'jit_object_typo(Self)')
        with self.assertRaisesRegex(DBaseCompilerError, 'Nicht deklarierte externe Klassenfunktion'):
            self.build(source=text)

    def test_wrong_arity_is_compile_error(self):
        text = self.source.replace('jit_object_free(Self)', 'jit_object_free(Self, Self)')
        with self.assertRaisesRegex(DBaseCompilerError, 'Parameter erwartet'):
            self.build(source=text)

    def test_procedure_must_not_return_value(self):
        text = self.source.replace('jit_object_free(Self)\n        endif\n        return',
                                   'jit_object_free(Self)\n        endif\n        return Self')
        with self.assertRaisesRegex(DBaseCompilerError, 'darf keinen Wert zurueckgeben'):
            self.build(source=text)

    def test_function_must_return_value(self):
        text = self.source.replace('return jit_object_class_type(Self)', 'return')
        with self.assertRaisesRegex(DBaseCompilerError, 'muss einen Wert zurueckgeben'):
            self.build(source=text)

    def test_multiline_nested_ffi_call(self):
        text = self.source.replace('return jit_class_parent(jit_object_class_type(Self))',
                                   'return jit_class_parent(\n            jit_object_class_type(\n                Self\n            )\n        )')
        self.assertIn('call __dbase_ffi_jit_class_parent', self.build(source=text))

    def test_condition_else_codegeneration(self):
        text = self.source.replace('''        if Self <> NULL
            jit_object_free(Self)
        endif''', '''        if Self <> NULL
            jit_object_free(Self)
        else
            jit_object_instance_free(Self)
        endif''')
        asm = self.build(source=text)
        free = self.method_code(asm, 'Free')
        self.assertIn('jmp __dbase_cls_tobject_free_endif', free)
        self.assertIn('call __dbase_ffi_jit_object_instance_free', free)

    def test_dbase_string_result_copied_on_object_call(self):
        for t in ('pe32', 'pe64'):
            asm = self.build('\nobj = new TObject()\n? obj.ClassName()\n', target=t)
            self.assertIn('call __dbase_ffi_lstrlenA', asm)
            self.assertIn('call __dbase_memcpy', asm)
            self.assertIn('call __dbase_cls_tobject_classnameaddress', asm)

    def test_declared_pointer_result_is_not_pascal_dynstring(self):
        self.assertIn('extern PVOID jit_class_name', self.source)
        self.assertNotIn('extern LPCSTR  jit_dynstring_from_cstr', self.source)

    def test_legacy_stage600_stub_remains_supported(self):
        source = '''CLASS TObject OF CUSTOM\nprocedure Free\nreturn\nfunction ClassType\nreturn PVOID\nENDCLASS'''
        asm = self.build(source=source)
        self.assertIn('call __dbase_obj_jit_object_free', asm)
        self.assertIn('__dbase_vmt_tobject:', asm)

    def test_derived_class_keeps_inherited_vmt_slots(self):
        asm = self.build('\nCLASS TChild OF TObject ENDCLASS\nx = new TChild()\nx.Free()\n')
        self.assertIn('dd __dbase_vmt_tobject', asm)
        self.assertIn('call __dbase_ffi_jit_object_free', asm)

    def test_no_custom_class_body_silently_ignored(self):
        source = '''CLASS TObject OF CUSTOM\nprocedure Free\ninvalid_command foo\nreturn\nENDCLASS'''
        with self.assertRaises(DBaseCompilerError):
            self.build(source=source)

    def test_pe32_calling_convention_driven_by_extern(self):
        # STDCALL cleans its own argument stack; no caller ADD is allowed.
        src = self.source.replace(
            'extern       jit_object_free         (PVOID); cdecl;',
            'extern       jit_object_free         (PVOID); stdcall;')
        asm = self.build(source=src)
        free = self.method_code(asm, 'Free')
        self.assertIn('call __dbase_ffi_jit_object_free', free)
        self.assertNotIn('call __dbase_ffi_jit_object_free\n    add esp, 4', free)

    def test_void_external_cannot_be_returned(self):
        src = self.source.replace('return jit_object_class_type(Self)',
                                  'return jit_object_free(Self)')
        with self.assertRaisesRegex(DBaseCompilerError, 'keinen Rueckgabewert'):
            self.build(source=src)

    def test_undeclared_native_identifier_rejected(self):
        src = self.source.replace('jit_object_class_type(Self)',
                                  'jit_object_class_type(UnknownPtr)', 1)
        with self.assertRaisesRegex(DBaseCompilerError, 'UnknownPtr'):
            self.build(source=src)


if __name__ == '__main__':
    unittest.main()
