from __future__ import annotations

import importlib.util
import struct
import sys
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from d64lisp import LispCompilerError, compile_lisp_to_assembly, parse_lisp


def load_d64_module():
    if "flags_rc" not in sys.modules:
        sys.modules["flags_rc"] = types.ModuleType("flags_rc")
    spec = importlib.util.spec_from_file_location("d64_lisp_test_base", ROOT / "d64_dism.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class LispCompilerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d64 = load_d64_module()

    def test_grammar_shape(self):
        forms = parse_lisp("(println (+ 1 2)) 'nil ; comment\n")
        self.assertEqual(len(forms), 2)
        self.assertEqual(forms[0].kind, "list")
        self.assertEqual(forms[1].kind, "quote")

    def test_pe32_and_pe64_end_to_end(self):
        source = """
(setq counter 2)
(defun square (x) (* x x))
(defun main ()
  (println "LISP")
  (println (square counter)))
(start main)
"""
        for target in ("pe32", "pe64"):
            generated = compile_lisp_to_assembly(source, filename="test.lisp", target=target)
            self.assertEqual(generated.source_kind, "program")
            if target == "pe32":
                obj = self.d64.assemble_pe32_coff_object(generated.assembly)
                image = self.d64.link_coff32_objects([obj], entry_symbol="_start", gui=False).executable
                expected_machine, expected_magic = 0x014C, 0x010B
            else:
                obj = self.d64.assemble_pe64_coff_object(generated.assembly)
                image = self.d64.link_coff64_objects([obj], entry_symbol="_start", gui=False).executable
                expected_machine, expected_magic = 0x8664, 0x020B
            pe = struct.unpack_from("<I", image, 0x3C)[0]
            self.assertEqual(struct.unpack_from("<H", image, pe + 4)[0], expected_machine)
            self.assertEqual(struct.unpack_from("<H", image, pe + 24)[0], expected_magic)
            self.assertEqual(struct.unpack_from("<H", image, pe + 24 + 0x44)[0], 3)

    def test_separate_module_links(self):
        unit_source = "(defun cube (x) (* x x x))\n"
        main_source = "(defun main () (println (cube 4)))\n(start main)\n"
        for target in ("pe32", "pe64"):
            unit = compile_lisp_to_assembly(unit_source, filename="math.lisp", target=target)
            main = compile_lisp_to_assembly(main_source, filename="main.lisp", target=target)
            self.assertEqual(unit.source_kind, "unit")
            self.assertEqual(main.source_kind, "program")
            if target == "pe32":
                uo = self.d64.assemble_pe32_coff_object(unit.assembly)
                mo = self.d64.assemble_pe32_coff_object(main.assembly)
                linked = self.d64.link_coff32_objects([mo, uo], entry_symbol="_start", gui=False)
            else:
                uo = self.d64.assemble_pe64_coff_object(unit.assembly)
                mo = self.d64.assemble_pe64_coff_object(main.assembly)
                linked = self.d64.link_coff64_objects([mo, uo], entry_symbol="_start", gui=False)
            self.assertEqual(linked.executable[:2], b"MZ")

    def test_recursive_function_links_for_both_windows_targets(self):
        source = """
(defun factorial (n)
  (if (<= n 1)
      1
      (* n (factorial (- n 1)))))
(defun main () (println (factorial 5)))
(start main)
"""
        for target in ("pe32", "pe64"):
            generated = compile_lisp_to_assembly(
                source, filename="factorial.lisp", target=target
            )
            self.assertIn("call lisp_func_factorial", generated.assembly)
            if target == "pe32":
                obj = self.d64.assemble_pe32_coff_object(generated.assembly)
                linked = self.d64.link_coff32_objects(
                    [obj], entry_symbol="_start", gui=False
                )
            else:
                obj = self.d64.assemble_pe64_coff_object(generated.assembly)
                linked = self.d64.link_coff64_objects(
                    [obj], entry_symbol="_start", gui=False
                )
            self.assertEqual(linked.executable[:2], b"MZ")

    def test_lisp_punctuation_is_mangled_for_coff(self):
        source = """
(setq my-value 5)
(defun add-one (x) (+ x 1))
(defun main () (println (add-one my-value)))
(start main)
"""
        generated = compile_lisp_to_assembly(source, filename="dash.lisp", target="pe64")
        self.assertIn("lisp_func_add_x2d_one", generated.assembly)
        self.assertIn("lisp_var_my_x2d_value", generated.assembly)
        self.d64.assemble_pe64_coff_object(generated.assembly)

    def test_reject_non_windows_target(self):
        with self.assertRaises(LispCompilerError):
            compile_lisp_to_assembly("(println 1)", filename="x.lisp", target="c64")


if __name__ == "__main__":
    unittest.main()

class LispGuiCompilerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d64 = load_d64_module()

    def test_console_and_gui_subsystems_for_both_targets(self):
        source = '(defun main () (println "mode") (println 42))\n(start main)\n'
        for target in ("pe32", "pe64"):
            for mode, subsystem in (("Console", 3), ("GUI", 2)):
                generated = compile_lisp_to_assembly(
                    source,
                    filename="mode.lisp",
                    target=target,
                    windows_application_mode=mode,
                )
                if mode == "Console":
                    self.assertIn("AllocConsole", generated.assembly)
                    self.assertIn("WriteFile", generated.assembly)
                    self.assertNotIn("MessageBoxA", generated.assembly)
                else:
                    self.assertNotIn("AllocConsole", generated.assembly)
                    self.assertNotIn("WriteFile", generated.assembly)
                    self.assertIn("MessageBoxA", generated.assembly)

                if target == "pe32":
                    obj = self.d64.assemble_pe32_coff_object(generated.assembly)
                    image = self.d64.link_coff32_objects(
                        [obj], entry_symbol="_start", gui=(mode == "GUI")
                    ).executable
                else:
                    obj = self.d64.assemble_pe64_coff_object(generated.assembly)
                    image = self.d64.link_coff64_objects(
                        [obj], entry_symbol="_start", gui=(mode == "GUI")
                    ).executable
                pe = struct.unpack_from("<I", image, 0x3C)[0]
                self.assertEqual(
                    struct.unpack_from("<H", image, pe + 24 + 0x44)[0],
                    subsystem,
                )


    def test_read_returns_string_and_links_console_for_both_targets(self):
        source = """
(defun main ()
  (println "Input:")
  (setq text (read))
  (println text))
(start main)
"""
        for target in ("pe32", "pe64"):
            generated = compile_lisp_to_assembly(
                source, filename="read.lisp", target=target,
                windows_application_mode="Console",
            )
            self.assertIn('import ReadFile, "kernel32.dll", "ReadFile"', generated.assembly)
            self.assertIn('import VirtualAlloc, "kernel32.dll", "VirtualAlloc"', generated.assembly)
            self.assertIn("call __lisp_read_text", generated.assembly)
            self.assertIn("__lisp_stdin:", generated.assembly)
            self.assertIn("__lisp_input_buffer:", generated.assembly)
            if target == "pe32":
                obj = self.d64.assemble_pe32_coff_object(generated.assembly)
                linked = self.d64.link_coff32_objects([obj], entry_symbol="_start", gui=False)
            else:
                obj = self.d64.assemble_pe64_coff_object(generated.assembly)
                linked = self.d64.link_coff64_objects([obj], entry_symbol="_start", gui=False)
            self.assertEqual(linked.executable[:2], b"MZ")

    def test_read_rejected_for_gui(self):
        with self.assertRaises(LispCompilerError):
            compile_lisp_to_assembly(
                "(defun main () (read)) (start main)",
                filename="read_gui.lisp", target="pe64",
                windows_application_mode="GUI",
            )

    def test_reject_unsupported_lisp_windows_mode(self):
        with self.assertRaises(LispCompilerError):
            compile_lisp_to_assembly(
                "(println 1)",
                filename="x.lisp",
                target="pe32",
                windows_application_mode="Direct2D",
            )

    def test_d64_lisp_assemble_path_and_navy_code_editor_source(self):
        source = (ROOT / "d64_dism.py").read_text(encoding="utf-8")
        self.assertIn("or document.is_lisp_document", source)
        self.assertIn("mode_text in {\"Console\", \"GUI\"}", source)
        self.assertIn("windows_application_mode=document.windows_application_mode", source)
        self.assertIn("palette.setColor(QPalette.Base, QColor(0, 0, 128))", source)
        self.assertIn("or code_suffix in self.LISP_EXTENSIONS", source)
        self.assertIn("or code_suffix in self.ASSEMBLER_EXTENSIONS", source)
        self.assertIn("QColor(255, 255, 0) if asm_editor", source)
        self.assertIn("print|println|read|", source)
