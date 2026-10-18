# -*- coding: utf-8 -*-
"""Stage 422–424 – Mathe/Fakten/Matrizen/Rechnen mit/Multiplikation.

Skalierbares QPainter-Lehrblatt mit echten Hell-/Dunkel-Farbpaletten für die
schrittweise Matrixmultiplikation (2x2 · 2x3 -> 2x3) nach der Bildreferenz.
Keine externen Assets nötig.
"""
from __future__ import annotations

from PyQt5.QtCore import QPointF, QRectF, Qt
from PyQt5.QtGui import QColor, QFont, QPainter, QPen
from PyQt5.QtWidgets import QWidget

from math_matrix_theme import multiplication_palette


class MultiplicationMatrixFactWidget(QWidget):
    """Hell-/Dunkel-fähiges Lernblatt zur Matrixmultiplikation."""

    BASE_WIDTH = 1180
    BASE_HEIGHT = 1520

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('math_multiplication_matrix_page')
        self._dark_mode = True
        self._colors = multiplication_palette(True)
        self.setMinimumSize(980, self.BASE_HEIGHT)
        self.setToolTip('Multiplikation: Matrixmultiplikation Schritt für Schritt')

    def set_dark_mode(self, enabled):
        self._dark_mode = bool(enabled)
        self._colors = multiplication_palette(self._dark_mode)
        self.update()

    @staticmethod
    def _font(size, bold=False, family='Arial'):
        font = QFont(family)
        font.setPixelSize(int(size))
        font.setBold(bool(bold))
        return font

    def _write(self, painter, x, y, text, *, size=20, color=None, bold=False,
               width=None, align=Qt.AlignLeft, family='Arial'):
        painter.setPen(QColor(color or self._colors['formula']))
        painter.setFont(self._font(size, bold=bold, family=family))
        if width is None:
            painter.drawText(QPointF(x, y), text)
        else:
            painter.drawText(QRectF(x, y-size*1.10, width, size*1.45),
                             Qt.AlignVCenter | align, text)

    def _line(self, painter, x1, y1, x2, y2, color=None, width=2):
        painter.setPen(QPen(QColor(color or self._colors['bracket']), width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.drawLine(x1, y1, x2, y2)

    def _matrix_brackets(self, painter, left, top, width, height, *, color=None, thickness=2):
        color = color or self._colors['bracket']
        # left bracket
        self._line(painter, left+10, top, left, top, color, thickness)
        self._line(painter, left, top, left, top+height, color, thickness)
        self._line(painter, left, top+height, left+10, top+height, color, thickness)
        # right bracket
        right = left + width
        self._line(painter, right-10, top, right, top, color, thickness)
        self._line(painter, right, top, right, top+height, color, thickness)
        self._line(painter, right, top+height, right-10, top+height, color, thickness)

    def _draw_matrix(self, painter, left, top, values, *, cell_w=52, cell_h=48,
                     highlights=None, highlight_fill=None, text_color=None,
                     font_size=19):
        rows = len(values)
        cols = len(values[0]) if rows else 0
        width = cols * cell_w + 20
        height = rows * cell_h + 4
        self._matrix_brackets(painter, left, top, width, height)
        highlights = highlights or {}
        default_highlight = {
            'row': QColor(*self._colors['row']),
            'col': QColor(*self._colors['col']),
            'cell': QColor(*self._colors['cell']),
            'result': QColor(*self._colors['result']),
        }
        if highlight_fill:
            default_highlight.update(highlight_fill)
        for r, row in enumerate(values):
            for c, value in enumerate(row):
                rect = QRectF(left+10+c*cell_w, top+2+r*cell_h, cell_w, cell_h)
                mode = highlights.get((r, c))
                if mode:
                    painter.fillRect(rect.adjusted(2, 3, -3, -4), default_highlight[mode])
                self._write(painter, rect.x(), rect.y()+cell_h/2+7, str(value), size=font_size,
                           color=text_color or self._colors['text'], width=cell_w, align=Qt.AlignHCenter,
                           family='Times New Roman', bold=(mode in {'cell', 'result'}))

    def _draw_formula_tokens(self, painter, left, top, tokens, *, spacing=12, size=19):
        x = left
        for text, color, bold in tokens:
            painter.setFont(self._font(size, bold=bold, family='Times New Roman'))
            painter.setPen(QColor(self._colors.get(color, color)))
            fm = painter.fontMetrics()
            painter.drawText(QPointF(x, top), text)
            x += fm.horizontalAdvance(text) + spacing

    def _draw_result_matrix(self, painter, left, top, result, current_index):
        rows = len(result)
        cols = len(result[0]) if rows else 0
        highlights = {}
        filled = 0
        for r in range(rows):
            for c in range(cols):
                if filled < current_index:
                    highlights[(r, c)] = 'result'
                elif filled == current_index:
                    highlights[(r, c)] = 'cell'
                filled += 1
        display = []
        counter = 0
        for r in range(rows):
            row = []
            for c in range(cols):
                if counter < current_index:
                    row.append(str(result[r][c]))
                elif counter == current_index:
                    row.append(str(result[r][c]))
                else:
                    row.append('')
                counter += 1
            display.append(tuple(row))
        self._draw_matrix(painter, left, top, tuple(display), cell_w=62, cell_h=52,
                         highlights=highlights, font_size=18)

    def _panel(self, painter, top, row_index, col_index, current_index, expressions, result):
        panel_left = 28
        panel_width = self.BASE_WIDTH - 56
        panel_height = 225
        panel_rect = QRectF(panel_left, top, panel_width, panel_height)
        painter.fillRect(panel_rect, QColor(self._colors['panel']))
        painter.setPen(QPen(QColor(self._colors['panel_border']), 2))
        painter.drawRect(panel_rect)

        a = ((1, 2), (3, 4))
        b = ((5, 6, 7), (8, 9, 0))
        result_matrix = ((21, 24, 7), (47, 54, 21))

        left_matrix_x = panel_left + 12
        top_matrix_y = top + 28
        left_highlights = {(row_index, 0): 'row', (row_index, 1): 'row'}
        self._draw_matrix(painter, left_matrix_x, top_matrix_y, a,
                          highlights=left_highlights, font_size=21)
        times_x = left_matrix_x + 142
        self._write(painter, times_x, top + 76, '×', size=28, color=self._colors['formula'], bold=False)
        right_matrix_x = times_x + 28
        col_highlights = {(0, col_index): 'col', (1, col_index): 'col'}
        self._draw_matrix(painter, right_matrix_x, top_matrix_y, b,
                          highlights=col_highlights, cell_w=48, font_size=21)
        eq_x = right_matrix_x + 190
        self._write(painter, eq_x, top + 76, '=', size=28, color=self._colors['formula'])

        formula_left = eq_x + 36
        formula_top = top + 52
        for idx, token_list in enumerate(expressions):
            self._draw_formula_tokens(painter, formula_left + idx*290, formula_top, token_list)
        self._write(painter, formula_left - 6, top + 150, '=', size=28, color=self._colors['formula'])
        self._draw_result_matrix(painter, formula_left + 52, top + 112, result_matrix, current_index)

        # Soft result highlight strip like the reference image.
        strip_x = formula_left + 62 + (current_index % 3) * 62
        strip_y = top + 114 + (current_index // 3) * 52
        painter.fillRect(QRectF(strip_x, strip_y, 60, 20), QColor(*self._colors['strip']))

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.TextAntialiasing, True)
        painter.fillRect(self.rect(), QColor(self._colors['canvas']))
        scale = min(self.width()/self.BASE_WIDTH, self.height()/self.BASE_HEIGHT)
        painter.translate((self.width()-self.BASE_WIDTH*scale)/2.0,
                          (self.height()-self.BASE_HEIGHT*scale)/2.0)
        painter.scale(scale, scale)

        page_color = QColor(self._colors['page'])
        painter.fillRect(QRectF(0, 0, self.BASE_WIDTH, self.BASE_HEIGHT), page_color)
        self._write(painter, 34, 54, 'Matrix Multiplikation: Schritt für Schritt',
                    size=42, color=self._colors['title'], bold=False, family='Arial')

        expressions = [
            [
                [('(1)', 'token_normal', False), ('(5)', 'token_blue', True), ('+', 'token_normal', False), ('(2)', 'token_red', True), ('(8)', 'token_blue', True)],
            ],
            [
                [('(1)', 'token_normal', False), ('(5)', 'token_normal', False), ('+', 'token_normal', False), ('(2)', 'token_normal', False), ('(8)', 'token_normal', False)],
                [('(1)', 'token_normal', False), ('(6)', 'token_blue', True), ('+', 'token_normal', False), ('(2)', 'token_red', True), ('(9)', 'token_blue', True)],
            ],
            [
                [('(1)', 'token_normal', False), ('(5)', 'token_normal', False), ('+', 'token_normal', False), ('(2)', 'token_normal', False), ('(8)', 'token_normal', False)],
                [('(1)', 'token_normal', False), ('(6)', 'token_normal', False), ('+', 'token_normal', False), ('(2)', 'token_normal', False), ('(9)', 'token_normal', False)],
                [('(1)', 'token_normal', False), ('(7)', 'token_blue', True), ('+', 'token_normal', False), ('(2)', 'token_red', True), ('(0)', 'token_blue', True)],
            ],
            [
                [('(1)', 'token_normal', False), ('(5)', 'token_normal', False), ('+', 'token_normal', False), ('(2)', 'token_normal', False), ('(8)', 'token_normal', False)],
                [('(1)', 'token_normal', False), ('(6)', 'token_normal', False), ('+', 'token_normal', False), ('(2)', 'token_normal', False), ('(9)', 'token_normal', False)],
                [('(1)', 'token_normal', False), ('(7)', 'token_normal', False), ('+', 'token_normal', False), ('(2)', 'token_normal', False), ('(0)', 'token_normal', False)],
                [('(3)', 'token_red', True), ('(5)', 'token_blue', True), ('+', 'token_normal', False), ('(4)', 'token_red', True), ('(8)', 'token_blue', True)],
            ],
            [
                [('(1)', 'token_normal', False), ('(5)', 'token_normal', False), ('+', 'token_normal', False), ('(2)', 'token_normal', False), ('(8)', 'token_normal', False)],
                [('(1)', 'token_normal', False), ('(6)', 'token_normal', False), ('+', 'token_normal', False), ('(2)', 'token_normal', False), ('(9)', 'token_normal', False)],
                [('(1)', 'token_normal', False), ('(7)', 'token_normal', False), ('+', 'token_normal', False), ('(2)', 'token_normal', False), ('(0)', 'token_normal', False)],
                [('(3)', 'token_normal', False), ('(5)', 'token_normal', False), ('+', 'token_normal', False), ('(4)', 'token_normal', False), ('(8)', 'token_normal', False)],
                [('(3)', 'token_red', True), ('(6)', 'token_blue', True), ('+', 'token_normal', False), ('(4)', 'token_red', True), ('(9)', 'token_blue', True)],
            ],
            [
                [('(1)', 'token_normal', False), ('(5)', 'token_normal', False), ('+', 'token_normal', False), ('(2)', 'token_normal', False), ('(8)', 'token_normal', False)],
                [('(1)', 'token_normal', False), ('(6)', 'token_normal', False), ('+', 'token_normal', False), ('(2)', 'token_normal', False), ('(9)', 'token_normal', False)],
                [('(1)', 'token_normal', False), ('(7)', 'token_normal', False), ('+', 'token_normal', False), ('(2)', 'token_normal', False), ('(0)', 'token_normal', False)],
                [('(3)', 'token_normal', False), ('(5)', 'token_normal', False), ('+', 'token_normal', False), ('(4)', 'token_normal', False), ('(8)', 'token_normal', False)],
                [('(3)', 'token_normal', False), ('(6)', 'token_normal', False), ('+', 'token_normal', False), ('(4)', 'token_normal', False), ('(9)', 'token_normal', False)],
                [('(3)', 'token_red', True), ('(7)', 'token_blue', True), ('+', 'token_normal', False), ('(4)', 'token_red', True), ('(0)', 'token_blue', True)],
            ],
        ]

        steps = [
            (0, 0, 0),
            (0, 1, 1),
            (0, 2, 2),
            (1, 0, 3),
            (1, 1, 4),
            (1, 2, 5),
        ]
        y = 82
        for index, (row_index, col_index, current_index) in enumerate(steps):
            self._panel(painter, y + index*236, row_index, col_index, current_index,
                        expressions[index], ((21, 24, 7), (47, 54, 21)))
        painter.end()


if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication, QScrollArea
    app = QApplication(sys.argv)
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    widget = MultiplicationMatrixFactWidget()
    scroll.setWidget(widget)
    scroll.resize(1280, 920)
    scroll.setWindowTitle('Multiplikation – Stage 424')
    scroll.show()
    sys.exit(app.exec_())
