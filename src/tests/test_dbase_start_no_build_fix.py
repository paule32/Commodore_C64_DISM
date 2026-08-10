from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "d64_dism.py").read_text(encoding="utf-8")


def function_block(name: str, next_name: str | None = None) -> str:
    start = SOURCE.index(f"def {name}")
    if next_name is not None:
        end = SOURCE.index(f"def {next_name}", start)
        return SOURCE[start:end]
    match = re.search(r"\n\s{8}def [A-Za-z_]", SOURCE[start + 1 :])
    if match:
        return SOURCE[start : start + 1 + match.start()]
    return SOURCE[start:]


class DBaseStartNoBuildFixTests(unittest.TestCase):
    def test_start_button_only_selects_existing_workdir_exe(self):
        block = function_block(
            "_start_existing_dbase_executable",
            "start_assembled_document",
        )
        self.assertIn("self.current_directory", block)
        self.assertIn('with_suffix(".exe")', block)
        self.assertIn("executable.is_file()", block)
        self.assertIn("self._launch_assembled_document(document)", block)
        self.assertNotIn("assemble_document(", block)
        self.assertNotIn("assemble_generated_document(", block)
        self.assertNotIn("build_and_run_source_document(", block)

    def test_qt5_launch_directly_executes_exe_without_runtime_build(self):
        block = function_block(
            "_launch_dbase_qt5_gui",
            "_launch_dbase_embedded_console",
        )
        self.assertIn("subprocess.Popen([str(output_path)]", block)
        self.assertNotIn("ensure_dbase_qt5_runtime", block)
        self.assertNotIn("build_dbase_qt5_runtime_dll", block)
        self.assertNotIn("subprocess.run(", block)
        self.assertNotIn("shutil.which(\"qmake", block)
        self.assertNotIn("shutil.which(\"mingw32-make", block)

    def test_runtime_build_helpers_are_completely_removed(self):
        self.assertNotIn("def ensure_dbase_qt5_runtime", SOURCE)
        self.assertNotIn("def build_dbase_qt5_runtime_dll", SOURCE)
        self.assertNotIn("mingw32-make", SOURCE)
        self.assertNotIn("qmake.exe", SOURCE)

    def test_cli_link_does_not_auto_build_qt5_runtime(self):
        start = SOURCE.index("def _compile_cli_source") if "def _compile_cli_source" in SOURCE else SOURCE.index("def run_cli") if "def run_cli" in SOURCE else SOURCE.index("def main(")
        cli = SOURCE[start:]
        self.assertNotIn("ensure_dbase_qt5_runtime(output_path.parent", cli)
        self.assertNotIn("build_dbase_qt5_runtime_dll(output_path.parent", cli)

    def test_f2_still_links_then_launches(self):
        block = function_block("build_and_run_source_document", "assemble_document")
        self.assertIn("assemble_document(document)", block)
        self.assertIn("return self._launch_assembled_document(document)", block)


if __name__ == "__main__":
    unittest.main()
