"""Stage 599: dBASE CLASS TObject OF CUSTOM (declarations, metadata, code generation)."""
from __future__ import annotations

import unittest

from d64dbase import (
    DBaseClassDefinition,
    DBaseClassError,
    DBaseClassRegistry,
    DBaseCompilerError,
    compile_dbase_to_assembly,
    evaluate_dbase_statements,
    parse_dbase_class_metadata,
    parse_dbase_statements,
)


class Stage599CustomClassTests(unittest.TestCase):
    def test_inline_tobject_custom(self):
        definitions = parse_dbase_statements('CLASS TObject of CUSTOM ENDCLASS\n? 123', filename='test.prg')
        self.assertEqual(definitions[0], DBaseClassDefinition('TObject', '', True, 1, 1))
        self.assertEqual(evaluate_dbase_statements(definitions), '123\r\n')

    def test_multiline_tobject_custom_and_derived(self):
        code = '''CLASS TObject OF CUSTOM
ENDCLASS
CLASS TChild OF TObject
ENDCLASS
? "OK"'''
        definitions = parse_dbase_statements(code)
        self.assertEqual([(x.name, x.parent) for x in definitions if isinstance(x, DBaseClassDefinition)],
                         [('TObject', ''), ('TChild', 'TObject')])
        model = parse_dbase_class_metadata(code)
        self.assertFalse(model.get('TObject').builtin)
        self.assertTrue(model.inherits_from('TChild', 'TObject'))
        self.assertEqual(model.get('TObject').parent, '')

    def test_assembly_pe32_and_pe64(self):
        source = 'CLASS TObject OF CUSTOM ENDCLASS\n? "Hallo"'
        for target in ('pe32', 'pe64'):
            with self.subTest(target=target):
                result = compile_dbase_to_assembly(source, filename='System.Objects.prg', target=target)
                self.assertIn('global _start', result.assembly)
                self.assertTrue(any(isinstance(x, DBaseClassDefinition) for x in result.statements))

    def test_macro_expansion(self):
        code = '#define ROOT CUSTOM\nCLASS TObject OF ROOT ENDCLASS\n? 1'
        statements = parse_dbase_statements(code)
        self.assertTrue(statements[0].custom)

    def test_valid_builtin_inheritance_unchanged(self):
        model = parse_dbase_class_metadata('CLASS AppMain OF FORM\nENDCLASS')
        self.assertTrue(model.inherits_from('AppMain', 'TObject'))
        self.assertTrue(model.get('TObject').builtin)

    def test_duplicate_custom_tobject_is_rejected(self):
        code = 'CLASS TObject OF CUSTOM ENDCLASS\nCLASS TObject OF CUSTOM ENDCLASS'
        with self.assertRaisesRegex(DBaseCompilerError, 'bereits definiert'):
            parse_dbase_statements(code)

    def test_missing_endclass_is_rejected(self):
        with self.assertRaisesRegex(DBaseCompilerError, 'ENDCLASS fehlt'):
            parse_dbase_statements('CLASS TObject OF CUSTOM\n')

    def test_stray_endclass_is_rejected(self):
        with self.assertRaisesRegex(DBaseCompilerError, 'ENDCLASS ohne'):
            parse_dbase_statements('ENDCLASS')

    def test_unknown_base_is_rejected(self):
        with self.assertRaisesRegex(DBaseCompilerError, 'Unbekannte Basisklasse'):
            parse_dbase_statements('CLASS Foo OF Something ENDCLASS')

    def test_cycles_are_rejected(self):
        source = 'CLASS A OF B ENDCLASS\nCLASS B OF A ENDCLASS'
        with self.assertRaisesRegex(DBaseCompilerError, 'Zyklische'):
            parse_dbase_statements(source)

    def test_nested_classes_rejected(self):
        code = 'CLASS TObject OF CUSTOM\nCLASS Foo OF TObject ENDCLASS\nENDCLASS'
        with self.assertRaisesRegex(DBaseCompilerError, 'verschachtelt'):
            parse_dbase_statements(code)

    def test_member_codegen_not_silently_discarded(self):
        code = 'CLASS TObject OF CUSTOM\nMETHOD Init\nENDCLASS'
        with self.assertRaisesRegex(DBaseCompilerError, 'Klassenmember'):
            compile_dbase_to_assembly(code)

    def test_comments_do_not_create_classes(self):
        code = '/*\nCLASS TObject OF CUSTOM\nENDCLASS\n*/\n? 2'
        self.assertFalse(any(isinstance(x, DBaseClassDefinition) for x in parse_dbase_statements(code)))

    def test_registry_no_unintended_builtin_override(self):
        reg = DBaseClassRegistry()
        self.assertTrue(reg.get('TObject').builtin)
        with self.assertRaises(DBaseClassError):
            reg.register('TObject', 'FORM')
        self.assertTrue(reg.get('TObject').builtin)
        custom = reg.register('TObject', 'CUSTOM', custom=True)
        self.assertFalse(custom.builtin)
        self.assertEqual(custom.parent, '')


if __name__ == '__main__':
    unittest.main()
