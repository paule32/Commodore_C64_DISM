from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / 'd64_dism.py').read_text(encoding='utf-8')


class EditorMiniMapStage48Tests(unittest.TestCase):
    def test_minimap_class_exists(self):
        self.assertIn('class SourceMiniMap(QWidget):', SOURCE)
        self.assertIn('MINI_MAP_WIDTH = 92', SOURCE)

    def test_editor_scroll_updates_minimap(self):
        minimap = SOURCE[
            SOURCE.index('class SourceMiniMap(QWidget):'):
            SOURCE.index('class SourceTextEdit(QPlainTextEdit):')
        ]
        self.assertIn(
            'vertical = self.editor.verticalScrollBar()',
            minimap,
        )
        self.assertIn(
            'vertical.valueChanged.connect(self.update)',
            minimap,
        )

    def test_minimap_uses_same_scrollbar_for_reverse_control(self):
        body = SOURCE[
            SOURCE.index('class SourceMiniMap(QWidget):'):
            SOURCE.index('class SourceTextEdit(QPlainTextEdit):')
        ]
        self.assertIn('scrollbar = self.editor.verticalScrollBar()', body)
        self.assertIn('QStyle.sliderValueFromPosition(', body)
        self.assertIn('scrollbar.setValue(value)', body)
        self.assertIn('QStyle.sliderPositionFromValue(', body)

    def test_minimap_drag_capture_is_present(self):
        self.assertIn('self.grabMouse()', SOURCE)
        self.assertIn('self.releaseMouse()', SOURCE)
        self.assertIn('self._dragging = True', SOURCE)
        self.assertIn('event.buttons() & Qt.LeftButton', SOURCE)

    def test_source_editor_container_keeps_original_editor_type(self):
        self.assertIn('class SourceEditorWithMiniMap(QWidget):', SOURCE)
        self.assertIn('self.editor = SourceTextEdit(self)', SOURCE)
        self.assertIn('self.minimap = SourceMiniMap(self.editor, self)', SOURCE)
        self.assertIn('layout.addWidget(self.editor, 1)', SOURCE)
        self.assertIn('layout.addWidget(self.minimap)', SOURCE)

    def test_raw_editor_is_wrapped_without_changing_public_reference(self):
        self.assertIn(
            'self.raw_editor_container = SourceEditorWithMiniMap(',
            SOURCE,
        )
        self.assertIn(
            'self.raw_editor = self.raw_editor_container.editor',
            SOURCE,
        )
        self.assertIn(
            'self.raw_minimap = self.raw_editor_container.minimap',
            SOURCE,
        )
        self.assertIn(
            'source_layout.addWidget(self.raw_editor_container, 1)',
            SOURCE,
        )

    def test_existing_editor_features_remain_on_raw_editor(self):
        required = [
            'self.raw_editor.assembler_help_requested.connect(',
            'self.raw_editor.context_help_requested.connect(',
            'self.raw_editor.build_requested.connect(',
            'self.raw_editor.breakpoints_changed.connect(',
            'AssemblerSyntaxHighlighter(\n                self.raw_editor.document()',
        ]
        for marker in required:
            with self.subTest(marker=marker):
                self.assertIn(marker, SOURCE)

    def test_no_second_scroll_state_variable_is_introduced(self):
        minimap = SOURCE[
            SOURCE.index('class SourceMiniMap(QWidget):'):
            SOURCE.index('class SourceTextEdit(QPlainTextEdit):')
        ]
        self.assertNotRegex(minimap, r'self\._scroll_(?:value|position)\s*=')


if __name__ == '__main__':
    unittest.main()
