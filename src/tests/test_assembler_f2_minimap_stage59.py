from __future__ import annotations

import importlib.util
import sys
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "d64_dism.py").read_text(encoding="utf-8")


def function_block(name: str, next_name: str) -> str:
    start = SOURCE.index(f"def {name}")
    end = SOURCE.index(f"def {next_name}", start)
    return SOURCE[start:end]


def load_d64():
    name = "d64_stage59_test_module"
    if name in sys.modules:
        return sys.modules[name]
    sys.modules.setdefault("flags_rc", types.ModuleType("flags_rc"))
    spec = importlib.util.spec_from_file_location(name, ROOT / "d64_dism.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class AssemblerF2MiniMapStage59Tests(unittest.TestCase):
    def test_raw_and_generated_assembler_editors_have_minimap(self):
        self.assertIn("self.raw_editor_container = SourceEditorWithMiniMap(", SOURCE)
        self.assertIn("self.raw_minimap = self.raw_editor_container.minimap", SOURCE)
        self.assertIn(
            "self.generated_assembly_editor_container = SourceEditorWithMiniMap(",
            SOURCE,
        )
        self.assertIn(
            "self.generated_assembly_minimap = (\n                self.generated_assembly_editor_container.minimap",
            SOURCE,
        )

    def test_f2_from_generated_assembler_editor_is_wired(self):
        self.assertIn("build_generated_requested = pyqtSignal(object)", SOURCE)
        self.assertIn("self.generated_assembly_editor.build_requested.connect(", SOURCE)
        self.assertIn("lambda: self.build_generated_requested.emit(self)", SOURCE)
        self.assertIn("document.build_generated_requested.connect(", SOURCE)
        self.assertIn("self.build_and_run_generated_assembly_document", SOURCE)

    def test_raw_assembler_f2_assembles_and_only_launches_exe(self):
        block = function_block(
            "build_and_run_source_document",
            "build_and_run_generated_assembly_document",
        )
        self.assertIn("document.is_assembler_document", block)
        self.assertIn("self.assemble_document(document)", block)
        self.assertIn('output_path.suffix.casefold() == ".exe"', block)
        self.assertIn("return self._launch_assembled_document(document)", block)
        self.assertNotIn("mingw32-make", block)
        self.assertNotIn("qmake", block)

    def test_generated_asm_f2_forces_assemble_link_then_only_launches_exe(self):
        block = function_block(
            "build_and_run_generated_assembly_document",
            "assemble_document",
        )
        self.assertIn("self.assemble_generated_document(", block)
        self.assertIn("extra_link_inputs=extra_inputs", block)
        self.assertIn('output_path.suffix.casefold() == ".exe"', block)
        self.assertIn("return self._launch_assembled_document(document)", block)
        self.assertNotIn("assemble_document(document)", block)
        self.assertNotIn("mingw32-make", block)
        self.assertNotIn("qmake", block)

    def test_internal_pe32_assembler_produces_linked_exe(self):
        d64 = load_d64()
        source = """bits 32\nglobal _start\nentry _start\nsection .text\n_start:\n    ret\n"""
        program = d64.assemble_pe32_source(source, filename="stage59.asm", gui=False)
        self.assertTrue(program.executable.startswith(b"MZ"))
        self.assertGreaterEqual(len(program.executable), 1024)

    def test_internal_pe64_assembler_produces_linked_exe(self):
        d64 = load_d64()
        source = """bits 64\nglobal _start\nentry _start\nsection .text\n_start:\n    ret\n"""
        program = d64.assemble_pe64_source(source, filename="stage59.asm", gui=False)
        self.assertTrue(program.executable.startswith(b"MZ"))
        self.assertGreaterEqual(len(program.executable), 1024)


if __name__ == "__main__":
    unittest.main()
