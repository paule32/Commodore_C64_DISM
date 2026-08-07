from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "d64_dism.py").read_text(encoding="utf-8")


class EditorStatusHelpSourceTests(unittest.TestCase):
    def test_log_clear_button_lives_in_dock_title_bar(self) -> None:
        self.assertIn('extra_text="Protokoll löschen"', SOURCE)
        self.assertIn('extra_callback=self.log_edit.clear', SOURCE)
        self.assertNotIn('QPushButton("Protokoll löschen", container)', SOURCE)

    def test_status_bar_contains_keyboard_file_and_cursor_panels(self) -> None:
        for token in (
            'self.insert_status_label = QLabel("INS"',
            'self.caps_status_label = QLabel("CAPS"',
            'self.num_status_label = QLabel("NUM"',
            '"Dateigröße: " + self._format_byte_count(size)',
            'f"Zeile: {cursor.blockNumber() + 1}',
            'f"Spalte: {cursor.positionInBlock() + 1}"',
        ):
            self.assertIn(token, SOURCE)

    def test_insert_caps_num_use_green_and_red_states(self) -> None:
        self.assertIn('color = "#32d26f" if enabled else "#ff5b5b"', SOURCE)
        self.assertIn('GetKeyState(virtual_key) & 1', SOURCE)
        self.assertIn('insert_enabled = not editor.overwriteMode()', SOURCE)

    def test_document_tab_context_menu_has_requested_actions(self) -> None:
        start = SOURCE.index('def _show_document_tab_context_menu')
        end = SOURCE.index('def rename_document_tab', start)
        block = SOURCE[start:end]
        self.assertIn('new_menu = menu.addMenu("Neu")', block)
        self.assertIn('self._populate_new_document_menu(new_menu)', block)
        self.assertIn('menu.addAction("Speichern")', block)
        self.assertIn('menu.addAction("Speichern unter...")', block)
        self.assertNotIn('menu.addAction("Hilfe")', block)
        self.assertNotIn('menu.addAction("Schließen")', block)
        self.assertNotIn('menu.addAction("Umbenennen")', block)

    def test_tab_close_and_dock_icons_are_white(self) -> None:
        self.assertIn('self._toolbar_symbol_icon("close_white")', SOURCE)
        self.assertIn('QColor(255, 255, 255)', SOURCE)
        self.assertIn('class DockTitleBar(QWidget)', SOURCE)
        self.assertIn('self.float_button.setIcon(self._symbol_icon("float"))', SOURCE)
        self.assertIn('self.close_button.setIcon(self._symbol_icon("close"))', SOURCE)

    def test_file_new_submenu_contains_all_requested_types(self) -> None:
        for label in (
            'QAction("BASIC-Programm"',
            'QAction("Assembler-Programm"',
            'QAction("Pascal-Programm"',
            'QAction("C-Programm"',
            'QAction("C-64 Character Map"',
            'QAction("C-64 Text Screen"',
            'QAction("C-64 Pixel Screen"',
            '"Textdatei"',
        ):
            self.assertIn(label, SOURCE)
        self.assertIn('self.new_document_menu = file_menu.addMenu(', SOURCE)

    def test_f1_uses_word_at_cursor_and_language_context(self) -> None:
        self.assertIn('if event.key() == Qt.Key_F1:', SOURCE)
        self.assertIn('self.request_context_help()', SOURCE)
        self.assertIn('def help_word_at_cursor(self) -> str:', SOURCE)
        self.assertIn('return "basic"', SOURCE)
        self.assertIn('return "assembler"', SOURCE)
        self.assertIn('return "pascal"', SOURCE)
        self.assertIn('return "c"', SOURCE)

    def test_debug_message_contains_chm_link(self) -> None:
        self.assertIn('# DEBUG: Diese MessageBox zeigt vorläufig', SOURCE)
        self.assertIn('"DEBUG – F1-Kontexthilfe"', SOURCE)
        self.assertIn('return f"mk:@MSITStore:{native}::/{folder}/{topic}.html"', SOURCE)

    def test_help_viewer_searches_keywords_and_topics(self) -> None:
        self.assertIn('def open_context_topic(self, language: str, word: str)', SOURCE)
        self.assertIn('(self.keywords_tab.tree, self.topics_tab.tree)', SOURCE)
        self.assertIn('dialog.set_pending_context(context_language, context_word)', SOURCE)

    def test_unsaved_language_documents_keep_correct_save_extension(self) -> None:
        self.assertIn('if not Path(suggested_name).suffix:', SOURCE)
        self.assertIn('suggested_name += ".txt"', SOURCE)
        self.assertIn('"BASIC-Dateien (*.bas *.basic);;"', SOURCE)


if __name__ == "__main__":
    unittest.main()
