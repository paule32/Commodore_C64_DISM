from __future__ import annotations

import importlib.util
import sys
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from d64prolog.compiler import (
    PrologCompilerError,
    _Resolver,
    compile_prolog_to_assembly,
    parse_prolog,
)
from d64prolog.knowledge import PrologKnowledgeBase


def load_d64():
    name = "d64_stage56_test_module"
    if name in sys.modules:
        return sys.modules[name]
    sys.modules.setdefault("flags_rc", types.ModuleType("flags_rc"))
    spec = importlib.util.spec_from_file_location(name, ROOT / "d64_dism.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class PrologNamedKnowledgeStage56Tests(unittest.TestCase):
    def test_assignment_is_lowered_to_database_owned_predicate(self):
        clauses, queries = parse_prolog('_apfel = "Ein Apfel ist gesund".', filename="wissen.pl")
        self.assertFalse(queries)
        self.assertEqual(len(clauses), 1)
        head = clauses[0].head
        self.assertEqual((head.kind, head.value, len(head.args)), ("compound", "d64_knowledge_value", 2))
        self.assertEqual(head.args[0].value, "apfel")
        self.assertEqual(head.args[1].value, "Ein Apfel ist gesund")

    def test_bare_underscore_and_underscore_capital_remain_variables(self):
        clauses, _ = parse_prolog('p(_, _Name).', filename="vars.pl")
        args = clauses[0].head.args
        self.assertEqual(args[0].kind, "var")
        self.assertEqual(args[1].kind, "var")
        self.assertTrue(str(args[0].value).startswith("__anon_"))
        self.assertEqual(args[1].value, "_Name")

    def test_writeln_named_value_is_resolved_at_goal_position(self):
        source = '''
_apfel = "Ein Apfel ist gesund".
main :- writeln(_apfel).
'''
        clauses, _ = parse_prolog(source, filename="main.pl")
        main = next(c for c in clauses if c.head.kind == "atom" and c.head.value == "main")
        self.assertEqual(main.body[0].value, "d64_knowledge_value")
        self.assertEqual(main.body[1].value, "writeln")
        resolver = _Resolver(clauses, filename="main.pl")
        solutions = list(resolver.solve(main.body))
        self.assertEqual(solutions[0][1], ("Ein Apfel ist gesund\r\n",))

    def test_database_open_stays_before_named_value_lookup(self):
        source = '''
main :- database_open("patient.pl", DB), writeln(_name), database_close(DB).
'''
        clauses, _ = parse_prolog(source, filename="main.pl")
        main = clauses[0]
        names = [str(goal.value) for goal in main.body]
        self.assertEqual(
            names,
            ["database_open", "d64_knowledge_value", "writeln", "database_close"],
        )

    def test_unification_with_named_value(self):
        source = '''
_apfel = gesund.
?- X = _apfel.
'''
        clauses, queries = parse_prolog(source, filename="query.pl")
        resolver = _Resolver(clauses, filename="query.pl")
        solutions = list(resolver.solve(queries[0].goals))
        self.assertTrue(solutions)
        self.assertEqual(solutions[0][0]["X"].value, "gesund")

    def test_duplicate_named_assignment_in_one_source_is_rejected(self):
        with self.assertRaises(PrologCompilerError):
            parse_prolog('_apfel = gesund.\n_apfel = rot.\n', filename="dup.pl")

    def test_knowledge_browser_exposes_named_value_not_internal_predicate(self):
        model = PrologKnowledgeBase.from_source(
            '_apfel = "Ein Apfel ist gesund".\napfel(gesund).\n', filename="wissen.pl"
        )
        names = [p.display_name for p in model.predicates]
        self.assertIn("_apfel", names)
        self.assertIn("apfel/1", names)
        self.assertNotIn("d64_knowledge_value/2", names)
        pred = next(p for p in model.predicates if p.name == "_apfel")
        self.assertEqual(model.alternatives_for_level(pred, ()), ('Ein Apfel ist gesund',))

    def test_native_external_loader_has_stage56_assignment_parser_and_pretty_save(self):
        asm = compile_prolog_to_assembly("main :- true.", filename="stage56.pl", target="pe32").assembly
        self.assertIn("__rt_parse_knowledge_assignment:", asm)
        self.assertIn("call __rt_parse_knowledge_assignment", asm)
        self.assertIn("__rt_emit_clause_knowledge:", asm)
        self.assertIn("__prolog_text_knowledge_sep", asm)


    def test_static_named_value_is_not_skipped_as_a_builtin(self):
        asm = compile_prolog_to_assembly(
            '_apfel = "gesund".\nmain :- writeln(_apfel).',
            filename="static_knowledge.pl",
            target="pe32",
        ).assembly
        dispatch = asm.split("__rt_try_user_dispatch:", 1)[1].split("__rt_try_user_dynamic:", 1)[0]
        self.assertIn("call __prolog_clause_0_build", dispatch)

    def test_stage56_antlr_grammar_and_editor_highlighter_are_in_sync(self):
        lexer = (ROOT / "d64prolog" / "grammar" / "PrologLexer.g4").read_text(encoding="utf-8")
        parser = (ROOT / "d64prolog" / "grammar" / "PrologParser.g4").read_text(encoding="utf-8")
        gui = (ROOT / "d64_dism.py").read_text(encoding="utf-8")
        self.assertIn("KNOWLEDGE   : '_' [a-z]", lexer)
        self.assertIn("KNOWLEDGE EQ term DOT", parser)
        self.assertIn("PROLOG_KNOWLEDGE_PATTERN", gui)

    def test_named_knowledge_program_links_pe32_and_pe64(self):
        d64 = load_d64()
        source = '''
_apfel = "Ein Apfel ist gesund".
main :- writeln(_apfel), X = _apfel, writeln(X).
'''
        for target in ("pe32", "pe64"):
            with self.subTest(target=target):
                result = compile_prolog_to_assembly(source, filename="knowledge_value.pl", target=target)
                if target == "pe32":
                    obj = d64.assemble_pe32_object_source(result.assembly, filename="knowledge_value.asm")
                    raw = d64.write_coff32_object(obj)
                    program = d64.link_coff32_objects((raw,), entry_symbol="_start", gui=False)
                else:
                    obj = d64.assemble_pe64_object_source(result.assembly, filename="knowledge_value.asm")
                    raw = d64.write_coff64_object(obj)
                    program = d64.link_coff64_objects((raw,), entry_symbol="_start", gui=False)
                self.assertTrue(program.executable.startswith(b"MZ"))


if __name__ == "__main__":
    unittest.main()
