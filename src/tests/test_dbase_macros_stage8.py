from __future__ import annotations

import importlib.util
import struct
import subprocess
import sys
import tempfile
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from d64dbase import (
    DBaseCompilerError,
    compile_dbase_to_assembly,
    evaluate_dbase_statements,
    parse_dbase_statements,
    preprocess_dbase_source,
)


def load_d64():
    sys.modules.setdefault("flags_rc", types.ModuleType("flags_rc"))
    name = "_d64_dbase_stage8_test"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, ROOT / "d64_dism.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class DBaseMacroStage8Tests(unittest.TestCase):
    def test_define_object_macro_in_expression(self):
        src = '#define foo 5\nX = foo + 3 * 4\n? "X=" + X\n'
        self.assertEqual(evaluate_dbase_statements(parse_dbase_statements(src)), "X=17\r\n")

    def test_ifdef_expression(self):
        src = '''#define foo 5
#ifdef foo >= 5
? "yes"
#else
? "no"
#endif
'''
        self.assertEqual(compile_dbase_to_assembly(src).transcript, "yes\r\n")

    def test_if_defined_value_expression(self):
        src = '''#define foo 5
#if defined(foo) >= 5
? "yes"
#else
? "no"
#endif
'''
        self.assertEqual(compile_dbase_to_assembly(src).transcript, "yes\r\n")

    def test_ifndef_and_nested_scopes(self):
        src = '''#define outer 1
#ifndef missing
#define local 7
#ifdef local >= 7
? local
#endif
#endif
#ifdef local
? "leaked"
#else
? "scoped"
#endif
'''
        self.assertEqual(compile_dbase_to_assembly(src).transcript, "7\r\nscoped\r\n")

    def test_else_branch_gets_clean_scope(self):
        src = '''#define value 0
#ifdef value >= 1
#define branch 11
#else
#define branch 22
? branch
#endif
#ifdef branch
? "leaked"
#else
? "clean"
#endif
'''
        self.assertEqual(compile_dbase_to_assembly(src).transcript, "22\r\nclean\r\n")

    def test_function_macro_token_paste(self):
        src = '''#define foo(x) bar ## x
bar5 = 14
? foo(5)
'''
        pre = preprocess_dbase_source(src)
        self.assertIn("? bar5", pre.preprocessed_source)
        self.assertEqual(compile_dbase_to_assembly(src).transcript, "14\r\n")

    def test_multi_parameter_token_paste(self):
        src = '''#define join(a,b) a ## b
foobar = 9
? join(foo,bar)
'''
        self.assertEqual(compile_dbase_to_assembly(src).transcript, "9\r\n")

    def test_macros_do_not_expand_inside_strings_or_comments(self):
        src = '''#define foo 5
? "foo"
// foo
/* foo */
? foo
'''
        self.assertEqual(compile_dbase_to_assembly(src).transcript, "foo\r\n5\r\n")

    def test_missing_endif_is_error(self):
        with self.assertRaises(DBaseCompilerError):
            compile_dbase_to_assembly("#ifdef foo\n? 1\n")

    def test_pragma_link_resolves_relative_path(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            obj = root / "obj" / "foo.o"
            obj.parent.mkdir()
            obj.write_bytes(b"dummy")
            src_path = root / "main.dbase"
            src = '#pragma link obj/foo.o\n? "ok"\n'
            result = compile_dbase_to_assembly(src, filename=str(src_path))
            self.assertEqual(result.linked_object_files, (str(obj.resolve()),))
            self.assertEqual(result.frontend.pragma_links[0].raw_path, "obj/foo.o")

    def test_pragma_link_rejects_wrong_extension(self):
        with self.assertRaises(DBaseCompilerError):
            compile_dbase_to_assembly('#pragma link foo.txt\n? 1\n', filename='/tmp/a.dbase')

    def test_pragma_object_is_used_by_cli_link_pe32_and_pe64(self):
        d64 = load_d64()
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for target in ("pe32", "pe64"):
                helper_asm = "bits 64\nglobal pragma_helper\nsection .text\npragma_helper:\n    ret\n" if target == "pe64" else "bits 32\nglobal pragma_helper\nsection .text\npragma_helper:\n    ret\n"
                helper_obj = (
                    d64.assemble_pe64_coff_object(helper_asm, filename="helper.asm")
                    if target == "pe64" else d64.assemble_pe32_coff_object(helper_asm, filename="helper.asm")
                )
                obj_path = root / f"helper_{target}.o"
                obj_path.write_bytes(helper_obj)
                src_path = root / f"main_{target}.dbase"
                src_path.write_text(f'#pragma link "{obj_path.name}"\n? "ok"\n', encoding='utf-8')
                result = compile_dbase_to_assembly(src_path.read_text(), filename=str(src_path), target=target)
                main_obj = root / f"main_{target}.o"
                main_obj.write_bytes(
                    d64.assemble_pe64_coff_object(result.assembly, filename="main.asm")
                    if target == "pe64" else d64.assemble_pe32_coff_object(result.assembly, filename="main.asm")
                )
                linked = (
                    d64.link_coff64_inputs([main_obj, Path(result.linked_object_files[0])], entry_symbol="_start", gui=True)
                    if target == "pe64" else d64.link_coff32_inputs([main_obj, Path(result.linked_object_files[0])], entry_symbol="_start", gui=True)
                )
                self.assertTrue(linked.executable.startswith(b"MZ"))

    def test_pragma_archive_links(self):
        d64 = load_d64()
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            helper = "bits 32\nglobal archive_helper\nsection .text\narchive_helper:\n ret\n"
            obj = d64.assemble_pe32_coff_object(helper, filename="h.asm")
            archive = root / "libfoo.a"
            archive.write_bytes(d64.create_coff32_archive((("h.o", obj),)))
            src_path = root / "main.dbase"
            result = compile_dbase_to_assembly('#pragma link libfoo.a\n? "ok"\n', filename=str(src_path), target='pe32')
            main = root / "main.o"
            main.write_bytes(d64.assemble_pe32_coff_object(result.assembly, filename="main.asm"))
            linked = d64.link_coff32_inputs([main, archive], entry_symbol="_start", gui=True)
            self.assertTrue(linked.executable.startswith(b"MZ"))

    def test_ide_has_no_dbase_console_or_debug_tabs(self):
        text = (ROOT / "d64_dism.py").read_text(encoding="utf-8")
        self.assertNotIn('self.views.addTab(self.console_editor, "Konsole")', text)
        self.assertNotIn('self.views.addTab(self.debug_console_editor, "DEBUG")', text)

    def test_f2_launches_linked_executable(self):
        text = (ROOT / "d64_dism.py").read_text(encoding="utf-8")
        start = text.index("def build_and_run_source_document")
        end = text.index("def assemble_document", start)
        block = text[start:end]
        self.assertIn("assemble_generated_document", block)
        self.assertIn("return self._launch_assembled_document(document)", block)
        self.assertNotIn("focus_dbase_console()", block)


if __name__ == "__main__":
    unittest.main()
