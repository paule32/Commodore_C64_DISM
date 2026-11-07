"""Stage 536 pure tests: parallel scheduler, Windows settings, system information.

These do not require Qt, Windows, or ANTLR 4.13.2; native IDE build tests
must be run on Windows with the original project/toolchain.
"""
import ast
import collections
from pathlib import Path
import threading
import time
import unittest

from pascal_parallel_build import (
    PascalParallelBuildError, normalize_parallel_options,
    effective_parallel_processes, run_parallel_units, validate_jobs,
    compile_unit_in_worker)
from system_information import collect_system_information

ROOT = Path(__file__).resolve().parent
D64 = (ROOT / "d64_dism.py").read_text("utf-8")


def make_job(name, deps=()):
    return {"name": name, "dependencies": list(deps),
            "path": f"/test/{name}.pas", "object_path": f"/test/{name}.o",
            "assembly_path": f"/test/{name}.asm", "pui_path": f"/test/{name}.pui"}


class TestStage536(unittest.TestCase):
    def test_process_auto_detection_and_limits(self):
        self.assertEqual(normalize_parallel_options(), {
            "automatic_cpu_detection": True, "max_compiler_processes": 2})
        self.assertEqual(effective_parallel_processes({}, cpu_count=1), 1)
        self.assertEqual(effective_parallel_processes({}, cpu_count=8), 2)
        self.assertEqual(effective_parallel_processes({"max_compiler_processes": 4}, 2), 2)
        self.assertEqual(effective_parallel_processes({"max_compiler_processes": 4}, 16), 4)
        self.assertEqual(effective_parallel_processes({"automatic_cpu_detection": False,
                                                       "max_compiler_processes": 3}, 1), 3)
        self.assertEqual(normalize_parallel_options({"max_compiler_processes": 42})
                         ["max_compiler_processes"], 4)
        self.assertEqual(normalize_parallel_options({"max_compiler_processes": 0})
                         ["max_compiler_processes"], 1)

    def test_dependency_scheduler_reaches_real_parallelism(self):
        jobs = [make_job("UnitA"), make_job("UnitB"),
                make_job("UnitC", ("UnitA",)),
                make_job("UnitD", ("UnitB", "UnitC"))]
        active = 0
        peak = 0
        ended = []
        lock = threading.Lock()
        def runner(job):
            nonlocal active, peak
            with lock:
                for dep in job["dependencies"]:
                    if dep.casefold() in {"unita", "unitb", "unitc", "unitd"}:
                        assert dep.casefold() in ended
                active += 1
                peak = max(peak, active)
            time.sleep(0.025)
            with lock:
                active -= 1
                ended.append(job["name"].casefold())
            return {"object_path": job["object_path"]}
        outputs = run_parallel_units(jobs, 2, runner=runner)
        self.assertEqual(set(outputs), {"unita", "unitb", "unitc", "unitd"})
        self.assertEqual(peak, 2, "Independent jobs should overlap")

    def test_cycle_and_output_collision_abort(self):
        with self.assertRaisesRegex(PascalParallelBuildError, "Zyklische"):
            validate_jobs([make_job("A", ["B"]), make_job("B", ["A"])])
        duplicate = make_job("Duplicate")
        duplicate["object_path"] = make_job("A")["object_path"]
        with self.assertRaisesRegex(PascalParallelBuildError, "Ausgabepfad"):
            validate_jobs([make_job("A"), duplicate])

    def test_worker_failure_prevents_dependent_compile(self):
        jobs = [make_job("A"), make_job("B", ["A"])]
        executed = []
        def runner(job):
            executed.append(job["name"])
            if job["name"] == "A":
                raise ValueError("compile failed")
            return {}
        with self.assertRaises(PascalParallelBuildError):
            run_parallel_units(jobs, 2, runner=runner)
        self.assertEqual(executed, ["A"])

    def test_real_worker_subprocess_utf8_and_machine_reply(self):
        import tempfile
        import json
        import subprocess
        import sys
        with tempfile.TemporaryDirectory() as work:
            root = Path(work)
            (root / "pascal_parallel_build.py").write_text(
                (ROOT / "pascal_parallel_build.py").read_text(encoding="utf-8"),
                encoding="utf-8")
            (root / "c64pascal.py").write_text('from types import SimpleNamespace\ndef preprocess_pascal_source(text, *, filename, predefined_macros):\n    return SimpleNamespace(source=text, macros=predefined_macros, link_files=())\ndef compile_pascal_to_assembly(text, **kwargs):\n    print("Diagnose aus Compiler: öäü")\n    return SimpleNamespace(assembly="section .text\\nDemo: ret\\n", source_kind="unit", unit_name="Demo")\n', encoding="utf-8")
            (root / "d64_dism.py").write_text('def assemble_pe32_coff_object(text, **kwargs):\n    return b"COFF32"\ndef assemble_pe64_coff_object(text, **kwargs):\n    return b"COFF64"\n', encoding="utf-8")
            source = root / "Demo.pas"
            source.write_text("unit Demo; interface implementation end. // Größe", encoding="utf-8")
            job = make_job("Demo")
            job.update({"path": str(source), "source": source.read_text(encoding="utf-8"),
                        "target": "pe32", "assembly_path": str(root / "demo.asm"),
                        "object_path": str(root / "demo.o"),
                        "pui_path": str(root / "demo.pui")})
            result = subprocess.run([sys.executable, str(root / "pascal_parallel_build.py"),
                                     "--worker"], input=json.dumps(job, ensure_ascii=False),
                                    text=True, encoding="utf-8", errors="replace",
                                    capture_output=True, check=False)
            self.assertEqual(result.returncode, 0, result.stderr)
            parsed = json.loads(result.stdout)
            self.assertTrue(parsed["ok"])
            self.assertIn("Diagnose", result.stderr)
            self.assertEqual((root / "demo.o").read_bytes(), b"COFF32")

    def test_compiler_worker_writes_asm_and_coff(self):
        import tempfile
        import types
        import sys
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as work:
            base = Path(work)
            source = base / "Demo.pas"
            source.write_text("unit Demo; interface implementation end.", encoding="utf-8")
            kwargs_seen = []
            def preprocess(text, *, filename, predefined_macros):
                return types.SimpleNamespace(source=text, macros=predefined_macros,
                                             link_files=())
            def compile_unit(text, *, filename, target, include_paths,
                             link_search_paths, output_directory,
                             predefined_macros, linked_object_files,
                             graphics_backend, breakpoint_lines, stack_protector):
                kwargs_seen.append((filename, target, stack_protector))
                return types.SimpleNamespace(
                    assembly="section .text\nDemo: ret\n", source_kind="unit",
                    unit_name="Demo")
            compiler = types.ModuleType("c64pascal")
            compiler.compile_pascal_to_assembly = compile_unit
            compiler.preprocess_pascal_source = preprocess
            backend = types.ModuleType("d64_dism")
            backend.assemble_pe32_coff_object = lambda source, **kw: b"COFF32"
            backend.assemble_pe64_coff_object = lambda source, **kw: b"COFF64"
            for target, expected in (("pe32", b"COFF32"), ("pe64", b"COFF64")):
                job = make_job("Demo")
                job.update({"path": str(source), "target": target,
                            "source": source.read_text(),
                            "assembly_path": str(base / f"demo.{target}.asm"),
                            "object_path": str(base / f"demo.{target}.o"),
                            "pui_path": str(base / f"demo.{target}.pui"),
                            "stack_protector": True})
                with patch.dict(sys.modules, {"c64pascal": compiler,
                                               "d64_dism": backend}):
                    result = compile_unit_in_worker(job)
                self.assertTrue(result["ok"])
                self.assertEqual(Path(job["object_path"]).read_bytes(), expected)
            self.assertEqual(kwargs_seen, [(str(source), "pe32", True),
                                           (str(source), "pe64", True)])

    def test_parallel_pro_sections_roundtrip(self):
        import configparser
        from pascal_parallel_build import normalize_parallel_options
        source = D64.replace("lazy from app_lang.deu import", "from app_lang.deu import")
        source = source.replace("lazy from app_lang.enu import", "from app_lang.enu import")
        tree = ast.parse(source)
        def loop(name):
            func = next(f for f in tree.body if isinstance(f, ast.FunctionDef)
                        and f.name == name)
            return next(node for node in func.body if isinstance(node, ast.For)
                        and 'Settings.Windows.{_suffix}.Compiler.Parallelisierung'
                        in ast.get_source_segment(source, node))
        def execute(node, parser, entries):
            imports = {"parser": parser, "entries": entries,
                       "PROJECT_WINDOWS_COMPILER_PARALLEL_KEYS":
                           {"pe32": "p32", "pe64": "p64"},
                       "normalize_parallel_options": normalize_parallel_options}
            code = compile(ast.fix_missing_locations(ast.Module(
                body=[node], type_ignores=[])), '<parallel-settings>', 'exec')
            exec(code, imports)
        cfg = configparser.ConfigParser(interpolation=None)
        cfg.optionxform = str
        original = {'p32': [{'automatic_cpu_detection': False,
                             'max_compiler_processes': 4}],
                    'p64': [{'automatic_cpu_detection': True,
                             'max_compiler_processes': 2}]}
        execute(loop('format_project_ini'), cfg, original)
        self.assertEqual(cfg.get('Settings.Windows.32Bit.Compiler.Parallelisierung',
                                 'MaxCompilerProcesses'), '4')
        self.assertEqual(cfg.get('Settings.Windows.64Bit.Compiler.Parallelisierung',
                                 'MaxCompilerProcesses'), '2')
        restored = {}
        execute(loop('parse_project_ini'), cfg, restored)
        self.assertEqual(restored, original)
        # Legacy projects without sections retain separate defaults.
        execute(loop('parse_project_ini'), configparser.ConfigParser(), restored := {})
        self.assertEqual(restored['p32'][0]['max_compiler_processes'], 2)
        self.assertEqual(restored['p64'][0]['max_compiler_processes'], 2)

    def test_source_parses_with_existing_python_315_lazy_imports_masked(self):
        source = D64.replace("lazy from app_lang.deu import", "from app_lang.deu import")
        source = source.replace("lazy from app_lang.enu import", "from app_lang.enu import")
        ast.parse(source)

    def test_independent_project_settings_and_menu_wired(self):
        for keyword in (
            "Settings.Windows.{_suffix}.Compiler.Parallelisierung",
            "AutomaticCpuDetection", "MaxCompilerProcesses",
            "project_windows_{tag}_automatic_cpu_detection",
            "project_windows_{tag}_max_compiler_processes",
            "self._parallel_pages", "panel.set_parallel_options",
            "_debug_panel.set_parallel_options",
            "PROJECT_WINDOWS_COMPILER_PARALLEL_KEYS[target]",
            "_project_pascal_parallel_objects(target, main_path)",
            "self.show_system_information_dialog",
            'QAction("System-Informationen", self)',
        ):
            self.assertIn(keyword, D64)

    def test_system_information_fields(self):
        groups = dict(collect_system_information())
        self.assertIn("Betriebssystem", groups)
        self.assertIn("Prozessor", groups)
        self.assertIn("Speicher", groups)
        keys = {key for rows in groups.values() for key, _ in rows}
        for key in ("Edition", "Version", "Architektur", "Physische CPU-Kerne",
                    "Logische Prozessoren", "Installierter RAM",
                    "Aktuell verfügbarer RAM", "Virtueller Speicher (Commit-Limit)"):
            self.assertIn(key, keys)

    def test_atomic_pui_writes(self):
        source = (ROOT / "c64pascal" / "compiler.py").read_text("utf-8")
        self.assertIn('uuid.uuid4().hex', source)
        self.assertIn('temporary.replace(path)', source)


if __name__ == "__main__":
    unittest.main(verbosity=2)
