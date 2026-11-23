"""Stage 639: typed managed dBASE exceptions, ENDTRY and THROW."""
import unittest
from pathlib import Path
from d64dbase.compiler import (
    DBaseCompilerError, DBaseTryStatement, DBaseCatchClause, DBaseThrowStatement,
    compile_dbase_to_assembly, parse_dbase_statements, evaluate_dbase_statements,
)

ROOT = Path(__file__).resolve().parent
UNIT = ROOT / 'runtime' / 'dbase' / 'src'

class TestStage639(unittest.TestCase):
    def compile(self, src, target='pe32', **options):
        return compile_dbase_to_assembly(src, target=target,
            filename=str(UNIT / 'App001.prg'), include_paths=[str(UNIT)], **options)

    def check_both(self, src, expected):
        for target in ('pe32', 'pe64'):
            with self.subTest(target=target):
                result = self.compile(src, target)
                self.assertIn('__dbase_exception_id:', result.assembly)
                self.assertIn('exception_unhandled', result.assembly)
                self.assertEqual(evaluate_dbase_statements(result.statements), expected)

    def test_basic_try_catch_finally(self):
        src='''TRY
THROW NEW Exception("boom")
CATCH (Exception e)
? e.Message
FINALLY
? "cleanup"
ENDTRY'''
        self.check_both(src, 'boom\r\ncleanup\r\n')
        parsed=parse_dbase_statements(src)
        self.assertIsInstance(parsed[0], DBaseTryStatement)
        self.assertIsInstance(parsed[0].catches[0], DBaseCatchClause)
        self.assertIsInstance(parsed[0].try_body[0], DBaseThrowStatement)

    def test_catch_multiple_order_and_runtime_dispatch(self):
        src='''TRY
THROW NEW DbException("db failed")
CATCH (DbException e)
? e.ClassName
? e.error
CATCH (Exception e)
? "generic"
ENDTRY'''
        self.check_both(src, 'DbException\r\ndb failed\r\n')

    def test_general_catch_for_db_subclass(self):
        src='''TRY
THROW NEW DbException("io")
CATCH (Exception e)
? e.Message
ENDTRY'''
        self.check_both(src, 'io\r\n')

    def test_nested_rethrow_and_finalizers(self):
        src='''TRY
  TRY
    THROW NEW DbException("broken")
  CATCH (DbException e)
    ? "inner"
    THROW e
  FINALLY
    ? "first"
  ENDTRY
CATCH (Exception outer)
  ? outer.Message
FINALLY
  ? "last"
ENDTRY'''
        self.check_both(src, 'inner\r\nfirst\r\nbroken\r\nlast\r\n')

    def test_bare_throw_inside_catch(self):
        src='''TRY
 TRY
  THROW NEW Exception("hidden")
 CATCH (Exception e)
  THROW
 ENDTRY
CATCH (Exception a)
 ? a.Message
ENDTRY'''
        self.check_both(src, 'hidden\r\n')

    def test_unmatched_passes_through_finally(self):
        src='''TRY
 TRY
  THROW NEW DbException("db")
 CATCH (Exception e)
  THROW NEW Exception("new")
 FINALLY
  ? "inner final"
 ENDTRY
CATCH (Exception e)
 ? e.Message
ENDTRY'''
        self.check_both(src, 'inner final\r\nnew\r\n')

    def test_procedure_propagation(self):
        src='''PROCEDURE Run()
 TRY
  THROW NEW Exception("from Run")
 FINALLY
  ? "routine final"
 ENDTRY
 RETURN
TRY
 Run()
CATCH (Exception e)
 ? e.Message
FINALLY
 ? "caller final"
ENDTRY'''
        self.check_both(src, 'routine final\r\nfrom Run\r\ncaller final\r\n')
        asm=self.compile(src).assembly
        self.assertIn('call __dbase_procedure_run__void', asm)
        self.assertIn('jmp __dbase_catch_dispatch_', asm)

    def test_return_runs_finally(self):
        src='''FUNCTION F()
 TRY
  RETURN 42
 FINALLY
  ? "clean"
 ENDTRY
 RETURN 0
? F()'''
        self.check_both(src, 'clean\r\n42\r\n')

    def test_finally_overrides_return(self):
        src='''FUNCTION F()
 TRY
  RETURN 42
 FINALLY
  RETURN 17
 ENDTRY
 RETURN 0
? F()'''
        self.check_both(src, '17\r\n')

    def test_try_inside_if_and_catch_thrown_inside_if(self):
        src='''IF 1
 TRY
  IF 1
   THROW NEW Exception("inside IF")
  ENDIF
 CATCH (Exception e)
  IF 1
   ? e.Message
  ENDIF
 ENDTRY
ENDIF'''
        self.check_both(src, 'inside IF\r\n')

    def test_user_class_inherits_exception(self):
        src='''#include "System.SysUtils"
CLASS ECustom OF DbException
ENDCLASS
TRY
 THROW NEW ECustom("custom")
CATCH (DbException e)
 ? e.ClassName
 ? e.Message
ENDTRY'''
        # Stage 640: the actual inherited Exception.__ini__ decorates Message.
        self.check_both(src, 'ECustom\r\nError.: custom\r\n')
        for target in ('pe32','pe64'):
            compiled=self.compile(src, target)
            self.assertIn('__dbase_vmt_ecustom', compiled.assembly)

    def test_macros_in_exception_message(self):
        self.check_both('#define ERROR_TEXT "makro"\nTRY\nTHROW NEW Exception(ERROR_TEXT)\nCATCH (Exception e)\n? e.Message\nENDTRY',
                        'makro\r\n')

    def test_try_finally_without_catch(self):
        self.check_both('TRY\n? "first"\nFINALLY\n? "last"\nENDTRY', 'first\r\nlast\r\n')

    def test_try_catch_without_finally(self):
        self.check_both('TRY\nTHROW NEW DbException("x")\nCATCH (Exception e)\n? e.error\nENDTRY', 'x\r\n')

    def test_short_throw_string_defaults_exception(self):
        self.check_both('TRY\nTHROW "oops"\nCATCH (Exception e)\n? e.Message\nENDTRY', 'oops\r\n')

    def test_empty_finally(self):
        self.check_both('TRY\n? "ok"\nFINALLY\nENDTRY', 'ok\r\n')

    def test_legacy_end_rejected(self):
        with self.assertRaisesRegex(DBaseCompilerError, 'ENDTRY'):
            self.compile('TRY\n? "old"\nFINALLY\n? "end"\nEND')

    def test_stray_catch(self):
        with self.assertRaisesRegex(DBaseCompilerError, 'CATCH'):
            self.compile('CATCH (Exception e)\n? e.Message\nENDTRY')

    def test_stray_throw_variable(self):
        with self.assertRaisesRegex(DBaseCompilerError, 'CATCH'):
            self.compile('THROW e')

    def test_unknown_exception_class(self):
        with self.assertRaisesRegex(DBaseCompilerError, 'keine bekannte Exception-Klasse'):
            self.compile('TRY\nTHROW NEW AlienError("x")\nFINALLY\n? "cleanup"\nENDTRY')

    def test_catch_order_rejected(self):
        with self.assertRaisesRegex(DBaseCompilerError, 'bereits'):
            self.compile('TRY\nTHROW NEW Exception("x")\nCATCH (Exception e)\n? 1\nCATCH (DbException d)\n? 2\nENDTRY')

    def test_missing_endtry(self):
        with self.assertRaisesRegex(DBaseCompilerError, 'ENDTRY'):
            self.compile('TRY\n? 1\nFINALLY\n? 2')

    def test_throw_invalid_message_type(self):
        with self.assertRaisesRegex(DBaseCompilerError, 'Textmeldung'):
            self.compile('TRY\nTHROW NEW Exception(123)\nFINALLY\n? 1\nENDTRY')

    def test_invalid_catch_class(self):
        with self.assertRaisesRegex(DBaseCompilerError, 'keine Exception-Unterklasse'):
            self.compile('TRY\n? 1\nCATCH (TObject e)\n? 2\nENDTRY')

    def test_bare_throw_outside_catch(self):
        with self.assertRaisesRegex(DBaseCompilerError, 'CATCH'):
            self.compile('TRY\nTHROW\nFINALLY\n? 1\nENDTRY')

if __name__=='__main__': unittest.main()
