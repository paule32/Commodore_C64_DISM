from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / 'd64_dism.py').read_text(encoding='utf-8')


class MarkdownPreviewMiniMapStage57Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        preview_start = SOURCE.index('class MarkdownPreviewEdit(QPlainTextEdit):')
        preview_end = SOURCE.index('class SourceMiniMap(QWidget):', preview_start)
        cls.preview_body = SOURCE[preview_start:preview_end]

    def test_preview_base_font_is_one_point_larger(self):
        self.assertIn('preview_font = QFont("Segoe UI", 11)', self.preview_body)
        self.assertIn('fmt.setFontPointSize(11.0)', self.preview_body)

    def test_preview_code_font_is_one_point_larger(self):
        self.assertIn('fmt.setFontPointSize(10.5)', self.preview_body)
        self.assertIn('label_fmt.setFontPointSize(9.5)', self.preview_body)

    def test_heading_fonts_are_one_point_larger(self):
        self.assertIn(
            'sizes = {1: 23.0, 2: 19.0, 3: 17.0, 4: 15.0, 5: 13.0, 6: 12.0}',
            self.preview_body,
        )

    def test_markdown_preview_uses_same_source_minimap_class(self):
        self.assertIn('self.markdown_minimap = SourceMiniMap(', SOURCE)
        self.assertIn('self.markdown_preview,', SOURCE)
        self.assertIn('markdown_preview_layout.addWidget(self.markdown_minimap)', SOURCE)

    def test_preview_minimap_uses_horizontal_sibling_layout(self):
        self.assertIn(
            'markdown_preview_layout = QHBoxLayout(self.markdown_preview_page)',
            SOURCE,
        )
        self.assertIn('markdown_preview_layout.setSpacing(0)', SOURCE)

    def test_same_bidirectional_minimap_behavior_is_reused(self):
        start = SOURCE.index('class SourceMiniMap(QWidget):')
        end = SOURCE.index('class SourceTextEdit(QPlainTextEdit):', start)
        body = SOURCE[start:end]
        self.assertIn('vertical.valueChanged.connect(self.update)', body)
        self.assertIn('QStyle.sliderValueFromPosition(', body)
        self.assertIn('scrollbar.setValue(value)', body)
        self.assertIn('MINI_MAP_SCROLL_HEIGHT = 120', body)


if __name__ == '__main__':
    unittest.main()
