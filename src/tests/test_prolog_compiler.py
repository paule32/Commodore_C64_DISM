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

from d64prolog import PrologCompilerError, compile_prolog_to_assembly, parse_prolog
from d64prolog.compiler import PrologCompiler, _term_text


def load_d64():
    if "d64_test_module" in sys.modules:
        return sys.modules["d64_test_module"]
    sys.modules.setdefault("flags_rc", types.ModuleType("flags_rc"))
    spec = importlib.util.spec_from_file_location("d64_test_module", ROOT / "d64_dism.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["d64_test_module"] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def pe_info(image: bytes):
    pe = struct.unpack_from("<I", image, 0x3C)[0]
    machine = struct.unpack_from("<H", image, pe + 4)[0]
    opt = pe + 4 + 20
    magic = struct.unpack_from("<H", image, opt)[0]
    subsystem = struct.unpack_from("<H", image, opt + 0x44)[0]
    return machine, magic, subsystem


class PrologCompilerTests(unittest.TestCase):
    def test_parse_facts_rules_queries_and_lists(self):
        clauses, queries = parse_prolog(
            "list([a,b|T]).\nancestor(X,Y) :- edge(X,Y).\n?- list([a,b,c]).\n",
            filename="lists.pl",
        )
        self.assertEqual(len(clauses), 2)
        self.assertEqual(len(queries), 1)
        list_arg = clauses[0].head.args[0]
        self.assertEqual(list_arg.kind, "compound")
        self.assertEqual(list_arg.value, ".")

    def test_native_runtime_labels_are_emitted(self):
        source = """
parent(john, mary).
parent(mary, susan).
ancestor(X, Y) :- parent(X, Y).
ancestor(X, Y) :- parent(X, Z), ancestor(Z, Y).
?- ancestor(john, Who).
"""
        result = compile_prolog_to_assembly(source, filename="family.pl", target="pe32")
        asm = result.assembly
        for marker in (
            "__rt_unify:",
            "__rt_choice_push:",
            "__rt_choice_restore_pop:",
            "__rt_trail_push:",
            "__rt_untrail_to:",
            "__rt_solve_goals:",
            "__prolog_clause_0_build:",
            "__prolog_query_0_build:",
        ):
            self.assertIn(marker, asm)
        # The old compile-time transcript is intentionally gone.
        self.assertNotIn("Who = mary", asm)

    def test_assert_retract_and_dynamic_heap_runtime_exist(self):
        result = compile_prolog_to_assembly(
            "main :- assert(parent(X,bob)), retract(parent(A,B)), writeln([A,B]).\n",
            filename="dynamic.pl",
            target="pe64",
        )
        asm = result.assembly
        for marker in (
            "__rt_assert:",
            "__rt_retract:",
            "__rt_dyn_copy_ground:",
            "__rt_dyn_clone:",
            "__prolog_dyn_heap_top",
            "__prolog_dyn_copy_var_count",
            "__prolog_dyn_clone_var_count",
        ):
            self.assertIn(marker, asm)

    def test_console_repl_and_runtime_query_parser_exist(self):
        result = compile_prolog_to_assembly(
            "parent(john,mary).\n",
            filename="repl.pl",
            target="pe32",
            windows_application_mode="Console",
        )
        asm = result.assembly
        for marker in (
            "__rt_repl:",
            "__rt_parse_query:",
            "__rt_parse_term:",
            "__rt_parse_list_elements:",
            "__rt_intern_atom:",
            'import ReadFile, "kernel32.dll", "ReadFile"',
            "__prolog_text_prompt:",
        ):
            self.assertIn(marker, asm)

    def test_gui_keeps_runtime_and_database_file_io_but_has_no_console_repl(self):
        result = compile_prolog_to_assembly(
            "p(a).\n?- p(X).\n",
            filename="gui.pl",
            target="pe64",
            windows_application_mode="GUI",
        )
        asm = result.assembly
        self.assertIn("__rt_unify:", asm)
        self.assertIn('import MessageBoxA, "user32.dll", "MessageBoxA"', asm)
        # External knowledge databases are available in GUI programs as well,
        # so the database subsystem intentionally keeps file I/O imports.
        self.assertIn('import ReadFile, "kernel32.dll", "ReadFile"', asm)
        self.assertIn('import CreateFileA, "kernel32.dll", "CreateFileA"', asm)
        self.assertIn("__rt_database_open:", asm)
        self.assertNotIn("__rt_repl:", asm)

    def test_pe32_and_pe32plus_console_and_gui_link(self):
        d64 = load_d64()
        source = """
parent(john,mary).
ancestor(X,Y) :- parent(X,Y).
?- ancestor(john, Who).
"""
        for target, machine, magic in (
            ("pe32", 0x014C, 0x010B),
            ("pe64", 0x8664, 0x020B),
        ):
            for mode, subsystem in (("Console", 3), ("GUI", 2)):
                with self.subTest(target=target, mode=mode):
                    result = compile_prolog_to_assembly(
                        source,
                        filename="x.pl",
                        target=target,
                        windows_application_mode=mode,
                    )
                    if target == "pe32":
                        obj = d64.assemble_pe32_object_source(result.assembly, filename="x.asm")
                        raw = d64.write_coff32_object(obj)
                        program = d64.link_coff32_objects((raw,), entry_symbol="_start", gui=(mode == "GUI"))
                    else:
                        obj = d64.assemble_pe64_object_source(result.assembly, filename="x.asm")
                        raw = d64.write_coff64_object(obj)
                        program = d64.link_coff64_objects((raw,), entry_symbol="_start", gui=(mode == "GUI"))
                    self.assertEqual(pe_info(program.executable), (machine, magic, subsystem))


    def test_dynamic_struct_clone_returns_success_for_asserted_compounds(self):
        d64 = load_d64()
        source = (
            "main :-\n"
            "    assert(parent(tom, lisa)),\n"
            "    assert(parent(lisa, emma)),\n"
            "    parent(tom, X),\n"
            "    writeln(X),\n"
            "    retract(parent(tom, X)),\n"
            "    repl.\n"
        )
        for target in ("pe32", "pe64"):
            with self.subTest(target=target):
                result = compile_prolog_to_assembly(
                    source, filename="dynamic_parent.pl", target=target,
                    windows_application_mode="Console",
                )
                asm = result.assembly
                clone_struct = asm.split("__rt_dyn_clone_struct:", 1)[1].split("__rt_dyn_clone_fail:", 1)[0]
                self.assertIn("call __rt_make_struct", clone_struct)
                self.assertIn("jmp __rt_dyn_clone_done", clone_struct)
                if target == "pe32":
                    obj = d64.assemble_pe32_object_source(asm, filename="dynamic_parent.asm")
                    raw = d64.write_coff32_object(obj)
                    program = d64.link_coff32_objects((raw,), entry_symbol="_start", gui=False)
                else:
                    obj = d64.assemble_pe64_object_source(asm, filename="dynamic_parent.asm")
                    raw = d64.write_coff64_object(obj)
                    program = d64.link_coff64_objects((raw,), entry_symbol="_start", gui=False)
                self.assertTrue(program.executable.startswith(b"MZ"))

    def test_standard_member_is_available_without_source_definition(self):
        compiler = PrologCompiler(
            "", filename="member_repl.pl", target="pe32",
            windows_application_mode="Console",
        )
        _clauses, queries = parse_prolog(
            "?- member(X,[a,b,c]).", filename="member_query.pl"
        )
        query = queries[0]
        solutions = list(compiler.resolver.solve(query.goals))
        values = [
            _term_text(query.goals[0].args[0], env)
            for env, _effects in solutions
        ]
        self.assertEqual(values, ["a", "b", "c"])
        self.assertEqual(len(compiler.resolver.by_predicate[("member", 2)]), 2)

    def test_standard_member_links_pe32_and_pe32plus(self):
        d64 = load_d64()
        source = "main :- repl.\n"
        for target in ("pe32", "pe64"):
            with self.subTest(target=target):
                result = compile_prolog_to_assembly(
                    source, filename="member_runtime.pl", target=target,
                    windows_application_mode="Console",
                )
                self.assertIn("member/2", result.predicates)
                self.assertIn("member/2", "\n".join(result.notes))
                if target == "pe32":
                    obj = d64.assemble_pe32_object_source(result.assembly, filename="member_runtime.asm")
                    raw = d64.write_coff32_object(obj)
                    program = d64.link_coff32_objects((raw,), entry_symbol="_start", gui=False)
                else:
                    obj = d64.assemble_pe64_object_source(result.assembly, filename="member_runtime.asm")
                    raw = d64.write_coff64_object(obj)
                    program = d64.link_coff64_objects((raw,), entry_symbol="_start", gui=False)
                self.assertTrue(program.executable.startswith(b"MZ"))

    def test_user_member_definition_replaces_standard_library_member(self):
        compiler = PrologCompiler(
            "member(custom, _).\n", filename="custom_member.pl", target="pe32",
            windows_application_mode="Console",
        )
        self.assertEqual(len(compiler.resolver.by_predicate[("member", 2)]), 1)

    def test_runtime_supports_lists_in_both_internal_assemblers(self):
        d64 = load_d64()
        source = "member_head([H|_], H).\n?- member_head([a,b,c], X).\n"
        for target in ("pe32", "pe64"):
            result = compile_prolog_to_assembly(source, filename="list.pl", target=target)
            if target == "pe32":
                obj = d64.assemble_pe32_object_source(result.assembly, filename="list.asm")
                self.assertGreater(len(d64.write_coff32_object(obj)), 0)
            else:
                obj = d64.assemble_pe64_object_source(result.assembly, filename="list.asm")
                self.assertGreater(len(d64.write_coff64_object(obj)), 0)


    def test_stage2_parser_precedence_dynamic_rules_and_disjunction(self):
        clauses, queries = parse_prolog(
            "main :- assert((dyn(X) :- p(X), q(X))), asserta(a(1)), assertz(a(2)).\n"
            "?- X is -(3+4)*2, (p(X); q(X)).\n",
            filename="stage2.pl",
        )
        self.assertEqual(len(clauses), 1)
        self.assertEqual(len(queries), 1)
        asserted = clauses[0].body[0].args[0]
        self.assertEqual((asserted.kind, asserted.value), ("compound", ":-"))
        self.assertEqual(asserted.args[1].value, ",")
        self.assertEqual(queries[0].goals[0].value, "is")
        self.assertEqual(queries[0].goals[0].args[1].value, "*")
        self.assertEqual(queries[0].goals[1].value, ";")

    def test_stage2_runtime_labels_are_emitted(self):
        result = compile_prolog_to_assembly(
            "p(1). p(2). q(X) :- (p(X); X is 1+2*3), X >= 1.\n"
            "main :- asserta((dyn(X) :- p(X))), assertz(dyn(9)), "
            "retract((dyn(A) :- B)), gc, repl.\n",
            filename="stage2.pl", target="pe64", windows_application_mode="Console",
        )
        asm = result.assembly
        for marker in (
            "__rt_occurs:",
            "__rt_equal_terms:",
            "__rt_eval_arith:",
            "__rt_goal_expr_to_chain:",
            "__rt_asserta:",
            "__rt_assertz:",
            "__rt_gc_dynamic:",
            "__rt_dyn_db_compact:",
            "__rt_parse_mul:",
            "__rt_parse_add:",
            "__rt_parse_relation:",
            "__rt_parse_disjunction:",
            "__rt_parse_rule_expr:",
            "__rt_emit_solution_more:",
            "__prolog_text_more_prompt:",
        ):
            self.assertIn(marker, asm)

    def test_stage2_rich_runtime_links_all_windows_modes(self):
        d64 = load_d64()
        source = (
            "p(1). p(2). p(3).\n"
            "q(X) :- (p(X); X is 3+4*2), X >= 1.\n"
            "r(X) :- p(X), !.\n"
            "main :- asserta((dyn(X) :- p(X))), assertz(dyn(9)), "
            "q(Y), writeln(Y), retract((dyn(A):-B)), gc.\n"
        )
        for target, machine, magic in (("pe32", 0x014C, 0x010B), ("pe64", 0x8664, 0x020B)):
            for mode, subsystem in (("Console", 3), ("GUI", 2)):
                with self.subTest(target=target, mode=mode):
                    result = compile_prolog_to_assembly(source, filename="stage2.pl", target=target, windows_application_mode=mode)
                    if target == "pe32":
                        obj = d64.assemble_pe32_object_source(result.assembly, filename="stage2.asm")
                        raw = d64.write_coff32_object(obj)
                        program = d64.link_coff32_objects((raw,), entry_symbol="_start", gui=(mode == "GUI"))
                    else:
                        obj = d64.assemble_pe64_object_source(result.assembly, filename="stage2.asm")
                        raw = d64.write_coff64_object(obj)
                        program = d64.link_coff64_objects((raw,), entry_symbol="_start", gui=(mode == "GUI"))
                    self.assertEqual(pe_info(program.executable), (machine, magic, subsystem))

    def test_stage2_notes_describe_completed_runtime(self):
        result = compile_prolog_to_assembly(
            "p(a).\n", filename="notes.pl", target="pe32", windows_application_mode="Console"
        )
        text = "\n".join(result.notes)
        self.assertIn("Fakten und Regeln", text)
        self.assertIn("Occurs-Check", text)
        self.assertIn("asserta fuegt vorne", text)
        self.assertIn("';'", text)


    def test_runtime_unify_keeps_right_handle_out_of_ecx_scratch(self):
        result = compile_prolog_to_assembly(
            "?- X is 1 + 2.\n", filename="is_unify.pl", target="pe64",
            windows_application_mode="Console",
        )
        asm = result.assembly
        start = asm.index("__rt_unify:")
        end = asm.index("__rt_equal_terms:", start)
        block = asm[start:end]
        # __rt_node_ptr clobbers ECX/RCX, therefore the dereferenced right
        # term must live in EBX while tags and recursive nodes are inspected.
        self.assertIn("mov ebx, eax", block)
        self.assertIn("push rbx\n    push rsi\n    call __rt_bind_var", block)
        self.assertIn("push rcx\n    mov eax, edx\n    call __rt_node_ptr", block)

    def test_is_query_assembles_and_links_both_windows_targets_after_unify_fix(self):
        d64 = load_d64()
        source = "?- X is 1 + 2.\n"
        for target in ("pe32", "pe64"):
            with self.subTest(target=target):
                result = compile_prolog_to_assembly(
                    source, filename="is_query.pl", target=target,
                    windows_application_mode="Console",
                )
                if target == "pe32":
                    obj = d64.assemble_pe32_object_source(result.assembly, filename="is_query.asm")
                    raw = d64.write_coff32_object(obj)
                    program = d64.link_coff32_objects((raw,), entry_symbol="_start", gui=False)
                else:
                    obj = d64.assemble_pe64_object_source(result.assembly, filename="is_query.asm")
                    raw = d64.write_coff64_object(obj)
                    program = d64.link_coff64_objects((raw,), entry_symbol="_start", gui=False)
                self.assertTrue(program.executable.startswith(b"MZ"))
    def test_prolog_is_windows_only(self):
        with self.assertRaises(PrologCompilerError):
            compile_prolog_to_assembly("main.", filename="x.pl", target="c64")

    def test_project_ini_persists_prolog_category(self):
        d64 = load_d64()
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            project = Path(td) / "demo.pro"
            source = Path(td) / "main.pl"
            source.write_text("main.\n", encoding="utf-8")
            entries = d64.empty_project_entries()
            entries["prolog"] = [{"title": "main.pl", "path": str(source)}]
            d64.save_project_ini(project, entries)
            loaded = d64.load_project_ini(project)
            self.assertEqual(loaded["prolog"][0]["title"], "main.pl")
            self.assertEqual(Path(loaded["prolog"][0]["path"]), source.resolve())

    def test_gui_integration_markers_exist(self):
        text = (ROOT / "d64_dism.py").read_text(encoding="utf-8")
        for marker in (
            '("prolog", "PROLOG-Programme", (".pl", ".prolog"))',
            '"Projekt: PROLOG"',
            '"Prolog-Programm"',
            'PROLOG_EXTENSIONS    = {".pl", ".prolog"}',
            'from d64prolog import PrologCompilerError, compile_prolog_to_assembly',
            'return self._compile_prolog_document(document)',
        ):
            self.assertIn(marker, text)

    def test_pe64_rip_relative_symbol_memory_immediates_use_rel32_tail(self):
        d64 = load_d64()
        source = (
            "section .text\n"
            "global _start\n"
            "_start:\n"
            "    add dword ptr [counter], 2\n"
            "    mov dword ptr [counter], 7\n"
            "    shl dword ptr [counter], 1\n"
            "    ret\n"
            "section .bss\n"
            "counter:\n"
            "    resd 1\n"
        )
        obj = d64.assemble_pe64_object_source(source, filename="rel32_tail.asm")
        kinds = [rel.relocation_type for rel in obj.relocations]
        self.assertEqual(
            kinds,
            [
                d64.IMAGE_REL_AMD64_REL32_4,
                d64.IMAGE_REL_AMD64_REL32_4,
                d64.IMAGE_REL_AMD64_REL32_1,
            ],
        )
        raw = d64.write_coff64_object(obj)
        program = d64.link_coff64_objects((raw,), entry_symbol="_start")
        self.assertTrue(program.executable.startswith(b"MZ"))

    def test_prolog_pe64_parser_parse_pos_uses_rel32_4_for_word_operators(self):
        d64 = load_d64()
        result = compile_prolog_to_assembly(
            "main :- repl.\n",
            filename="arith_repl.pl",
            target="pe64",
            windows_application_mode="Console",
        )
        obj = d64.assemble_pe64_object_source(result.assembly, filename="arith_repl.asm")
        parse_pos_relocs = [
            rel.relocation_type
            for rel in obj.relocations
            if rel.symbol.casefold() == "__prolog_parse_pos"
        ]
        # INC [parse_pos] has no trailing immediate (REL32), whereas
        # ADD [parse_pos],2/3 needs REL32_4.  Both forms must occur.
        self.assertIn(d64.IMAGE_REL_AMD64_REL32, parse_pos_relocs)
        self.assertIn(d64.IMAGE_REL_AMD64_REL32_4, parse_pos_relocs)




class PrologStringPredicateTests(unittest.TestCase):
    def test_string_predicate_is_pure_type_test(self):
        compiler = PrologCompiler(
            "", filename="string_predicate.pl", target="pe32",
            windows_application_mode="Console",
        )
        cases = (
            ('?- string("Hallo").', 1),
            ('?- string(X).', 0),
            ("?- string('Hallo').", 0),
            ('?- string(123).', 0),
            ('?- string(1.25).', 0),
            ('?- X = "Hallo", string(X).', 1),
        )
        for query_text, expected in cases:
            with self.subTest(query=query_text):
                _clauses, queries = parse_prolog(query_text, filename="string_query.pl")
                solutions = list(compiler.resolver.solve(queries[0].goals))
                self.assertEqual(len(solutions), expected)

    def test_native_string_builtin_checks_node_string_without_binding(self):
        for target in ("pe32", "pe64"):
            with self.subTest(target=target):
                result = compile_prolog_to_assembly(
                    'main :- repl.\n',
                    filename="string_runtime.pl", target=target,
                    windows_application_mode="Console",
                )
                asm = result.assembly
                block = asm[asm.index("__rt_bi_string:"):asm.index("__rt_bi_number:")]
                self.assertIn("call __rt_deref", block)
                self.assertIn("call __rt_node_ptr", block)
                self.assertRegex(block, r"cmp dword ptr \[[^\]]+\], 4")
                self.assertNotIn("__rt_bind_var", block)

    def test_string_predicate_assembles_and_links_both_windows_targets(self):
        d64 = load_d64()
        source = 'main :- X = "Hallo", string(X), writeln(X).\n'
        for target in ("pe32", "pe64"):
            with self.subTest(target=target):
                result = compile_prolog_to_assembly(
                    source, filename="string_runtime.pl", target=target,
                    windows_application_mode="Console",
                )
                if target == "pe32":
                    obj = d64.assemble_pe32_coff_object(result.assembly)
                    image = d64.link_coff32_objects((obj,), entry_symbol="_start").executable
                    self.assertEqual(pe_info(image)[:2], (0x014C, 0x010B))
                else:
                    obj = d64.assemble_pe64_coff_object(result.assembly)
                    image = d64.link_coff64_objects((obj,), entry_symbol="_start").executable
                    self.assertEqual(pe_info(image)[:2], (0x8664, 0x020B))
    def test_float_non_commutative_x87_operand_order(self):
        # FSUBP/FDIVP use ST1 := ST1 op ST0. Therefore the runtime must
        # load the left operand first and the right operand second.
        for target, left_reg, right_reg in (("pe32", "ebx", "esi"), ("pe64", "rbx", "rsi")):
            with self.subTest(target=target):
                result = compile_prolog_to_assembly(
                    "main :- A is 1/2, B is 5.0 - 2.0, writeln(A), writeln(B).",
                    filename="float_order.pl", target=target,
                    windows_application_mode="Console",
                )
                asm = result.assembly
                for start_marker, end_marker in (("__rt_eval_div:", "__rt_eval_mod:"), ("__rt_eval_sub:", "__rt_eval_mul:")):
                    block = asm[asm.index(start_marker):asm.index(end_marker, asm.index(start_marker))]
                    first = block.index("call __rt_load_number")
                    second = block.index("call __rt_load_number", first + 1)
                    left_push = block.rfind(f"push {left_reg}", 0, first)
                    right_push = block.rfind(f"push {right_reg}", first, second)
                    self.assertGreaterEqual(left_push, 0)
                    self.assertGreaterEqual(right_push, 0)
                    self.assertLess(left_push, first)
                    self.assertLess(first, right_push)
                    self.assertLess(right_push, second)

    def test_float_division_and_subtraction_semantics(self):
        _clauses, queries = parse_prolog(
            "?- A is 1/2, B is 2/1, C is 5.0 - 2.0, D is 2.0 - 5.0.",
            filename="float_noncommutative.pl",
        )
        compiler = PrologCompiler(
            "", filename="float_noncommutative.pl", target="pe32",
            windows_application_mode="Console",
        )
        solutions = list(compiler.resolver.solve(queries[0].goals))
        self.assertEqual(len(solutions), 1)
        env, _out = solutions[0]
        values = {}
        for goal in queries[0].goals:
            lhs = goal.args[0]
            values[str(lhs.value)] = float(_term_text(lhs, env))
        self.assertAlmostEqual(values["A"], 0.5)
        self.assertAlmostEqual(values["B"], 2.0)
        self.assertAlmostEqual(values["C"], 3.0)
        self.assertAlmostEqual(values["D"], -3.0)


class PrologArithmeticFloatFunctionTests(unittest.TestCase):
    def test_float_function_inside_is_evaluates_expression(self):
        _clauses, queries = parse_prolog(
            "?- A is float(1/2), B is float(1), C is float(2.5).\n",
            filename="float_function.pl",
        )
        compiler = PrologCompiler(
            "", filename="float_function.pl", target="pe32",
            windows_application_mode="Console",
        )
        solutions = list(compiler.resolver.solve(queries[0].goals))
        self.assertEqual(len(solutions), 1)
        env, _out = solutions[0]
        values = {}
        for goal in queries[0].goals:
            lhs = goal.args[0]
            values[str(lhs.value)] = float(_term_text(lhs, env))
        self.assertAlmostEqual(values["A"], 0.5)
        self.assertAlmostEqual(values["B"], 1.0)
        self.assertAlmostEqual(values["C"], 2.5)

    def test_float_function_and_float_type_predicate_remain_distinct(self):
        compiler = PrologCompiler(
            "", filename="float_function_types.pl", target="pe32",
            windows_application_mode="Console",
        )
        _clauses, queries = parse_prolog(
            "?- X is float(1/2), float(X), number(X).\n",
            filename="float_function_types.pl",
        )
        self.assertEqual(len(list(compiler.resolver.solve(queries[0].goals))), 1)

        _clauses, queries = parse_prolog(
            "?- float(1).\n",
            filename="float_function_types.pl",
        )
        self.assertEqual(len(list(compiler.resolver.solve(queries[0].goals))), 0)

    def test_float_function_respects_fraction_grouping(self):
        _clauses, queries = parse_prolog(
            "?- X is float(1/2 / 1/2 / 2).\n",
            filename="float_fraction_function.pl",
        )
        compiler = PrologCompiler(
            "", filename="float_fraction_function.pl", target="pe32",
            windows_application_mode="Console",
        )
        solutions = list(compiler.resolver.solve(queries[0].goals))
        self.assertEqual(len(solutions), 1)
        env, _out = solutions[0]
        goal = queries[0].goals[0]
        self.assertAlmostEqual(float(_term_text(goal.args[0], env)), 0.5)

    def test_native_float_function_assembles_and_links_both_targets(self):
        d64 = load_d64()
        source = "main :- X is float(1/2), Y is float(1/2 / 1/2 / 2), writeln(X), writeln(Y).\n"
        for target in ("pe32", "pe64"):
            with self.subTest(target=target):
                result = compile_prolog_to_assembly(
                    source,
                    filename="float_function_runtime.pl",
                    target=target,
                    windows_application_mode="Console",
                )
                asm = result.assembly
                self.assertIn("__rt_eval_float:", asm)
                float_block = asm[
                    asm.index("__rt_eval_float:"):
                    asm.index("__rt_eval_uplus:")
                ]
                self.assertIn("call __rt_eval_arith", float_block)
                self.assertIn("call __rt_load_number", float_block)
                self.assertIn("call __rt_make_float_from_st0", float_block)
                if target == "pe32":
                    obj = d64.assemble_pe32_coff_object(asm)
                    image = d64.link_coff32_objects((obj,), entry_symbol="_start").executable
                    self.assertEqual(pe_info(image)[:2], (0x014C, 0x010B))
                else:
                    obj = d64.assemble_pe64_coff_object(asm)
                    image = d64.link_coff64_objects((obj,), entry_symbol="_start").executable
                    self.assertEqual(pe_info(image)[:2], (0x8664, 0x020B))


if __name__ == "__main__":
    unittest.main()

class PrologVerboseRuntimeTests(unittest.TestCase):
    def test_verbose_compile_flag_controls_runtime_default(self):
        source = "?- X is 2 + 3 * 4.\n"
        normal = compile_prolog_to_assembly(
            source, filename="verbose.pl", target="pe32", verbose=False
        )
        quiet = compile_prolog_to_assembly(
            source, filename="verbose.pl", target="pe32", verbose=True
        )
        self.assertFalse(normal.verbose)
        self.assertTrue(quiet.verbose)
        self.assertIn("mov dword ptr [__prolog_verbose], 0", normal.assembly)
        self.assertIn("mov dword ptr [__prolog_verbose], 1", quiet.assembly)
        self.assertIn("cmp dword ptr [__prolog_verbose], 0", quiet.assembly)

    def test_verbose_runtime_predicate_and_explicit_output_are_emitted(self):
        result = compile_prolog_to_assembly(
            "main :- verbose(true), X is 2 + 3 * 4, writeln(X).\n",
            filename="verbose_runtime.pl",
            target="pe64",
        )
        asm = result.assembly
        self.assertIn("__rt_bi_verbose:", asm)
        self.assertIn("mov dword ptr [__prolog_verbose], 1", asm)
        self.assertIn("__rt_bi_writeln:", asm)
        # Only the automatic solution printer is guarded by verbose.
        solution = asm[asm.index("__rt_emit_solution:"):asm.index("__rt_solve_goals:")]
        self.assertIn("cmp dword ptr [__prolog_verbose], 0", solution)
        writeln = asm[asm.index("__rt_bi_writeln:"):asm.index("__rt_bi_var:")]
        self.assertNotIn("__prolog_verbose", writeln)

    def test_verbose_modes_assemble_and_link_pe32_and_pe64(self):
        d64 = load_d64()
        source = "?- X is 2 + 3 * 4.\n"
        for target in ("pe32", "pe64"):
            for verbose in (False, True):
                with self.subTest(target=target, verbose=verbose):
                    result = compile_prolog_to_assembly(
                        source,
                        filename="verbose_link.pl",
                        target=target,
                        verbose=verbose,
                    )
                    if target == "pe32":
                        obj = d64.assemble_pe32_coff_object(result.assembly)
                        image = d64.link_coff32_objects((obj,), entry_symbol="_start").executable
                        self.assertEqual(pe_info(image)[:2], (0x014C, 0x010B))
                    else:
                        obj = d64.assemble_pe64_coff_object(result.assembly)
                        image = d64.link_coff64_objects((obj,), entry_symbol="_start").executable
                        self.assertEqual(pe_info(image)[:2], (0x8664, 0x020B))


class PrologRuntimeSyntaxValidationTests(unittest.TestCase):
    def test_repl_rejects_trailing_tokens_after_valid_expression_prefix(self):
        result = compile_prolog_to_assembly(
            "main :- repl.\n",
            filename="syntax_repl.pl",
            target="pe64",
            windows_application_mode="Console",
        )
        asm = result.assembly
        block = asm[asm.index("__rt_parse_goal_list:"):asm.index("_start:")]
        self.assertIn("__rt_parse_goal_list_after_dot:", block)
        self.assertIn("__rt_parse_goal_list_valid_end:", block)
        self.assertIn("call __rt_parse_skip_ws", block)
        self.assertIn("test eax, eax", block)
        self.assertIn("mov eax, 4294967295", block)

    def test_malformed_adjacent_arithmetic_terms_are_rejected_by_source_parser(self):
        with self.assertRaises(PrologCompilerError):
            parse_prolog("?- X is 2 2 * 5.\n", filename="bad.pl")

    def test_syntax_validation_assembles_and_links_both_windows_targets(self):
        d64 = load_d64()
        for target in ("pe32", "pe64"):
            with self.subTest(target=target):
                result = compile_prolog_to_assembly(
                    "main :- repl.\n",
                    filename="syntax_repl.pl",
                    target=target,
                    windows_application_mode="Console",
                )
                if target == "pe32":
                    obj = d64.assemble_pe32_coff_object(result.assembly)
                    image = d64.link_coff32_objects((obj,), entry_symbol="_start").executable
                    self.assertEqual(pe_info(image)[:2], (0x014C, 0x010B))
                else:
                    obj = d64.assemble_pe64_coff_object(result.assembly)
                    image = d64.link_coff64_objects((obj,), entry_symbol="_start").executable
                    self.assertEqual(pe_info(image)[:2], (0x8664, 0x020B))

class PrologRuntimePromptPrefixTests(unittest.TestCase):
    def test_runtime_requires_dash_after_question_mark(self):
        result = compile_prolog_to_assembly(
            "main :- repl.\n",
            filename="prompt_guard.pl",
            target="pe32",
            windows_application_mode="Console",
        )
        asm = result.assembly
        block = asm[asm.index("__rt_parse_query:"):asm.index("__rt_repl:")]
        self.assertIn("je __rt_parse_query_fail", block)
        self.assertIn("__rt_parse_query_fail:", block)

class PrologRuntimeIncompleteOperatorTests(unittest.TestCase):
    def test_source_parser_rejects_missing_right_operands(self):
        bad_sources = (
            "?- X is 2 + 2 -.\n",
            "?- X is 2 +.\n",
            "?- X is 2 *.\n",
            "?- X is 2 /.\n",
            "?- X is 2 mod.\n",
            "?- X is.\n",
            "?- X =.\n",
            "?- X = 1,.\n",
            "?- X = 1;.\n",
        )
        for source in bad_sources:
            with self.subTest(source=source.strip()):
                with self.assertRaises(PrologCompilerError):
                    parse_prolog(source, filename="missing_rhs.pl")

    def test_runtime_parser_propagates_invalid_rhs_in_all_operator_layers(self):
        result = compile_prolog_to_assembly(
            "main :- repl.\n",
            filename="missing_rhs_repl.pl",
            target="pe64",
            windows_application_mode="Console",
        )
        asm = result.assembly
        checks = (
            ("__rt_parse_unary:", "__rt_parse_mul:", "__rt_parse_unary_fail:"),
            ("__rt_parse_mul:", "__rt_parse_add:", "__rt_parse_mul_fail:"),
            ("__rt_parse_add:", "__rt_parse_relation:", "__rt_parse_add_fail:"),
            ("__rt_parse_relation:", "__rt_parse_conjunction:", "__rt_parse_rel_fail:"),
            ("__rt_parse_conjunction:", "__rt_parse_disjunction:", "__rt_parse_conjunction_fail:"),
            ("__rt_parse_disjunction:", "__rt_parse_rule_expr:", "__rt_parse_disjunction_fail:"),
            ("__rt_parse_rule_expr:", "__rt_parse_goal:", "__rt_parse_rule_fail:"),
        )
        for start_marker, end_marker, fail_marker in checks:
            with self.subTest(layer=start_marker):
                block = asm[asm.index(start_marker):asm.index(end_marker, asm.index(start_marker))]
                self.assertIn(fail_marker, block)
                self.assertIn("cmp eax, 4294967295", block)

    def test_incomplete_operator_guard_assembles_and_links_both_windows_targets(self):
        d64 = load_d64()
        for target in ("pe32", "pe64"):
            with self.subTest(target=target):
                result = compile_prolog_to_assembly(
                    "main :- repl.\n",
                    filename="missing_rhs_repl.pl",
                    target=target,
                    windows_application_mode="Console",
                )
                if target == "pe32":
                    obj = d64.assemble_pe32_coff_object(result.assembly)
                    image = d64.link_coff32_objects((obj,), entry_symbol="_start").executable
                    self.assertEqual(pe_info(image)[:2], (0x014C, 0x010B))
                else:
                    obj = d64.assemble_pe64_coff_object(result.assembly)
                    image = d64.link_coff64_objects((obj,), entry_symbol="_start").executable
                    self.assertEqual(pe_info(image)[:2], (0x8664, 0x020B))

    def test_float_literals_and_fraction_semantics(self):
        _clauses, queries = parse_prolog(
            "?- A is 0.33, B is 1/3, C is 2 + 0.5, D is 2e-3.",
            filename="float_parse.pl",
        )
        compiler = PrologCompiler(
            "", filename="float_parse.pl", target="pe32",
            windows_application_mode="Console",
        )
        solutions = list(compiler.resolver.solve(queries[0].goals))
        self.assertEqual(len(solutions), 1)
        env, _out = solutions[0]
        # Query variables are shared across the parsed goals.
        vals = {}
        for goal in queries[0].goals:
            lhs = goal.args[0]
            vals[str(lhs.value)] = _term_text(lhs, env)
        self.assertEqual(vals["A"], "0.33")
        self.assertTrue(vals["B"].startswith("0.333333333333"))
        self.assertEqual(vals["C"], "2.5")
        self.assertEqual(vals["D"], "0.002")

    def test_float_type_predicates(self):
        compiler = PrologCompiler(
            "", filename="float_types.pl", target="pe32",
            windows_application_mode="Console",
        )
        _c, q = parse_prolog(
            "?- float(0.5), number(0.5), number(2), integer(2).",
            filename="float_types.pl",
        )
        self.assertEqual(len(list(compiler.resolver.solve(q[0].goals))), 1)

    def test_float_runtime_assembles_links_pe32_and_pe32plus(self):
        d64 = load_d64()
        source = (
            "main :-\n"
            "    A is 0.33, writeln(A),\n"
            "    B is 1/3, writeln(B),\n"
            "    C is 2 + 0.5, writeln(C),\n"
            "    C > 2.4.\n"
        )
        for target, machine, magic in (("pe32", 0x014C, 0x010B), ("pe64", 0x8664, 0x020B)):
            with self.subTest(target=target):
                result = compile_prolog_to_assembly(
                    source, filename="float_runtime.pl", target=target,
                    windows_application_mode="Console",
                )
                asm = result.assembly
                self.assertIn("__rt_make_float_bits:", asm)
                self.assertIn("__rt_load_number:", asm)
                self.assertIn("__rt_numeric_compare:", asm)
                self.assertIn('import __prolog_strtod, "msvcrt.dll", "strtod"', asm)
                self.assertIn('import __prolog_gcvt, "msvcrt.dll", "_gcvt"', asm)
                if target == "pe32":
                    obj = d64.assemble_pe32_coff_object(asm)
                    image = d64.link_coff32_objects((obj,), entry_symbol="_start").executable
                else:
                    obj = d64.assemble_pe64_coff_object(asm)
                    image = d64.link_coff64_objects((obj,), entry_symbol="_start").executable
                self.assertEqual(pe_info(image)[:2], (machine, magic))

class PrologFractionGroupingTests(unittest.TestCase):
    def test_numeric_fraction_operands_group_before_outer_division(self):
        _clauses, queries = parse_prolog(
            "?- X is 1/2 / 1/2.\n",
            filename="fraction_grouping.pl",
        )
        goal = queries[0].goals[0]
        expr = goal.args[1]
        self.assertEqual((expr.kind, expr.value, len(expr.args)), ("compound", "/", 2))
        self.assertEqual((expr.args[0].kind, expr.args[0].value), ("compound", "/"))
        self.assertEqual((expr.args[1].kind, expr.args[1].value), ("compound", "/"))
        compiler = PrologCompiler(
            "", filename="fraction_grouping.pl", target="pe32",
            windows_application_mode="Console",
        )
        solutions = list(compiler.resolver.solve(queries[0].goals))
        self.assertEqual(len(solutions), 1)
        env, _out = solutions[0]
        self.assertAlmostEqual(float(_term_text(goal.args[0], env)), 1.0)

    def test_runtime_repl_has_fraction_operand_parser(self):
        result = compile_prolog_to_assembly(
            "main :- repl.\n",
            filename="fraction_repl.pl",
            target="pe64",
            windows_application_mode="Console",
        )
        asm = result.assembly
        self.assertIn("__rt_parse_fraction:", asm)
        block = asm[asm.index("__rt_parse_mul:"):asm.index("__rt_parse_add:")]
        self.assertGreaterEqual(block.count("call __rt_parse_fraction"), 2)

    def test_fraction_grouping_assembles_and_links_both_targets(self):
        d64 = load_d64()
        source = "main :- X is 1/2 / 1/2, writeln(X).\n"
        for target in ("pe32", "pe64"):
            with self.subTest(target=target):
                result = compile_prolog_to_assembly(
                    source,
                    filename="fraction_grouping.pl",
                    target=target,
                    windows_application_mode="Console",
                )
                if target == "pe32":
                    obj = d64.assemble_pe32_coff_object(result.assembly)
                    image = d64.link_coff32_objects((obj,), entry_symbol="_start").executable
                    self.assertEqual(pe_info(image)[:2], (0x014C, 0x010B))
                else:
                    obj = d64.assemble_pe64_coff_object(result.assembly)
                    image = d64.link_coff64_objects((obj,), entry_symbol="_start").executable
                    self.assertEqual(pe_info(image)[:2], (0x8664, 0x020B))
