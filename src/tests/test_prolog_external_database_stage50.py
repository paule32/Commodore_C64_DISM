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
from d64prolog import runtime as prolog_runtime


def load_d64():
    if "d64_stage50_test_module" in sys.modules:
        return sys.modules["d64_stage50_test_module"]
    sys.modules.setdefault("flags_rc", types.ModuleType("flags_rc"))
    spec = importlib.util.spec_from_file_location(
        "d64_stage50_test_module", ROOT / "d64_dism.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["d64_stage50_test_module"] = module
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


class PrologExternalDatabaseStage50Tests(unittest.TestCase):
    SOURCE = """
main :-
    database_open("patient_4711.pl", read_write, record, Patient),
    database_open("medizin_wissen.pl", read_only, knowledge, Wissen),
    database_assert(Patient, notiz(4711, kontrolle)),
    with_database(Patient, assert(termin(4711, kontrolle))),
    database_retract(Patient, notiz(4711, alt)),
    current_database(Current),
    writeln(Current),
    database_modified(Patient),
    database_save(Patient),
    database_save_as(Patient, "patient_4711_copy.pl"),
    database_close(Patient),
    database_close(Wissen).
"""

    def test_builtin_surface_and_runtime_helpers_are_emitted(self):
        asm = compile_prolog_to_assembly(
            self.SOURCE, filename="database_demo.pl", target="pe32"
        ).assembly
        for marker in (
            "__rt_database_open:",
            "__rt_database_save_id:",
            "__rt_database_close_id:",
            "__rt_database_save_as:",
            "__rt_database_assert_scoped:",
            "__rt_database_retract_scoped:",
            "__rt_bi_database_open2:",
            "__rt_bi_database_open3:",
            "__rt_bi_database_open4:",
            "__rt_bi_database_select:",
            "__rt_bi_current_database:",
            "__rt_bi_database_modified:",
            "__rt_bi_with_database:",
        ):
            self.assertIn(marker, asm)

    def test_clause_database_owner_is_parallel_and_moves_with_records(self):
        source = (ROOT / "d64prolog" / "runtime.py").read_text(encoding="utf-8")
        self.assertIn("DYN_DB_OWNER_OFF", source)
        self.assertIn("Keep the parallel Database-ID owner table in the same order", source)
        self.assertIn("Move the parallel Database-ID owner alongside the compacted record", source)
        self.assertIn("mov edx, dword ptr [__prolog_current_db]", source)
        self.assertIn("cmp dword ptr [{ar.di}+{ar.si}*4], edx", source)

    def test_close_unloads_only_owned_clauses_then_compacts(self):
        asm = compile_prolog_to_assembly(
            "main :- database_open(\"x.pl\", read_write, record, DB), database_close(DB).",
            filename="close.pl",
            target="pe64",
        ).assembly
        body = asm.split("__rt_db_unload_id:", 1)[1].split("__rt_database_save_id:", 1)[0]
        self.assertIn("__prolog_dyn_count", body)
        self.assertIn("call __rt_dyn_db_compact", body)
        self.assertIn("call __rt_gc_dynamic", body)
        self.assertIn("add rdi, 770048", body)  # DB_ACTIVE_OFF lives in VirtualAlloc arena
        self.assertIn("__prolog_current_db", body)

    def test_read_only_and_system_are_protected(self):
        asm = compile_prolog_to_assembly(
            "main :- true.", filename="guard.pl", target="pe32"
        ).assembly
        guard = asm.split("__rt_db_can_modify_id:", 1)[1].split("__rt_db_mark_modified_id:", 1)[0]
        self.assertIn("add edi, 770304", guard)  # DB_MODES_OFF
        self.assertIn("add edi, 770432", guard)  # DB_KINDS_OFF
        # Numeric values are deliberately fixed ABI values in runtime.py.
        self.assertEqual(prolog_runtime.DATABASE_MODE_READ_ONLY, 0)
        self.assertEqual(prolog_runtime.DATABASE_MODE_READ_WRITE, 1)
        self.assertEqual(prolog_runtime.DATABASE_KIND_SYSTEM, 3)
        open_body = asm.split("__rt_database_open:", 1)[1].split("__rt_db_unload_id:", 1)[0]
        self.assertIn("__rt_database_open_mode_ok", open_body)
        close_body = asm.split("__rt_database_close_id:", 1)[1].split("__rt_database_save_as:", 1)[0]
        self.assertIn("add edi, 770432", close_body)  # DB_KINDS_OFF

    def test_file_loader_parser_and_comment_support_exist(self):
        source = (ROOT / "d64prolog" / "runtime.py").read_text(encoding="utf-8")
        asm = compile_prolog_to_assembly(
            "main :- true.", filename="loader.pl", target="pe64"
        ).assembly
        self.assertGreaterEqual(prolog_runtime.FILE_BUFFER_SIZE, 1024 * 1024)
        self.assertEqual(prolog_runtime.DATABASE_MAX, 32)
        self.assertIn("__rt_db_load_slot:", asm)
        self.assertIn("call __rt_parse_rule_expr", asm)
        self.assertIn("__prolog_parser_db_mode", asm)
        self.assertIn("DB_PARSER_NAME_POOL_OFF", source)
        self.assertIn("__rt_db_parser_var", asm)
        self.assertIn("File-backed databases may contain normal PROLOG comments", source)
        self.assertIn("__rt_parse_skip_ws_line_comment", source)
        self.assertIn("__rt_parse_skip_ws_block_comment", source)

    def test_atomic_save_and_rule_serialization_are_emitted(self):
        asm = compile_prolog_to_assembly(
            self.SOURCE, filename="save.pl", target="pe64"
        ).assembly
        for marker in (
            'import CreateFileA, "kernel32.dll", "CreateFileA"',
            'import FlushFileBuffers, "kernel32.dll", "FlushFileBuffers"',
            'import MoveFileExA, "kernel32.dll", "MoveFileExA"',
            'import DeleteFileA, "kernel32.dll", "DeleteFileA"',
            "__rt_emit_clause_source:",
            "__rt_emit_source_expr:",
            "__rt_emit_saved_var:",
            "__prolog_fmt_saved_var:",
            "__prolog_text_rule_sep:",
            "__prolog_text_clause_end:",
        ):
            self.assertIn(marker, asm)
        # _V%d is emitted as raw db bytes: 95, 86, 37, 100, 0.
        self.assertIn("db 95, 86, 37, 100, 0", asm)

    def test_gui_has_database_io_without_console_repl(self):
        asm = compile_prolog_to_assembly(
            'main :- database_open("x.pl", read_only, knowledge, DB), database_close(DB).',
            filename="gui_database.pl",
            target="pe64",
            windows_application_mode="GUI",
        ).assembly
        self.assertIn('import MessageBoxA, "user32.dll", "MessageBoxA"', asm)
        self.assertIn('import ReadFile, "kernel32.dll", "ReadFile"', asm)
        self.assertIn("__rt_database_open:", asm)
        self.assertNotIn("__rt_repl:", asm)

    def test_database_program_links_pe32_and_pe64(self):
        d64 = load_d64()
        for target, machine, magic in (
            ("pe32", 0x014C, 0x010B),
            ("pe64", 0x8664, 0x020B),
        ):
            with self.subTest(target=target):
                result = compile_prolog_to_assembly(
                    self.SOURCE,
                    filename="database_link.pl",
                    target=target,
                    windows_application_mode="Console",
                )
                if target == "pe32":
                    obj = d64.assemble_pe32_object_source(result.assembly, filename="database_link.asm")
                    raw = d64.write_coff32_object(obj)
                    program = d64.link_coff32_objects((raw,), entry_symbol="_start", gui=False)
                else:
                    obj = d64.assemble_pe64_object_source(result.assembly, filename="database_link.asm")
                    raw = d64.write_coff64_object(obj)
                    program = d64.link_coff64_objects((raw,), entry_symbol="_start", gui=False)
                self.assertEqual(pe_info(program.executable), (machine, magic, 3))

    def test_compiler_notes_document_database_runtime_limits(self):
        result = compile_prolog_to_assembly(
            "main :- true.", filename="notes.pl", target="pe32"
        )
        joined = "\n".join(result.notes)
        self.assertIn("Database-ID", joined)
        self.assertIn("database_close/1", joined)
        self.assertIn("database_select/1", joined)
        self.assertIn("database_save/1", joined)
        self.assertIn("maximal 32", joined)

    def test_shipped_database_examples_parse_and_compile(self):
        from d64prolog import parse_prolog

        base = ROOT / "examples" / "prolog_database"
        for name in ("patient_4711.pl", "medizin_wissen.pl"):
            clauses, queries = parse_prolog(
                (base / name).read_text(encoding="utf-8"), filename=name
            )
            self.assertTrue(clauses)
            self.assertFalse(queries)
        for name in ("arzt_patient.pl", "arzt_mit_fachwissen.pl"):
            text = (base / name).read_text(encoding="utf-8")
            for target in ("pe32", "pe64"):
                with self.subTest(name=name, target=target):
                    result = compile_prolog_to_assembly(
                        text, filename=name, target=target,
                        windows_application_mode="Console",
                    )
                    self.assertIn("__rt_database_open:", result.assembly)



if __name__ == "__main__":
    unittest.main()
