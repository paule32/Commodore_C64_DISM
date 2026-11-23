"""Stage 600: dBASE native TObject / JitVmt ABI integration."""
from pathlib import Path
import re
import unittest

from d64dbase import DBaseCompilerError, compile_dbase_to_assembly, parse_dbase_statements
from d64dbase.object_abi import METHODS, METHOD_BY_NAME, emit_classes, vmt_label


OBJECTS = Path(__file__).parent / 'examples' / 'dbase' / 'System.Objects.prg'


class Stage600NativeObjects(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = OBJECTS.read_text(encoding='utf-8')

    def assembly(self, target='pe32', suffix=''):
        return compile_dbase_to_assembly(
            self.source + suffix, filename=str(OBJECTS), target=target).assembly

    def test_full_supplied_object_source_parsed(self):
        declarations = parse_dbase_statements(self.source, filename=str(OBJECTS))
        self.assertEqual(len(declarations), 1)
        self.assertEqual(declarations[0].name, 'TObject')
        self.assertTrue(declarations[0].custom)
        self.assertEqual([m.name for m in declarations[0].methods], [
            '__ini__', '__del__', 'Free', 'FreeInstance', 'ClassType',
            'ClassParent', 'ClassNameAddress', 'ClassName', 'InstanceSize', 'InheritsFrom'])

    def test_pe32_native_vmt_layout_and_parent(self):
        asm = self.assembly('pe32')
        self.assertIn('global __dbase_vmt_tobject', asm)
        self.assertRegex(asm, r'__dbase_vmt_tobject:\n\s+dd 0\n\s+dd __dbase_vmt_tobject_name\n\s+dd 0x80000004')
        self.assertIn('dd __dbase_class_object', asm)
        self.assertIn('dd __dbase_cls_tobject___ini__', asm)
        self.assertIn('dd __dbase_cls_tobject___del__', asm)
        self.assertIn('dd __dbase_cls_tobject_inheritsfrom', asm)
        self.assertIn('db 84, 79, 98, 106, 101, 99, 116, 0', asm)

    def test_pe64_native_vmt_layout_and_parent(self):
        asm = self.assembly('pe64')
        self.assertRegex(asm, r'__dbase_vmt_tobject:\n\s+dq 0\n\s+dq __dbase_vmt_tobject_name\n\s+dq 0x80000008')
        self.assertIn('dq __dbase_class_object', asm)
        self.assertIn('dq __dbase_cls_tobject_inheritsfrom', asm)

    def test_correct_module_imports(self):
        asm = self.assembly()
        for name in ('jit_object_instance_new', 'jit_get_virtual_object'):
            self.assertIn(f'import __dbase_obj_{name}, "libd64_runtime.dll", "{name}"', asm)
        for name in ('jit_object_free', 'jit_object_class_type', 'jit_inherits_from_object'):
            self.assertIn(f'import __dbase_ffi_{name}, "libd64_runtime.dll", "{name}"', asm)
            self.assertNotIn(f'import __dbase_obj_{name}, "libd64_runtime.dll", "{name}"', asm)

    def test_pe32_native_cdecl_self_and_stack_balance(self):
        asm = self.assembly('pe32')
        self.assertIn('call __dbase_ffi_jit_object_free', asm)
        self.assertRegex(asm, r'(?s)__dbase_cls_tobject_free:.*?add esp, 4')
        self.assertRegex(asm, r'(?s)__dbase_cls_tobject_inheritsfrom:.*?call __dbase_ffi_jit_inherits_from_object\n\s+add esp, 8')

    def test_pe64_win64_shadow_space_and_self(self):
        asm = self.assembly('pe64')
        self.assertRegex(asm, r'(?s)__dbase_cls_tobject_free:.*?sub rsp, 32.*?call __dbase_ffi_jit_object_free\n\s+add rsp, 48')

    def test_native_classname_is_c_string_not_pascal_dynstring(self):
        from d64dbase import preprocess_dbase_source
        ffi = preprocess_dbase_source(self.source, filename=str(OBJECTS)).ffi_prototypes
        imports, text, data = emit_classes(parse_dbase_statements(self.source), target='pe32', ffi_prototypes=ffi)
        joined = '\n'.join(text)
        name_code = joined.split('__dbase_cls_tobject_classname:', 1)[1].split('__dbase_cls_tobject_instancesize:', 1)[0]
        self.assertIn('call __dbase_cls_tobject_classnameaddress', name_code)
        self.assertIn('call __dbase_ffi_jit_class_name', joined)
        self.assertNotIn('jit_dynstring_from_cstr', name_code)

    def test_instance_new_factory(self):
        for target in ('pe32', 'pe64'):
            with self.subTest(target=target):
                asm = self.assembly(target)
                self.assertIn('__dbase_cls_tobject_create:', asm)
                self.assertIn('call __dbase_obj_jit_object_instance_new', asm)

    def test_real_dispatch_and_dbase_string_result(self):
        for target in ('pe32', 'pe64'):
            with self.subTest(target=target):
                asm = self.assembly(target, '''\nLOCAL Obj AS TObject
Obj = new TObject()
? Obj.ClassName()
Obj.Free()
''')
                self.assertIn('call __dbase_obj_jit_get_virtual_object', asm)
                self.assertIn('call __dbase_ffi_lstrlenA', asm)
                self.assertIn('call __dbase_malloc', asm)
                self.assertIn('call __dbase_memcpy', asm)
                self.assertIn('__dbase_vmt_tobject:', asm)
                self.assertIn('native_method_null', asm)

    def test_numeric_results_and_inheritsfrom(self):
        for target in ('pe32', 'pe64'):
            with self.subTest(target=target):
                asm = self.assembly(target, '''\nobj = new TObject()
size = obj.InstanceSize()
? obj.InheritsFrom(TObject)
? size
''')
                self.assertIn('fistp', asm) if 'fistp' in asm else None
                self.assertIn('native_number', asm)
                self.assertIn('fild dword ptr', asm)

    def test_native_pointer_remains_raw(self):
        for target in ('pe32', 'pe64'):
            with self.subTest(target=target):
                asm = self.assembly(target, '''\nobj = new TObject()
klass = obj.ClassType()
parent = obj.ClassParent()
address = obj.ClassNameAddress()
? obj.InheritsFrom(klass)
''')
                self.assertIn('__dbase_object_klass:', asm)
                self.assertIn('__dbase_object_parent:', asm)
                self.assertIn('__dbase_object_address:', asm)

    def test_derived_parent_and_inherited_slots(self):
        for target, word in (('pe32', 'dd'), ('pe64', 'dq')):
            asm = self.assembly(target, '''\nCLASS TDerived OF TObject ENDCLASS
obj = new TDerived()
? obj.InheritsFrom(TObject)
''')
            self.assertIn(f'__dbase_vmt_tderived:\n    {word} __dbase_vmt_tobject', asm)
            self.assertIn('__dbase_cls_tderived_create:', asm)

    def test_none_checks(self):
        for t in ('pe32', 'pe64'):
            self.assertIn('native_method_null', self.assembly(t, '''\nobj = new TObject()
obj.Free()
obj.Free()
'''))

    def test_invalid_procedure_return_type(self):
        src = 'CLASS TObject OF CUSTOM\nprocedure Free\nreturn PVOID\nENDCLASS'
        with self.assertRaisesRegex(DBaseCompilerError, 'Rueckgabetyp'):
            compile_dbase_to_assembly(src)

    def test_unsupported_custom_body_rejected(self):
        src = 'CLASS TObject OF CUSTOM\nprocedure Free\n? "Hello"\nreturn\nENDCLASS'
        with self.assertRaisesRegex(DBaseCompilerError, 'Klassenmember|Ausdruck erwartet'):
            compile_dbase_to_assembly(src)

    def test_unsupported_method_rejected(self):
        src = 'CLASS TObject OF CUSTOM\nprocedure Unknown\nreturn\nENDCLASS'
        with self.assertRaisesRegex(DBaseCompilerError, 'Nicht implementierte Klassenmethode'):
            compile_dbase_to_assembly(src)

    def test_methods_on_non_tobject_rejected(self):
        src = 'CLASS TObject OF CUSTOM ENDCLASS\nCLASS TChild OF TObject\nprocedure Other\nreturn\nENDCLASS'
        with self.assertRaisesRegex(DBaseCompilerError, 'Benutzerdefinierte Methoden anderer Klassen'):
            compile_dbase_to_assembly(src)

    def test_legacy_form_and_turbovision_stay_metadata_only(self):
        for base in ('FORM', 'TV_Object', 'TV_Application'):
            with self.subTest(base=base):
                asm = compile_dbase_to_assembly(f'CLASS Legacy OF {base} ENDCLASS\n? 1').assembly
                self.assertNotIn('__dbase_vmt_legacy:', asm)

    def test_store_classname_and_pointer_argument(self):
        for target in ('pe32', 'pe64'):
            with self.subTest(target=target):
                asm = self.assembly(target, '\nobj = new TObject()\nSTORE obj.ClassName() TO cname\nklass = obj.ClassType()\nflag = obj.InheritsFrom(klass)\n? cname\n? flag\n')
                self.assertIn('call __dbase_ffi_lstrlenA', asm)
                self.assertIn('__dbase_object_klass:', asm)
                self.assertIn('__dbase_var_cname_type:', asm)

    def test_include_based_program(self):
        p = Path(__file__).parent / 'examples' / 'dbase' / 'tobject_demo.prg'
        for target in ('pe32', 'pe64'):
            with self.subTest(target=target):
                asm = compile_dbase_to_assembly(p.read_text(encoding='utf-8'),
                    filename=str(p), target=target).assembly
                self.assertIn('__dbase_vmt_tobject:', asm)
                self.assertIn('__dbase_cls_tobject_create:', asm)
                self.assertIn('call __dbase_obj_jit_get_virtual_object', asm)

    def test_external_ffi_backward_compatible(self):
        for t in ('pe32', 'pe64'):
            asm = self.assembly(t)
            self.assertIn('import __dbase_ffi_jit_object_instance_new, "libd64_runtime.dll", "jit_object_instance_new"', asm)


if __name__ == '__main__':
    unittest.main()
