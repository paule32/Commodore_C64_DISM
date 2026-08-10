from __future__ import annotations

import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from d64dbase import (
    DBaseCompilerError,
    compile_dbase_to_assembly,
    preprocess_dbase_source,
)


class DBasePreprocessorStage9Tests(unittest.TestCase):
    def test_misspelled_else_is_rejected(self):
        with self.assertRaises(DBaseCompilerError) as ctx:
            preprocess_dbase_source("#if 1\n? 1\n#el" + "lse\n? 2\n#endif\n", filename="x.dbase")
        self.assertIn("Unbekannte", str(ctx.exception))

    def test_if_zero_excludes_large_invalid_block(self):
        src = '''#if 0
THIS IS NOT DBASE @@@
function broken(,,,,
return "unterminated? no parser sees this"
X = !!! $$$ ???
#endif
? "ok"
'''
        result = compile_dbase_to_assembly(src, filename="if0.dbase", windows_application_mode="GUI")
        self.assertEqual(result.transcript, "ok\r\n")
        # Zeilenstruktur bleibt erhalten.
        self.assertEqual(result.frontend.preprocessed_source.count("\n"), src.count("\n"))

    def test_nested_if_zero_still_tracks_scopes(self):
        src = '''#if 0
#if 1
? "bad"
#else
? "bad2"
#endif
#endif
? "good"
'''
        self.assertEqual(compile_dbase_to_assembly(src, windows_application_mode="GUI").transcript, "good\r\n")

    def test_error_stops_compile_with_text(self):
        with self.assertRaises(DBaseCompilerError) as ctx:
            compile_dbase_to_assembly('#error Dieser Build ist verboten\n? "never"\n', filename="err.dbase")
        self.assertIn("Dieser Build ist verboten", str(ctx.exception))
        self.assertIn("err.dbase:1:1", str(ctx.exception))

    def test_error_in_inactive_block_is_ignored(self):
        src = '#if 0\n#error darf nicht ausloesen\n#endif\n? "ok"\n'
        self.assertEqual(compile_dbase_to_assembly(src, windows_application_mode="GUI").transcript, "ok\r\n")

    def test_warning_and_info_are_reported(self):
        result = compile_dbase_to_assembly(
            '#warning Vorsicht\n#info Compilerinformation\n? "ok"\n',
            filename="diag.dbase",
            windows_application_mode="GUI",
        )
        self.assertTrue(any("diag.dbase:1: Vorsicht" in item for item in result.warnings))
        self.assertTrue(any("diag.dbase:2: Compilerinformation" in item for item in result.notes))
        self.assertEqual(result.transcript, "ok\r\n")

    def test_predefined_file_and_line_in_expression(self):
        filename = r"C:\work\demo.dbase"
        src = '? "File: " + __FILE__ + ", Zeile: " + __LINE__\n'
        result = compile_dbase_to_assembly(src, filename=filename, windows_application_mode="GUI")
        self.assertEqual(result.transcript, f"File: {filename}, Zeile: 1\r\n")

    def test_line_expands_at_macro_use_site(self):
        src = '''#define HERE __LINE__
? HERE
? HERE
'''
        result = compile_dbase_to_assembly(src, filename="line.dbase", windows_application_mode="GUI")
        self.assertEqual(result.transcript, "2\r\n3\r\n")

    def test_date_and_time_are_string_literals(self):
        result = compile_dbase_to_assembly(
            '? __DATE__ + "|" + __TIME__\n',
            filename="clock.dbase",
            windows_application_mode="GUI",
        )
        text = result.transcript.rstrip("\r\n")
        date_text, time_text = text.split("|", 1)
        self.assertRegex(date_text, r"^[A-Z][a-z]{2} [ 0-9][0-9] [0-9]{4}$")
        self.assertRegex(time_text, r"^[0-9]{2}:[0-9]{2}:[0-9]{2}$")

    def test_predefined_symbols_work_in_if_expression(self):
        src = '''#if __LINE__ == 1
? "yes"
#else
? "no"
#endif
'''
        self.assertEqual(compile_dbase_to_assembly(src, windows_application_mode="GUI").transcript, "yes\r\n")

    def test_start_button_does_not_build_dbase(self):
        text = (ROOT / "d64_dism.py").read_text(encoding="utf-8")
        helper_start = text.index("def _start_existing_dbase_executable")
        helper_end = text.index("def start_assembled_document", helper_start)
        helper = text[helper_start:helper_end]
        self.assertNotIn("assemble_document(", helper)
        self.assertNotIn("assemble_generated_document(", helper)
        self.assertIn("self.current_directory", helper)
        self.assertIn('with_suffix(".exe")', helper)

    def test_dbase_link_output_is_working_directory(self):
        text = (ROOT / "d64_dism.py").read_text(encoding="utf-8")
        start = text.index("def assemble_generated_document")
        end = text.index("def _c_source_has_main_definition", start)
        block = text[start:end]
        self.assertIn('document.is_dbase_document', block)
        self.assertIn('self.current_directory / output_path.name', block)

    def test_f2_still_builds_links_and_launches(self):
        text = (ROOT / "d64_dism.py").read_text(encoding="utf-8")
        start = text.index("def build_and_run_source_document")
        end = text.index("def assemble_document", start)
        block = text[start:end]
        self.assertIn("assemble_document(document)", block)
        self.assertIn("assemble_generated_document", block)
        self.assertIn("return self._launch_assembled_document(document)", block)

    def test_ide_dbase_console_debug_tabs_remain_removed(self):
        text = (ROOT / "d64_dism.py").read_text(encoding="utf-8")
        self.assertNotIn('self.views.addTab(self.console_editor, "Konsole")', text)
        self.assertNotIn('self.views.addTab(self.debug_console_editor, "DEBUG")', text)


if __name__ == "__main__":
    unittest.main()
