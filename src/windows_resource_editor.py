# -*- coding: utf-8 -*-
"""Qt5 editor frontend for the internal Windows resource compiler.

Stage 153 keeps the Stage-152 workspace/dialog integration and additionally
adds a synchronized source-editor line-number gutter. File operations are exposed
through the application's main menu; the local toolbar only contains compiler
operations.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from PyQt5.QtCore import Qt, QRect, QSize, pyqtSignal
from PyQt5.QtGui import (
    QColor, QFont, QFontDatabase, QIcon, QPainter, QPalette, QPixmap,
    QSyntaxHighlighter, QTextCharFormat, QTextFormat,
)
from PyQt5.QtWidgets import (
    QAction, QApplication, QComboBox, QFileDialog, QHBoxLayout, QHeaderView, QLabel, QMessageBox,
    QPlainTextEdit, QPushButton, QSizePolicy, QSplitter, QStyle, QTableWidget, QTextEdit,
    QTableWidgetItem, QTabWidget, QToolBar, QTreeWidget, QTreeWidgetItem,
    QVBoxLayout, QWidget,
)

from windows_resource import (
    RT_STRING, ResourceCompilerError, ResourceEntry, compile_rc, describe_resource_id,
    read_res, save_res, save_resource_coff,
)


RESOURCE_PLACEHOLDER = 'STRINGTABLE BEGIN IDS_HELLO,   "Moin" IDS_GOODBYE, "Tschüß" END'

# Stage 154: values written to IMAGE_RESOURCE_DATA_ENTRY.CodePage.
RESOURCE_CODEPAGES = (
    ("Unicode", 1200),
    ("UTF-8", 65001),
    ("ASCII", 20127),
)


def resource_dialog_stylesheet(dark_mode: bool) -> str:
    """Return a complete stylesheet for modal resource-editor dialogs.

    QFileDialog is deliberately used in Qt/non-native mode by Stage 152 so the
    application, not the current Windows shell theme, owns every surface color.
    """
    if dark_mode:
        return r"""
QDialog, QFileDialog, QMessageBox {
    background-color: #202630;
    color: #ffffff;
}
QDialog QLabel, QFileDialog QLabel, QMessageBox QLabel,
QCheckBox, QRadioButton, QGroupBox {
    color: #ffffff;
    background-color: transparent;
}
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QTextEdit, QPlainTextEdit,
QListView, QTreeView, QTableView {
    color: #f4f4f4;
    background-color: #171c24;
    alternate-background-color: #202732;
    selection-background-color: #315a82;
    selection-color: #ffffff;
    border: 1px solid #536172;
}
QComboBox QAbstractItemView {
    color: #f4f4f4;
    background-color: #202630;
    selection-background-color: #315a82;
    selection-color: #ffffff;
    border: 1px solid #536172;
}
QHeaderView::section {
    color: #ffffff;
    background-color: #303844;
    border: 0;
    border-right: 1px solid #536172;
    border-bottom: 1px solid #536172;
    padding: 4px 6px;
    font-weight: bold;
}
QPushButton, QToolButton {
    color: #ffffff;
    background-color: #343e4d;
    border: 1px solid #596779;
    border-radius: 3px;
    padding: 5px 9px;
}
QPushButton:hover, QToolButton:hover {
    background-color: #414d5f;
    border-color: #718198;
}
QPushButton:pressed, QToolButton:pressed {
    background-color: #27313e;
}
QPushButton:disabled, QToolButton:disabled {
    color: #858c96;
    background-color: #272e38;
    border-color: #414b58;
}
QDialogButtonBox { background-color: transparent; }
QMenu {
    color: #ffffff;
    background-color: #202630;
    border: 1px solid #596779;
}
QMenu::item:selected { background-color: #315a82; }
QScrollBar:vertical, QScrollBar:horizontal {
    background: #1a2029;
    border: 0;
}
QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
    background: #536172;
    min-height: 20px;
    min-width: 20px;
}
QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover {
    background: #6c7b8e;
}
"""
    return r"""
QDialog, QFileDialog, QMessageBox { background-color: #f0f0f0; color: #000000; }
QLineEdit, QComboBox, QTextEdit, QPlainTextEdit, QListView, QTreeView, QTableView {
    color: #000000; background-color: #ffffff; selection-background-color: #cce8ff;
    selection-color: #000000; border: 1px solid #a0a0a0;
}
QHeaderView::section { background-color: #e2e2e2; color: #111111; padding: 4px 6px; }
QPushButton, QToolButton {
    color: #000000; background-color: #f5f5f5; border: 1px solid #9b9b9b;
    border-radius: 3px; padding: 5px 9px;
}
QPushButton:hover, QToolButton:hover { background-color: #e4f1fb; border-color: #5b9bd5; }
"""


def apply_resource_dialog_theme(dialog, dark_mode: bool):
    """Apply an explicit palette and stylesheet to a modal resource dialog."""
    dark_mode = bool(dark_mode)
    app = QApplication.instance()
    base = app.palette() if app is not None else dialog.palette()
    palette = QPalette(base)
    if dark_mode:
        palette.setColor(QPalette.Window, QColor('#202630'))
        palette.setColor(QPalette.WindowText, QColor('#ffffff'))
        palette.setColor(QPalette.Base, QColor('#171c24'))
        palette.setColor(QPalette.AlternateBase, QColor('#202732'))
        palette.setColor(QPalette.Text, QColor('#f4f4f4'))
        palette.setColor(QPalette.Button, QColor('#343e4d'))
        palette.setColor(QPalette.ButtonText, QColor('#ffffff'))
        palette.setColor(QPalette.Highlight, QColor('#315a82'))
        palette.setColor(QPalette.HighlightedText, QColor('#ffffff'))
    else:
        palette.setColor(QPalette.Window, QColor('#f0f0f0'))
        palette.setColor(QPalette.WindowText, QColor('#000000'))
        palette.setColor(QPalette.Base, QColor('#ffffff'))
        palette.setColor(QPalette.Text, QColor('#000000'))
        palette.setColor(QPalette.Button, QColor('#f5f5f5'))
        palette.setColor(QPalette.ButtonText, QColor('#000000'))
    dialog.setAttribute(Qt.WA_StyledBackground, True)
    dialog.setAutoFillBackground(True)
    dialog.setPalette(palette)
    dialog.setStyleSheet(resource_dialog_stylesheet(dark_mode))
    for child in dialog.findChildren(QWidget):
        child.setPalette(palette)
    return dialog


class ResourceRcHighlighter(QSyntaxHighlighter):
    """Small RC highlighter with C/C++ style comments."""

    KEYWORDS = {
        "ACCELERATORS", "ALT", "ASCII", "BEGIN", "BITMAP", "BLOCK",
        "CAPTION", "CHARACTERISTICS", "CHECKBOX", "CLASS", "COMBOBOX",
        "CONTROL", "CTEXT", "CURSOR", "DEFPUSHBUTTON", "DIALOG",
        "DIALOGEX", "EDITTEXT", "END", "EXSTYLE", "FILEFLAGS",
        "FILEFLAGSMASK", "FILEOS", "FILESUBTYPE", "FILETYPE",
        "FILEVERSION", "FIXED", "FONT", "GROUPBOX", "HTML", "ICON",
        "IMPURE", "LANGUAGE", "LISTBOX", "LOADONCALL", "LTEXT",
        "MANIFEST", "MENU", "MENUEX", "MENUITEM", "MESSAGETABLE",
        "MOVEABLE", "NOINVERT", "POPUP", "PRELOAD", "PRODUCTVERSION",
        "PURE", "PUSHBUTTON", "RADIOBUTTON", "RCDATA", "RTEXT", "SHIFT",
        "STRINGTABLE", "STYLE", "TOOLBAR", "VALUE", "VERSION",
        "VERSIONINFO", "VIRTKEY",
    }

    def __init__(self, document):
        super().__init__(document)
        self._dark = True
        self._keyword_re = re.compile(
            r"\b(" + "|".join(sorted(self.KEYWORDS, key=len, reverse=True)) + r")\b",
            re.IGNORECASE,
        )
        self._number_re = re.compile(r"(?<![A-Za-z_])(?:0[xX][0-9A-Fa-f]+|\d+)(?![A-Za-z_])")
        self._string_re = re.compile(r'"(?:\\.|""|[^"\\])*"')
        self._line_comment_re = re.compile(r"//.*$")
        self._block_start = re.compile(r"/\*")
        self._block_end = re.compile(r"\*/")
        self.set_dark_mode(True)

    @staticmethod
    def _fmt(color: str, *, bold: bool = False, italic: bool = False) -> QTextCharFormat:
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))
        if bold:
            fmt.setFontWeight(QFont.Bold)
        fmt.setFontItalic(bool(italic))
        return fmt

    def set_dark_mode(self, enabled: bool) -> None:
        self._dark = bool(enabled)
        # Stage 154: yellow in dark mode, dark blue in light mode.
        if self._dark:
            self.keyword_format = self._fmt("#FFD84D", bold=True)
        else:
            self.keyword_format = self._fmt("#003A8C", bold=True)
        self.comment_format = self._fmt("#6A9955" if self._dark else "#2E7D32", italic=True)
        self.number_format = self._fmt("#7FDBFF" if self._dark else "#005A9C")
        self.string_format = self._fmt("#FFB86C" if self._dark else "#A31515")
        self.rehighlight()

    def highlightBlock(self, text: str) -> None:
        # Base lexical items first; comments are painted last and therefore win.
        for match in self._keyword_re.finditer(text):
            self.setFormat(match.start(), match.end() - match.start(), self.keyword_format)
        for match in self._number_re.finditer(text):
            self.setFormat(match.start(), match.end() - match.start(), self.number_format)
        for match in self._string_re.finditer(text):
            self.setFormat(match.start(), match.end() - match.start(), self.string_format)
        for match in self._line_comment_re.finditer(text):
            self.setFormat(match.start(), match.end() - match.start(), self.comment_format)

        self.setCurrentBlockState(0)
        start = 0 if self.previousBlockState() == 1 else self._block_start.search(text)
        while start is not None:
            start_pos = start if isinstance(start, int) else start.start()
            end_match = self._block_end.search(text, start_pos + (0 if isinstance(start, int) else 2))
            if end_match is None:
                self.setCurrentBlockState(1)
                self.setFormat(start_pos, len(text) - start_pos, self.comment_format)
                break
            end_pos = end_match.end()
            self.setFormat(start_pos, end_pos - start_pos, self.comment_format)
            start = self._block_start.search(text, end_pos)


class ResourceLineNumberArea(QWidget):
    """Left gutter used by :class:`ResourceCodeEditor`."""

    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor
        self.setObjectName("resource_line_number_area")

    def sizeHint(self) -> QSize:
        return QSize(self.editor.line_number_area_width(), 0)

    def paintEvent(self, event) -> None:
        self.editor.line_number_area_paint_event(event)


class ResourceCodeEditor(QPlainTextEdit):
    """QPlainTextEdit with a scroll-synchronized line-number gutter."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._dark_mode = True
        self.line_number_area = ResourceLineNumberArea(self)
        self.blockCountChanged.connect(self._update_line_number_area_width)
        self.updateRequest.connect(self._update_line_number_area)
        self.cursorPositionChanged.connect(self.line_number_area.update)
        self.cursorPositionChanged.connect(self._highlight_current_line)
        self._update_line_number_area_width(0)
        self._highlight_current_line()

    def setFont(self, font) -> None:
        super().setFont(font)
        if hasattr(self, "line_number_area"):
            self._update_line_number_area_width(0)
            self.line_number_area.update()

    def line_number_area_width(self) -> int:
        digits = max(2, len(str(max(1, self.blockCount()))))
        return 12 + self.fontMetrics().horizontalAdvance("9") * digits

    def _update_line_number_area_width(self, _block_count: int) -> None:
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def _update_line_number_area(self, rect, dy: int) -> None:
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self._update_line_number_area_width(0)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(
            QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height())
        )

    def set_dark_mode(self, enabled: bool) -> None:
        self._dark_mode = bool(enabled)
        self.line_number_area.update()
        self._highlight_current_line()

    def _highlight_current_line(self) -> None:
        selection = QTextEdit.ExtraSelection()
        selection.cursor = self.textCursor()
        selection.cursor.clearSelection()
        if self._dark_mode:
            selection.format.setBackground(QColor("#303030"))
            selection.format.setForeground(QColor("#FFFFFF"))
        else:
            selection.format.setBackground(QColor("#FFF2A8"))
            selection.format.setForeground(QColor("#000000"))
        selection.format.setProperty(QTextFormat.FullWidthSelection, True)
        self.setExtraSelections([selection])

    def line_number_area_paint_event(self, event) -> None:
        painter = QPainter(self.line_number_area)
        try:
            if self._dark_mode:
                background = QColor("#252526")
                foreground = QColor("#9A9A9A")
                current = QColor("#FFFFFF")
                current_background = QColor("#303030")
                separator = QColor("#3A3A3A")
            else:
                background = QColor("#F0F0F0")
                foreground = QColor("#707070")
                current = QColor("#000000")
                current_background = QColor("#FFF2A8")
                separator = QColor("#C8C8C8")

            painter.fillRect(event.rect(), background)
            painter.setPen(separator)
            painter.drawLine(
                self.line_number_area.width() - 1,
                event.rect().top(),
                self.line_number_area.width() - 1,
                event.rect().bottom(),
            )

            block = self.firstVisibleBlock()
            block_number = block.blockNumber()
            top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
            bottom = top + int(self.blockBoundingRect(block).height())
            current_block = self.textCursor().blockNumber()

            while block.isValid() and top <= event.rect().bottom():
                if block.isVisible() and bottom >= event.rect().top():
                    if block_number == current_block:
                        painter.fillRect(0, top, self.line_number_area.width(), self.fontMetrics().height(), current_background)
                    painter.setPen(current if block_number == current_block else foreground)
                    painter.drawText(
                        0,
                        top,
                        self.line_number_area.width() - 6,
                        self.fontMetrics().height(),
                        Qt.AlignRight | Qt.AlignVCenter,
                        str(block_number + 1),
                    )
                block = block.next()
                block_number += 1
                top = bottom
                if not block.isValid():
                    break
                bottom = top + int(self.blockBoundingRect(block).height())
        finally:
            painter.end()


class ResourceMiniMap(QWidget):
    """Compact source overview synchronized with a QPlainTextEdit."""

    WIDTH = 88
    MAX_LINE_LENGTH = 180

    def __init__(self, editor: QPlainTextEdit, parent=None):
        super().__init__(parent)
        self.editor = editor
        self._line_lengths: list[int] = []
        self._dragging = False
        self.setObjectName("resource_source_minimap")
        self.setFixedWidth(self.WIDTH)
        self.setMinimumHeight(80)
        self.setCursor(Qt.PointingHandCursor)
        self.setMouseTracking(True)
        self.editor.textChanged.connect(self._rebuild)
        self.editor.blockCountChanged.connect(lambda _count: self._rebuild())
        bar = self.editor.verticalScrollBar()
        bar.valueChanged.connect(self.update)
        bar.rangeChanged.connect(lambda _a, _b: self.update())
        self._rebuild()

    def sizeHint(self) -> QSize:
        return QSize(self.WIDTH, 180)

    def _rebuild(self) -> None:
        result = []
        block = self.editor.document().firstBlock()
        while block.isValid():
            result.append(min(self.MAX_LINE_LENGTH, len(block.text().expandtabs(4))))
            block = block.next()
        self._line_lengths = result
        self.update()

    def _viewport_rect(self) -> QRect:
        bar = self.editor.verticalScrollBar()
        height = max(1, self.height())
        if bar.maximum() <= bar.minimum():
            return QRect(0, 0, self.width(), height)
        page = max(1, bar.pageStep())
        total = max(1, bar.maximum() - bar.minimum() + page)
        thumb_h = max(18, int(height * page / total))
        thumb_h = min(height, thumb_h)
        available = max(0, height - thumb_h)
        top = QStyle.sliderPositionFromValue(
            bar.minimum(), bar.maximum(), bar.value(), available, False
        )
        return QRect(0, int(top), max(1, self.width() - 1), thumb_h)

    def _set_scroll_from_y(self, y: int) -> None:
        bar = self.editor.verticalScrollBar()
        rect = self._viewport_rect()
        available = max(0, self.height() - rect.height())
        if available <= 0 or bar.maximum() <= bar.minimum():
            bar.setValue(bar.minimum())
            return
        top = max(0, min(available, int(y - rect.height() / 2)))
        value = QStyle.sliderValueFromPosition(
            bar.minimum(), bar.maximum(), top, available, False
        )
        bar.setValue(value)

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        try:
            palette = self.editor.palette()
            background = palette.base().color()
            foreground = QColor(palette.text().color())
            highlight = QColor(palette.highlight().color())
            painter.fillRect(self.rect(), background)

            foreground.setAlpha(145)
            painter.setPen(foreground)
            count = max(1, len(self._line_lengths))
            available_w = max(1, self.width() - 10)
            height = max(1, self.height())
            for index, length in enumerate(self._line_lengths):
                y = int(index * (height - 1) / max(1, count - 1))
                width = int(available_w * length / self.MAX_LINE_LENGTH)
                if length:
                    width = max(2, width)
                painter.drawLine(4, y, 4 + width, y)

            viewport = self._viewport_rect()
            fill = QColor(highlight)
            fill.setAlpha(55)
            painter.fillRect(viewport, fill)
            border = QColor(highlight)
            border.setAlpha(220)
            painter.setPen(border)
            painter.drawRect(viewport.adjusted(0, 0, -1, -1))
        finally:
            painter.end()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self._dragging = True
            self._set_scroll_from_y(event.pos().y())
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if self._dragging and event.buttons() & Qt.LeftButton:
            self._set_scroll_from_y(event.pos().y())
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self._dragging = False
            event.accept()
            return
        super().mouseReleaseEvent(event)


class WindowsResourceEditorWidget(QWidget):
    """Dock-friendly RC/RES editor and compiler UI."""

    file_changed = pyqtSignal(str)
    status_message = pyqtSignal(str)

    def __init__(self, parent=None, language_codes=None):
        super().__init__(parent)
        self.current_path: Optional[Path] = None
        self.language_codes = []
        for item in (language_codes or []):
            if len(item) >= 4:
                code, title, flag_path, lang_id = item[:4]
                self.language_codes.append((str(code), str(title), str(flag_path), int(lang_id) & 0xFFFF))
        if not self.language_codes:
            self.language_codes = [
                ("ENU", "English (USA)", "enu", 0x0409),
                ("DEU", "German", "deu", 0x0407),
            ]
        self.current_target = "pe32"
        self.entries: list[ResourceEntry] = []
        self._loading = False
        self._dirty = False
        self._dark_mode = True
        self._build_ui()
        self.set_dark_mode(True)

    @staticmethod
    def _editor_font() -> QFont:
        families = set(QFontDatabase().families())
        selected = next(
            (name for name in ("Consolas", "Courier New", "Courier") if name in families),
            "Courier",
        )
        font = QFont(selected, 10)
        font.setStyleHint(QFont.Monospace)
        font.setFixedPitch(True)
        return font

    def _language_info(self, lang_id: int):
        lang_id = int(lang_id) & 0xFFFF
        for item in self.language_codes:
            if item[3] == lang_id:
                return item
        return ("---", f"Unbekannt 0x{lang_id:04X}", "", lang_id)

    @staticmethod
    def _flag_icon(flag_path: str) -> QIcon:
        if not flag_path:
            return QIcon()
        return QIcon(f":/flags/{flag_path}.png")

    def _set_source_text_preserve_cursor(self, text: str) -> None:
        cursor = self.source_edit.textCursor()
        position = cursor.position()
        self._loading = True
        try:
            self.source_edit.setPlainText(text)
            cursor = self.source_edit.textCursor()
            cursor.setPosition(min(position, len(text)))
            self.source_edit.setTextCursor(cursor)
        finally:
            self._loading = False
        self._dirty = True

    def _write_rc_language(self, lang_id: int) -> None:
        text = self.source_edit.toPlainText()
        primary = int(lang_id) & 0x03FF
        sublang = (int(lang_id) >> 10) & 0x003F
        statement = f"LANGUAGE 0x{primary:04X}, 0x{sublang:02X}"
        pattern = re.compile(r"(?mi)^[ \t]*LANGUAGE\b[^\r\n]*$")
        if pattern.search(text):
            text = pattern.sub(statement, text, count=1)
        else:
            # Place the language before the first resource declaration. This is
            # standard RC syntax and therefore also works with external rc.exe.
            text = statement + "\n\n" + text.lstrip("\ufeff")
        self._set_source_text_preserve_cursor(text)

    def _write_rc_codepage(self, codepage: int) -> None:
        text = self.source_edit.toPlainText()
        statement = f"#pragma code_page({int(codepage)})"
        pattern = re.compile(r"(?mi)^[ \t]*#\s*pragma\s+code_page\s*\([^\r\n)]*\)[ \t]*$")
        if pattern.search(text):
            text = pattern.sub(statement, text, count=1)
        else:
            text = statement + "\n" + text.lstrip("\ufeff")
        self._set_source_text_preserve_cursor(text)

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(3, 3, 3, 3)
        root.setSpacing(3)

        # File actions intentionally live in the application's main menu.
        self.toolbar = QToolBar("Resourcen-Editor", self)
        self.toolbar.setObjectName("resource_editor_toolbar")
        self.toolbar.setMovable(False)
        self.toolbar.setFloatable(False)
        root.addWidget(self.toolbar)

        def add_action(text, slot, tip=""):
            action = QAction(text, self)
            if tip:
                action.setToolTip(tip)
                action.setStatusTip(tip)
            action.triggered.connect(slot)
            self.toolbar.addAction(action)
            return action

        self.act_compile = add_action("RC → RES", self.compile_to_res, "RC-Datei als Microsoft RES erzeugen")
        self.act_coff32 = add_action("COFF32", lambda: self.compile_to_coff("x86"), "PE32-Resource-COFF erzeugen")
        self.act_coff64 = add_action("COFF64", lambda: self.compile_to_coff("x64"), "PE32+-Resource-COFF erzeugen")
        self.toolbar.addSeparator()
        self.act_refresh = add_action("Aktualisieren", self.refresh_resources, "Ressourcen neu einlesen")

        info = QHBoxLayout()
        info.setSpacing(6)
        info.addWidget(QLabel("Datei:"))
        self.file_label = QLabel("(keine)")
        self.file_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        info.addWidget(self.file_label, 1)
        self.target_label = QLabel("Ziel: Windows PE32")
        info.addWidget(self.target_label)
        root.addLayout(info)

        splitter = QSplitter(Qt.Horizontal, self)
        splitter.setChildrenCollapsible(False)
        root.addWidget(splitter, 1)

        left = QWidget(splitter)
        left.setMinimumWidth(180)
        left_lay = QVBoxLayout(left)
        left_lay.setContentsMargins(0, 0, 0, 0)
        left_lay.setSpacing(2)
        left_lay.addWidget(QLabel("Ressourcen"))
        self.resource_tree = QTreeWidget(left)
        self.resource_tree.setObjectName("resource_tree")
        self.resource_tree.setHeaderLabels(["Typ / Name", "Sprache", "Größe"])
        self.resource_tree.setAlternatingRowColors(True)
        self.resource_tree.setRootIsDecorated(True)
        self.resource_tree.setUniformRowHeights(True)
        self.resource_tree.header().setStretchLastSection(False)
        self.resource_tree.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self.resource_tree.header().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.resource_tree.header().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.resource_tree.itemSelectionChanged.connect(self._resource_selected)
        left_lay.addWidget(self.resource_tree, 1)
        splitter.addWidget(left)

        self.tabs = QTabWidget(splitter)
        self.tabs.setObjectName("resource_editor_tabs")
        splitter.addWidget(self.tabs)

        source_page = QWidget(self.tabs)
        source_layout = QHBoxLayout(source_page)
        source_layout.setContentsMargins(0, 0, 0, 0)
        source_layout.setSpacing(0)
        self.source_edit = ResourceCodeEditor(source_page)
        self.source_edit.setObjectName("resource_source_editor")
        self.source_edit.setFont(self._editor_font())
        self.source_edit.setPlaceholderText(RESOURCE_PLACEHOLDER)
        self.source_edit.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.source_edit.setTabStopWidth(
            max(16, self.source_edit.fontMetrics().horizontalAdvance(" ") * 4)
        )
        self.source_edit.textChanged.connect(self._source_changed)
        self.source_highlighter = ResourceRcHighlighter(self.source_edit.document())
        self.source_minimap = ResourceMiniMap(self.source_edit, source_page)
        source_layout.addWidget(self.source_edit, 1)
        source_layout.addWidget(self.source_minimap)
        self.tabs.addTab(source_page, "RC-Quelltext")

        self.properties = QTableWidget(0, 2, self.tabs)
        self.properties.setObjectName("resource_properties_grid")
        self.properties.setHorizontalHeaderLabels(["Eigenschaft", "Wert"])
        self.properties.horizontalHeader().setStretchLastSection(True)
        self.properties.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.properties.verticalHeader().setVisible(False)
        self.properties.setAlternatingRowColors(True)
        self.properties.setEditTriggers(QTableWidget.NoEditTriggers)
        self.properties.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabs.addTab(self.properties, "Eigenschaften")

        self.hex_edit = QPlainTextEdit(self.tabs)
        self.hex_edit.setObjectName("resource_hex_editor")
        self.hex_edit.setReadOnly(True)
        self.hex_edit.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.hex_edit.setFont(self._editor_font())
        self.tabs.addTab(self.hex_edit, "Hex")

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 4)
        splitter.setSizes([260, 900])

        bottom = QHBoxLayout()
        self.status = QLabel("Bereit")
        bottom.addWidget(self.status, 1)
        compile_button = QPushButton("Ressourcen neu einlesen")
        compile_button.setObjectName("resource_refresh_button")
        compile_button.clicked.connect(self.refresh_resources)
        bottom.addWidget(compile_button)
        root.addLayout(bottom)

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def set_target(self, target: str):
        self.current_target = "pe64" if str(target).lower() in {"pe64", "x64", "amd64", "pe32+"} else "pe32"
        self.target_label.setText("Ziel: Windows PE32+" if self.current_target == "pe64" else "Ziel: Windows PE32")

    def set_dark_mode(self, enabled: bool):
        self._dark_mode = bool(enabled)
        self.setProperty("darkMode", self._dark_mode)
        self.source_highlighter.set_dark_mode(self._dark_mode)
        self.source_edit.set_dark_mode(self._dark_mode)
        if self._dark_mode:
            self.setStyleSheet(
                """
                WindowsResourceEditorWidget { background:#202020; color:#F2F2F2; }
                QToolBar#resource_editor_toolbar { background:#252525; border:1px solid #353535; spacing:3px; }
                QToolBar#resource_editor_toolbar QToolButton { color:#F5F5F5; background:#303030; border:1px solid #484848; padding:4px 8px; }
                QToolBar#resource_editor_toolbar QToolButton:hover { background:#3A3A3A; border-color:#6A6A6A; }
                QTreeWidget#resource_tree, QTableWidget#resource_properties_grid,
                QPlainTextEdit#resource_source_editor, QPlainTextEdit#resource_hex_editor {
                    background:#1E1E1E; color:#F2F2F2; alternate-background-color:#252525;
                    selection-background-color:#264F78; selection-color:#FFFFFF;
                    border:1px solid #3A3A3A;
                }
                QComboBox#resource_language_combo, QComboBox#resource_codepage_combo {
                    background:#252525; color:#F2F2F2; border:1px solid #505050;
                    padding:3px 6px; min-height:20px;
                }
                QComboBox#resource_language_combo QAbstractItemView,
                QComboBox#resource_codepage_combo QAbstractItemView {
                    background:#252525; color:#F2F2F2; selection-background-color:#264F78;
                    selection-color:#FFFFFF; border:1px solid #505050;
                }
                QHeaderView::section {
                    background:#303030; color:#FFFFFF; border:0px;
                    border-right:1px solid #4A4A4A; border-bottom:1px solid #4A4A4A;
                    padding:5px 7px; font-weight:bold;
                }
                QTabWidget::pane { border:1px solid #3A3A3A; background:#202020; }
                QTabBar::tab { background:#292929; color:#EAEAEA; border:1px solid #3A3A3A; padding:6px 10px; }
                QTabBar::tab:selected { background:#353535; color:#FFFFFF; }
                QPushButton { background:#303030; color:#FFFFFF; border:1px solid #505050; padding:5px 9px; }
                QPushButton:hover { background:#3B3B3B; }
                QLabel { color:#F0F0F0; }
                QSplitter::handle { background:#3A3A3A; }
                QWidget#resource_source_minimap { border-left:1px solid #3A3A3A; }
                """
            )
        else:
            self.setStyleSheet(
                """
                QPlainTextEdit#resource_source_editor {
                    background:#FFFFFF; color:#000000; selection-background-color:#CCE8FF;
                    selection-color:#000000;
                }
                QComboBox#resource_language_combo, QComboBox#resource_codepage_combo {
                    background:#FFFFFF; color:#111111; border:1px solid #A8A8A8;
                    padding:3px 6px; min-height:20px;
                }
                QComboBox#resource_language_combo QAbstractItemView,
                QComboBox#resource_codepage_combo QAbstractItemView {
                    background:#FFFFFF; color:#111111; selection-background-color:#CCE8FF;
                    selection-color:#000000; border:1px solid #A8A8A8;
                }
                QHeaderView::section {
                    background:#E2E2E2; color:#111111; border:0px;
                    border-right:1px solid #B8B8B8; border-bottom:1px solid #B8B8B8;
                    padding:5px 7px; font-weight:bold;
                }
                """
            )
        self.source_minimap.update()
        self.update()

    def _set_status(self, text: str):
        self.status.setText(text)
        self.status_message.emit(text)

    def _source_changed(self):
        if self._loading:
            return
        # New, not-yet-saved projects are dirty as well.
        if self.current_path is None or self.current_path.suffix.lower() == ".rc":
            self._dirty = True

    def _dialog_host(self):
        host = self.window()
        return host if host is not None else self

    def _message_box(
        self, icon, title: str, text: str, *, buttons=QMessageBox.Ok,
        default_button=QMessageBox.NoButton,
    ) -> int:
        # Reuse the MainWindow's established theme path when available.
        host = self._dialog_host()
        creator = getattr(host, "_create_message_box", None)
        if callable(creator):
            box = creator(
                icon, title, text, buttons=buttons, default_button=default_button
            )
        else:
            box = QMessageBox(self)
            box.setWindowTitle(title)
            box.setIcon(icon)
            box.setText(text)
            box.setStandardButtons(buttons)
            if default_button != QMessageBox.NoButton:
                box.setDefaultButton(default_button)
            apply_resource_dialog_theme(box, self._dark_mode)
        return box.exec_()

    def _critical(self, title: str, text: str) -> int:
        return self._message_box(QMessageBox.Critical, title, text)

    def _warning(self, title: str, text: str) -> int:
        return self._message_box(QMessageBox.Warning, title, text)

    def _question(self, title: str, text: str, buttons, default_button) -> int:
        return self._message_box(
            QMessageBox.Question, title, text, buttons=buttons,
            default_button=default_button,
        )

    def _file_dialog(
        self, title: str, initial: str, name_filter: str, *, save: bool = False
    ) -> str:
        # Native Windows dialogs do not reliably follow a Qt application
        # palette. Using Qt's own dialog guarantees the resource workspace's
        # dark/light colors on every supported Windows version.
        initial_path = Path(str(initial)).expanduser()
        dialog_directory = initial_path.parent if save else initial_path
        dialog = QFileDialog(self, title, str(dialog_directory), name_filter)
        dialog.setOption(QFileDialog.DontUseNativeDialog, True)
        dialog.setViewMode(QFileDialog.Detail)
        dialog.setAcceptMode(QFileDialog.AcceptSave if save else QFileDialog.AcceptOpen)
        dialog.setFileMode(QFileDialog.AnyFile if save else QFileDialog.ExistingFile)
        if save:
            dialog.setOption(QFileDialog.DontConfirmOverwrite, False)
            dialog.selectFile(initial_path.name)
        apply_resource_dialog_theme(dialog, self._dark_mode)
        if dialog.exec_() != QFileDialog.Accepted:
            return ""
        files = dialog.selectedFiles()
        return files[0] if files else ""

    def maybe_save(self) -> bool:
        if not self._dirty:
            return True
        answer = self._question(
            "Resourcen-Editor",
            "Das Resourcen-Projekt wurde geändert. Änderungen speichern?",
            QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
            QMessageBox.Yes,
        )
        if answer == QMessageBox.Cancel:
            return False
        if answer == QMessageBox.Yes:
            return bool(self.save())
        return True

    def new_rc(self, *, target: Optional[str] = None):
        if not self.maybe_save():
            return False
        if target is not None:
            self.set_target(target)
        self.current_path = None
        self.entries = []
        self._loading = True
        self.source_edit.clear()
        self.source_edit.setReadOnly(False)
        self._loading = False
        self._dirty = True
        self.file_label.setText("(neues Resourcen-Projekt)")
        self.resource_tree.clear()
        self.properties.setRowCount(0)
        self.hex_edit.clear()
        self.tabs.setCurrentIndex(0)
        self.source_edit.setFocus(Qt.OtherFocusReason)
        self._set_status(
            "Neues Resourcen-Projekt: "
            + ("Windows PE32+" if self.current_target == "pe64" else "Windows PE32")
        )
        return True

    def choose_open(self):
        path = self._file_dialog(
            "Resourcen-Projekt öffnen",
            str(self.current_path.parent if self.current_path else Path.cwd()),
            "Windows Ressourcen (*.rc *.res);;RC Dateien (*.rc);;RES Dateien (*.res);;Alle Dateien (*.*)",
        )
        if path:
            return self.open_path(path, target=self.current_target)
        return False

    def open_path(self, path, *, target: Optional[str] = None):
        if not self.maybe_save():
            return False
        p = Path(path).expanduser().resolve()
        if target is not None:
            self.set_target(target)
        if not p.exists():
            self._warning("Resourcen-Editor", f"Datei nicht gefunden:\n{p}")
            return False
        self.current_path = p
        self.file_label.setText(str(p))
        self._dirty = False
        suffix = p.suffix.lower()
        try:
            self._loading = True
            if suffix == ".rc":
                self.source_edit.setReadOnly(False)
                self.source_edit.setPlainText(p.read_text(encoding="utf-8-sig", errors="replace"))
                self.tabs.setTabEnabled(0, True)
                self.tabs.setCurrentIndex(0)
                self._loading = False
                self.refresh_resources(show_dialog=False)
            elif suffix == ".res":
                self.source_edit.setReadOnly(True)
                self.source_edit.setPlainText("// Binäre .res-Datei – Ansicht über Ressourcen/Eigenschaften/Hex\n")
                self.entries = read_res(p)
                self._populate_tree()
                self.tabs.setCurrentWidget(self.properties)
            else:
                raise ResourceCompilerError("Nur .rc und .res können im Resourcen-Editor geöffnet werden")
            self._dirty = False
            self._set_status(f"Geöffnet: {p.name} ({len(self.entries)} Einträge)")
            self.file_changed.emit(str(p))
            return True
        except Exception as exc:
            self._critical("Resource-Fehler", str(exc))
            self._set_status(str(exc))
            return False
        finally:
            self._loading = False

    def save(self):
        if self.current_path is None:
            return self.save_as()
        try:
            if self.current_path.suffix.lower() == ".rc":
                self.current_path.write_text(self.source_edit.toPlainText(), encoding="utf-8")
            elif self.current_path.suffix.lower() == ".res":
                save_res(self.current_path, self.entries)
            self._dirty = False
            self._set_status(f"Gespeichert: {self.current_path.name}")
            return True
        except Exception as exc:
            self._critical("Speichern", str(exc))
            return False

    def save_as(self):
        suggested = str(self.current_path or (Path.cwd() / "resource.rc"))
        path = self._file_dialog(
            "Resourcen-Projekt speichern",
            suggested,
            "RC Dateien (*.rc);;RES Dateien (*.res);;Alle Dateien (*.*)",
            save=True,
        )
        if not path:
            return False
        target = Path(path)
        try:
            if target.suffix.lower() == ".res":
                self.refresh_resources(show_dialog=False)
                save_res(target, self.entries)
            else:
                if target.suffix.lower() != ".rc":
                    target = target.with_suffix(".rc")
                target.write_text(self.source_edit.toPlainText(), encoding="utf-8")
            self.current_path = target.resolve()
            self.file_label.setText(str(self.current_path))
            self._dirty = False
            self.file_changed.emit(str(self.current_path))
            self._set_status(f"Gespeichert: {self.current_path.name}")
            return True
        except Exception as exc:
            self._critical("Speichern unter", str(exc))
            return False

    def _compile_current_rc(self):
        if self.current_path is None or self.current_path.suffix.lower() != ".rc":
            raise ResourceCompilerError("Für diese Aktion muss das Resourcen-Projekt zuerst als .rc gespeichert werden")
        if self._dirty and not self.save():
            raise ResourceCompilerError("Speichern der RC-Datei wurde abgebrochen")
        compilation = compile_rc(self.current_path, include_dirs=[self.current_path.parent])
        self.entries = compilation.entries
        self._populate_tree()
        return compilation

    def refresh_resources(self, checked=False, *, show_dialog=True):
        del checked
        try:
            if self.current_path and self.current_path.suffix.lower() == ".res":
                self.entries = read_res(self.current_path)
            elif self.current_path and self.current_path.suffix.lower() == ".rc":
                self._compile_current_rc()
            else:
                return False
            self._populate_tree()
            self._set_status(f"{len(self.entries)} Ressourcen eingelesen")
            return True
        except Exception as exc:
            self._set_status(str(exc))
            if show_dialog:
                self._critical("Resource Compiler", str(exc))
            return False

    def compile_to_res(self):
        try:
            self._compile_current_rc()
            suggested = self.current_path.with_suffix(".res")
            path = self._file_dialog("RES schreiben", str(suggested), "RES Dateien (*.res)", save=True)
            if not path:
                return
            out = save_res(path, self.entries)
            self._set_status(f"RES erzeugt: {out}")
        except Exception as exc:
            self._critical("RC → RES", str(exc))

    def compile_to_coff(self, machine: str):
        arch = "64" if machine == "x64" else "32"
        try:
            if self.current_path and self.current_path.suffix.lower() == ".res":
                self.entries = read_res(self.current_path)
            else:
                self._compile_current_rc()
            suggested = (self.current_path or Path("resource.res")).with_name(
                (self.current_path.stem if self.current_path else "resource") + f"_res{arch}.obj"
            )
            path = self._file_dialog(f"COFF{arch} schreiben", str(suggested), "COFF Objekt (*.obj *.o)", save=True)
            if not path:
                return
            out = save_resource_coff(path, self.entries, machine=machine)
            self._set_status(f"COFF{arch} erzeugt: {out}")
        except Exception as exc:
            self._critical(f"COFF{arch}", str(exc))

    def _populate_tree(self, selected_index: Optional[int] = None):
        self.resource_tree.clear()
        groups = {}
        wanted = None
        for index, entry in enumerate(self.entries):
            type_label = describe_resource_id(entry.type_id)
            parent = groups.get(type_label)
            if parent is None:
                parent = QTreeWidgetItem(self.resource_tree, [type_label, "", ""])
                parent.setExpanded(True)
                groups[type_label] = parent
            code, _title, flag_path, lang_id = self._language_info(entry.language)
            language_text = f"{code}  0x{lang_id:04X}" if code != "---" else f"0x{lang_id:04X}"
            child = QTreeWidgetItem(parent, [str(entry.name_id), language_text, str(len(entry.data))])
            if flag_path:
                child.setIcon(1, self._flag_icon(flag_path))
            child.setData(0, Qt.UserRole, index)
            if selected_index is not None and index == selected_index:
                wanted = child
        if wanted is not None:
            self.resource_tree.setCurrentItem(wanted)
        elif self.entries:
            first_group = self.resource_tree.topLevelItem(0)
            if first_group and first_group.childCount():
                self.resource_tree.setCurrentItem(first_group.child(0))

    def _resource_selected(self):
        item = self.resource_tree.currentItem()
        if item is None:
            return
        index = item.data(0, Qt.UserRole)
        if index is None:
            return
        try:
            index = int(index)
            entry = self.entries[index]
        except Exception:
            return

        rows = [
            ("Typ", describe_resource_id(entry.type_id)),
            ("Name/ID", str(entry.name_id)),
            ("Sprache", None),
            ("Datenlänge", str(len(entry.data))),
            ("Memory Flags", f"0x{entry.memory_flags:04X}"),
            ("Data Version", f"0x{entry.data_version:08X}"),
            ("Version", f"0x{entry.version:08X}"),
            ("Characteristics", f"0x{entry.characteristics:08X}"),
            ("Codepage", None),
        ]
        self.properties.clearContents()
        self.properties.setRowCount(len(rows))
        for row, (key, value) in enumerate(rows):
            self.properties.setItem(row, 0, QTableWidgetItem(key))
            if value is not None:
                self.properties.setItem(row, 1, QTableWidgetItem(value))

        self._install_language_property(2, index, entry)
        self._install_codepage_property(8, index, entry)

        data = entry.data
        lines = []
        for off in range(0, len(data), 16):
            chunk = data[off:off + 16]
            hexpart = " ".join(f"{b:02X}" for b in chunk)
            asciipart = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
            lines.append(f"{off:08X}  {hexpart:<47}  {asciipart}")
        self.hex_edit.setPlainText("\n".join(lines))

    def _install_language_property(self, row: int, index: int, entry: ResourceEntry) -> None:
        host = QWidget(self.properties)
        layout = QHBoxLayout(host)
        layout.setContentsMargins(3, 1, 3, 1)
        layout.setSpacing(7)
        combo = QComboBox(host)
        combo.setObjectName("resource_language_combo")
        current = -1
        for pos, (code, title, flag_path, lang_id) in enumerate(self.language_codes):
            combo.addItem(code, lang_id)
            combo.setItemData(pos, title, Qt.ToolTipRole)
            if lang_id == (entry.language & 0xFFFF):
                current = pos
        if current >= 0:
            combo.setCurrentIndex(current)
        code_label = QLabel(f"0x{entry.language & 0xFFFF:04X}", host)
        code_label.setMinimumWidth(58)
        flag_label = QLabel(host)
        flag_label.setFixedSize(28, 20)
        flag_label.setAlignment(Qt.AlignCenter)

        def refresh_flag(pos: int):
            lang_id = int(combo.itemData(pos) or 0) & 0xFFFF
            code_label.setText(f"0x{lang_id:04X}")
            info = self._language_info(lang_id)
            pix = QPixmap(f":/flags/{info[2]}.png") if info[2] else QPixmap()
            if not pix.isNull():
                flag_label.setPixmap(pix.scaled(24, 16, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            else:
                flag_label.clear()

        def changed(pos: int):
            if pos < 0:
                return
            refresh_flag(pos)
            self._language_changed(index, int(combo.itemData(pos)))

        refresh_flag(combo.currentIndex())
        combo.currentIndexChanged.connect(changed)
        layout.addWidget(combo, 1)
        layout.addWidget(code_label)
        layout.addWidget(flag_label)
        self.properties.setCellWidget(row, 1, host)

    def _install_codepage_property(self, row: int, index: int, entry: ResourceEntry) -> None:
        combo = QComboBox(self.properties)
        combo.setObjectName("resource_codepage_combo")
        current = -1
        for pos, (title, value) in enumerate(RESOURCE_CODEPAGES):
            combo.addItem(title, value)
            combo.setItemData(pos, f"{value} / 0x{value:04X}", Qt.ToolTipRole)
            if int(entry.codepage) == value:
                current = pos
        if current < 0:
            combo.addItem(f"Benutzerdefiniert ({int(entry.codepage)})", int(entry.codepage))
            current = combo.count() - 1
        combo.setCurrentIndex(current)
        if self.current_path is not None and self.current_path.suffix.lower() == ".res":
            combo.setEnabled(False)
            combo.setToolTip(
                "Die klassische .res-Datei besitzt kein CodePage-Feld im Resource-Header. "
                "Bitte die Codepage im zugehörigen .rc-Projekt setzen; beim RC→COFF-Pfad "
                "wird sie in IMAGE_RESOURCE_DATA_ENTRY gespeichert."
            )
        combo.currentIndexChanged.connect(
            lambda pos: self._codepage_changed(index, int(combo.itemData(pos))) if pos >= 0 else None
        )
        self.properties.setCellWidget(row, 1, combo)

    def _language_changed(self, index: int, lang_id: int) -> None:
        if not (0 <= index < len(self.entries)):
            return
        lang_id &= 0xFFFF
        if self.current_path is not None and self.current_path.suffix.lower() == ".rc":
            self._write_rc_language(lang_id)
            for entry in self.entries:
                entry.language = lang_id
        else:
            self.entries[index].language = lang_id
            self._dirty = True
        self._populate_tree(selected_index=index)
        self._set_status(f"Sprache geändert: LANGID 0x{lang_id:04X}")

    def _codepage_changed(self, index: int, codepage: int) -> None:
        if not (0 <= index < len(self.entries)):
            return
        codepage &= 0xFFFFFFFF
        if self.current_path is not None and self.current_path.suffix.lower() == ".rc":
            self._write_rc_codepage(codepage)
            for entry in self.entries:
                entry.codepage = codepage
        else:
            self.entries[index].codepage = codepage
            self._dirty = True
        self._set_status(f"Codepage geändert: {codepage} / 0x{codepage:04X}")
