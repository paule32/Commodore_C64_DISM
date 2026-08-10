from __future__ import annotations

import importlib.util
import struct
import sys
import types
import unittest
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from d64dbase import (
    DBaseAssignmentStatement,
    DBaseCompilerError,
    DBaseSetFormatStatement,
    DBaseSetDebugStatement,
    compile_dbase_to_assembly,
    parse_dbase_statements,
)


def load_d64_dism():
    sys.modules.setdefault("flags_rc", types.ModuleType("flags_rc"))
    name = "_d64_dism_dbase_vars_stage3_test"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, ROOT / "d64_dism.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("d64_dism.py konnte nicht geladen werden")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class DBaseVariableStage3Tests(unittest.TestCase):
    def test_assignment_ast(self):
        statements = parse_dbase_statements('X = 2 + 3 * 4\n')
        self.assertEqual(len(statements), 1)
        self.assertIsInstance(statements[0], DBaseAssignmentStatement)
        self.assertEqual(statements[0].name, "X")

    def test_numeric_variables_and_existing_constants(self):
        source = 'X = 1\nY = X + 2 + 3 * 4\n? X\n? Y\n'
        result = compile_dbase_to_assembly(source)
        self.assertEqual(result.transcript, '1\r\n15\r\n')
        variables = {item.name.casefold(): item for item in result.variables}
        self.assertEqual(variables['x'].constant_value.value, Decimal('1'))
        self.assertEqual(variables['y'].constant_value.value, Decimal('15'))
        self.assertIn('__dbase_var_x_num', result.assembly)
        self.assertIn('__dbase_var_y_num', result.assembly)
        self.assertIn('fld qword ptr [__dbase_var_x_num]', result.assembly)

    def test_hex_forms_are_numeric(self):
        result = compile_dbase_to_assembly('X = 0x10 + $10 + 10h\n? X\n')
        self.assertEqual(result.transcript, '48\r\n')
        self.assertEqual(result.variables[0].value_type, 'number')

    def test_char_and_string_variables(self):
        result = compile_dbase_to_assembly(
            "C = 'A'\nS = \"text 1\" + \"text 2\"\n? C\n? S\n"
        )
        variables = {item.name: item for item in result.variables}
        self.assertEqual(variables['C'].value_type, 'char')
        self.assertEqual(variables['S'].value_type, 'string')
        self.assertEqual(result.transcript, 'A\r\ntext 1text 2\r\n')
        self.assertIn('__dbase_var_c_ptr', result.assembly)
        self.assertIn('__dbase_var_s_ptr', result.assembly)

    def test_string_plus_numeric_variable_formats_value(self):
        result = compile_dbase_to_assembly('X = 14\n? "Wert von X = " + X\n')
        self.assertEqual(result.transcript, 'Wert von X = 14\r\n')
        self.assertIn('__dbase_gcvt', result.assembly)
        self.assertIn('fld qword ptr [__dbase_var_x_num]', result.assembly)

    def test_double_question_with_variable_has_no_newline(self):
        result = compile_dbase_to_assembly('X = 3\n?? "X=" + X\n?? ";Ende"\n')
        self.assertEqual(result.transcript, 'X=3;Ende')

    def test_variable_reassignment_may_change_type(self):
        result = compile_dbase_to_assembly('X = 3\n? X\nX = "Text"\n? X\n')
        self.assertEqual(result.transcript, '3\r\nText\r\n')
        self.assertEqual(result.variables[0].value_type, 'string')
        self.assertIn('mov dword ptr [__dbase_var_x_type], 1', result.assembly)
        self.assertIn('mov dword ptr [__dbase_var_x_type], 2', result.assembly)

    def test_unknown_variable_has_exact_source_location(self):
        with self.assertRaises(DBaseCompilerError) as ctx:
            compile_dbase_to_assembly('? "X=" + X\n', filename='unknown.dbp')
        self.assertEqual(ctx.exception.line, 1)
        self.assertEqual(ctx.exception.column, 10)
        self.assertIn("Variable 'X'", str(ctx.exception))

    def test_no_arg_function_generates_external_assembler_and_dynamic_variable(self):
        source = 'foo = 5\nX = foo + foobar() + 11\n? X\n'
        result = compile_dbase_to_assembly(source, target='pe32')
        self.assertEqual(result.external_functions, ('foobar',))
        self.assertIn('extern foobar', result.assembly)
        self.assertIn('call foobar', result.assembly)
        variables = {item.name: item for item in result.variables}
        self.assertTrue(variables['X'].dynamic)
        d64 = load_d64_dism()
        obj = d64.assemble_pe32_object_source(result.assembly, filename='external32.asm')
        self.assertIn('foobar', obj.externals)

    def test_external_function_object_assembles_for_pe32_plus(self):
        result = compile_dbase_to_assembly('X = foobar() + 11\n? X\n', target='pe64')
        d64 = load_d64_dism()
        obj = d64.assemble_pe64_object_source(result.assembly, filename='external64.asm')
        self.assertIn('foobar', obj.externals)
        self.assertIn('movsd qword ptr [__dbase_call_number], xmm0', result.assembly)

    def test_function_arguments_are_not_silently_guessed(self):
        with self.assertRaises(DBaseCompilerError) as ctx:
            compile_dbase_to_assembly('X = foo(1)\n')
        self.assertIn('Parameter', str(ctx.exception))

    def test_set_format_screen_splits_console_and_debug_transcripts(self):
        source = (
            'X = 14\n'
            '? "normal=" + X\n'
            'SET FORMAT TO SCREEN\n'
            '?? "debug="\n'
            '? X\n'
            'SET FORMAT TO CONSOLE\n'
            '? "done"\n'
        )
        statements = parse_dbase_statements(source)
        self.assertTrue(any(isinstance(item, DBaseSetFormatStatement) for item in statements))
        result = compile_dbase_to_assembly(source)
        self.assertEqual(result.transcript, 'normal=14\r\ndone\r\n')
        self.assertEqual(result.debug_transcript, 'debug=14\r\n')
        self.assertTrue(result.uses_debug_output)
        self.assertNotIn('CreateNamedPipeA', result.assembly)
        self.assertNotIn('CreateProcessA', result.assembly)
        self.assertNotIn('AllocConsole', result.assembly)
        self.assertIn('DBaseQtAppendDebug', result.assembly)
        self.assertIn('DBaseQtSetDebugVisible', result.assembly)

    def test_set_debug_on_off_routes_console_to_stderr_then_stdout(self):
        source = (
            'X = 14\n'
            'SET FORMAT TO CONSOLE\n'
            'SET DEBUG ON\n'
            '? "debug=" + X\n'
            'SET DEBUG OFF\n'
            '? "normal=" + X\n'
        )
        statements = parse_dbase_statements(source)
        debug_statements = [item for item in statements if isinstance(item, DBaseSetDebugStatement)]
        self.assertEqual([item.enabled for item in debug_statements], [True, False])
        for target in ('pe32', 'pe64'):
            result = compile_dbase_to_assembly(source, target=target)
            self.assertEqual(result.debug_transcript, 'debug=14\r\n')
            self.assertEqual(result.transcript, 'normal=14\r\n')
            self.assertTrue(result.uses_debug_output)
            self.assertNotIn('AllocConsole', result.assembly)
            self.assertNotIn('cmd.exe', result.assembly)
            self.assertNotIn('CreateProcessA', result.assembly)
            self.assertIn('DBaseQtAppendConsole', result.assembly)
            self.assertIn('DBaseQtAppendDebug', result.assembly)
            self.assertIn('DBaseQtSetDebugVisible', result.assembly)

    def test_set_debug_off_without_debug_output_does_not_request_stderr(self):
        source = 'SET FORMAT TO CONSOLE\nSET DEBUG OFF\n? "normal"\n'
        result = compile_dbase_to_assembly(source)
        self.assertFalse(result.uses_debug_output)
        self.assertEqual(result.debug_transcript, '')
        self.assertEqual(result.transcript, 'normal\r\n')
        self.assertNotIn('push -12', result.assembly)

    def test_stage3_program_links_pe32_and_pe32_plus(self):
        d64 = load_d64_dism()
        source = (
            "X = 1\n"
            "Y = 2 + 3 * 4\n"
            "C = 'A'\n"
            "S = \"text 1\" + \"text 2\"\n"
            "? \"Wert von X = \" + X\n"
            "?? S\n"
            "? C\n"
            "SET FORMAT TO SCREEN\n"
            "? \"Debug Y = \" + Y\n"
        )
        for target, expected_magic in (("pe32", 0x10B), ("pe64", 0x20B)):
            result = compile_dbase_to_assembly(source, target=target)
            program = (
                d64.assemble_pe32_source(result.assembly, filename='vars32.asm', gui=False)
                if target == 'pe32'
                else d64.assemble_pe64_source(result.assembly, filename='vars64.asm', gui=False)
            )
            self.assertTrue(program.executable.startswith(b'MZ'))
            pe_offset = struct.unpack_from('<I', program.executable, 0x3C)[0]
            optional = pe_offset + 24
            self.assertEqual(struct.unpack_from('<H', program.executable, optional)[0], expected_magic)
            self.assertEqual(struct.unpack_from('<H', program.executable, optional + 68)[0], 3)

    def test_gui_subsystem_also_links_stage3(self):
        d64 = load_d64_dism()
        source = 'X=3\nSET FORMAT TO SCREEN\n? "X=" + X\n'
        for target in ('pe32', 'pe64'):
            result = compile_dbase_to_assembly(source, target=target, windows_application_mode='GUI')
            program = (
                d64.assemble_pe32_source(result.assembly, filename='varsg32.asm', gui=True)
                if target == 'pe32'
                else d64.assemble_pe64_source(result.assembly, filename='varsg64.asm', gui=True)
            )
            pe_offset = struct.unpack_from('<I', program.executable, 0x3C)[0]
            optional = pe_offset + 24
            self.assertEqual(struct.unpack_from('<H', program.executable, optional + 68)[0], 2)


if __name__ == '__main__':
    unittest.main()
