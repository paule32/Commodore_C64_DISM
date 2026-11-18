"""Stage 612 – include line stack, guards, native CLASS fields and SUPER."""
from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from d64dbase import DBaseCompilerError, compile_dbase_to_assembly, preprocess_dbase_source
from d64dbase.class_model import parse_dbase_class_metadata
from d64dbase.compiler import parse_dbase_statements, DBaseClassDefinition
from d64dbase.derived_class_abi import field_layout
from pascal_console_dependencies import inspect_pe

HERE = Path(__file__).resolve().parent
SYSUTILS = HERE / 'runtime/dbase/src/System.SysUtils.prg'


class SourceLineStackTests(unittest.TestCase):
    def test_guarded_circular_include_restores_filename_and_line(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'A.prg').write_text(
                '#ifndef A_GUARD\n#define A_GUARD\n#include "B"\n? __FILE__\n? __LINE__\n#endif\n', encoding='utf-8')
            (root / 'B.prg').write_text(
                '#ifndef B_GUARD\n#define B_GUARD\n#include "A"\n? __FILE__\n? __LINE__\n#endif\n', encoding='utf-8')
            path = root / 'A.prg'
            result = preprocess_dbase_source(path.read_text('utf-8'), filename=str(path))
            self.assertEqual(result.preprocessed_source.count('"' + str(path) + '"'), 1)
            self.assertEqual(result.preprocessed_source.count('"' + str(root/'B.prg') + '"'), 1)
            self.assertIn('? 5', result.preprocessed_source)
            self.assertEqual(len(result.source_locations), len(result.preprocessed_source.splitlines()))
            target = next(x for x in result.source_locations if x.filename == str(root / 'B.prg') and x.line == 4)
            self.assertEqual(target.include_chain, ((str(path), 3),))
            self.assertEqual(result.source_locations[-1].filename, str(path))

    def test_unguarded_cycle_still_errors(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'A.prg').write_text('#include "B"\n')
            (root / 'B.prg').write_text('#include "A"\n')
            with self.assertRaisesRegex(DBaseCompilerError, 'Rekursives #include ohne wirksamen Include-Guard'):
                preprocess_dbase_source((root/'A.prg').read_text(), filename=str(root/'A.prg'))

    def test_error_in_include_reports_physical_source(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            inner = root / 'Bad.prg'
            inner.write_text('CLASS Broken OF TObject\nNO_SUCH_PROPERTY FOO\nENDCLASS\n')
            with self.assertRaises(DBaseCompilerError) as raised:
                compile_dbase_to_assembly('#include "Bad"\n', filename=str(root/'Main.prg'),
                                          source_kind='library')
            self.assertEqual(raised.exception.filename, str(inner))
            self.assertEqual(raised.exception.line, 2)
            self.assertIn('Main.prg:1', str(raised.exception))

    def test_no_assembler_markers_for_line_manager(self):
        src = '#include "System.SysUtils.prg"\n'
        result = compile_dbase_to_assembly(src, filename=str(SYSUTILS.parent/'Main.prg'),
                                           source_kind='library')
        self.assertIn('System.SysUtils.prg',
                      {Path(loc.filename).name for loc in result.frontend.source_locations})
        self.assertNotIn('__dbase_include_line_stack', result.assembly)
        self.assertNotIn('push_source_line', result.assembly)


class NativeExceptionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SYSUTILS.read_text('utf-8')

    def test_baseline_class_and_properties_are_parsed(self):
        classes = [x for x in parse_dbase_statements(self.source, filename=str(SYSUTILS))
                   if isinstance(x, DBaseClassDefinition)]
        child = next(x for x in classes if x.name == 'Exception')
        self.assertEqual(child.parent, 'TObject')
        self.assertEqual(child.properties[0].name, 'Message')
        self.assertEqual(child.properties[0].initial_value, '"Error."')
        self.assertEqual(child.properties[0].visibility, 'public')
        ctor = next(x for x in child.methods if x.name == '__ini__')
        self.assertEqual(ctor.parameters, ('AMessage',))
        self.assertTrue(any('super().__ini__(self)' in code.lower() for _, code in ctor.body) is False if False else
                        any('super().__ini__(self)' in code.casefold() for _, code in ctor.body))
        registry = parse_dbase_class_metadata(self.source)
        meta = registry.get('Exception')
        self.assertIn('Message', meta.properties)
        self.assertEqual(meta.property_access, (('Message', 'public'),))

    def test_native_source_and_class_layout_pe32_pe64(self):
        from types import SimpleNamespace
        classes = {c.name.casefold(): c for c in parse_dbase_statements(self.source, filename=str(SYSUTILS))
                   if isinstance(c, DBaseClassDefinition)}
        for target,word, size in (('pe32','dd',12), ('pe64','dq',24)):
            with self.subTest(target=target):
                asm = compile_dbase_to_assembly(self.source, filename=str(SYSUTILS),
                    target=target, source_kind='library').assembly
                self.assertIn('call __dbase_cls_tobject___ini__', asm)
                self.assertIn('call __dbase_cls_concat3', asm)
                self.assertIn('__dbase_cls_exception_fields_init:', asm)
                self.assertIn('__dbase_cls_exception_fields_done:', asm)
                self.assertIn(f'__dbase_vmt_exception:\n    {word} __dbase_vmt_tobject', asm)
                self.assertIn(f'    {word} {size}', asm)
                self.assertIn('export "__dbase_cls_exception_get_message"', asm)
                self.assertIn('export "__dbase_cls_exception_set_message"', asm)
                self.assertIn('call __dbase_cls_exception___ini__', asm)
                self.assertIn('import __dbase_cls_api_LocalAlloc, "kernel32.dll", "LocalAlloc"', asm)

    def test_public_property_access_and_constructor_in_exe(self):
        src = self.source + '\nobj = new Exception("Dateifehler")\n? obj.Message\nobj.Message = "OK"\n? obj.Message\nobj.Free()\n'
        for target in ('pe32','pe64'):
            with self.subTest(target=target):
                assembly = compile_dbase_to_assembly(src, filename=str(SYSUTILS), target=target).assembly
                self.assertIn('call __dbase_cls_exception_create', assembly)
                self.assertIn('call __dbase_cls_exception_get_message', assembly)
                self.assertIn('call __dbase_cls_exception_set_message', assembly)
                self.assertIn('resd 1' if target == 'pe32' else 'resq 1', assembly)

    def test_private_property_hidden_outside_and_inherited_access(self):
        src = '''CLASS TObject OF CUSTOM ENDCLASS
CLASS Parent OF TObject
    PRIVATE PROPERTY Secret = "X"
    PUBLIC PROPERTY Visible = "Y"
ENDCLASS
CLASS Child OF Parent
    function Foo
        return Secret
ENDCLASS
'''
        with self.assertRaisesRegex(DBaseCompilerError, 'PRIVATE PROPERTY'):
            compile_dbase_to_assembly(src, source_kind='library')
        src2 = src.replace('return Secret','return Visible')
        asm = compile_dbase_to_assembly(src2, source_kind='library').assembly
        self.assertNotIn('export "__dbase_cls_parent_get_secret"', asm)
        self.assertIn('export "__dbase_cls_parent_get_visible"', asm)
        for change in ('? obj.Secret', 'obj.Secret = "Q"'):
            with self.subTest(action=change):
                with self.assertRaisesRegex(DBaseCompilerError, 'PRIVATE PROPERTY'):
                    compile_dbase_to_assembly(src2 + '\nobj = new Parent()\n' + change + '\n')

    def test_constructor_arity_and_type_enforced(self):
        for source, expected in ((self.source + '\nobj = new Exception()\n','erwartet 1'),
                                 (self.source + '\nobj = new Exception(4)\n','String')):
            with self.subTest(expected=expected):
                with self.assertRaisesRegex(DBaseCompilerError, expected):
                    compile_dbase_to_assembly(source, filename=str(SYSUTILS))

    def test_actual_pe_dll_and_exe_link_both_architectures(self):
        from test_stage605_link import _load_pe_linker
        link = _load_pe_linker()
        for target,machine in (('pe32',0x14c),('pe64',0x8664)):
            for kind in ('dll','exe'):
                with self.subTest(target=target,kind=kind):
                    source = self.source if kind=='dll' else (
                        self.source+'\nobj = new Exception("H")\n? obj.Message\nobj.Message = "Y"\nobj.Free()\n')
                    asm=compile_dbase_to_assembly(source,filename=str(SYSUTILS),target=target,
                        source_kind='library' if kind=='dll' else 'program').assembly
                    if target=='pe32':
                        obj=link['assemble_pe32_object_source'](asm)
                        coff=link['write_coff32_object'](obj)
                        image=link['link_coff32_objects']((coff,),entry_symbol='__d64_dll_entry' if kind=='dll' else '_start',dll=(kind=='dll'),dll_name='SysUtils.dll')
                    else:
                        obj=link['assemble_pe64_object_source'](asm)
                        coff=link['write_coff64_object'](obj)
                        image=link['link_coff64_objects']((coff,),entry_symbol='__d64_dll_entry' if kind=='dll' else '_start',dll=(kind=='dll'),dll_name='SysUtils.dll')
                    with TemporaryDirectory() as tmp:
                        path=Path(tmp)/('SysUtils.dll' if kind=='dll' else 'SysUtils.exe')
                        path.write_bytes(image.executable)
                        got, imports, exports=inspect_pe(path)
                    self.assertEqual(got,machine)
                    self.assertIn('kernel32.dll',{x.casefold() for x in imports})
                    if kind=='dll':
                        self.assertIn('__dbase_cls_exception_get_message',exports)
                        self.assertIn('__dbase_cls_exception_set_message',exports)


if __name__=='__main__':
    unittest.main()
