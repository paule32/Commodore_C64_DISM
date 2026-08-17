from __future__ import annotations

import importlib.util
import sys
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from d64prolog.compiler import PrologCompilerError, _Resolver, compile_prolog_to_assembly, parse_prolog
from d64prolog.knowledge import PrologKnowledgeBase


def load_d64():
    name = "d64_stage58_test_module"
    if name in sys.modules:
        return sys.modules[name]
    sys.modules.setdefault("flags_rc", types.ModuleType("flags_rc"))
    spec = importlib.util.spec_from_file_location(name, ROOT / "d64_dism.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class PrologKnowledgeConcatUmlautAsmMiniMapStage58Tests(unittest.TestCase):
    def test_named_knowledge_string_concat_is_materialized(self):
        source = '''
_apfel = "Ein Apfel ist ".
_apfel_gesund = _apfel + "gesund".
_apfel_essbar = _apfel + "essbar".
_apfel_obst = _apfel + "Obstsorte".
'''
        clauses, _ = parse_prolog(source, filename="obst.pl")
        values = {
            str(c.head.args[0].value): c.head.args[1]
            for c in clauses
            if c.head.kind == "compound" and c.head.value == "d64_knowledge_value"
        }
        self.assertEqual(values["apfel_gesund"].kind, "string")
        self.assertEqual(values["apfel_gesund"].value, "Ein Apfel ist gesund")
        self.assertEqual(values["apfel_essbar"].value, "Ein Apfel ist essbar")
        self.assertEqual(values["apfel_obst"].value, "Ein Apfel ist Obstsorte")

    def test_forward_reference_is_resolved_and_cycle_is_rejected(self):
        clauses, _ = parse_prolog(
            '_b = _a + " B".\n_a = "A".\n', filename="forward.pl"
        )
        b = next(c for c in clauses if c.head.args[0].value == "b")
        self.assertEqual(b.head.args[1].value, "A B")
        with self.assertRaises(PrologCompilerError):
            parse_prolog('_a = _b + "a".\n_b = _a + "b".\n', filename="cycle.pl")

    def test_german_umlaut_named_knowledge_and_atom_are_accepted(self):
        source = '''
_äpfel = "sind gesund".
äpfel(obst).
main :- writeln(_äpfel).
'''
        clauses, _ = parse_prolog(source, filename="umlaut.pl")
        named = next(c for c in clauses if c.head.kind == "compound" and c.head.value == "d64_knowledge_value")
        self.assertEqual(named.head.args[0].value, "äpfel")
        self.assertEqual(named.head.args[1].value, "sind gesund")
        self.assertTrue(any(c.head.value == "äpfel" for c in clauses))
        main = next(c for c in clauses if c.head.kind == "atom" and c.head.value == "main")
        solutions = list(_Resolver(clauses, filename="umlaut.pl").solve(main.body))
        self.assertEqual(solutions[0][1], ("sind gesund\r\n",))

    def test_underscore_uppercase_umlaut_remains_variable(self):
        clauses, _ = parse_prolog('p(_Äpfel).', filename="vars.pl")
        self.assertEqual(clauses[0].head.args[0].kind, "var")
        self.assertEqual(clauses[0].head.args[0].value, "_Äpfel")

    def test_knowledge_browser_exposes_umlaut_value(self):
        model = PrologKnowledgeBase.from_source('_äpfel = "sind gesund".\n', filename="wissen.pl")
        pred = next(p for p in model.predicates if p.name == "_äpfel")
        self.assertEqual(model.alternatives_for_level(pred, ()), ("sind gesund",))

    def test_runtime_contains_external_string_materializer_and_utf8_normalizer(self):
        asm = compile_prolog_to_assembly("main :- true.", filename="stage58.pl", target="pe32").assembly
        self.assertIn("__rt_parse_knowledge_string_expr:", asm)
        self.assertIn("__rt_db_lookup_knowledge_string:", asm)
        self.assertIn("__rt_knowledge_concat_append:", asm)
        self.assertIn("__rt_is_knowledge_start:", asm)
        self.assertIn("__rt_parse_token_utf8_228:", asm)  # ä -> Latin-1 E4

    def test_antlr_and_editor_patterns_include_german_umlauts(self):
        lexer = (ROOT / "d64prolog" / "grammar" / "PrologLexer.g4").read_text(encoding="utf-8")
        gui = (ROOT / "d64_dism.py").read_text(encoding="utf-8")
        self.assertIn("[a-zäöüß]", lexer)
        self.assertIn("[A-Z_ÄÖÜ]", lexer)
        self.assertIn("_[a-zäöüß]", gui)

    def test_assembler_editor_reuses_source_editor_with_minimap(self):
        gui = (ROOT / "d64_dism.py").read_text(encoding="utf-8")
        self.assertIn("self.generated_assembly_editor_container = SourceEditorWithMiniMap(", gui)
        self.assertIn("self.generated_assembly_editor_container.editor", gui)
        self.assertIn("self.generated_assembly_editor_container.minimap", gui)
        self.assertIn("generated_assembly_layout.addWidget(\n                self.generated_assembly_editor_container,", gui)


    def test_knowledge_browser_alternatives_use_direct_combobox(self):
        gui = (ROOT / "d64_dism.py").read_text(encoding="utf-8")
        self.assertIn('self.alternative_combo = QComboBox(right_panel)', gui)
        self.assertIn('self.alternative_combo.activated[str].connect(', gui)
        self.assertIn('self.query_edit.setText(value)', gui)
        self.assertIn('self.arrow_button.setVisible(bool(self.alternatives))', gui)

    def test_knowledge_browser_large_alternative_list_is_searchable(self):
        gui = (ROOT / "d64_dism.py").read_text(encoding="utf-8")
        self.assertIn('searchable = len(values) > 10', gui)
        self.assertIn('completer.setFilterMode(Qt.MatchContains)', gui)
        self.assertIn('completer.setCaseSensitivity(Qt.CaseInsensitive)', gui)
        self.assertIn('line_edit.setPlaceholderText("Alternative suchen …")', gui)

    def test_knowledge_browser_alternative_status_is_redrawn(self):
        gui = (ROOT / "d64_dism.py").read_text(encoding="utf-8")
        self.assertIn('"weitere Alternativen vorhanden"', gui)
        self.assertIn('"keine weiteren Alternativen"', gui)
        self.assertIn('self._clear_alternative_controls()\n            if level_index < 0:', gui)
        self.assertIn('self.alternative_status_label.setVisible(False)', gui)

    def test_progressive_alternatives_follow_prefix(self):
        model = PrologKnowledgeBase.from_source(
            "obst(apfel, gesund, rot).\n"
            "obst(apfel, gesund, gruen).\n"
            "obst(apfel, essbar, ja).\n"
            "obst(birne, gesund, gruen).\n",
            filename="alternativen.pl",
        )
        predicate = next(p for p in model.predicates if p.name == "obst")
        self.assertEqual(
            model.alternatives_for_level(predicate, ()),
            ("apfel", "birne"),
        )
        apfel = model.parse_value("apfel")
        gesund = model.parse_value("gesund")
        self.assertEqual(
            model.alternatives_for_level(predicate, (apfel,)),
            ("essbar", "gesund"),
        )
        self.assertEqual(
            model.alternatives_for_level(predicate, (apfel, gesund)),
            ("gruen", "rot"),
        )

    def test_stage58_program_links_pe32_and_pe64(self):
        d64 = load_d64()
        source = '''
_apfel = "Ein Apfel ist ".
_apfel_gesund = _apfel + "gesund".
_äpfel = "sind gesund".
main :- writeln(_apfel_gesund), writeln(_äpfel).
'''
        for target in ("pe32", "pe64"):
            with self.subTest(target=target):
                result = compile_prolog_to_assembly(source, filename="stage58.pl", target=target)
                if target == "pe32":
                    obj = d64.assemble_pe32_object_source(result.assembly, filename="stage58.asm")
                    raw = d64.write_coff32_object(obj)
                    program = d64.link_coff32_objects((raw,), entry_symbol="_start", gui=False)
                else:
                    obj = d64.assemble_pe64_object_source(result.assembly, filename="stage58.asm")
                    raw = d64.write_coff64_object(obj)
                    program = d64.link_coff64_objects((raw,), entry_symbol="_start", gui=False)
                self.assertTrue(program.executable.startswith(b"MZ"))


if __name__ == "__main__":
    unittest.main()
