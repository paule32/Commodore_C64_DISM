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
    name = "d64_stage53_test_module"
    if name in sys.modules:
        return sys.modules[name]
    sys.modules.setdefault("flags_rc", types.ModuleType("flags_rc"))
    spec = importlib.util.spec_from_file_location(name, ROOT / "d64_dism.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class PrologDatabaseRuntimeStage53Tests(unittest.TestCase):
    def _asm(self, source: str = "main :- 150 > 140, true.", target: str = "pe32") -> str:
        return compile_prolog_to_assembly(source, filename="stage53.pl", target=target).assembly

    def _comparison_body(self, asm: str, label: str, next_label: str) -> str:
        return asm.split(label + ":", 1)[1].split(next_label + ":", 1)[0]

    def test_arithmetic_comparisons_preserve_ebx_continuation_pe32(self):
        asm = self._asm(target="pe32")
        labels = (
            ("__rt_bi_lt", "__rt_bi_lt_ok"),
            ("__rt_bi_le", "__rt_bi_le_ok"),
            ("__rt_bi_gt", "__rt_bi_gt_ok"),
            ("__rt_bi_ge", "__rt_bi_ge_ok"),
        )
        for label, ok in labels:
            with self.subTest(label=label):
                body = self._comparison_body(asm, label, ok)
                self.assertIn("mov esi, eax", body)
                self.assertIn("push esi", body)
                self.assertNotIn("mov ebx, eax", body)

    def test_gt_success_continues_with_original_goal_chain(self):
        asm = self._asm(target="pe32")
        body = asm.split("__rt_bi_gt:", 1)[1].split("__rt_bi_ge:", 1)[0]
        # The successful comparison reaches the shared solve_rest sequence,
        # which must still pass EBX (the original rest chain) to solve_goals.
        ok = body.split("__rt_bi_gt_ok:", 1)[1]
        self.assertIn("push ebx", ok)
        self.assertIn("call __rt_solve_goals", ok)

    def test_pe64_uses_same_non_ebx_numeric_scratch(self):
        asm = self._asm(target="pe64")
        body = asm.split("__rt_bi_gt:", 1)[1].split("__rt_bi_gt_ok:", 1)[0]
        self.assertIn("mov esi, eax", body)
        self.assertNotIn("mov ebx, eax", body)

    def test_medical_database_example_still_links_pe32_and_pe64(self):
        d64 = load_d64()
        src_path = ROOT / "examples" / "prolog_database" / "arzt_mit_fachwissen.pl"
        source = src_path.read_text(encoding="utf-8")
        for target in ("pe32", "pe64"):
            with self.subTest(target=target):
                result = compile_prolog_to_assembly(source, filename=src_path.name, target=target)
                if target == "pe32":
                    obj = d64.assemble_pe32_object_source(result.assembly, filename=src_path.name + ".asm")
                    raw = d64.write_coff32_object(obj)
                    program = d64.link_coff32_objects((raw,), entry_symbol="_start", gui=False)
                else:
                    obj = d64.assemble_pe64_object_source(result.assembly, filename=src_path.name + ".asm")
                    raw = d64.write_coff64_object(obj)
                    program = d64.link_coff64_objects((raw,), entry_symbol="_start", gui=False)
                self.assertTrue(program.executable.startswith(b"MZ"))


if __name__ == "__main__":
    unittest.main()
