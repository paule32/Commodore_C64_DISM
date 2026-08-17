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

from d64prolog import compile_prolog_to_assembly
from d64prolog import runtime as rt


def load_d64():
    name = "d64_stage51_test_module"
    if name in sys.modules:
        return sys.modules[name]
    sys.modules.setdefault("flags_rc", types.ModuleType("flags_rc"))
    spec = importlib.util.spec_from_file_location(name, ROOT / "d64_dism.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def longest_zero_run(data: bytes) -> int:
    best = 0
    run = 0
    for byte in data:
        if byte == 0:
            run += 1
            best = max(best, run)
        else:
            run = 0
    return best


class PrologDatabaseRuntimeStage51Tests(unittest.TestCase):
    def test_dynamic_clause_root_survives_choice_push(self):
        asm = compile_prolog_to_assembly(
            'main :- database_open("patient_4711.pl", DB), name(4711, X), writeln(X).',
            filename="arzt_patient.pl", target="pe32",
        ).assembly
        body = asm.split("__rt_try_dynamic:", 1)[1].split("__rt_run_query:", 1)[0]
        root = body.index("mov eax, dword ptr [edi+12]")
        preserve = body.index("mov edi, eax", root)
        choice = body.index("call __rt_choice_push", preserve)
        clone_arg = body.index("push edi", choice)
        clone = body.index("call __rt_dyn_clone", clone_arg)
        guard = body.index("cmp eax, 4294967295", clone)
        node_ptr = body.index("call __rt_node_ptr", guard)
        self.assertLess(root, preserve)
        self.assertLess(preserve, choice)
        self.assertLess(choice, clone_arg)
        self.assertLess(clone_arg, clone)
        self.assertLess(clone, guard)
        self.assertLess(guard, node_ptr)

    def test_dyn_clone_rejects_invalid_or_out_of_range_handle(self):
        asm = compile_prolog_to_assembly("main :- true.", filename="guard.pl", target="pe32").assembly
        body = asm.split("__rt_dyn_clone:", 1)[1].split("__rt_dyn_clone_var:", 1)[0]
        self.assertIn("cmp eax, 4294967295", body)
        self.assertIn(f"cmp eax, {rt.DYN_NODE_COUNT}", body)
        self.assertIn("je __rt_dyn_clone_fail", body)
        self.assertIn("jae __rt_dyn_clone_fail", body)

    def test_database_metadata_uses_virtualalloc_gap(self):
        self.assertEqual(rt.DB_META_OFF, 0xBC000)
        self.assertLessEqual(rt.DB_META_END, rt.OUTPUT_OFF)
        self.assertGreater(rt.OUTPUT_OFF - rt.DB_META_END, 0)
        asm = compile_prolog_to_assembly("main :- true.", filename="meta.pl", target="pe32").assembly
        for obsolete in (
            "__prolog_db_active:", "__prolog_db_ids:", "__prolog_db_modes:",
            "__prolog_db_kinds:", "__prolog_db_modified:", "__prolog_db_filenames:",
            "__prolog_db_temp_path:", "__prolog_db_old_path:",
        ):
            self.assertNotIn(obsolete, asm)
        self.assertIn(f"add edi, {rt.DB_ACTIVE_OFF}", asm)
        self.assertIn(f"add edi, {rt.DB_FILENAMES_OFF}", asm)

    def test_patient_example_pe32_has_no_large_zero_payload(self):
        d64 = load_d64()
        source = (ROOT / "examples" / "prolog_database" / "arzt_patient.pl").read_text(encoding="utf-8")
        result = compile_prolog_to_assembly(
            source, filename="arzt_patient.pl", target="pe32", windows_application_mode="Console"
        )
        obj = d64.assemble_pe32_object_source(result.assembly, filename="arzt_patient.asm")
        raw = d64.write_coff32_object(obj)
        program = d64.link_coff32_objects((raw,), entry_symbol="_start", gui=False)
        self.assertLess(len(program.executable), 32 * 1024)
        self.assertLess(longest_zero_run(program.executable), 1024)
        pe = struct.unpack_from("<I", program.executable, 0x3C)[0]
        self.assertEqual(struct.unpack_from("<H", program.executable, pe + 4)[0], 0x014C)

    def test_database_examples_still_link_pe32_and_pe64(self):
        d64 = load_d64()
        source = (ROOT / "examples" / "prolog_database" / "arzt_patient.pl").read_text(encoding="utf-8")
        for target in ("pe32", "pe64"):
            result = compile_prolog_to_assembly(source, filename="arzt_patient.pl", target=target)
            if target == "pe32":
                obj = d64.assemble_pe32_object_source(result.assembly, filename="arzt_patient.asm")
                raw = d64.write_coff32_object(obj)
                program = d64.link_coff32_objects((raw,), entry_symbol="_start", gui=False)
            else:
                obj = d64.assemble_pe64_object_source(result.assembly, filename="arzt_patient.asm")
                raw = d64.write_coff64_object(obj)
                program = d64.link_coff64_objects((raw,), entry_symbol="_start", gui=False)
            self.assertTrue(program.executable.startswith(b"MZ"))


if __name__ == "__main__":
    unittest.main()
