"""Stage 638: structured dBL TRY/FINALLY/END and explicit Win32 ExitProcess."""
import unittest

from d64dbase.compiler import (
    DBaseCompilerError, DBaseIfStatement, DBaseRoutineDefinition,
    DBaseTryStatement, compile_dbase_to_assembly,
    parse_dbase_statements, evaluate_dbase_statements,
)

SAMPLE = '''try
    set debug on
    set format to screen
    set background to 1, 14, 176
    ? "hihi"
    ? "halöo"
finally
    ? "Das Ende"
    ExitProcess(0)
endtry
'''

class TestStage638(unittest.TestCase):
    def compile(self, source, target='pe32'):
        return compile_dbase_to_assembly(source, target=target,
                                         filename='stage638_test.prg')

    def test_sample_pe32(self):
        result = self.compile(SAMPLE)
        self.assertEqual(len(result.statements), 1)
        self.assertIsInstance(result.statements[0], DBaseTryStatement)
        self.assertIn('call DBaseQtFillBackground', result.assembly)
        self.assertIn('call ExitProcess', result.assembly)
        self.assertEqual(result.debug_transcript, 'hihi\r\nhalöo\r\nDas Ende\r\n')
        self.assertFalse(result.external_functions)

    def test_sample_pe64(self):
        result = self.compile(SAMPLE, 'pe64')
        self.assertIn('call ExitProcess', result.assembly)
        self.assertIn('mov ecx, dword ptr [__dbase_temp_number]', result.assembly)
        self.assertEqual(result.debug_transcript.count('\r\n'), 3)

    def test_case_insensitive(self):
        result = self.compile('TrY\n? "eins"\nFiNaLlY\n? "zwei"\nEnDtRy')
        self.assertEqual(result.debug_transcript, 'eins\r\nzwei\r\n')

    def test_nested_try(self):
        text = '''try
  try
    ? "eins"
  finally
    ? "inner"
  endtry
finally
  ? "outer"
endtry'''
        a = self.compile(text)
        self.assertEqual(a.debug_transcript, 'eins\r\ninner\r\nouter\r\n')

    def test_try_inside_if(self):
        text = '''if 1
  try
    ? "eins"
  finally
    ? "zwei"
  endtry
endif'''
        a = self.compile(text)
        self.assertIsInstance(a.statements[0], DBaseIfStatement)
        self.assertEqual(a.debug_transcript, 'eins\r\nzwei\r\n')

    def test_if_inside_try(self):
        text = '''try
  if 1
    ? "ja"
  endif
finally
  ? "fertig"
endtry'''
        a = self.compile(text)
        self.assertEqual(a.debug_transcript, 'ja\r\nfertig\r\n')

    def test_procedure_return_runs_finally(self):
        text = '''procedure p()
try
  ? "start"
  return
finally
  ? "cleanup"
endtry
return
p()'''
        statements = parse_dbase_statements(text)
        self.assertIsInstance(statements[0], DBaseRoutineDefinition)
        self.assertEqual(evaluate_dbase_statements(statements), 'start\r\ncleanup\r\n')
        compiled = self.compile(text)
        self.assertIn('call DBaseQtRuntimeStartup', compiled.assembly)

    def test_nested_procedure_return_runs_all_finalizers(self):
        text = '''procedure p()
try
  try
    ? "start"
    return
  finally
    ? "inner"
  endtry
finally
  ? "outer"
endtry
return
p()'''
        self.assertEqual(evaluate_dbase_statements(parse_dbase_statements(text)),
                         'start\r\ninner\r\nouter\r\n')
        self.compile(text)

    def test_function_return_runs_finally(self):
        text = '''function foo()
try
  return 42
finally
  ? "cleanup"
endtry
return 0
? foo()'''
        statements = parse_dbase_statements(text)
        self.assertEqual(evaluate_dbase_statements(statements), 'cleanup\r\n42\r\n')
        self.compile(text)

    def test_finally_return_overrides_try_return(self):
        text = '''function foo()
try
  return 42
finally
  return 17
endtry
return 0
? foo()'''
        statements = parse_dbase_statements(text)
        self.assertEqual(evaluate_dbase_statements(statements), '17\r\n')
        self.compile(text)

    def test_empty_blocks(self):
        self.compile('try\nfinally\nendtry')

    def test_macro_in_finally(self):
        text = '#define N 123\ntry\n? "ok"\nfinally\n? N\nendtry\n'
        a = self.compile(text)
        self.assertEqual(a.debug_transcript, 'ok\r\n123\r\n')

    def test_exitprocess_variable(self):
        result = self.compile('code = 2\nExitProcess(code)')
        self.assertIn('call ExitProcess', result.assembly)

    def test_exitprocess_rejects_missing_argument(self):
        with self.assertRaisesRegex(DBaseCompilerError, 'genau einen'):
            self.compile('ExitProcess()')

    def test_exitprocess_rejects_string(self):
        with self.assertRaisesRegex(DBaseCompilerError, 'Zahl'):
            self.compile('ExitProcess("zwei")')

    def test_missing_finally(self):
        with self.assertRaisesRegex(DBaseCompilerError, 'ENDTRY'):
            self.compile('try\n ? "x"\nend')

    def test_missing_end(self):
        with self.assertRaisesRegex(DBaseCompilerError, 'ENDTRY'):
            self.compile('try\n ? "x"\nfinally\n ? "y"')

    def test_stray_finally(self):
        with self.assertRaisesRegex(DBaseCompilerError, 'FINALLY'):
            self.compile('finally\n? "x"')

    def test_stray_end(self):
        with self.assertRaisesRegex(DBaseCompilerError, 'END'):
            self.compile('end')

    def test_stray_return_in_try(self):
        with self.assertRaisesRegex(DBaseCompilerError, 'RETURN ist nur'):
            self.compile('try\nreturn\nfinally\n? "x"\nendtry')

    def test_extra_header_args(self):
        with self.assertRaisesRegex(DBaseCompilerError, 'TRY darf keine Parameter'):
            self.compile('try 123\nfinally\nendtry')

    def test_extra_end_args(self):
        with self.assertRaisesRegex(DBaseCompilerError, 'ENDTRY darf'):
            self.compile('try\nfinally\nendtry test')

if __name__ == '__main__':
    unittest.main()
