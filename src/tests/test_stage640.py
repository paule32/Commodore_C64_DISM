"""Stage 640: real TObject exception allocation and native lifetime tests.

These are compiler/ASM structure tests; they do NOT claim Windows SEH runtime
or the actual execution of the generated PE32/PE64 binaries.
"""
from pathlib import Path
import re
import unittest

from d64dbase.compiler import (
    compile_dbase_to_assembly, evaluate_dbase_statements,
)

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "runtime" / "dbase" / "src"


def compiled(source, target):
    return compile_dbase_to_assembly(
        source, target=target,
        filename=str(SRC / "ExceptionTest.prg"),
        include_paths=[str(SRC)],
    )


class TestNativeTObjectExceptions(unittest.TestCase):
    def targets(self):
        return ("pe32", "pe64")

    def test_synthetic_exception_has_real_vmt_and_managed_field(self):
        source = '''TRY
 THROW NEW Exception("synthetic")
CATCH (Exception e)
 ? e.Message
ENDTRY'''
        for target in self.targets():
            with self.subTest(target=target):
                a = compiled(source, target).assembly
                self.assertIn("__dbase_cls_exception_create:", a)
                self.assertIn("__dbase_cls_exception_get_message:", a)
                self.assertIn("__dbase_cls_exception_set_message:", a)
                self.assertIn("call __dbase_cls_exception_create", a)
                self.assertIn("call __dbase_cls_exception_set_message", a)
                self.assertIn("__dbase_exception_object_ptr:", a)
                self.assertIn("__dbase_exception_objects_head:", a)
                self.assertIn("call __dbase_exception_cleanup_all", a)
                self.assertEqual(evaluate_dbase_statements(compiled(source, target).statements),
                                 "synthetic\r\n")

    def test_inherited_fields_in_object_allocation(self):
        src = '''#include "System.SysUtils"
CLASS ECustom OF DbException
ENDCLASS
TRY
 THROW NEW ECustom("foo")
CATCH (DbException e)
 ? e.Message
ENDTRY'''
        # Stage 646: Exception erbt neben Message nun auch Code;
        # jede geerbte numerische Property hat einen nativen Speicher-Slot.
        for target, word, byte_size in (("pe32", "dd", 20), ("pe64", "dq", 40)):
            with self.subTest(target=target):
                a = compiled(src, target).assembly
                vmt = a.split("__dbase_vmt_ecustom:\n", 1)[1]
                self.assertIn(f"    {word} 0x{(byte_size | 0x80000000):08X}", vmt[:150])
                self.assertIn("__dbase_cls_ecustom_fields_init:", a)
                self.assertIn("__dbase_cls_dbexception_fields_init:", a)
                self.assertIn("__dbase_cls_exception_fields_init:", a)
                self.assertIn("call __dbase_cls_exception___ini__", a)
                self.assertIn("call __dbase_cls_ecustom_create", a)
                self.assertEqual(evaluate_dbase_statements(compiled(src, target).statements),
                                 "Error.: foo\r\n")

    def test_rethrow_preserves_object_pointer(self):
        src = '''TRY
 TRY
  THROW NEW Exception("keep")
 CATCH (Exception e)
  THROW e
 ENDTRY
CATCH (Exception x)
 ? x.Message
ENDTRY'''
        for target in self.targets():
            with self.subTest(target=target):
                a = compiled(src, target).assembly
                ptr = "qword" if target == "pe64" else "dword"
                self.assertRegex(a, rf"mov {ptr} ptr \[__dbase_exception_object_ptr\], (?:r|e)ax")
                self.assertIn("_object_ptr", a)
                self.assertIn("__dbase_catch_dispatch_", a)
                self.assertEqual(evaluate_dbase_statements(compiled(src, target).statements),
                                 "keep\r\n")

    def test_native_property_modification_updates_object_and_preview(self):
        src = '''TRY
 THROW NEW Exception("old")
CATCH (Exception e)
 e.Message = "changed"
 ? e.Message
ENDTRY'''
        for target in self.targets():
            with self.subTest(target=target):
                c = compiled(src, target)
                self.assertIn("call __dbase_cls_exception_set_message", c.assembly)
                self.assertEqual(evaluate_dbase_statements(c.statements), "changed\r\n")

    def test_string_is_zero_terminated_before_constructor(self):
        src = '''#include "System.SysUtils"
TRY
 THROW NEW DbException("not-null-terminated")
CATCH (Exception e)
 ? e.Message
ENDTRY'''
        for target in self.targets():
            with self.subTest(target=target):
                a = compiled(src, target).assembly
                self.assertIn("call __dbase_memcpy", a)
                self.assertIn("mov byte ptr [", a)
                self.assertIn("call __dbase_exc_free", a)
                self.assertIn("import __dbase_exc_object_free", a)

    def test_all_generated_call_targets_exist(self):
        source = '''#include "System.SysUtils"
CLASS ECustom OF DbException
ENDCLASS
PROCEDURE DoIt()
 TRY
  THROW NEW ECustom("hello")
 FINALLY
  ? "finished"
 ENDTRY
 RETURN
TRY
 DoIt()
CATCH (Exception e)
 e.Message = "changed"
 ? e.Message
 THROW e
FINALLY
 ? "last"
ENDTRY'''
        for target in self.targets():
            with self.subTest(target=target):
                a = compiled(source, target).assembly
                labels = set(re.findall(r"^([A-Za-z_]\w*):", a, re.M))
                imports = set(re.findall(r"^import\s+([A-Za-z_]\w*)\s*,", a, re.M))
                calls = set(re.findall(r"\bcall\s+([A-Za-z_]\w*)\b", a))
                self.assertEqual(calls - labels - imports, set())

    def test_lifetime_cleanup_is_emitted_before_runtime_shutdown(self):
        src = 'THROW NEW Exception("unhandled")'
        for target in self.targets():
            with self.subTest(target=target):
                a = compiled(src, target).assembly
                self.assertLess(a.index("call __dbase_exception_cleanup_all"),
                                a.index("call DBaseConsoleShutdown"))
                self.assertIn("call __dbase_exc_object_free", a)

    def test_nested_if_thrown_exception_inserts_class(self):
        src = '''IF 1
 IF 1
  TRY
   THROW NEW DbException("hidden")
  CATCH (Exception e)
   ? e.Message
  ENDTRY
 ENDIF
ENDIF'''
        for target in self.targets():
            with self.subTest(target=target):
                a = compiled(src, target).assembly
                self.assertIn("__dbase_vmt_exception:", a)
                self.assertIn("__dbase_vmt_dbexception:", a)


if __name__ == "__main__":
    unittest.main()
