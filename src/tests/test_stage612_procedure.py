"""Stage 612 SET PROCEDURE source loading: include paths and Windows share contracts."""
from __future__ import annotations

import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from d64dbase import DBaseCompilerError, compile_dbase_to_assembly, preprocess_dbase_source
from d64dbase.procedure_files import (DBaseProcedureFileManager, windows_share_mode,
    FILE_SHARE_READ, FILE_SHARE_WRITE, FILE_SHARE_DELETE)

ROOT = Path(__file__).resolve().parent
SYSTEM_SRC = ROOT / 'runtime/dbase/src'


class SetProcedureTests(unittest.TestCase):
    def test_exclusive_includes_class_from_input_path_no_assembly_instruction(self):
        with TemporaryDirectory() as temp:
            path = Path(temp)
            lib = path/'library'
            lib.mkdir()
            (lib/'Obj.prg').write_text('#ifndef OBJ_GUARD\n#define OBJ_GUARD\n'
                                       'CLASS TObject OF CUSTOM ENDCLASS\n#endif\n', encoding='utf-8')
            source = 'SET PROCEDURE "Obj" EXCLUSIVE\n'
            front = preprocess_dbase_source(source, filename=str(path/'Main.prg'), include_paths=(lib,))
            self.assertIn('CLASS TObject OF CUSTOM ENDCLASS', front.preprocessed_source)
            self.assertIn(str(lib/'Obj.prg'), {loc.filename for loc in front.source_locations})
            self.assertEqual(front.source_locations[1].include_chain, ((str(path/'Main.prg'), 1),))
            built = compile_dbase_to_assembly(source, filename=str(path/'Main.prg'),
                include_paths=(lib,), source_kind='library')
            self.assertIn('__dbase_vmt_tobject', built.assembly)
            self.assertNotIn('SET PROCEDURE', built.assembly)

    def test_additive_file_and_nested_include_with_extension_fallback(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            (root/'B.prg').write_text('#ifndef B_GUARD\n#define B_GUARD\n? __FILE__\n#endif\n')
            (root/'A.prg').write_text('#ifndef A_GUARD\n#define A_GUARD\n'
                                      '#include "B"\n? __LINE__\n#endif\n')
            front = preprocess_dbase_source('SET PROCEDURE "A" ADDITIVE\n',
                filename=str(root/'Main.prg'))
            self.assertIn(str(root/'B.prg'), front.preprocessed_source)
            self.assertIn('? 4',front.preprocessed_source)
            self.assertEqual(len(front.source_locations),len(front.preprocessed_source.splitlines()))
            target = next(loc for loc in front.source_locations if loc.filename == str(root/'B.prg') and loc.line == 3)
            self.assertEqual(target.include_chain, ((str(root/'Main.prg'),1), (str(root/'A.prg'),3)))

    def test_guards_skip_recursive_set_procedure_and_include(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            (root/'A.prg').write_text('#ifndef A\n#define A\nSET PROCEDURE "B" EXCLUSIVE\n? 1\n#endif\n')
            (root/'B.prg').write_text('#ifndef B\n#define B\n#include "A"\n? 2\n#endif\n')
            front = preprocess_dbase_source('SET PROCEDURE "A" ADDITIVE\n',
                filename=str(root/'Main.prg'))
            self.assertEqual(front.preprocessed_source.count('? 1'),1)
            self.assertEqual(front.preprocessed_source.count('? 2'),1)

    def test_same_source_can_be_loaded_by_both_without_duplicate_definitions(self):
        source = ('SET PROCEDURE "System.Objects" ADDITIVE\n'
                  'SET PROCEDURE "System.SysUtils.prg" EXCLUSIVE\n')
        for target in ('pe32', 'pe64'):
            with self.subTest(target=target):
                result = compile_dbase_to_assembly(source,
                    filename=str(SYSTEM_SRC/'Main.prg'), source_kind='library',target=target,
                    include_paths=(SYSTEM_SRC,))
                self.assertEqual(result.assembly.count('__dbase_cls_exception_create:'), 1)
                self.assertEqual(result.assembly.count('__dbase_cls_tobject_free:'), 1)
                self.assertEqual(result.assembly.count('__dbase_vmt_tobject:'), 1)

    def test_guarded_duplicate_avoids_conflicting_share_mode(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            (root/'x.prg').write_text('#ifndef X_PRG\n#define X_PRG\n? 5\n#endif\n')
            result = preprocess_dbase_source(
                'SET PROCEDURE "x" ADDITIVE\nSET PROCEDURE "x" EXCLUSIVE\n',
                filename=str(root/'main.prg'))
            self.assertEqual(result.preprocessed_source.count('? 5'), 1)

    def test_set_procedure_error_maps_to_original_file(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            (root/'wrong.prg').write_text('CLASS Broken OF TObject\nBAD_STMT no\nENDCLASS\n')
            with self.assertRaises(DBaseCompilerError) as raised:
                compile_dbase_to_assembly('SET PROCEDURE "wrong" EXCLUSIVE\n',
                    filename=str(root/'Main.prg'),source_kind='library')
            self.assertEqual(raised.exception.filename,str(root/'wrong.prg'))
            self.assertEqual(raised.exception.line,2)
            self.assertIn('Main.prg:1',str(raised.exception))

    def test_share_modes_and_handle_cleanup(self):
        self.assertEqual(windows_share_mode('exclusive'), 0)
        self.assertEqual(windows_share_mode('ADDITIVE'),
                         FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE)
        with self.assertRaises(ValueError):
            windows_share_mode('invalid')
        with TemporaryDirectory() as temp:
            path = Path(temp)/'One.prg'
            path.write_text('? 1\n')
            manager = DBaseProcedureFileManager()
            with manager:
                self.assertEqual(manager.read(path,mode='exclusive'),b'? 1\n')
                self.assertEqual(manager.read(path,mode='include'),b'? 1\n')
                with self.assertRaises(OSError):
                    manager.read(path,mode='additive')
            self.assertTrue(manager._closed)
            with self.assertRaises(RuntimeError):
                manager.read(path,mode='exclusive')

    def test_disabled_directive_ignored_and_invalid_mode_rejected(self):
        front = preprocess_dbase_source('#if 0\nSET PROCEDURE "no-file" EXCLUSIVE\n#endif\n? 1\n')
        self.assertIn('? 1',front.preprocessed_source)
        with self.assertRaisesRegex(DBaseCompilerError,'SET PROCEDURE erwartet'):
            preprocess_dbase_source('SET PROCEDURE "one.prg" LOCKED\n')
        with TemporaryDirectory() as temp:
            root=Path(temp)
            with self.assertRaises(DBaseCompilerError) as raised:
                preprocess_dbase_source('SET PROCEDURE "missing" ADDITIVE\n',
                    filename=str(root/'Main.prg'),include_paths=(root/'inputs',))
            self.assertIn(str(root/'inputs'/'missing.prg'),str(raised.exception))

    def test_include_and_set_procedure_both_use_configured_paths(self):
        with TemporaryDirectory() as temp:
            root=Path(temp)
            lib=root/'include'; lib.mkdir()
            (lib/'proc.prg').write_text('? 111\n')
            (lib/'inc.prg').write_text('? 222\n')
            result=preprocess_dbase_source('SET PROCEDURE "proc.prg" ADDITIVE\n#include "inc.prg"\n',
                filename=str(root/'Main.prg'),include_paths=(lib,))
            self.assertIn('? 111',result.preprocessed_source)
            self.assertIn('? 222',result.preprocessed_source)

    @unittest.skipUnless(os.name == 'nt','Real CreateFileW sharing semantics require Windows')
    def test_actual_win32_share_contract(self):
        import ctypes
        from ctypes import wintypes
        k32=ctypes.WinDLL('kernel32',use_last_error=True)
        create=k32.CreateFileW
        create.argtypes=(wintypes.LPCWSTR,wintypes.DWORD,wintypes.DWORD,wintypes.LPVOID,
                         wintypes.DWORD,wintypes.DWORD,wintypes.HANDLE)
        create.restype=wintypes.HANDLE
        close=k32.CloseHandle; close.argtypes=(wintypes.HANDLE,); close.restype=wintypes.BOOL
        invalid=ctypes.c_void_p(-1).value
        with TemporaryDirectory() as temp:
            path=Path(temp)/'case.prg';path.write_text('? 1\n')
            for mode,possible in (('exclusive',False),('additive',True)):
                with self.subTest(mode=mode):
                    with DBaseProcedureFileManager() as manager:
                        manager.read(path,mode=mode)
                        second=create(str(path),0x40000000,FILE_SHARE_READ|FILE_SHARE_WRITE,
                                      None,3,0x80,None)
                        if possible:
                            self.assertNotEqual(second,invalid)
                            close(second)
                        else:
                            self.assertEqual(second,invalid)


if __name__ == '__main__':
    unittest.main()
