"""Stage 545: DLL ownership, source-free PUI consumers, PE32/PE64 ABI."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from test_stage532 import _compiler
from pascal_library_contract import (write_contract, read_contract,
                                      public_routine_export)

c = _compiler()
p = c.SourcePosition(1, 1)


def _pui(unit='UFoo'):
    klass = {'name': 'TFoo', 'parent': None, 'size': 4, 'methods': [
        {'name': 'Bar', 'symbol': '__pas_method_tfoo_bar',
         'visibility': 'public', 'kind': 'procedure', 'params': []}],
        'fields': [], 'properties': []}
    return {'unit': {'name': unit}, 'exported_classes': ['TFoo'],
            'symbols': {'classes': [klass], 'functions': [
                {'name': 'Answer', 'kind': 'function',
                 'return_type': 'integer', 'params': [],
                 'symbol': '__pas_UFoo_Answer'}], 'procedures': []},
            'imports': {}, 'uses': {'interface': [], 'implementation': []}}


class Stage545Tests(unittest.TestCase):
    def test_export_manifest_per_target(self):
        for target in ('pe32', 'pe64'):
            with self.subTest(target=target), tempfile.TemporaryDirectory() as tmp:
                doc = _pui()
                content = ('export "TFoo_Bar", __pas_method_tfoo_bar\n'
                           'export "D64_UFoo_Answer", __pas_global_answer\n')
                path = write_contract(tmp, 'Runtime', target, {'UFoo': doc}, content)
                self.assertTrue(path.exists())
                data = read_contract(Path(tmp) / 'Runtime.dll', target, (tmp,))
                self.assertEqual(data['units']['ufoo']['classes'], ['TFoo'])
                self.assertEqual(data['units']['ufoo']['routines'],
                                 [{'name': 'Answer', 'export': 'D64_UFoo_Answer'}])
                with self.assertRaisesRegex(ValueError, 'Zielarchitektur'):
                    read_contract(Path(tmp) / 'Runtime.dll', 'pe64' if target == 'pe32' else 'pe32', (tmp,))

    def test_dll_provider_skips_coff_and_implementation(self):
        for target in ('pe32','pe64'):
            with self.subTest(target=target), tempfile.TemporaryDirectory() as tmp:
                directory = Path(tmp)
                doc = _pui()
                write_contract(directory,'Runtime',target,{'UFoo':doc},
                     'export "TFoo_Bar", foo\nexport "D64_UFoo_Answer", answer\n')
                pre = c.PascalPreprocessor()
                pre.link_dlls.append(str(directory / 'Runtime.dll'))
                resolver = c._PascalUnitResolver(
                    filename=str(directory/'test.pas'),
                    include_paths=(directory,), preprocessor=pre,
                    target=target, output_directory=directory)
                with (
                    patch.object(c, '_find_unit_artifacts', return_value=[directory/'UFoo.pui']),
                    patch.object(c, '_find_unit_file', return_value=None),
                    patch.object(c, '_read_pui_document', return_value=doc),
                    patch.object(c, '_pui_validate_target'),
                    patch.object(c, '_pui_is_legacy', return_value=False),
                    patch.object(c, '_pui_uses', return_value=((),())),
                    patch.object(c, '_pui_primary_object_file', return_value=directory/'UFoo.o'),
                    patch.object(c, '_pui_link_object_files', return_value=[str(directory/'UFoo.o')]),
                ):
                    resolver.resolve('UFoo')
                self.assertFalse(resolver.object_files)
                self.assertFalse(resolver.assembly_files)
                self.assertEqual(resolver.class_import_libraries['TFoo'], 'Runtime.dll')
                self.assertFalse(resolver.programs[0].methods)
                self.assertFalse(resolver.programs[0].global_routines)
                self.assertEqual(resolver.external_routines[0].library_reference, 'Runtime.dll')
                self.assertEqual(resolver.external_routines[0].import_name, 'D64_UFoo_Answer')
                program=c.PascalProgram('Client',(),
                  (c.VarDeclaration(('Foo',),'TFoo',None,p),),
                  c.CompoundStatement(p,(c.CallStatement(p,
                    c.DesignatorExpression(p,'Foo',(c.FieldSelector(p,'Bar'),)),()),)),
                  types=resolver.programs[0].types,
                  class_export_contracts=tuple(resolver.class_export_contracts.values()),
                  class_import_libraries=tuple(resolver.class_import_libraries.items()),
                  external_routines=tuple(resolver.external_routines))
                backend=c._PE64CodeGenerator if target=='pe64' else c._PE32CodeGenerator
                asm=backend(program).generate().assembly
                self.assertIn('import __pas_method_tfoo_bar, "Runtime.dll", "TFoo_Bar"',asm)
                self.assertIn('call __pas_method_tfoo_bar',asm)
                self.assertNotIn('__pas_method_tfoo_bar:',asm)

    def test_dll_unit_source_does_not_leak_its_link_objects(self):
        # A unit compiled INTO Runtime.dll can itself contain {$L internal.o}.
        # The consumer must not link internal.o again into its EXE.
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            source=root/'UFoo.pas'
            source.write_text('unit UFoo; interface type {$export TFoo} '
                'TFoo = class end; implementation {$L internal.o} end.',encoding='utf-8')
            doc=_pui()
            write_contract(root,'Runtime','pe32',{'UFoo':doc},
                           'export "TFoo_Bar", foo\nexport "D64_UFoo_Answer", answer\n')
            pre=c.PascalPreprocessor()
            pre.link_dlls.append(str(root/'Runtime.dll'))
            pre.link_files.append(str(root/'main-explicit.o'))
            resolver=c._PascalUnitResolver(filename=str(root/'client.pas'),
                include_paths=(root,),preprocessor=pre,target='pe32',output_directory=root)
            blank=c.PascalProgram('UFoo',(),(),c.CompoundStatement(p,()))
            with (
                patch.object(c,'_find_unit_artifacts',return_value=[root/'UFoo.pui']),
                patch.object(c,'_find_unit_file',return_value=source),
                patch.object(c,'_read_pui_document',return_value=doc),
                patch.object(c,'_pui_validate_target'),
                patch.object(c,'_pui_is_legacy',return_value=False),
                patch.object(c,'_pui_uses',return_value=((),())),
                patch.object(c,'_parse_pascal_program_with_progress',return_value=blank),
                patch.object(c,'_pui_document',return_value=doc),
                patch.object(c,'_write_pui_document'),
                patch.object(c,'_pui_source_matches',return_value=True),
                patch.object(c,'_pui_primary_object_file',return_value=root/'UFoo.o'),
                patch.object(c,'_pui_link_object_files',return_value=[str(root/'UFoo.o')]),
            ):
                resolver.resolve('UFoo')
            self.assertEqual(pre.link_files,[str(root/'main-explicit.o')])
            self.assertNotIn('internal.o',str(resolver.object_files))

    def test_ide_preprocessed_dll_directive_survives_compiler_api(self):
        # The IDE strips {$L ...} before passing source into the compiler.
        # It must supply the resulting DLL list as an explicit argument.
        blank=c.PascalProgram('Client',(),(),c.CompoundStatement(p,()))
        with patch.object(c,'_parse_pascal_program_with_progress',return_value=blank):
            _program, preprocessed=c._parse_pascal_frontend(
                'program Client; begin end.',filename='<unit-test>',
                target='pe32', linked_dll_files=('Runtime.dll',))
        self.assertEqual(tuple(Path(x).name for x in preprocessed.link_dlls),
                         ('Runtime.dll',))

    def test_owned_class_without_export_is_compile_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            doc=_pui()
            doc['exported_classes']=[]
            write_contract(root,'Runtime','pe32',{'UFoo':doc},'export "D64_UFoo_Answer", x\n')
            pre=c.PascalPreprocessor()
            pre.link_dlls.append(str(root/'Runtime.dll'))
            resolver=c._PascalUnitResolver(filename=str(root/'test.pas'),
                  include_paths=(root,),preprocessor=pre,target='pe32',output_directory=root)
            with (
                patch.object(c,'_find_unit_artifacts',return_value=[root/'UFoo.pui']),
                patch.object(c,'_find_unit_file',return_value=None),
                patch.object(c,'_read_pui_document',return_value=doc),
                patch.object(c,'_pui_validate_target'),
                patch.object(c,'_pui_is_legacy',return_value=False),
                patch.object(c,'_pui_uses',return_value=((),())),
            ):
                with self.assertRaisesRegex(c.C64PascalError,'keinen Klassenexport'):
                    resolver.resolve('UFoo')

    def test_library_exports_public_unit_global(self):
        doc=_pui()
        routine=c.GlobalRoutineImplementation('function','Answer',(), 'integer',(),
                  c.CompoundStatement(p,()),p)
        program=c.PascalProgram('Runtime',(),(),c.CompoundStatement(p,()),
                 global_routines=(routine,),
                 library_unit_documents=(('UFoo',doc),))
        for backend in (c._PE32CodeGenerator,c._PE64CodeGenerator):
            with self.subTest(backend=backend.__name__):
                asm=backend(program,library_name='Runtime').generate().assembly
                self.assertIn('export "D64_UFoo_Answer", __pas_global_answer',asm)
                self.assertNotIn('import __pas_global_answer',asm)

    def test_library_contract_is_metadata_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=write_contract(tmp,'Runtime','pe32',{'UFoo':_pui()},
                  'export "TFoo_Bar", foo\n')
            text=path.read_text(encoding='utf-8')
            self.assertNotIn('procedure Bar',text)
            self.assertNotIn('__pas_method_tfoo_bar',text)
            self.assertNotIn('source', json.loads(text))

if __name__=='__main__':
    unittest.main()
