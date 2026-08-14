from __future__ import annotations

import importlib.util
import sys
import tempfile
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "d64_dism.py").read_text(encoding="utf-8")


def load_d64():
    sys.modules.setdefault("flags_rc", types.ModuleType("flags_rc"))
    name = "_d64_stage31_open_dialog_test"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, ROOT / "d64_dism.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class CustomOpenFileDialogStage31Tests(unittest.TestCase):
    def test_custom_dialog_replaces_main_file_open_native_dialog(self):
        self.assertIn("class ProjectOpenFileDialog(QDialog):", SOURCE)
        self.assertIn("dialog = ProjectOpenFileDialog(", SOURCE)
        start = SOURCE.index("        def open_document_dialog(self) -> None:")
        end = SOURCE.index("        def open_document(self, path: Path) -> bool:", start)
        block = SOURCE[start:end]
        self.assertNotIn("QFileDialog.getOpenFileName", block)
        self.assertIn("dialog.fileName", block)

    def test_navigation_and_address_bar_controls_exist(self):
        for token in (
            'setObjectName("open_back_button")',
            'setObjectName("open_forward_button")',
            'setObjectName("open_up_button")',
            'setObjectName("open_path_combo")',
            'QLineEdit.LeadingPosition',
            'setObjectName("breadcrumb_subdir_button")',
            'setArrowType(Qt.DownArrow)',
            'def show_subdirectory_menu(self)',
            'def show_editable_path(self)',
            'def show_breadcrumb_path(self)',
        ):
            self.assertIn(token, SOURCE)

    def test_search_splitter_directory_tree_and_extension_check_list(self):
        for token in (
            'setObjectName("open_search_edit")',
            'QLineEdit.TrailingPosition',
            'setObjectName("open_main_splitter")',
            'setObjectName("open_directory_tree")',
            'setObjectName("open_file_view")',
            'setObjectName("open_extension_check_list")',
            'QSplitter(Qt.Horizontal, self)',
            'QListWidgetItem("Alle *.*", self.extension_list)',
        ):
            self.assertIn(token, SOURCE)

    def test_file_combo_is_rebuilt_per_directory_and_open_sets_filename_first(self):
        self.assertIn('setObjectName("open_full_path_combo")', SOURCE)
        self.assertIn("self.file_combo.clear()", SOURCE)
        self.assertIn("def _rebuild_file_combo(self) -> None:", SOURCE)
        open_start = SOURCE.index("        def open_selected(self) -> None:")
        open_end = SOURCE.index("\n\n    class ExplorerWindow", open_start)
        block = SOURCE[open_start:open_end]
        self.assertLess(block.index("self.fileName = str(candidate)"), block.index("self.accept()"))

    def test_search_filters_directories_and_files_and_extension_only_files(self):
        start = SOURCE.index("    class OpenFileFilterProxyModel")
        end = SOURCE.index("    class ProjectOpenFileDialog", start)
        block = SOURCE[start:end]
        self.assertIn("self._search_text not in name.casefold()", block)
        self.assertIn("if info.isDir():", block)
        self.assertIn("Path(name).suffix.casefold() in self._extensions", block)

    def test_opened_file_is_registered_in_project_by_extension(self):
        self.assertIn("def _register_opened_file_in_project(self, path: Path) -> None:", SOURCE)
        self.assertIn("category_key = project_category_for_path(path)", SOURCE)
        self.assertIn("self._add_project_entry(", SOURCE)
        self.assertIn("self.save_project()", SOURCE)

    def test_project_category_mapping_used_for_saved_project_entry(self):
        d64 = load_d64()
        self.assertEqual(d64.project_category_for_path(Path("demo.dbase")), "dbase")
        self.assertEqual(d64.project_category_for_path(Path("demo.pas")), "pascal")
        self.assertEqual(d64.project_category_for_path(Path("demo.asm")), "assembler")
        self.assertEqual(d64.project_category_for_path(Path("demo.xyz")), "other")

    def test_project_ini_roundtrip_keeps_opened_style_entry(self):
        d64 = load_d64()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = root / "sample.pro"
            source = root / "source.dbase"
            source.write_text('? "ok"\n', encoding="utf-8")
            entries = d64.empty_project_entries()
            entries["dbase"].append({"title": source.name, "path": str(source)})
            d64.save_project_ini(project, entries)
            loaded = d64.load_project_ini(project)
            self.assertEqual(len(loaded["dbase"]), 1)
            self.assertEqual(Path(loaded["dbase"][0]["path"]).resolve(), source.resolve())


if __name__ == "__main__":
    unittest.main()
