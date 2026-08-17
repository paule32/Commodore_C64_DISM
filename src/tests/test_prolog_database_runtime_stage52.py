from __future__ import annotations

import importlib.util
import sys
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from d64prolog import compile_prolog_to_assembly


def load_d64():
    name = "d64_stage52_test_module"
    if name in sys.modules:
        return sys.modules[name]
    sys.modules.setdefault("flags_rc", types.ModuleType("flags_rc"))
    spec = importlib.util.spec_from_file_location(name, ROOT / "d64_dism.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class PrologDatabaseRuntimeStage52Tests(unittest.TestCase):
    def _asm(self, source: str = "main :- true.", target: str = "pe32") -> str:
        return compile_prolog_to_assembly(source, filename="stage52.pl", target=target).assembly

    def test_struct_serializer_preserves_argument_link_across_separator_write(self):
        asm = self._asm()
        body = asm.split("__rt_emit_term_struct_loop:", 1)[1].split("__rt_emit_term_struct_no_comma:", 1)[0]
        push = body.index("push ecx")
        emit = body.index("call __rt_emit_text", push)
        pop = body.index("pop ecx", emit)
        self.assertLess(push, emit)
        self.assertLess(emit, pop)

    def test_external_parser_variable_scan_does_not_cache_count_in_ecx(self):
        asm = self._asm()
        body = asm.split("__rt_db_parser_var_scan:", 1)[1].split("__rt_db_parser_var_found:", 1)[0]
        self.assertIn("cmp edx, dword ptr [__prolog_db_parser_var_count]", body)
        self.assertNotIn("cmp edx, ecx", body)
        new = asm.split("__rt_db_parser_var_new:", 1)[1].split("__rt_db_parser_var_copy:", 1)[0]
        self.assertIn("mov ecx, dword ptr [__prolog_db_parser_var_count]", new)

    def test_query_variable_scan_uses_same_safe_count_rule(self):
        asm = self._asm()
        body = asm.split("__rt_query_var_scan:", 1)[1].split("__rt_query_var_found:", 1)[0]
        self.assertIn("cmp edx, dword ptr [__prolog_query_var_count]", body)
        self.assertNotIn("cmp edx, ecx", body)
        new = asm.split("__rt_query_var_new:", 1)[1].split("__rt_query_var_copy:", 1)[0]
        self.assertIn("mov ecx, dword ptr [__prolog_query_var_count]", new)

    def test_goal_chain_uses_stable_barrier_argument_not_volatile_edx(self):
        asm = self._asm()
        body = asm.split("__rt_goal_expr_to_chain:", 1)[1].split("__rt_make_binary_term:", 1)[0]
        self.assertNotIn("mov edx, dword ptr [ebp+16]", body)
        self.assertGreaterEqual(body.count("push dword ptr [ebp+16]"), 3)

    def test_both_database_examples_still_link_pe32_and_pe64(self):
        d64 = load_d64()
        base = ROOT / "examples" / "prolog_database"
        for name in ("arzt_patient.pl", "arzt_mit_fachwissen.pl"):
            source = (base / name).read_text(encoding="utf-8")
            for target in ("pe32", "pe64"):
                with self.subTest(name=name, target=target):
                    result = compile_prolog_to_assembly(source, filename=name, target=target)
                    if target == "pe32":
                        obj = d64.assemble_pe32_object_source(result.assembly, filename=name + ".asm")
                        raw = d64.write_coff32_object(obj)
                        program = d64.link_coff32_objects((raw,), entry_symbol="_start", gui=False)
                    else:
                        obj = d64.assemble_pe64_object_source(result.assembly, filename=name + ".asm")
                        raw = d64.write_coff64_object(obj)
                        program = d64.link_coff64_objects((raw,), entry_symbol="_start", gui=False)
                    self.assertTrue(program.executable.startswith(b"MZ"))


if __name__ == "__main__":
    unittest.main()
