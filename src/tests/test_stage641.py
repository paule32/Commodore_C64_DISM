"""Stage 641 – managed OOP exceptions across native dBL CLASS methods.

These verify parser placement, PE32/PE64 code generation and COFF encoding;
no native Windows runtime execution or OS-level SEH is implied.
"""
import re
import unittest
from d64dbase.compiler import (compile_dbase_to_assembly, parse_dbase_statements,
                               DBaseCompilerError, DBaseNativeClassCallStatement,
                               DBaseTryStatement)
from test_stage605_link import _load_pe_linker

SOURCE = '''#include "System.SysUtils"
CLASS ECustom OF DbException
ENDCLASS
CLASS TWorker OF TObject
    PUBLIC PROPERTY Info = "initial"
    PROCEDURE Fail(reason)
        THROW NEW ECustom(reason)
        RETURN
    PROCEDURE Run()
        TRY
            self.Fail("from method")
        CATCH (Exception e)
            ? e.ClassName
            ? e.Message
            THROW e
        FINALLY
            ? "inner finally"
        ENDTRY
        RETURN
ENDCLASS
LOCAL worker AS TWorker
worker = NEW TWorker()
TRY
    worker.Run()
CATCH (DbException caught)
    ? caught.Message
FINALLY
    ? "outer finally"
ENDTRY
'''

def compile_src(src, target):
    return compile_dbase_to_assembly(src, target=target,
        filename='runtime/dbase/src/stage641.prg',
        include_paths=['runtime/dbase/src']).assembly


class TestStage641NativeMethodExceptions(unittest.TestCase):
    def test_native_method_call_kept_inside_try(self):
        parsed = parse_dbase_statements(SOURCE, filename='runtime/dbase/src/stage641.prg')
        outer = next(s for s in parsed if isinstance(s,DBaseTryStatement))
        self.assertEqual(len(outer.try_body),1)
        self.assertIsInstance(outer.try_body[0],DBaseNativeClassCallStatement)

    def test_compiles_both_targets_and_resolves_all_calls(self):
        for target in ('pe32','pe64'):
            with self.subTest(target=target):
                asm=compile_src(SOURCE,target)
                self.assertIn('__dbase_cls_tworker_fail:',asm)
                self.assertIn('__dbase_cls_tworker_run:',asm)
                self.assertIn('call __dbase_raise_ecustom',asm)
                self.assertIn('call __dbase_cls_tworker_run',asm)
                self.assertIn('call __dbase_cls_tworker_fail',asm)
                self.assertIn('call DBaseQtAppendDebug',asm)
                self.assertIn('__dbase_exception_object_ptr',asm)
                labels=set(re.findall(r'^([A-Za-z_]\w*):',asm,re.M))
                imports=set(re.findall(r'^import\s+([A-Za-z_]\w*)\s*,',asm,re.M))
                calls=set(re.findall(r'\bcall\s+([A-Za-z_]\w*)\b',asm))
                self.assertEqual(calls-labels-imports,set())

    def test_internal_coff_assembler_both_targets(self):
        link=_load_pe_linker()
        for target in ('pe32','pe64'):
            with self.subTest(target=target):
                # Stage 642: exercise the genuine FNINIT opcode in both
                # PE assemblers; no instruction substitution is permitted.
                asm=compile_src(SOURCE,target)
                if target=='pe32':
                    obj=link['assemble_pe32_object_source'](asm)
                    self.assertTrue(link['write_coff32_object'](obj))
                else:
                    obj=link['assemble_pe64_object_source'](asm)
                    self.assertTrue(link['write_coff64_object'](obj))

    def test_inherited_method_and_nested_finally(self):
        src='''#include "System.SysUtils"
CLASS TParent OF TObject
    PROCEDURE ThrowError()
        THROW NEW Exception("inherited")
        RETURN
ENDCLASS
CLASS TChild OF TParent
    PROCEDURE Start()
        TRY
            TRY
                self.ThrowError()
            FINALLY
                ? "inner"
            ENDTRY
        CATCH (Exception e)
            ? e.Message
        FINALLY
            ? "outer"
        ENDTRY
        RETURN
ENDCLASS
LOCAL c AS TChild
c = NEW TChild()
c.Start()'''
        for target in ('pe32','pe64'):
            with self.subTest(target=target):
                asm=compile_src(src,target)
                self.assertIn('call __dbase_cls_tparent_throwerror',asm)
                self.assertRegex(asm,r'__dbase_cls_tchild_start_catch_dispatch_\d+:')

    def test_return_finalizers_and_empty_finally(self):
        src='''CLASS TTest OF TObject
 FUNCTION Value()
  TRY
   RETURN 42
  FINALLY
   ? "finally"
  ENDTRY
  RETURN 0
ENDCLASS
'''
        for target in ('pe32','pe64'):
            with self.subTest(target=target):
                asm=compile_src(src,target)
                self.assertIn('__dbase_cls_ttest_value:',asm)
                self.assertIn('return_finalizer_advance',asm)
        empty=src.replace('? "finally"','')
        compile_src(empty,'pe32')

    def test_catch_message_modification_and_rethrow(self):
        src='''CLASS TTest OF TObject
 PROCEDURE Work()
  TRY
   THROW NEW Exception("first")
  CATCH (Exception e)
   e.Message = "changed"
   THROW
  ENDTRY
  RETURN
ENDCLASS'''
        for target in ('pe32','pe64'):
            with self.subTest(target=target):
                asm=compile_src(src,target)
                self.assertIn('call __dbase_cls_exception_set_message',asm)
                self.assertIn('call __dbase_cls_exception_get_message',asm)

    def test_reject_malformed_blocks(self):
        cases=('TRY\n THROW NEW Exception("x")\n RETURN',
               'CATCH (Exception e)\n RETURN',
               'TRY\n THROW NEW Alien("x")\n FINALLY\n ? "x"\n ENDTRY\n RETURN')
        for code in cases:
            src='CLASS TWorker OF TObject\nPROCEDURE Run()\n'+code+'\nENDCLASS'
            with self.subTest(code=code[:15]):
                with self.assertRaises(DBaseCompilerError):
                    compile_src(src,'pe32')

    def test_native_new_property_and_free_stay_inside_try(self):
        from d64dbase.compiler import (DBaseNewObjectStatement,
            DBaseNativePropertyStatement, DBaseNativeMethodStatement)
        src='''CLASS TWorker OF TObject
 PUBLIC PROPERTY Info = "Hallo"
 PROCEDURE Run()
  TRY
   THROW NEW Exception("inner")
  CATCH (Exception e)
   ? e.Message
  ENDTRY
  RETURN
ENDCLASS
LOCAL worker AS TWorker
TRY
 worker = NEW TWorker()
 ? worker.Info
 worker.Info = "changed"
 worker.Free()
CATCH (Exception e)
 ? e.Message
ENDTRY'''
        parsed=parse_dbase_statements(src)
        outer=next(s for s in parsed if isinstance(s,DBaseTryStatement))
        self.assertEqual([type(s) for s in outer.try_body],
            [DBaseNewObjectStatement,DBaseNativePropertyStatement,
             DBaseNativePropertyStatement,DBaseNativeMethodStatement])
        for target in ('pe32','pe64'):
            with self.subTest(target=target):
                compile_src(src,target)

    def test_throw_from_constructor_inside_outer_try(self):
        from d64dbase.compiler import DBaseNewObjectStatement
        src='''CLASS TWorker OF TObject
 PROCEDURE __ini__()
  THROW NEW Exception("ctor failed")
  RETURN
ENDCLASS
LOCAL worker AS TWorker
TRY
 worker = NEW TWorker()
CATCH (Exception e)
 ? e.Message
ENDTRY'''
        parsed=parse_dbase_statements(src)
        outer=next(s for s in parsed if isinstance(s,DBaseTryStatement))
        self.assertIsInstance(outer.try_body[0],DBaseNewObjectStatement)
        for target in ('pe32','pe64'):
            with self.subTest(target=target):
                asm=compile_src(src,target)
                self.assertIn('call __dbase_cls_tworker_create',asm)
                self.assertIn('call __dbase_raise_exception',asm)
                self.assertRegex(asm,r'jmp __dbase_catch_dispatch_\d+')

    def test_link_managed_class_methods_pe32_and_pe64(self):
        import tempfile
        from pathlib import Path
        from pascal_console_dependencies import inspect_pe
        link=_load_pe_linker()
        for target, machine in (('pe32',0x14c),('pe64',0x8664)):
            with self.subTest(target=target):
                asm=compile_src(SOURCE,target)
                if target=='pe32':
                    obj=link['assemble_pe32_object_source'](asm)
                    coff=link['write_coff32_object'](obj)
                    exe=link['link_coff32_objects']((coff,),entry_symbol='_start')
                else:
                    obj=link['assemble_pe64_object_source'](asm)
                    coff=link['write_coff64_object'](obj)
                    exe=link['link_coff64_objects']((coff,),entry_symbol='_start')
                with tempfile.TemporaryDirectory() as tmp:
                    binary=Path(tmp)/'stage641.exe'
                    binary.write_bytes(exe.executable)
                    actual, _imports, _exports=inspect_pe(binary)
                    self.assertEqual(actual,machine)

    def test_exception_in_destructor_and_free_inside_try(self):
        src='''CLASS TWorker OF TObject
 PROCEDURE __del__()
  TRY
   THROW NEW Exception("destructor")
  FINALLY
   ? "delete final"
  ENDTRY
  RETURN
ENDCLASS
LOCAL worker AS TWorker
TRY
 worker = NEW TWorker()
 worker.Free()
CATCH (Exception e)
 ? e.Message
ENDTRY'''
        parsed=parse_dbase_statements(src)
        outer=next(s for s in parsed if isinstance(s,DBaseTryStatement))
        self.assertEqual(type(outer.try_body[-1]).__name__,'DBaseNativeMethodStatement')
        for target in ('pe32','pe64'):
            with self.subTest(target=target):
                asm=compile_src(src,target)
                self.assertIn('__dbase_cls_tworker___del__:',asm)
                self.assertIn('call __dbase_raise_exception',asm)

    def test_exception_class_dll_without_shared_abi_is_rejected(self):
        src='''CLASS TWorker OF TObject
 PROCEDURE Run()
  THROW NEW Exception("DLL")
  RETURN
ENDCLASS'''
        with self.assertRaises(DBaseCompilerError) as cm:
            compile_dbase_to_assembly(src,target='pe32',source_kind='library')
        self.assertIn('Exception-Runtime-ABI',str(cm.exception))

if __name__=='__main__': unittest.main()
