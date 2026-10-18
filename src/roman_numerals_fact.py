# -*- coding: utf-8 -*-
"""Stage 442 – Fakten / Zahlen / Römische . . .

Kopierbare und schreibgeschützte Qt-Textseite nach der tabellarischen
Benutzerreferenz. Alle Inhalte sind echter Text; kein gerendertes Bild.
"""
from __future__ import annotations

from PyQt5.QtCore import Qt
from PyQt5.QtGui import (
    QColor, QFont, QFontMetricsF, QTextBlockFormat, QTextCharFormat, QTextCursor, QTextOption,
)
from PyQt5.QtWidgets import QPlainTextEdit, QSizePolicy


ROMAN_SYMBOLS = ('I', 'V', 'X', 'L', 'C', 'D', 'M')
ROMAN_VALUES = (1, 5, 10, 50, 100, 500, 1000)
ROMAN_THIRD_COLUMN = tuple(range(41, 51)) + (
    60, 70, 80, 90, 100, 200, 300, 400, 500, 1000,
)


def roman_numeral(number: int) -> str:
    """Römische Standardschreibweise für 1..3999 (inkl. Subtraktionsregel)."""
    if not isinstance(number, int) or isinstance(number, bool) or not 1 <= number <= 3999:
        raise ValueError('Römische Zahlen müssen zwischen 1 und 3999 liegen.')
    pieces = []
    for value, symbol in (
        (1000, 'M'), (900, 'CM'), (500, 'D'), (400, 'CD'),
        (100, 'C'), (90, 'XC'), (50, 'L'), (40, 'XL'),
        (10, 'X'), (9, 'IX'), (5, 'V'), (4, 'IV'), (1, 'I'),
    ):
        count, number = divmod(number, value)
        if count:
            pieces.append(symbol * count)
    return ''.join(pieces)


def roman_table_rows():
    """Die drei 20-zeiligen Spalten aus dem Referenzblatt."""
    return tuple(
        ((first, roman_numeral(first)),
         (second, roman_numeral(second)),
         (third, roman_numeral(third)))
        for first, second, third in zip(
            range(1, 21), range(21, 41), ROMAN_THIRD_COLUMN
        )
    )


def roman_column_stops(widths, gap=17.0):
    """Absolute Tabpositionen mit garantierter Breite fuer jede Textspalte.

    Auch die laengste roemische Ziffer muss vor dem Tabstopp der folgenden
    Spalte enden. Die letzte Spalte benoetigt keinen nachfolgenden Tabstopp.
    """
    positions = []
    offset = 0.0
    for width in widths[:-1]:
        offset += float(width) + float(gap)
        positions.append(offset)
    return tuple(positions)


ROMAN_DARK_COLORS = {
    'background': '#17212d',
    'text': '#f1f5fb',
    'title': '#8bc4ff',
    'rule': '#8ca0b9',
    'border': '#50637d',
    'selection_background': '#3b6896',
    'selection_text': '#ffffff',
}
ROMAN_LIGHT_COLORS = {
    'background': '#fdfdfb',
    'text': '#191919',
    'title': '#15457f',
    'rule': '#292929',
    'border': '#bababa',
    'selection_background': '#badbff',
    'selection_text': '#101820',
}


class RomanNumeralsFactWidget(QPlainTextEdit):
    """Read-only-Lernblatt mit formatierbaren/markierbaren Textbausteinen."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('math_roman_numerals_plain_text_page')
        self.setReadOnly(True)
        self.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.setUndoRedoEnabled(False)
        self.setFrameShape(QPlainTextEdit.NoFrame)
        self.setMinimumSize(0, 0)
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.setViewportMargins(22, 17, 22, 17)
        self.setToolTip('Römische Zahlen – Grundsymbole und Umrechnungstabelle')
        self._dark_mode = True
        self._build_text()
        self.set_dark_mode(True)

    @staticmethod
    def _style(size: float, *, bold=False, color='#191919', family='Georgia'):
        fmt = QTextCharFormat()
        fmt.setFontFamily(family)
        fmt.setFontPointSize(float(size))
        fmt.setFontWeight(QFont.Bold if bold else QFont.Normal)
        fmt.setForeground(QColor(color))
        return fmt

    @staticmethod
    def _tabs(positions):
        tabs = []
        for position in positions:
            tab = QTextOption.Tab()
            tab.position = float(position)
            tab.type = QTextOption.LeftTab
            tabs.append(tab)
        return tabs

    @staticmethod
    def _text_width(text, *, size=14, bold=False, family='Georgia'):
        font = QFont(family)
        font.setPointSizeF(float(size))
        font.setBold(bool(bold))
        return QFontMetricsF(font).horizontalAdvance(str(text))

    def _body_tab_positions(self):
        """Sechs Datenspalten: Zahl/Symbol in drei nebeneinander stehenden Paaren."""
        rows = roman_table_rows()
        widths = []
        for index in range(6):
            choices = (str(row[index // 2][0]) if index % 2 == 0
                       else row[index // 2][1] for row in rows)
            widest = max(self._text_width(value, size=14, bold=index % 2 == 1)
                         for value in choices)
            widths.append(widest + (6.0 if index % 2 == 0 else 8.0))
        # Statt fixer Positionen: die breiteste Ziffer jeder Spalte bestimmt
        # den Abstand. Damit kann XXXVIII nicht in die 5. Spalte hineinragen.
        return roman_column_stops(widths, gap=18.0)

    def _header_tab_positions(self):
        widths = [max(self._text_width(symbol, size=17, bold=True),
                      self._text_width(str(value), size=14)) + 8.0
                  for symbol, value in zip(ROMAN_SYMBOLS, ROMAN_VALUES)]
        return roman_column_stops(widths, gap=17.0)

    def _build_text(self):
        """Sieben Kopfspalten und sechs korrekt getrennte Tabellen-Spalten."""
        colors = ROMAN_DARK_COLORS if self._dark_mode else ROMAN_LIGHT_COLORS
        document = self.document()
        document.clear()
        document.setDocumentMargin(8.0)
        cursor = QTextCursor(document)
        cursor.movePosition(QTextCursor.Start)
        first_block = True

        def line(text='', *, size=14, bold=False, color=None,
                 family='Georgia', center=False, top=0, bottom=0,
                 left=0, tabs=None, pieces=None):
            nonlocal first_block
            block = QTextBlockFormat()
            block.setAlignment(Qt.AlignHCenter if center else Qt.AlignLeft)
            block.setTopMargin(float(top))
            block.setBottomMargin(float(bottom))
            block.setLeftMargin(float(left))
            if tabs is not None:
                block.setTabPositions(self._tabs(tabs))
            if first_block:
                cursor.setBlockFormat(block)
                first_block = False
            else:
                cursor.insertBlock(block)
            ink = color or colors['text']
            if pieces is None:
                cursor.insertText(text, self._style(size, bold=bold,
                                                     color=ink, family=family))
            else:
                for part, is_roman in pieces:
                    cursor.insertText(part, self._style(
                        size, bold=is_roman, color=ink, family=family,
                    ))

        line('RÖMISCHE ZAHLEN', size=22, bold=True,
             color=colors['title'], center=True, bottom=20)
        rule = '─' * 53
        line(rule, size=11, family='Consolas', center=True,
             color=colors['rule'], bottom=10)
        # Sieben vollstaendige Kopfspalten: I, V, X, L, C, D, M.
        header_tabs = self._header_tab_positions()
        line('\t'.join(ROMAN_SYMBOLS), size=17, bold=True,
             left=36, tabs=header_tabs, bottom=5)
        line('\t'.join(str(value) for value in ROMAN_VALUES), size=14,
             left=36, tabs=header_tabs, bottom=8)
        line(rule, size=11, family='Consolas', center=True,
             color=colors['rule'], bottom=20)

        # Die Datentabelle besteht aus sechs Spalten = drei Zahl/Symbol-Paaren.
        body_tabs = self._body_tab_positions()
        for row in roman_table_rows():
            pieces = []
            for col, (value, symbol) in enumerate(row):
                if col:
                    pieces.append(('\t', False))
                pieces.append((str(value) + '\t', False))
                pieces.append((symbol, True))
            line(size=14, pieces=pieces, tabs=body_tabs, left=13, bottom=4)

        cursor.movePosition(QTextCursor.Start)
        self.setTextCursor(cursor)
        self.verticalScrollBar().setValue(0)
        self.horizontalScrollBar().setValue(0)

    def set_dark_mode(self, enabled: bool):
        enabled = bool(enabled)
        changed = self._dark_mode != enabled
        self._dark_mode = enabled
        colors = ROMAN_DARK_COLORS if enabled else ROMAN_LIGHT_COLORS
        self.setStyleSheet(
            'QPlainTextEdit#math_roman_numerals_plain_text_page {'
            f'background-color: {colors["background"]};'
            f'color: {colors["text"]};'
            f'border: 1px solid {colors["border"]};'
            f'selection-background-color: {colors["selection_background"]};'
            f'selection-color: {colors["selection_text"]};'
            '}'
        )
        if changed:
            vertical = self.verticalScrollBar().value()
            horizontal = self.horizontalScrollBar().value()
            self._build_text()
            self.verticalScrollBar().setValue(vertical)
            self.horizontalScrollBar().setValue(horizontal)
