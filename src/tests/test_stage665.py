# -*- coding: utf-8 -*-
"""Stage 665: Turbo Help source gutter, minimap and fourth-column body."""
import ast
from pathlib import Path
import textwrap
from types import SimpleNamespace

ROOT = Path(__file__).parent
EDITOR = (ROOT / 'turbo_help_gui.py').read_text(encoding='utf-8')
WIDGETS = (ROOT / 'turbo_help_editor_widgets.py').read_text(encoding='utf-8')
HELP = (ROOT / 'd64qt5/d64_turbo_help_window.hpp').read_text(encoding='utf-8')


def method_from_source(class_name, method, extra):
    module = ast.parse(WIDGETS)
    source_class = next(n for n in module.body if isinstance(n, ast.ClassDef) and n.name == class_name)
    func = next(n for n in source_class.body if isinstance(n, ast.FunctionDef) and n.name == method)
    namespace = dict(extra)
    exec(compile(textwrap.dedent(ast.get_source_segment(WIDGETS, func)), 'widgets', 'exec'), namespace)
    return namespace[method]


def test_each_thlp_tab_is_real_qplaintextedit_with_gutter_and_minimap():
    assert 'class TurboHelpSourceEditor(QPlainTextEdit):' in WIDGETS
    assert 'edit = TurboHelpSourceEditor(self.tabs)' in EDITOR
    assert "edit.setObjectName('turbo_help_source_editor')" in EDITOR
    assert 'self.line_number_area = TurboHelpLineNumberArea(self)' in WIDGETS
    assert 'self.minimap = TurboHelpMiniMap(self)' in WIDGETS
    assert 'setViewportMargins(width, 0, self.minimap.WIDTH, 0)' in WIDGETS
    assert 'self.setLineWrapMode(QPlainTextEdit.NoWrap)' in WIDGETS


def test_editor_api_unchanged_for_save_switch_and_compile():
    for piece in ('edit.document().isModified()', 'edit.toPlainText()',
                  'edit._thlp_path = path', 'self.tabs.setCurrentWidget(edit)',
                  'widget.setFocus(Qt.OtherFocusReason)', 'self._save_changes_before_switch()'):
        assert piece in EDITOR
    assert 'QTabWidget(self)' in EDITOR
    assert 'compile_help_sources(paths, executable)' in EDITOR


def test_gutter_sizes_for_line_counts():
    fn = method_from_source('TurboHelpSourceEditor', 'line_number_area_width', {})
    metrics = SimpleNamespace(horizontalAdvance=lambda _text: 8)
    for count, expected in ((1, 36), (10, 36), (999, 36), (1000, 44), (1234567, 68)):
        owner = SimpleNamespace(blockCount=lambda: count, fontMetrics=lambda: metrics)
        assert fn(owner) == expected


def test_gutter_is_scroll_synced_and_highlights_current_row():
    assert 'self.blockCountChanged.connect(self._update_viewport_margins)' in WIDGETS
    assert 'self.updateRequest.connect(self._update_gutter)' in WIDGETS
    assert 'self.cursorPositionChanged.connect(self.line_number_area.update)' in WIDGETS
    assert 'self.line_number_area.scroll(0, dy)' in WIDGETS
    assert 'self.firstVisibleBlock()' in WIDGETS
    assert 'number == active' in WIDGETS
    assert "str(number + 1)" in WIDGETS
    assert "self.setObjectName('turbo_help_line_number_gutter')" in WIDGETS


def test_minimap_updates_with_text_scroll_and_resizes():
    assert "self.setObjectName('turbo_help_source_minimap')" in WIDGETS
    assert 'editor.textChanged.connect(self._rebuild)' in WIDGETS
    assert 'scroll.valueChanged.connect(self.update)' in WIDGETS
    assert 'scroll.rangeChanged.connect' in WIDGETS
    assert 'self._position_decorations()' in WIDGETS
    assert 'self.viewport().geometry().right() + 1' in WIDGETS
    assert 'self._scroll_to_y(event.pos().y())' in WIDGETS
    assert 'self.editor.setFocus(Qt.MouseFocusReason)' in WIDGETS
    assert 'if self._dragging and event.buttons() & Qt.LeftButton:' in WIDGETS


class FakeRect:
    def __init__(self, x, y, w, h):
        self._y = y
        self._h = h
        self._w = w
    def height(self):
        return self._h
    def width(self):
        return self._w
    def y(self):
        return self._y


class FakeQStyle:
    @staticmethod
    def sliderPositionFromValue(low, high, val, travel, inverted):
        if high == low:
            return 0
        return round(travel * (val - low) / (high - low))
    @staticmethod
    def sliderValueFromPosition(low, high, pos, travel, inverted):
        if travel == 0:
            return low
        return round(low + (high - low) * pos / travel)


class FakeBar:
    def __init__(self, maximum, value=0, page=10):
        self.max = maximum
        self.val = value
        self.page = page
    def maximum(self): return self.max
    def minimum(self): return 0
    def pageStep(self): return self.page
    def value(self): return self.val
    def setValue(self, value): self.val = value


def test_minimap_thumb_and_clicks_track_real_editor_scrollbar():
    bar = FakeBar(100, value=50, page=20)
    fn_rect = method_from_source('TurboHelpMiniMap', '_visible_region',
                                 {'QRect': FakeRect, 'QStyle': FakeQStyle})
    fn_scroll = method_from_source('TurboHelpMiniMap', '_scroll_to_y',
                                   {'QStyle': FakeQStyle})
    owner = SimpleNamespace(editor=SimpleNamespace(verticalScrollBar=lambda: bar),
                            height=lambda: 240, width=lambda: 92)
    owner._visible_region = lambda: fn_rect(owner)
    thumb = fn_rect(owner)
    assert thumb.height() == 40
    assert thumb.y() == 100
    fn_scroll(owner, 239)
    assert bar.value() == 100
    fn_scroll(owner, -100)
    assert bar.value() == 0
    bar.max = 0
    thumb = fn_rect(owner)
    assert thumb.height() == 240
    fn_scroll(owner, 100)
    assert bar.value() == 0


def test_bridge_inset_uses_actual_document_root_frame():
    assert 'format.setLeftMargin(qreal(qMax(1, gridCellWidth_)));' in HELP
    assert 'root->setFrameFormat(format);' in HELP
    assert 'browser_->document()->setDocumentMargin(0.0);' in HELP
    assert 'setHelpHtml(topics_.value(currentTopic_));' in HELP
    assert 'setHelpHtml(topics_.value(resolvedTopic));' in HELP
    assert 'setHelpHtml(QStringLiteral("<b>Hilfethema nicht gefunden: </b>") + topic);' in HELP
    assert 'border:2px solid #ffe600' in HELP
    assert 'shadow->setOffset(5.0, 5.0)' in HELP
    assert 'QStringLiteral("Hilfe:  ") + resolvedTopic' in HELP
