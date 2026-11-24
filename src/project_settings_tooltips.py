# ---------------------------------------------------------------------------
# Stage 684: tooltips in the project-settings dock are width-limited to the
# visible right settings pane, with pixel-based wrapping (including long words).
# This module does not import Qt until the GUI installs the event filter.
# ---------------------------------------------------------------------------
from __future__ import annotations

import html
import re
from typing import Callable

_RICH_START = re.compile(r"^\s*<(?:qt|html|body|p|div|table|span|b|i|font|ul|ol)\b", re.I)


def wrap_tooltip_lines(text: str, content_width: int,
                       text_width: Callable[[str], int]) -> list[str]:
    """Wrap at word boundaries, or inside words that cannot otherwise fit.

    The caller supplies Qt's font metrics. Existing newlines are retained.
    This is independent of widget size and can be exercised without PyQt5.
    """
    limit = max(1, int(content_width))
    lines: list[str] = []

    def append_word(word: str, line: str) -> str:
        candidate = (line + " " + word) if line else word
        if text_width(candidate) <= limit:
            return candidate
        if line:
            lines.append(line)
            line = ""
        # Break an indivisible string (long file path, URL, symbol, etc.).
        while word and text_width(word) > limit:
            low, high = 1, len(word)
            while low < high:
                middle = (low + high + 1) // 2
                if text_width(word[:middle]) <= limit:
                    low = middle
                else:
                    high = middle - 1
            take = max(1, low)
            lines.append(word[:take])
            word = word[take:]
        return word

    for paragraph in str(text).replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        if not paragraph.strip():
            lines.append("")
            continue
        line = ""
        for word in paragraph.split():
            line = append_word(word, line)
        if line:
            lines.append(line)
    return lines


def tooltip_html(text: str, content_width: int,
                 text_width: Callable[[str], int]) -> str:
    """Generate Qt-compatible rich text with explicit line breaks.

    Qt tooltip layout has additional padding; callers must subtract it from
    the right pane's visible width before passing content_width.
    """
    lines = wrap_tooltip_lines(text, content_width, text_width)
    return "<qt>" + "<br/>".join(html.escape(line) for line in lines) + "</qt>"


def install_project_settings_tooltip_limiter(dock, panel, scroll):
    """Install one scoped QApplication event filter; no other dock is affected.

    The selected Windows PE32/PE64 or C64 page owns the actual right pane.
    Width is evaluated at every hover rather than cached, so splitter and dock
    resizing immediately change the wrapping.
    """
    from PyQt5.QtCore import QObject, QEvent, QPoint, QRect, Qt
    from PyQt5.QtGui import QFontMetrics, QTextDocument
    from PyQt5.QtWidgets import (
        QAbstractItemView, QApplication, QToolTip, QWidget,
    )

    class _ProjectSettingsToolTipLimiter(QObject):
        def __init__(self):
            super().__init__(dock)
            self._dock = dock
            self._panel = panel
            self._scroll = scroll

        def _inside_dock(self, widget):
            current = widget
            while current is not None:
                if current is self._dock:
                    return True
                current = current.parentWidget()
            return False

        def _right_stack(self):
            # The active architecture/profile determines the width, not
            # the total dock width (which also contains the left tree).
            tabs = self._panel.tabs
            tab = tabs.currentWidget()
            if tab is self._panel.windows_tab:
                page = self._panel.windows_arch_tabs.currentWidget()
            elif tab is self._panel.c64_tab:
                page = self._panel.c64_arch_tabs.currentWidget()
            else:
                return None
            return getattr(page, "stack", None)

        def _visible_right_width(self):
            stack = self._right_stack()
            if stack is None:
                return 0
            width = int(stack.width())
            if width <= 0:
                return 0
            # The outer project-settings QScrollArea may clip its large
            # minimum-width settings panel, especially in narrow dock layouts.
            # Restrict the tooltip to the *visible* part of the right pane.
            viewport = self._scroll.viewport()
            pane_rect = QRect(stack.mapToGlobal(QPoint(0, 0)), stack.size())
            view_rect = QRect(viewport.mapToGlobal(QPoint(0, 0)), viewport.size())
            return max(0, pane_rect.intersected(view_rect).width())

        @staticmethod
        def _tooltip_for_widget(widget, event):
            # QTreeWidget/QTableWidget item tooltips live on the model, not
            # necessarily on the viewport's QWidget.toolTip property.
            view = widget.parentWidget()
            if isinstance(view, QAbstractItemView) and view.viewport() is widget:
                index = view.indexAt(event.pos())
                if index.isValid():
                    tip = index.data(Qt.ToolTipRole)
                    if tip:
                        return str(tip)
            return str(widget.toolTip() or "")

        def eventFilter(self, watched, event):
            if event.type() != QEvent.ToolTip or not isinstance(watched, QWidget):
                return False
            if not self._inside_dock(watched):
                return False
            original = self._tooltip_for_widget(watched, event)
            if not original:
                return False  # No custom behavior if Qt has no tooltip.
            pane_width = self._visible_right_width()
            if pane_width <= 0:
                return False

            # Reserve sufficient space for Qt tooltip frame, text margins,
            # and platform-dependent padding. Avoid extra global styles.
            content_width = max(1, pane_width - 36)
            metrics = QFontMetrics(QToolTip.font())
            measure = metrics.horizontalAdvance
            if _RICH_START.match(original):
                # Convert pre-existing rich text only for wrapping; it still
                # displays all text, including HTML-escaped special chars.
                document = QTextDocument()
                document.setHtml(original)
                original = document.toPlainText()
            formatted = tooltip_html(original, content_width, measure)
            QToolTip.showText(event.globalPos(), formatted, watched)
            event.accept()
            return True

    limiter = _ProjectSettingsToolTipLimiter()
    app = QApplication.instance()
    if app is not None:
        app.installEventFilter(limiter)
    # Keep a Python reference until the dock is destroyed.
    dock._project_settings_tooltip_limiter = limiter
    return limiter
