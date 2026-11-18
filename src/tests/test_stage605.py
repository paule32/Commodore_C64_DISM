"""Stage 605: dBASE RuntimeDB project emits a real class-library DLL path."""
from pathlib import Path
import re
import unittest

from d64dbase import compile_dbase_to_assembly, DBaseCompilerError
from d64dbase.dll_backend import compile_dbase_class_library

ROOT = Path(__file__).resolve().parent
OBJECTS = ROOT / 'runtime/dbase/src/System.Objects.prg'


class DBaseDllTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = OBJECTS.read_text(encoding='utf-8')

    def test_class_library_is_dll_not_program(self):
        for target, bits, dll_return in [('pe32','32','ret 12'), ('pe64','64','ret')]:
            with self.subTest(target=target):
                result = compile_dbase_to_assembly(
                    self.source, filename=str(OBJECTS), target=target,
                    source_kind='library')
                asm = result.assembly
                self.assertEqual(result.source_kind, 'library')
                self.assertIn(f'bits {bits}', asm)
                self.assertIn('__d64_dll_entry:\n    mov eax, 1\n    '+dll_return, asm)
                self.assertIn('entry __d64_dll_entry', asm)
                self.assertNotIn('entry _start', asm)
                self.assertNotIn('\n_start:', asm)
                self.assertNotIn('DBaseQtRuntimeStartup', asm)
                self.assertNotIn('ExitProcess', asm)
                self.assertIn('section .text', asm)
                self.assertIn('section .data', asm)
                self.assertIn('section .bss', asm)

    def test_vmt_methods_and_runtime_ffi_exports(self):
        for target in ('pe32','pe64'):
            with self.subTest(target=target):
                asm = compile_dbase_class_library(self.source, filename=str(OBJECTS), target=target).assembly
                self.assertIn('export "__dbase_cls_tobject_vmt", __dbase_cls_tobject_vmt', asm)
                self.assertIn('__dbase_cls_tobject_vmt:', asm)
                self.assertNotIn('export "__dbase_vmt_tobject",', asm)
                self.assertIn('export "__dbase_cls_tobject_create", __dbase_cls_tobject_create', asm)
                self.assertIn('export "__dbase_cls_tobject_free", __dbase_cls_tobject_free', asm)
                for symbol in ('jit_object_free','jit_class_parent','jit_class_name',
                               'jit_class_instance_size','jit_inherits_from_object'):
                    self.assertIn('call __dbase_ffi_'+symbol, asm)
                self.assertIn('call __dbase_obj_jit_object_instance_new', asm)
                self.assertIn('section .data\n\n;', asm)
                self.assertIn('__dbase_vmt_tobject:', asm)

    def test_project_compile_passes_explicit_library_mode(self):
        gui = (ROOT / 'd64_dism.py').read_text('utf-8')
        begin = gui.index('        def _compile_dbase_document(')
        end = gui.index('        def _compile_logo_document(', begin)
        compile_block = gui[begin:end]
        self.assertIn('_project_named_current_scope()', compile_block)
        self.assertIn('_project_named_matches_path(', compile_block)
        self.assertIn('source_kind="library" if _dbase_library else "program"', compile_block)
        self.assertIn('target=document.build_target', compile_block)
        self.assertIn('generated = compile_dbase_to_assembly(', compile_block)
        self.assertIn('generated_source_kind', gui)
        link_begin = gui.index('        def assemble_generated_document(')
        link_end = gui.index('        def ', link_begin + 10)
        link_block = gui[link_begin:link_end]
        self.assertIn('is_library = source_kind == "library"', link_block)
        self.assertIn('entry_symbol = "__d64_dll_entry"', link_block)
        self.assertIn('dll=is_library', link_block)

    def test_program_remains_program(self):
        for target in ('pe32', 'pe64'):
            with self.subTest(target=target):
                result = compile_dbase_to_assembly(
                    '? "EXE"', target=target, source_kind='program')
                self.assertEqual(result.source_kind, 'program')
                self.assertIn('entry _start', result.assembly)
                self.assertIn('DBaseQtRuntimeStartup', result.assembly)

    def test_invalid_module_content_reports_precise_error(self):
        with self.assertRaisesRegex(DBaseCompilerError, 'außerhalb von CLASS'):
            compile_dbase_to_assembly(self.source + '\n? "hallo"', source_kind='library')
        with self.assertRaisesRegex(DBaseCompilerError, 'Keine native CLASS-Deklaration'):
            compile_dbase_to_assembly('? "Hallo"', source_kind='library')
        with self.assertRaisesRegex(DBaseCompilerError, 'PE32/PE64'):
            compile_dbase_to_assembly(self.source, target='linux64', source_kind='library')
        with self.assertRaisesRegex(DBaseCompilerError, 'Unbekannte dBASE-Quellart'):
            compile_dbase_to_assembly(self.source, source_kind='unknown')


if __name__ == '__main__':
    unittest.main()
