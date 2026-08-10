from __future__ import annotations

import importlib.util
import struct
import sys
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from d64dbase import (
    DBaseCompilerError,
    compile_dbase_frontend,
    compile_dbase_to_assembly,
    normalize_dbase_target,
    preprocess_dbase_source,
    scan_dbase_comments,
    strip_dbase_comments,
)


def load_d64_dism():
    sys.modules.setdefault("flags_rc", types.ModuleType("flags_rc"))
    name = "_d64_dism_dbase_test"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, ROOT / "d64_dism.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("d64_dism.py konnte nicht geladen werden")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class DBaseCommentTests(unittest.TestCase):
    def test_three_line_comment_markers(self):
        source = "? 1 // a\n? 2 ** b\n? 3 && c\n"
        cleaned = strip_dbase_comments(source)
        self.assertEqual(len(cleaned), len(source))
        self.assertEqual(cleaned.count("\n"), source.count("\n"))
        self.assertEqual(
            [line.rstrip() for line in cleaned.splitlines()],
            ["? 1", "? 2", "? 3"],
        )

    def test_block_comment_can_start_and_end_mid_line(self):
        source = "? 2 /** text */ + 2 /* more */ * 3\n"
        cleaned = strip_dbase_comments(source)
        self.assertEqual(len(cleaned), len(source))
        self.assertIn("? 2", cleaned)
        self.assertIn("+ 2", cleaned)
        self.assertIn("* 3", cleaned)
        self.assertNotIn("text", cleaned)
        self.assertNotIn("more", cleaned)

    def test_multiline_block_comment_preserves_lines_and_columns(self):
        source = "? 2 + /* first\nsecond\nthird */ 3\n"
        cleaned = strip_dbase_comments(source)
        self.assertEqual(len(cleaned), len(source))
        self.assertEqual(cleaned.count("\n"), source.count("\n"))
        self.assertEqual(cleaned.index("3"), source.index("3", source.index("*/")))

    def test_markers_inside_strings_are_not_comments(self):
        source = '? "// x" + "/* y */" + "&& z" + "** q" // real\n'
        comments = scan_dbase_comments(source)
        self.assertEqual(len(comments), 1)
        self.assertEqual(comments[0].marker, "//")
        cleaned = strip_dbase_comments(source)
        self.assertIn('"// x"', cleaned)
        self.assertIn('"/* y */"', cleaned)
        self.assertIn('"&& z"', cleaned)
        self.assertIn('"** q"', cleaned)

    def test_doubled_quotes_do_not_end_string_early(self):
        source = '? "Text "" // kein Kommentar" // Kommentar\n'
        comments = scan_dbase_comments(source)
        self.assertEqual(len(comments), 1)
        self.assertEqual(comments[0].marker, "//")

    def test_line_comment_hides_later_block_marker(self):
        source = "? 1 && Kommentar /* kein Block mehr */\n? 2\n"
        comments = scan_dbase_comments(source)
        self.assertEqual(len(comments), 1)
        self.assertEqual(comments[0].marker, "&&")

    def test_block_comment_hides_comment_markers_until_first_close(self):
        source = "? 1 /* // && ** alles Block */ + 2 // Ende\n"
        comments = scan_dbase_comments(source)
        self.assertEqual([c.marker for c in comments], ["/*", "//"])

    def test_unterminated_block_comment_is_compile_error(self):
        with self.assertRaises(DBaseCompilerError) as ctx:
            strip_dbase_comments("? 1 + /* offen\nnoch offen\n", filename="test.dbase")
        self.assertEqual(ctx.exception.line, 1)
        self.assertEqual(ctx.exception.column, 7)
        self.assertIn("*/", str(ctx.exception))

    def test_user_example_semantics(self):
        source = (
            "? 2 /** text  */ + 2 /*\n"
            "text\n"
            "*/  *  && kommentar\n"
            "** Kommentar\n"
            "3\n"
        )
        result = preprocess_dbase_source(source, filename="example.dbase")
        self.assertEqual(len(result.comments), 4)
        cleaned = result.comment_free_source
        self.assertEqual(len(cleaned), len(source))
        self.assertIn("? 2", cleaned)
        self.assertIn("+ 2", cleaned)
        self.assertIn("*", cleaned)
        self.assertTrue(cleaned.rstrip().endswith("3"))

    def test_crlf_is_preserved_byte_for_byte_in_shape(self):
        source = "? 1 /* a\r\nb */ + 2 && x\r\n? 3\r\n"
        cleaned = strip_dbase_comments(source)
        self.assertEqual(len(cleaned), len(source))
        self.assertEqual(cleaned.count("\r\n"), source.count("\r\n"))

    def test_targets_are_pe32_and_pe32_plus_only(self):
        self.assertEqual(normalize_dbase_target("pe32"), "pe32")
        self.assertEqual(normalize_dbase_target("win32"), "pe32")
        self.assertEqual(normalize_dbase_target("pe64"), "pe64")
        self.assertEqual(normalize_dbase_target("PE32+"), "pe64")
        self.assertEqual(normalize_dbase_target("amd64"), "pe64")
        with self.assertRaises(DBaseCompilerError):
            normalize_dbase_target("c64")
        with self.assertRaises(DBaseCompilerError):
            normalize_dbase_target("amiga")

    def test_frontend_keeps_target(self):
        r32 = compile_dbase_frontend("// x\n", target="pe32")
        r64 = compile_dbase_frontend("// x\n", target="pe64")
        self.assertEqual(r32.target, "pe32")
        self.assertEqual(r64.target, "pe64")

    def test_comment_only_program_emits_both_architectures(self):
        source = "// Kommentar\n** Kommentar\n&& Kommentar\n/* Block */\n"
        p32 = compile_dbase_to_assembly(source, target="pe32")
        p64 = compile_dbase_to_assembly(source, target="pe64")
        self.assertTrue(p32.assembly.startswith("bits 32\n"))
        self.assertTrue(p64.assembly.startswith("bits 64\n"))
        self.assertIn("ExitProcess", p32.assembly)
        self.assertIn("ExitProcess", p64.assembly)

    def test_unknown_statement_is_not_silently_ignored(self):
        with self.assertRaises(DBaseCompilerError) as ctx:
            compile_dbase_to_assembly(
                "// Kommentar\nUSE test\n",
                filename="statement.dbase",
                target="pe64",
            )
        self.assertEqual(ctx.exception.line, 2)
        self.assertEqual(ctx.exception.column, 1)
        self.assertIn("'?' oder '??'", str(ctx.exception))

    def test_internal_toolchain_links_pe32_and_pe32_plus(self):
        d64 = load_d64_dism()
        source = "// a\n** b\n&& c\n/* mehr\nzeilig */\n"
        for target, expected_magic in (("pe32", 0x10B), ("pe64", 0x20B)):
            result = compile_dbase_to_assembly(source, target=target)
            program = (
                d64.assemble_pe32_source(result.assembly, filename="dbase32.asm", gui=False)
                if target == "pe32"
                else d64.assemble_pe64_source(result.assembly, filename="dbase64.asm", gui=False)
            )
            self.assertTrue(program.executable.startswith(b"MZ"))
            pe_offset = struct.unpack_from("<I", program.executable, 0x3C)[0]
            optional = pe_offset + 24
            magic = struct.unpack_from("<H", program.executable, optional)[0]
            subsystem = struct.unpack_from("<H", program.executable, optional + 68)[0]
            self.assertEqual(magic, expected_magic)
            self.assertEqual(subsystem, 3)

    def test_gui_subsystem_is_available_for_both_targets(self):
        d64 = load_d64_dism()
        source = "/* Nur Kommentar */\n"
        for target in ("pe32", "pe64"):
            result = compile_dbase_to_assembly(
                source, target=target, windows_application_mode="gui"
            )
            program = (
                d64.assemble_pe32_source(result.assembly, filename="dbase32g.asm", gui=True)
                if target == "pe32"
                else d64.assemble_pe64_source(result.assembly, filename="dbase64g.asm", gui=True)
            )
            pe_offset = struct.unpack_from("<I", program.executable, 0x3C)[0]
            optional = pe_offset + 24
            subsystem = struct.unpack_from("<H", program.executable, optional + 68)[0]
            self.assertEqual(subsystem, 2)


if __name__ == "__main__":
    unittest.main()
