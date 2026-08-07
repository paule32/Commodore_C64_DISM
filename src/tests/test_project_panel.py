from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from d64_dism import (
    PROJECT_CATEGORIES,
    PROJECT_CATEGORY_DEFAULT_EXTENSIONS,
    empty_project_entries,
    format_project_ini,
    load_project_ini,
    project_category_for_path,
    project_untitled_filename,
    save_project_ini,
)

ROOT = Path(__file__).resolve().parents[1]
GUI_SOURCE = ROOT / "d64_dism.py"


class ProjectIniTests(unittest.TestCase):
    def test_all_requested_categories_are_present(self) -> None:
        titles = [title for _key, title, _extensions in PROJECT_CATEGORIES]
        self.assertEqual(
            titles,
            [
                "BASIC - Programme",
                "Assembler-Programme",
                "Pascal-Programme",
                "C-Programme",
                "Character Map's",
                "Paletten",
                "Char Screen's",
                "Pixel Screen's",
                "Textdateien",
                "SID's",
                "Bilder",
                "Sonstiges",
            ],
        )

    def test_project_round_trip_uses_relative_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "src" / "main.c"
            source.parent.mkdir()
            source.write_text("int main(void) { return 0; }", encoding="utf-8")
            project = root / "demo.pro"
            entries = empty_project_entries()
            entries["c"].append({"title": "Hauptprogramm", "path": str(source)})
            save_project_ini(project, entries)
            project_text = project.read_text(encoding="utf-8")
            self.assertIn('"path":"src/main.c"', project_text)
            loaded = load_project_ini(project)
            self.assertEqual(loaded["c"][0]["title"], "Hauptprogramm")
            self.assertEqual(Path(loaded["c"][0]["path"]), source.resolve())

    def test_format_contains_ini_sections_for_every_root(self) -> None:
        text = format_project_ini(empty_project_entries(), Path("demo.pro"))
        for key, _title, _extensions in PROJECT_CATEGORIES:
            self.assertIn(f"[Category.{key}]", text)

    def test_default_extensions_for_new_project_items(self) -> None:
        self.assertEqual(PROJECT_CATEGORY_DEFAULT_EXTENSIONS["basic"], ".bas")
        self.assertEqual(PROJECT_CATEGORY_DEFAULT_EXTENSIONS["assembler"], ".asm")
        self.assertEqual(PROJECT_CATEGORY_DEFAULT_EXTENSIONS["pascal"], ".pas")
        self.assertEqual(PROJECT_CATEGORY_DEFAULT_EXTENSIONS["c"], ".c")
        self.assertEqual(PROJECT_CATEGORY_DEFAULT_EXTENSIONS["character_maps"], ".chr")
        self.assertEqual(PROJECT_CATEGORY_DEFAULT_EXTENSIONS["palettes"], ".pal")
        self.assertEqual(PROJECT_CATEGORY_DEFAULT_EXTENSIONS["char_screens"], ".scr")
        self.assertEqual(PROJECT_CATEGORY_DEFAULT_EXTENSIONS["pixel_screens"], ".px16")
        self.assertEqual(PROJECT_CATEGORY_DEFAULT_EXTENSIONS["text_files"], ".txt")
        self.assertEqual(PROJECT_CATEGORY_DEFAULT_EXTENSIONS["sid_files"], ".sid")
        self.assertEqual(PROJECT_CATEGORY_DEFAULT_EXTENSIONS["images"], ".png")
        self.assertEqual(PROJECT_CATEGORY_DEFAULT_EXTENSIONS["other"], ".dat")

    def test_untitled_name_skips_project_entries_and_existing_files(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            (directory / "Unbenannt_2.c").write_text("", encoding="utf-8")
            result = project_untitled_filename(
                "c",
                ["Unbenannt_1.c"],
                directory=directory,
            )
            self.assertEqual(result, "Unbenannt_3.c")

    def test_category_detection(self) -> None:
        self.assertEqual(project_category_for_path(Path("demo.bas")), "basic")
        self.assertEqual(project_category_for_path(Path("demo.asm")), "assembler")
        self.assertEqual(project_category_for_path(Path("demo.pas")), "pascal")
        self.assertEqual(project_category_for_path(Path("demo.c")), "c")
        self.assertEqual(project_category_for_path(Path("demo.chr")), "character_maps")
        self.assertEqual(project_category_for_path(Path("demo.pal")), "palettes")
        self.assertEqual(project_category_for_path(Path("demo.scr")), "char_screens")
        self.assertEqual(project_category_for_path(Path("demo.px16")), "pixel_screens")
        self.assertEqual(project_category_for_path(Path("demo.sid")), "sid_files")
        self.assertEqual(project_category_for_path(Path("demo.png")), "images")
        self.assertEqual(project_category_for_path(Path("demo.xyz")), "other")


class ProjectPanelSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = GUI_SOURCE.read_text(encoding="utf-8")

    def test_right_panel_has_project_before_information(self) -> None:
        project = 'self.right_panel_tabs.addTab(self.project_tab, "Projekt")'
        information = '"Informationen",\n            )'
        self.assertIn(project, self.source)
        self.assertIn(information, self.source)
        self.assertLess(self.source.index(project), self.source.index(information))
        self.assertIn('self.right_info_tabs.addTab(self.dism_info_tab, "DISM START")', self.source)
        self.assertIn('self.right_info_tabs.addTab(self.file_info_tab, "Datei-Informationen")', self.source)

    def test_project_context_menu_has_requested_collection_actions(self) -> None:
        for label in ("Hilfe", "Hinzufügen", "Einträge löschen"):
            self.assertIn(f'menu.addAction("{label}")', self.source)
        self.assertIn('def add_project_entries(', self.source)
        self.assertIn('def clear_project_entries(', self.source)
        self.assertIn('root.takeChildren()', self.source)
        self.assertIn('Die Dateien auf dem Datenträger werden nicht gelöscht', self.source)

    def test_project_controls_and_prompts_exist(self) -> None:
        self.assertIn('QPushButton("Neu", tab)', self.source)
        self.assertIn('QPushButton("Speichern", tab)', self.source)
        self.assertIn('QPushButton("Speichern unter...", tab)', self.source)
        self.assertIn('box.addButton("Ja, speichern"', self.source)
        self.assertIn('"Nein, nicht speichern"', self.source)
        self.assertIn('box.addButton("Abbrechen"', self.source)
        self.assertIn('"dBase2Many-Projekte (*.pro);;Alle Dateien (*)"', self.source)

    def test_project_items_route_to_existing_editors(self) -> None:
        self.assertIn('if path.suffix.casefold() in self.EDITOR_EXTENSIONS:', self.source)
        self.assertIn('self.open_document(path)', self.source)
        self.assertIn('self.open_path(path)', self.source)
        self.assertIn('if path.suffix.lower() == ".pro":', self.source)

    def test_toolbar_help_button_precedes_zoom_in(self) -> None:
        help_action = 'self.toolbar.addAction(self.chm_viewer_action)'
        zoom_action = 'self.toolbar.addAction(self.zoom_in_action)'
        self.assertIn('self._toolbar_symbol_icon("help")', self.source)
        self.assertLess(self.source.index(help_action), self.source.index(zoom_action))

    def test_project_open_button_has_explicit_dark_style(self) -> None:
        self.assertIn('QToolButton#project_open_button', self.source)
        self.assertIn('background-color: #2d3746;', self.source)

    def test_new_project_items_create_real_category_files(self) -> None:
        for token in (
            'def create_new_project_item(',
            'def _write_new_project_file(',
            'encode_c64_palette_data(C64_CHARACTER_PALETTE)',
            'encode_c64_text_screen_data(',
            'encode_c64_pixel_screen_data(',
            'self.show_character_editor(initial_path=path)',
            'self.show_palette_editor(initial_path=path)',
            'self.show_text_screen_editor(initial_path=path)',
            'self.show_pixel_screen_editor(initial_path=path)',
        ):
            self.assertIn(token, self.source)

    def test_help_tree_uses_different_branch_and_leaf_icons(self) -> None:
        self.assertIn('QStyle.SP_DirClosedIcon', self.source)
        self.assertIn('else QStyle.SP_FileIcon', self.source)


if __name__ == "__main__":
    unittest.main()
