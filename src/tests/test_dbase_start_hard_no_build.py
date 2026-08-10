from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "d64_dism.py"

class DBaseStartHardNoBuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = SOURCE.read_text(encoding="utf-8")

    def test_no_qmake_or_make_implementation_exists(self):
        lowered = self.text.casefold()
        for forbidden in (
            "mingw32-make",
            "qmake.exe",
            "shutil.which(\"qmake",
            "build_dbase_qt5_runtime_dll",
            "ensure_dbase_qt5_runtime",
            "d64qt5_bridge.pro\", \"config+=release",
        ):
            self.assertNotIn(forbidden.casefold(), lowered)

    def test_dbase_start_is_direct_exe_launch(self):
        start = self.text.index("def _start_existing_dbase_executable(")
        end = self.text.index("def start_assembled_document(", start)
        block = self.text[start:end]
        self.assertIn("self.current_directory", block)
        self.assertIn("with_suffix(\".exe\")", block)
        self.assertIn("return self._launch_assembled_document(document)", block)
        self.assertNotIn("assemble_document", block)
        self.assertNotIn("assemble_generated_document", block)

    def test_qt5_launcher_only_uses_popen(self):
        start = self.text.index("def _launch_dbase_qt5_gui(")
        end = self.text.index("def _launch_dbase_embedded_console(", start)
        block = self.text[start:end]
        self.assertIn("subprocess.Popen([str(output_path)]", block)
        self.assertNotIn("subprocess.run", block)
        self.assertNotIn("shutil.which", block)
        self.assertNotIn("TemporaryDirectory", block)

    def test_no_bytecode_is_shipped(self):
        bad = list(ROOT.rglob("*.pyc")) + list(ROOT.rglob("*.pyo"))
        self.assertEqual([], bad)

if __name__ == "__main__":
    unittest.main()
