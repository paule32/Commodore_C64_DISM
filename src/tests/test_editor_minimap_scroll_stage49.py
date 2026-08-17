from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / 'd64_dism.py').read_text(encoding='utf-8')


class EditorMiniMapScrollStage49Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        start = SOURCE.index('class SourceMiniMap(QWidget):')
        end = SOURCE.index('class SourceTextEdit(QPlainTextEdit):')
        cls.body = SOURCE[start:end]

    def test_scroll_threshold_is_120_pixels(self):
        self.assertIn('MINI_MAP_SCROLL_HEIGHT = 120', self.body)

    def test_long_minimap_uses_visible_window(self):
        self.assertIn('def _visible_line_window(self):', self.body)
        self.assertIn('visible = min(count, self.MINI_MAP_SCROLL_HEIGHT)', self.body)
        self.assertIn('maximum_start = count - visible', self.body)
        self.assertIn('self._scroll_ratio() * maximum_start', self.body)

    def test_minimap_scroll_is_derived_from_editor_scrollbar(self):
        self.assertIn('def _scroll_ratio(self) -> float:', self.body)
        self.assertIn('scrollbar = self.editor.verticalScrollBar()', self.body)
        self.assertIn('scrollbar.value() - minimum', self.body)
        self.assertNotIn('self._mini_scroll_value =', self.body)
        self.assertNotIn('self._mini_scroll_position =', self.body)

    def test_scroll_indicator_is_visible_for_long_documents(self):
        self.assertIn('def _mini_scroll_handle_rectangle(self) -> QRect:', self.body)
        self.assertIn('count <= self.MINI_MAP_SCROLL_HEIGHT', self.body)
        self.assertIn('painter.fillRect(scroll_handle, handle_color)', self.body)

    def test_painting_uses_scrolled_line_slice(self):
        self.assertIn('first, last = self._visible_line_window()', self.body)
        self.assertIn('visible_lines = lines[first:last]', self.body)
        self.assertIn('for local_index, line_length in enumerate(visible_lines):', self.body)

    def test_existing_bidirectional_editor_control_is_preserved(self):
        self.assertIn('vertical.valueChanged.connect(self.update)', self.body)
        self.assertIn('QStyle.sliderValueFromPosition(', self.body)
        self.assertIn('scrollbar.setValue(value)', self.body)
        self.assertIn('def wheelEvent(self, event) -> None:', self.body)


if __name__ == '__main__':
    unittest.main()
