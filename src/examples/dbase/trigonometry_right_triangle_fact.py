# -*- coding: utf-8 -*-
"""Stage 426 – Mathe/Fakten/Trigometrie/Rechtwinkliges Dreieck.

Eigenständige QPainter-Lernseite nach der Benutzerreferenz mit Dreiecksskizze
und Formelsammlung für Sinus, Cosinus und Tangens. Keine Pixelkopie.
"""
from __future__ import annotations

import math

from PyQt5.QtCore import QPointF, QRectF, Qt
from PyQt5.QtGui import QColor, QFont, QPainter, QPainterPath, QPen, QBrush
from PyQt5.QtWidgets import QWidget


class TrigonometryRightTriangleFactWidget(QWidget):
    """Spickzettel zum rechtwinkligen Dreieck."""

    BASE_WIDTH = 760
    BASE_HEIGHT = 980

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('math_trigonometry_right_triangle_page')
        self._dark_mode = True
        self._colors = self._palette(True)
        self.setMinimumSize(720, self.BASE_HEIGHT)
        self.setToolTip('Trigometrie: Rechtwinkliges Dreieck mit Sinus, Cosinus und Tangens')

    @staticmethod
    def _palette(dark_mode: bool) -> dict:
        if dark_mode:
            return {
                'canvas': '#151a22',
                'board': '#242934',
                'board_line': '#313948',
                'title': '#f1f3f6',
                'subtitle': '#e3e7ed',
                'paper': '#f1f1f1',
                'paper_shadow': '#1b1f27',
                'text': '#111111',
                'formula': '#161616',
                'triangle': '#2d5ea2',
                'angle': '#111111',
                'footer': '#eceef2',
            }
        return {
            'canvas': '#efebe4',
            'board': '#ddd8d0',
            'board_line': '#c8c0b5',
            'title': '#3a3d44',
            'subtitle': '#4a4d54',
            'paper': '#ffffff',
            'paper_shadow': '#c8c0b5',
            'text': '#161616',
            'formula': '#111111',
            'triangle': '#3766a7',
            'angle': '#111111',
            'footer': '#484b52',
        }

    def set_dark_mode(self, enabled: bool):
        self._dark_mode = bool(enabled)
        self._colors = self._palette(self._dark_mode)
        self.update()

    @staticmethod
    def _font(size, bold=False, family='Arial', italic=False):
        font = QFont(family)
        font.setPixelSize(int(size))
        font.setBold(bool(bold))
        font.setItalic(bool(italic))
        return font

    def _write(self, painter, x, y, text, *, size=24, bold=False, color=None,
               width=None, align=Qt.AlignLeft, family='Arial', italic=False):
        painter.setPen(QColor(color or self._colors['text']))
        painter.setFont(self._font(size, bold=bold, family=family, italic=italic))
        if width is None:
            painter.drawText(QPointF(x, y), text)
        else:
            painter.drawText(QRectF(x, y-size*1.20, width, size*1.50),
                             Qt.AlignVCenter | align, text)

    def _draw_board_background(self, painter):
        painter.fillRect(QRectF(0, 0, self.BASE_WIDTH, self.BASE_HEIGHT), QColor(self._colors['board']))
        # chalk-like texture
        pen = QPen(QColor(self._colors['board_line']), 2)
        painter.setPen(pen)
        for i in range(0, self.BASE_HEIGHT, 34):
            x1 = 12 + (i % 5) * 8
            x2 = self.BASE_WIDTH - 18 - (i % 7) * 5
            painter.drawLine(x1, i + 8, x2, i + 22)
        for i in range(0, self.BASE_WIDTH, 52):
            painter.drawLine(i + 10, 18, i + 26, 58)

    def _draw_paper(self, painter):
        painter.fillRect(QRectF(44, 176, 672, 760), QColor(self._colors['paper_shadow']))
        painter.fillRect(QRectF(34, 166, 672, 760), QColor(self._colors['paper']))

    def _draw_triangle(self, painter):
        pen = QPen(QColor(self._colors['triangle']), 4)
        painter.setPen(pen)
        a = QPointF(96, 432)
        b = QPointF(430, 236)
        c = QPointF(548, 439)
        painter.drawLine(a, b)
        painter.drawLine(b, c)
        painter.drawLine(a, c)

        # alpha angle near the left bottom corner between Hypotenuse and Ankathete
        painter.setPen(QPen(QColor(self._colors['angle']), 4))
        painter.drawArc(128, 352, 124, 124, -4 * 16, 72 * 16)
        self._write(painter, 190, 405, 'α', size=38, family='Times New Roman', italic=True)

        # upper point-angle marker near B: arc plus filled dot
        painter.drawArc(373, 228, 88, 88, 28 * 16, 88 * 16)
        painter.setBrush(QBrush(QColor(self._colors['angle'])))
        painter.drawEllipse(QPointF(448, 271), 4.5, 4.5)
        painter.setBrush(Qt.NoBrush)

        # labels along edges
        painter.save()
        painter.translate(214, 340)
        painter.rotate(-28)
        self._write(painter, 0, 0, 'Ankathete', size=26, family='Times New Roman', italic=True)
        painter.restore()

        painter.save()
        painter.translate(520, 292)
        painter.rotate(60)
        self._write(painter, 0, 0, 'Gegenkathete', size=26, family='Times New Roman', italic=True)
        painter.restore()

        self._write(painter, 255, 472, 'Hypotenuse', size=28, family='Times New Roman', italic=True)

    def _formula_block(self, painter, top):
        self._write(painter, 80, top, 'sin(α) =', size=34, family='Times New Roman', italic=True)
        self._write(painter, 244, top-26, 'Gegenkathete', size=32, family='Times New Roman', italic=True)
        painter.setPen(QPen(QColor(self._colors['formula']), 2))
        painter.drawLine(238, top+6, 474, top+6)
        self._write(painter, 268, top+48, 'Hypotenuse', size=32, family='Times New Roman', italic=True)

        top += 132
        self._write(painter, 80, top, 'cos(α) =', size=34, family='Times New Roman', italic=True)
        self._write(painter, 252, top-26, 'Ankathete', size=32, family='Times New Roman', italic=True)
        painter.drawLine(238, top+6, 474, top+6)
        self._write(painter, 268, top+48, 'Hypotenuse', size=32, family='Times New Roman', italic=True)

        top += 150
        self._write(painter, 80, top, 'tan(α) =', size=34, family='Times New Roman', italic=True)
        self._write(painter, 246, top-28, 'sin(α)', size=28, family='Times New Roman', italic=True)
        painter.drawLine(239, top+4, 334, top+4)
        self._write(painter, 252, top+40, 'cos(α)', size=28, family='Times New Roman', italic=True)
        self._write(painter, 364, top, '=', size=34, family='Times New Roman', italic=True)
        self._write(painter, 410, top-28, 'Gegenkathete', size=30, family='Times New Roman', italic=True)
        painter.drawLine(404, top+4, 630, top+4)
        self._write(painter, 448, top+42, 'Ankathete', size=30, family='Times New Roman', italic=True)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.TextAntialiasing, True)
        painter.fillRect(self.rect(), QColor(self._colors['canvas']))
        scale = min(self.width()/self.BASE_WIDTH, self.height()/self.BASE_HEIGHT)
        painter.translate((self.width()-self.BASE_WIDTH*scale)/2.0,
                          (self.height()-self.BASE_HEIGHT*scale)/2.0)
        painter.scale(scale, scale)

        self._draw_board_background(painter)
        self._write(painter, 86, 92, 'SPICKZETTEL', size=58, family='Arial', color=self._colors['title'])
        self._write(painter, 46, 154, 'Sinus, Cosinus & Tangens', size=40, family='Arial',
                    bold=True, color=self._colors['subtitle'])
        self._draw_paper(painter)
        self._draw_triangle(painter)
        self._formula_block(painter, 568)
        painter.end()


if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication, QScrollArea
    app = QApplication(sys.argv)
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    widget = TrigonometryRightTriangleFactWidget()
    scroll.setWidget(widget)
    scroll.resize(900, 940)
    scroll.setWindowTitle('Trigometrie – Rechtwinkliges Dreieck – Stage 430')
    scroll.show()
    sys.exit(app.exec_())
