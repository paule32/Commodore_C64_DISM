"""Stage 542: isolated ABI/metadata/assembler tests (no Windows runtime needed)."""
from __future__ import annotations
import unittest
from pathlib import Path
from test_stage532 import _compiler
from pascal_class_exports import exported_classes, export_name, bridge_symbol
from pascal_import_manager import externalize_declarations

c = _compiler()
p = c.SourcePosition(1,1)

def cls_contract():
    return {'name':'TFoo','parent':'TObject','size':8, 'dll_export':True,
      'methods':[{'name':'Bar','kind':'procedure','visibility':'public',
                  'dll_export_name':'TFoo_Bar','dll_bridge_symbol':bridge_symbol('TFoo','Bar'),
                  'symbol':'__pas_method_tfoo_bar','params':[], 'return_type':None}],
      'fields':[{'name':'FValue','type':'integer','offset':4,'visibility':'protected',
                 'dll_get_export':'TFoo_get_FValue','dll_set_export':'TFoo_set_FValue'}],
      'properties':[{'name':'Value','type':'integer','read':'FValue','write':'FValue','visibility':'public'}]}

def unit_program(*, imported=False, library=None):
    method = c.MethodDeclaration('procedure','Bar',(),None,p,visibility='public',
             external_symbol='__pas_method_tfoo_bar' if imported else None)
    root = c.TypeDeclaration('TObject', c.ClassTypeSpecification(p,None,(),()),p)
    klass = c.TypeDeclaration('TFoo', c.ClassTypeSpecification(p,'TObject',
        (c.FieldDeclaration(('FValue',),'integer',p,'protected',4),),
        (method,), (c.PropertyDeclaration('Value','integer','FValue','FValue',p),),8), p)
    if imported:
        methods=()
    else:
        methods=(c.MethodImplementation('procedure','TFoo','Bar',(),None,(), c.CompoundStatement(p,()),p),)
    result=c.PascalProgram('Smoke',(),(),c.CompoundStatement(p,()),types=(root,klass),
        methods=methods, class_export_contracts=(cls_contract(),),
        class_import_libraries=(('TFoo','libfoo.dll'),) if imported else ())
    return result

class Stage542Tests(unittest.TestCase):
    def test_export_marker_selects_next_class(self):
        source='type\n{$export TFoo}\n TFoo = class\n end;\n TOther = class end;\n'
        mask=c._pascal_code_mask(source)
        self.assertEqual(exported_classes(source,mask),('TFoo',))
        with self.assertRaisesRegex(ValueError,'nächsten'):
            exported_classes(source.replace('export TFoo','export Wrong'),mask)
        self.assertEqual(export_name('TFoo','Bar'),'TFoo_Bar')

    def test_preprocessor_preserves_export_and_parses_dll_link(self):
        pre=c.PascalPreprocessor()
        processed=pre.process('{$export TFoo}\n{$L libfoo}\n',filename='abc.pas')
        self.assertIn('{$export TFoo}',processed.source)
        self.assertEqual(Path(processed.link_dlls[0]).name,'libfoo.dll')
        self.assertEqual(processed.link_files,())
        # Disabled directives must not escape the conditional preprocessor.
        inactive=c.PascalPreprocessor().process('{$ifdef NOPE}{$L no.dll}{$export Fail}{$endif}')
        self.assertNotIn('no.dll',str(inactive.link_dlls))
        self.assertNotIn('{$export Fail}', inactive.source)

    def test_exported_unit_has_bridges_and_property_alias(self):
        for backend in (c._PE32CodeGenerator,c._PE64CodeGenerator):
            with self.subTest(backend=backend.__name__):
                asm=backend(unit_program(),unit_name='VCL.Windows').generate().assembly
                self.assertIn('__d64_cls_tfoo_method_bar:',asm) if backend==c._PE32CodeGenerator else None
                self.assertIn('global __d64_cls_tfoo_get_fvalue',asm)
                self.assertIn('__d64_cls_tfoo_set_fvalue:',asm)
                self.assertIn('global __pas_method_tfoo_bar',asm)
                self.assertNotIn('export "TFoo_Bar",',asm)

    def test_library_emits_class_exports(self):
        for backend in (c._PE32CodeGenerator,c._PE64CodeGenerator):
            with self.subTest(backend=backend.__name__):
                asm=backend(unit_program(imported=True, library='libfoo'),library_name='libfoo').generate().assembly
                self.assertIn('dllname "libfoo.dll"',asm)
                self.assertIn('export "TFoo_Bar",',asm)
                self.assertIn('export "TFoo_get_Value", __d64_cls_tfoo_get_fvalue',asm)
                self.assertIn('export "TFoo_set_FValue", __d64_cls_tfoo_set_fvalue',asm)

    def test_client_uses_dll_and_no_local_method_body(self):
        base=unit_program(imported=True)
        body=c.CompoundStatement(p,(c.CallStatement(p,c.DesignatorExpression(p,'Foo',(c.FieldSelector(p,'Bar'),)),()),))
        program=c.replace(base,variables=(c.VarDeclaration(('Foo',),'TFoo',None,p),),body=body)
        for backend in (c._PE32CodeGenerator,c._PE64CodeGenerator):
            with self.subTest(backend=backend.__name__):
                asm=backend(program).generate().assembly
                self.assertIn('import __pas_method_tfoo_bar, "libfoo.dll", "TFoo_Bar"',asm)
                self.assertNotIn('__pas_method_tfoo_bar:',asm)
                self.assertIn('call __pas_method_tfoo_bar',asm)
                if backend==c._PE32CodeGenerator:
                    self.assertIn('    push esi\n    call __pas_method_tfoo_bar\n    add esp, 4',asm)

    def test_no_comment_in_include_externalization(self):
        src='extern X\nimport F, "x.dll", "F"\ncall F\n'
        asm,_,_=externalize_declarations(src,Path('/tmp/check.generated.asm'))
        self.assertNotIn('Stage 541: Import in .imports.inc',asm)
        self.assertIn('%include "check.generated.asm.imports.inc"',asm)

    def test_imported_property_and_field_use_dll_bridges(self):
        prop = lambda name: c.DesignatorExpression(p, 'Foo', (c.FieldSelector(p,name),))
        actions = (
            c.AssignmentStatement(p, prop('Value'), c.LiteralExpression(p,42)),
            c.CallStatement(p, 'writeln', (prop('Value'),)),
            c.AssignmentStatement(p, prop('FValue'), c.LiteralExpression(p,9)),
            c.CallStatement(p, 'writeln', (prop('FValue'),)),
        )
        source = c.replace(unit_program(imported=True),
            variables=(c.VarDeclaration(('Foo',),'TFoo',None,p),),
            body=c.CompoundStatement(p, actions))
        for backend in (c._PE32CodeGenerator, c._PE64CodeGenerator):
            with self.subTest(backend=backend.__name__):
                asm=backend(source).generate().assembly
                for field in ('value','fvalue'):
                    for operation in ('get','set'):
                        symbol=f'__d64_cls_tfoo_{operation}_{field}'
                        self.assertIn('call '+symbol,asm)
                        self.assertIn('import '+symbol+', "libfoo.dll",',asm)

    def test_constructor_factory_export_and_import(self):
        param=c.ParameterDeclaration(('Value',),'integer','value',p)
        method=c.MethodDeclaration('constructor','Create',(param,),None,p,
                                   visibility='public')
        external=c.replace(method,external_symbol='__pas_method_tfoo_create')
        base=c.TypeDeclaration('TObject',c.ClassTypeSpecification(p,None,(),()),p)
        factory_class=lambda m: c.TypeDeclaration('TFoo',c.ClassTypeSpecification(
            p,'TObject',(),(m,),(),8),p)
        contract={'name':'TFoo','parent':'TObject','size':8,
                  'methods':[{'name':'Create','kind':'constructor',
                              'visibility':'public','symbol':'__pas_method_tfoo_create',
                              'params':[{'name':'Value','type':'integer'}]}],
                  'fields':[],'properties':[]}
        impl=c.MethodImplementation('constructor','TFoo','Create',(param,),None,(),
                   c.CompoundStatement(p,()),p)
        owner=c.PascalProgram('FooUnit',(),(),c.CompoundStatement(p,()),
            types=(base,factory_class(method)),methods=(impl,),
            class_export_contracts=(contract,),class_export_owners=('tfoo',))
        factory=c.CallExpression(p,c.DesignatorExpression(p,'TFoo',
                  (c.FieldSelector(p,'Create'),)),(c.LiteralExpression(p,42),))
        client=c.PascalProgram('User',(),(c.VarDeclaration(('Foo',),'TFoo',None,p),),
            c.CompoundStatement(p,(c.AssignmentStatement(p,'Foo',factory),)),
            types=(base,factory_class(external)),
            class_export_contracts=(contract,),
            class_import_libraries=(('TFoo','libfoo.dll'),))
        self.assertEqual(export_name('TFoo','Create','new'),'TFoo_new_Create')
        for backend in (c._PE32CodeGenerator,c._PE64CodeGenerator):
            with self.subTest(backend=backend.__name__):
                own=backend(owner,unit_name='FooUnit').generate().assembly
                self.assertIn('__d64_cls_tfoo_new_create:',own)
                self.assertIn('call __pas_method_tfoo_create',own)
                dll=backend(c.replace(client,body=c.CompoundStatement(p,()),
                            class_import_libraries=()),library_name='libfoo').generate().assembly
                self.assertIn('export "TFoo_new_Create",',dll)
                app=backend(client).generate().assembly
                self.assertIn('import __d64_cls_tfoo_new_create, "libfoo.dll", "TFoo_new_Create"',app)
                self.assertIn('call __d64_cls_tfoo_new_create',app)

    def test_pui_exported_class_metadata(self):
        from unittest.mock import patch
        foo = c.TypeDeclaration('TFoo', c.ClassTypeSpecification(
            p,None,
            (c.FieldDeclaration(('FValue',),'integer',p,'private',4),
             c.FieldDeclaration(('FVisible',),'integer',p,'protected',8)),
            (c.MethodDeclaration('procedure','Bar',(),None,p,visibility='public'),),
            (c.PropertyDeclaration('Value','integer','FValue','FValue',p,
                                   visibility='published'),),12),p)
        ast=c.PascalProgram('__pui_Foo',(),(),c.CompoundStatement(p,()),types=(foo,))
        text='unit Foo; interface type {$export TFoo} TFoo = class end; implementation end.'
        with patch.object(c,'_parse_pascal_program',return_value=ast):
            doc=c._pui_document(unit_name='Foo',interface_source=text,
                interface_units=(), source_path=None,target='pe32')
        self.assertEqual(doc['exported_classes'],['TFoo'])
        self.assertEqual(doc['class_export_abi'],1)
        raw=doc['symbols']['classes'][0]
        self.assertTrue(raw['dll_export'])
        self.assertEqual(raw['methods'][0]['dll_export_name'],'TFoo_Bar')
        self.assertEqual(raw['fields'][0]['visibility'],'private')
        self.assertNotIn('dll_get_export',raw['fields'][0])
        self.assertEqual(raw['fields'][1]['dll_get_export'],'TFoo_get_FVisible')
        self.assertEqual(raw['properties'][0]['dll_get_export'],'TFoo_get_Value')
        self.assertNotIn('unit Foo',str(doc))

    def test_pe_export_validation_dll_machine_and_missing_symbol(self):
        import struct, tempfile
        from pascal_class_exports import _pe_exports, validate_class_dll_references
        def dll_image(names, machine):
            is_64=machine==0x8664
            b=bytearray(0x1000)
            b[:2]=b'MZ'
            struct.pack_into('<I',b,0x3C,0x80)
            b[0x80:0x84]=b'PE\0\0'
            opt_size=0xF0 if is_64 else 0xE0
            struct.pack_into('<HHIIIHH',b,0x84,machine,1,0,0,0,opt_size,0x2002)
            opt=0x98
            struct.pack_into('<H',b,opt,0x20B if is_64 else 0x10B)
            struct.pack_into('<I',b,opt+60,0x200)
            struct.pack_into('<II',b,opt+(112 if is_64 else 96),0x1000,0x300)
            sec=opt+opt_size
            b[sec:sec+8]=b'.edata\0\0'
            struct.pack_into('<IIII',b,sec+8,0x600,0x1000,0x600,0x200)
            struct.pack_into('<I',b,0x200+24,len(names))
            struct.pack_into('<I',b,0x200+32,0x1080)
            cursor=0x300
            for i,name in enumerate(names):
                encoded=name.encode('ascii')+b'\0'
                struct.pack_into('<I',b,0x280+i*4,0x1000+cursor-0x200)
                b[cursor:cursor+len(encoded)]=encoded
                cursor+=len(encoded)
            return bytes(b)
        names=['TFoo_Bar','TFoo_get_FValue','TFoo_set_FValue',
               'TFoo_get_Value','TFoo_set_Value']
        for machine,target in ((0x14c,'pe32'),(0x8664,'pe64')):
            with self.subTest(target=target), tempfile.TemporaryDirectory() as directory:
                file=Path(directory)/'libfoo.dll'
                file.write_bytes(dll_image(names,machine))
                self.assertEqual(set(_pe_exports(file.read_bytes(),target)),set(names))
                location=validate_class_dll_references((str(file),),(cls_contract(),),
                    target=target,filename=str(file))
                self.assertEqual(location,(str(file.resolve()),))
                with self.assertRaisesRegex(ValueError,'fehlen'):
                    validate_class_dll_references((str(file),),
                        ({**cls_contract(),'methods':[{**cls_contract()['methods'][0],
                          'name':'Missing','dll_export_name':'TFoo_Missing'}]},),target=target,filename=str(file))
                with self.assertRaisesRegex(ValueError,'Architektur'):
                    validate_class_dll_references((str(file),),(cls_contract(),),
                        target='pe64' if target=='pe32' else 'pe32',filename=str(file))

if __name__=='__main__': unittest.main(verbosity=2)
