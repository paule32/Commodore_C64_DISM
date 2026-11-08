"""Stage 540: Property access regression for Windows Pascal.

Tests build the Pascal AST directly because this environment provides ANTLR
runtime 4.9.3, whereas the bundled generated parser requires 4.13.2.
"""
import unittest
from test_stage532 import _compiler

c = _compiler()
p = c.SourcePosition(1, 1)

def ident(name):
    return c.DesignatorExpression(p, name)

def field(receiver, name):
    return c.DesignatorExpression(p, receiver, (c.FieldSelector(p, name),))

def assign(target, value):
    return c.AssignmentStatement(p, target, value)


def program_with_properties():
    base = c.TypeDeclaration('TFaz', c.ClassTypeSpecification(p, None,
        (c.FieldDeclaration(('FBase',), 'string', p),), (),
        (c.PropertyDeclaration('InheritedName', 'string', 'FBase', 'FBase', p),)), p)
    getter = c.MethodDeclaration('function', 'GetTitle', (), 'string', p)
    setter = c.MethodDeclaration('procedure', 'SetTitle',
        (c.ParameterDeclaration(('Value',), 'string', 'value', p),), None, p)
    change = c.MethodDeclaration('procedure', 'Change', (), None, p)
    foo = c.TypeDeclaration('TFoo', c.ClassTypeSpecification(p, 'TFaz',
        (c.FieldDeclaration(('FString',), 'string', p),
         c.FieldDeclaration(('FDouble',), 'double', p),
         c.FieldDeclaration(('FName',), 'string', p)),
        (getter,setter,change),
        (c.PropertyDeclaration('OnTest1', 'string', 'FString', 'FString', p),
         c.PropertyDeclaration('OnTest2', 'double', 'FDouble', 'FDouble', p),
         c.PropertyDeclaration('Title', 'string', 'GetTitle', 'SetTitle', p),
         c.PropertyDeclaration('OnTest3', 'string', 'FName', 'FName', p),
         c.PropertyDeclaration('ReadOnly', 'string', 'FString', None, p),
         c.PropertyDeclaration('WriteOnly', 'string', None, 'FString', p),)), p)
    methods = (
        c.MethodImplementation('function','TFoo','GetTitle',(), 'string', (),
            c.CompoundStatement(p,(assign('Result',ident('FString')),)), p),
        c.MethodImplementation('procedure','TFoo','SetTitle',
            (c.ParameterDeclaration(('Value',), 'string', 'value', p),),None,(),
            c.CompoundStatement(p,(assign('FString', ident('Value')),)),p),
        c.MethodImplementation('procedure','TFoo','Change',(),None,(),
            c.CompoundStatement(p,(
                assign('OnTest1', c.LiteralExpression(p, 'Hello')),
                assign('OnTest2', c.LiteralExpression(p, 3.21)),
                assign(field('Self','OnTest3'), c.LiteralExpression(p,'World')),
                c.CallStatement(p, 'writeln', (ident('OnTest1'),)),
            )),p),
    )
    statements = (
        assign(field('Foo', 'OnTest1'), c.LiteralExpression(p, 'Hello')),
        assign(field('Foo', 'OnTest2'), c.LiteralExpression(p, 3.21)),
        assign(field('Foo','InheritedName'), c.LiteralExpression(p, 'Base')),
        assign(field('Foo','OnTest3'), c.LiteralExpression(p,'Name')),
        assign(field('Foo','Title'), c.LiteralExpression(p,'Setter')),
        c.CallStatement(p, 'writeln', (field('Foo','OnTest1'),)),
        c.CallStatement(p, 'writeln', (field('Foo','InheritedName'),)),
        c.CallStatement(p, 'writeln', (field('Foo','Title'),)),
        c.CallStatement(p, 'writeln', (field('Foo','OnTest3'),)),
    )
    return c.PascalProgram('PropertySmoke',(),
        (c.VarDeclaration(('Foo',),'TFoo',None,p),), c.CompoundStatement(p,statements),
        types=(base,foo),methods=methods)

class Stage540PropertyTests(unittest.TestCase):
    def test_field_property_and_accessor_methods_compile_both_architectures(self):
        for backend in (c._PE32CodeGenerator, c._PE64CodeGenerator):
            for optimize in (0,2,3):
                with self.subTest(backend=backend.__name__, optimize=optimize):
                    text = backend(program_with_properties(), optimization_level=optimize,
                                   stack_protector=True).generate().assembly
                    self.assertIn('__pas_method_tfoo_gettitle:', text)
                    self.assertIn('__pas_method_tfoo_settitle:', text)
                    self.assertIn('call __pas_method_tfoo_gettitle', text)
                    self.assertIn('call __pas_method_tfoo_settitle', text)
                    self.assertIn('__pas_cookie_failure:', text)
                    self.assertIn('__pas_string_', text)

    def test_property_metadata_and_backing_alias(self):
        g = c._PE32CodeGenerator(program_with_properties())
        g._prepare() if hasattr(g,'_prepare') else None
        # Codegen initialization is performed by generate(); retained to examine type records.
        g.generate()
        owner = g.types['tfoo']
        self.assertEqual(owner.properties['ontest1'].read_accessor, 'FString')
        self.assertEqual(owner.properties['ontest2'].write_accessor, 'FDouble')
        self.assertIn('inheritedname', owner.properties)
        direct = g._resolve_storage(field('Foo','OnTest1'))
        field_access = g._resolve_storage(field('Foo','FString'))
        self.assertEqual(direct.constant_offset, field_access.constant_offset)
        self.assertEqual(direct.dereference_offsets, field_access.dereference_offsets)

    def test_readonly_and_writeonly(self):
        g = c._PE32CodeGenerator(program_with_properties())
        g.generate()
        with self.assertRaisesRegex(c.C64PascalError, 'schreibgeschützt'):
            g._resolve_storage(field('Foo','ReadOnly'),for_write=True)
        with self.assertRaisesRegex(c.C64PascalError, 'nicht lesbar'):
            g._resolve_storage(field('Foo','WriteOnly'))

    def test_unknown_accessor_reports_property_name(self):
        p0=program_with_properties()
        types=list(p0.types)
        foo = types[1]
        properties=list(foo.specification.properties)
        properties.append(c.PropertyDeclaration('Broken','string','FNoSuchField',None,p))
        types[1]=c.TypeDeclaration(foo.name, c.ClassTypeSpecification(
            p,foo.specification.base_type_name,foo.specification.fields,
            foo.specification.methods,tuple(properties)),p)
        g=c._PE32CodeGenerator(c.PascalProgram(p0.name,p0.constants,p0.variables,
            p0.body,types=tuple(types),methods=p0.methods))
        g.generate()
        with self.assertRaisesRegex(c.C64PascalError, r'Broken.*FNoSuchField'):
            g._resolve_storage(field('Foo','Broken'))

if __name__ == '__main__':
    unittest.main(verbosity=2)
