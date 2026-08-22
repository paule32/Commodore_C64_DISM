from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "d64_dism.py").read_text(encoding="utf-8")


class EditorCompilePipelineSourceTests(unittest.TestCase):
    def test_unsaved_documents_use_display_name_suffix(self) -> None:
        self.assertIn("def effective_suffix(self) -> str:", SOURCE)
        self.assertIn("return Path(self.custom_display_name).suffix.casefold()", SOURCE)
        self.assertIn("suffix = self.effective_suffix", SOURCE)
        self.assertIn("document.update_syntax_highlighting()", SOURCE)

    def test_new_c_and_pascal_show_compile_toolbar(self) -> None:
        block_start = SOURCE.index("def update_syntax_highlighting")
        block_end = SOURCE.index("def invalidate_assembly_result", block_start)
        block = SOURCE[block_start:block_end]
        self.assertIn('self.assembler_panel.setVisible(', block)
        self.assertIn('self.assemble_button.setText("Compile")', block)
        self.assertIn('self.c64_target_button', SOURCE)
        self.assertIn('self.amiga_target_button', SOURCE)
        self.assertIn('self.start_assembled_button.setVisible(is_assembler)', block)

    def test_compile_stage_does_not_assemble_program(self) -> None:
        self.assertIn("def _finish_compile_stage(", SOURCE)
        self.assertIn("Beendet nur Compile: ASM speichern", SOURCE)
        self.assertIn("noch nicht erzeugt – jetzt Assemble verwenden", SOURCE)
        self.assertIn("return self._finish_compile_stage(", SOURCE)

    def test_generated_tab_uses_assemble_then_start(self) -> None:
        self.assertIn('self.assemble_generated_button.setText("Assemble")', SOURCE)
        self.assertIn("self.assemble_generated_requested.emit", SOURCE)
        self.assertIn("self.start_generated_requested.emit", SOURCE)
        self.assertIn("document.set_assembly_result(", SOURCE)
        self.assertIn("self.start_generated_button.setEnabled(has_generated_assembly)", SOURCE)

    def test_unsaved_build_prompts_for_save_as(self) -> None:
        block_start = SOURCE.index("def assemble_document")
        block_end = SOURCE.index("def _resolve_vice_for_program_start", block_start)
        block = SOURCE[block_start:block_end]
        self.assertIn("document.is_build_document and document.path is None", block)
        self.assertIn("self._save_document(document, save_as=True)", block)

    def test_tab_new_submenu_reuses_main_menu_actions(self) -> None:
        self.assertIn("def _populate_new_document_menu", SOURCE)
        context_start = SOURCE.index("def _show_document_tab_context_menu")
        context_end = SOURCE.index("def rename_document_tab", context_start)
        context = SOURCE[context_start:context_end]
        self.assertIn('new_menu = menu.addMenu("Neu")', context)
        self.assertIn("self._populate_new_document_menu(new_menu)", context)
        for action in (
            "new_basic_action",
            "new_assembler_action",
            "new_pascal_action",
            "new_c_action",
            "new_character_map_action",
            "new_text_screen_action",
            "new_pixel_screen_action",
            "new_text_file_action",
        ):
            self.assertIn(f"menu.addAction(self.{action})", SOURCE)


if __name__ == "__main__":
    unittest.main()
