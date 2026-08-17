from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / 'd64_dism.py').read_text(encoding='utf-8')


class MarkdownPreviewStage54Tests(unittest.TestCase):
    def test_markdown_extensions_are_recognized(self):
        self.assertIn('MARKDOWN_EXTENSIONS  = {".md", ".markdown"}', SOURCE)
        self.assertIn('if suffix in self.MARKDOWN_EXTENSIONS:', SOURCE)
        self.assertIn('return "markdown"', SOURCE)

    def test_markdown_preview_is_qplaintextedit(self):
        self.assertIn('class MarkdownPreviewEdit(QPlainTextEdit):', SOURCE)
        self.assertIn('self.setReadOnly(True)', SOURCE)
        self.assertIn('self.setLineWrapMode(QPlainTextEdit.WidgetWidth)', SOURCE)

    def test_markdown_tab_is_created_and_visibility_is_suffix_driven(self):
        self.assertIn('self.views.addTab(self.markdown_preview_page, "MarkDown")', SOURCE)
        self.assertIn('self._set_tab_visible_for_widget(self.markdown_preview_page, is_markdown)', SOURCE)

    def test_source_editor_keeps_gutter_and_minimap(self):
        self.assertIn('self.raw_editor_container = SourceEditorWithMiniMap(', SOURCE)
        self.assertIn('self.raw_minimap = self.raw_editor_container.minimap', SOURCE)
        self.assertIn('self.line_number_area = LineNumberArea(self)', SOURCE)

    def test_preview_tracks_source_changes(self):
        self.assertIn('self.raw_editor.textChanged.connect(self._markdown_source_changed)', SOURCE)
        self.assertIn('def _markdown_source_changed(self) -> None:', SOURCE)
        self.assertIn('self.markdown_preview.set_markdown_source(', SOURCE)
        self.assertIn('self._render_timer.setInterval(35)', SOURCE)

    def test_github_flavoured_constructs_are_supported(self):
        preview_start = SOURCE.index('class MarkdownPreviewEdit(QPlainTextEdit):')
        preview_end = SOURCE.index('class SourceMiniMap(QWidget):', preview_start)
        body = SOURCE[preview_start:preview_end]
        for marker in (
            '_HEADING_RE', '_FENCE_RE', '_QUOTE_RE', '_TASK_RE',
            '_UL_RE', '_OL_RE', '_HR_RE', '_TABLE_DELIMITER_RE',
            '"link"', '"image"', '"code"', '"strong"', '"strike"', '"em"',
        ):
            self.assertIn(marker, body)

    def test_markdown_raw_source_has_syntax_highlighting(self):
        self.assertIn('self.markdown_enabled = False', SOURCE)
        self.assertIn('def set_markdown_enabled(self, enabled: bool) -> None:', SOURCE)
        self.assertIn('def _highlight_markdown_block(self, text: str) -> None:', SOURCE)
        self.assertIn('self.syntax_highlighter.set_markdown_enabled(is_markdown)', SOURCE)

    def test_github_light_and_dark_palettes_are_present(self):
        self.assertIn('QColor("#0D1117")', SOURCE)
        self.assertIn('QColor("#C9D1D9")', SOURCE)
        self.assertIn('QColor("#FFFFFF")', SOURCE)
        self.assertIn('QColor("#24292F")', SOURCE)
        self.assertIn('self.markdown_preview.set_dark_mode(enabled)', SOURCE)

    def test_markdown_gutter_uses_matching_theme(self):
        self.assertIn('if self._markdown_mode and self._dark_mode:', SOURCE)
        self.assertIn('background = QColor("#161B22")', SOURCE)
        self.assertIn('background = QColor("#F6F8FA")', SOURCE)

    def test_links_are_rendered_as_anchors(self):
        self.assertIn('fmt.setAnchor(True)', SOURCE)
        self.assertIn('fmt.setAnchorHref(best.group(2).strip())', SOURCE)
        self.assertIn('QDesktopServices.openUrl(QUrl(href))', SOURCE)


if __name__ == '__main__':
    unittest.main()
