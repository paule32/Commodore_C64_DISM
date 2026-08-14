from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "d64_dism.py").read_text(encoding="utf-8")


class OpenDialogWorkdirStage32Tests(unittest.TestCase):
    def _open_dialog_block(self) -> str:
        start = SOURCE.index("        def open_document_dialog(self) -> None:")
        end = SOURCE.index("        def open_document(self, path: Path) -> bool:", start)
        return SOURCE[start:end]

    def test_last_dialog_directory_is_adopted_before_accept_cancel_test(self):
        block = self._open_dialog_block()
        self.assertIn("result = dialog.exec_()", block)
        self.assertIn("dialog_directory = Path(dialog.current_directory)", block)
        self.assertIn("self.set_current_directory(dialog_directory)", block)
        self.assertIn("if result != QDialog.Accepted or not dialog.fileName:", block)
        self.assertLess(
            block.index("self.set_current_directory(dialog_directory)"),
            block.index("if result != QDialog.Accepted or not dialog.fileName:"),
        )

    def test_cancel_keeps_new_working_directory_instead_of_start_directory(self):
        block = self._open_dialog_block()
        cancel = block[block.index("if result != QDialog.Accepted"):]
        self.assertNotIn("set_current_directory(Path.cwd", cancel)
        self.assertNotIn("self.current_directory = Path.cwd", cancel)
        self.assertIn("Arbeitsverzeichnis: {self.current_directory}", cancel)

    def test_dbase_build_targets_current_working_directory(self):
        needle = "output_path = (self.current_directory / output_path.name).resolve()"
        self.assertIn(needle, SOURCE)

    def test_dbase_start_searches_current_working_directory(self):
        start = SOURCE.index("        def _start_existing_dbase_executable(")
        end = SOURCE.index("        def start_assembled_document(", start)
        block = SOURCE[start:end]
        self.assertIn(
            'executable = (self.current_directory / document.path.with_suffix(".exe").name).resolve()',
            block,
        )

    def test_process_cwd_is_the_executable_directory(self):
        start = SOURCE.index("        def _launch_dbase_qt5_gui(")
        end = SOURCE.index("        def _launch_dbase_embedded_console(", start)
        block = SOURCE[start:end]
        self.assertIn('"cwd": str(output_path.parent)', block)


if __name__ == "__main__":
    unittest.main()
