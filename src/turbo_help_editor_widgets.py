# -*- coding: utf-8 -*-
"""Stage 665: DOS-like line-number gutter and scroll-synced THLP minimap.

The tab widget itself deliberately remains a QPlainTextEdit: all existing
TurboHelpEditor save/switch/F2 operations continue to work on the same object.
"""
from __future__ import annotations

from PyQt5.QtCore import QRect, QSize, Qt
from PyQt5.QtGui import QColor, QPainter
from PyQt5.QtWidgets import QPlainTextEdit, QStyle, QWidget


class TurboHelpLineNumberArea(QWidget):
    """Read-only line-number gutter beside a TurboHelpSourceEditor."""

    def __init__(self, editor: 'TurboHelpSourceEditor'):
        super().__init__(editor)
        self.editor = editor
        self.setObjectName('turbo_help_line_number_gutter')
        self.setFocusPolicy(Qt.NoFocus)

    def sizeHint(self):
        return QSize(self.editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self.editor.paint_line_numbers(event)


class TurboHelpMiniMap(QWidget):
    """Full-file overview. Click and drag to scroll the actual source editor."""

    WIDTH = 92
    MAX_LINE_LENGTH = 160

    def __init__(self, editor: 'TurboHelpSourceEditor'):
        super().__init__(editor)
        self.editor = editor
        self._line_lengths = []
        self._dragging = False
        self.setObjectName('turbo_help_source_minimap')
        self.setFocusPolicy(Qt.NoFocus)
        self.setCursor(Qt.PointingHandCursor)
        self.setMouseTracking(True)
        editor.textChanged.connect(self._rebuild)
        scroll = editor.verticalScrollBar()
        scroll.valueChanged.connect(self.update)
        scroll.rangeChanged.connect(lambda _minimum, _maximum: self.update())
        editor.updateRequest.connect(lambda _rect, _dy: self.update())
        self._rebuild()

    def sizeHint(self):
        return QSize(self.WIDTH, 180)

    def _rebuild(self):
        lengths = []
        block = self.editor.document().firstBlock()
        while block.isValid():
            lengths.append(min(self.MAX_LINE_LENGTH, len(block.text().expandtabs(4))))
            block = block.next()
        self._line_lengths = lengths
        self.update()

    def _visible_region(self):
        bar = self.editor.verticalScrollBar()
        height = max(1, self.height())
        if bar.maximum() <= bar.minimum():
            return QRect(0, 0, self.width(), height)
        page = max(1, bar.pageStep())
        total = max(1, bar.maximum() - bar.minimum() + page)
        visible_height = min(height, max(18, round(height * page / total)))
        travel = max(0, height - visible_height)
        y = QStyle.sliderPositionFromValue(
            bar.minimum(), bar.maximum(), bar.value(), travel, False)
        return QRect(0, int(y), self.width(), visible_height)

    def _scroll_to_y(self, y):
        bar = self.editor.verticalScrollBar()
        visible = self._visible_region()
        travel = max(0, self.height() - visible.height())
        if travel == 0 or bar.maximum() <= bar.minimum():
            bar.setValue(bar.minimum())
            return
        target = max(0, min(travel, int(y - visible.height() / 2)))
        bar.setValue(QStyle.sliderValueFromPosition(
            bar.minimum(), bar.maximum(), target, travel, False))

    def paintEvent(self, event):
        painter = QPainter(self)
        try:
            painter.fillRect(event.rect(), QColor('#102532'))
            painter.setPen(QColor('#63a7bb'))
            count = len(self._line_lengths)
            height = max(1, self.height())
            width = max(1, self.width() - 9)
            # Limit draw calls on very large .thlp documents.
            sample = max(1, (count + 2 * height - 1) // (2 * height))
            for i in range(0, count, sample):
                length = self._line_lengths[i]
                if length:
                    y = (i * (height - 1)) // max(1, count - 1)
                    bar_width = max(2, width * length // self.MAX_LINE_LENGTH)
                    painter.drawLine(4, y, 4 + bar_width, y)
            visible = self._visible_region()
            painter.fillRect(visible, QColor(110, 204, 228, 58))
            painter.setPen(QColor('#85d8e8'))
            painter.drawRect(visible.adjusted(0, 0, -1, -1))
            painter.setPen(QColor('#42616e'))
            painter.drawLine(0, 0, 0, height - 1)
        finally:
            painter.end()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._dragging = True
            self._scroll_to_y(event.pos().y())
            self.editor.setFocus(Qt.MouseFocusReason)
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._dragging and event.buttons() & Qt.LeftButton:
            self._scroll_to_y(event.pos().y())
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._dragging = False
            event.accept()
            return
        super().mouseReleaseEvent(event)


class TurboHelpSourceEditor(QPlainTextEdit):
    """Drop-in QPlainTextEdit with dynamic line numbers and a right minimap."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('turbo_help_source_editor')
        self.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.line_number_area = TurboHelpLineNumberArea(self)
        self.minimap = TurboHelpMiniMap(self)
        self._last_gutter_width = None
        self.blockCountChanged.connect(self._update_viewport_margins)
        self.updateRequest.connect(self._update_gutter)
        self.cursorPositionChanged.connect(self.line_number_area.update)
        self._update_viewport_margins()
        self._position_decorations()

    def setFont(self, font):
        super().setFont(font)
        if hasattr(self, 'line_number_area'):
            self._update_viewport_margins()
            self.line_number_area.update()
            if hasattr(self, 'minimap'):
                self.minimap.update()

    def line_number_area_width(self):
        digits = max(3, len(str(max(1, self.blockCount()))))
        return 12 + self.fontMetrics().horizontalAdvance('9') * digits

    def _update_viewport_margins(self, _count=0):
        width = self.line_number_area_width()
        if width != self._last_gutter_width:
            self._last_gutter_width = width
            self.setViewportMargins(width, 0, self.minimap.WIDTH, 0)
            self._position_decorations()

    def _update_gutter(self, rect, dy):
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self._update_viewport_margins()

    def _position_decorations(self):
        if not hasattr(self, 'line_number_area') or not hasattr(self, 'minimap'):
            return
        contents = self.contentsRect()
        self.line_number_area.setGeometry(QRect(
            contents.left(), contents.top(), self.line_number_area_width(), contents.height()))
        self.minimap.setGeometry(QRect(
            self.viewport().geometry().right() + 1, contents.top(),
            self.minimap.WIDTH, contents.height()))
        self.line_number_area.raise_()
        self.minimap.raise_()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._position_decorations()

    def paint_line_numbers(self, event):
        painter = QPainter(self.line_number_area)
        try:
            painter.fillRect(event.rect(), QColor('#21313e'))
            painter.setPen(QColor('#48616d'))
            x = self.line_number_area.width() - 1
            painter.drawLine(x, event.rect().top(), x, event.rect().bottom())
            block = self.firstVisibleBlock()
            number = block.blockNumber()
            top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
            active = self.textCursor().blockNumber()
            while block.isValid() and top <= event.rect().bottom():
                block_height = int(self.blockBoundingRect(block).height())
                if block.isVisible() and top + block_height >= event.rect().top():
                    if number == active:
                        painter.fillRect(0, top, x, block_height, QColor('#314b5f'))
                    painter.setPen(QColor('#ffffff' if number == active else '#9cb7c4'))
                    painter.drawText(0, top, x - 5, block_height,
                                     Qt.AlignRight | Qt.AlignVCenter, str(number + 1))
                top += block_height
                block = block.next()
                number += 1
        finally:
            painter.end()
