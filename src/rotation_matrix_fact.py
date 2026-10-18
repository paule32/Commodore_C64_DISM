# -*- coding: utf-8 -*-
"""Stage 421–424 – Mathe/Fakten/Matrizen/Rechnen mit/Verschieben 3-D.

Skalierbare QPainter-Lernseite nach der Bildreferenz mit echtem Hell-/Dunkel-
Theme. Der unerwünschte Schriftzug am Würfel bleibt entfernt und die
Stage-423-Anpassung der unteren Matrix bleibt erhalten.
"""
from __future__ import annotations

import math

from PyQt5.QtCore import QPointF, QRectF, Qt
from PyQt5.QtGui import (
    QBrush, QColor, QFont, QLinearGradient, QPainter, QPainterPath, QPen,
)
from PyQt5.QtWidgets import QWidget

from math_matrix_theme import rotation_palette


class RotationMatrixFactWidget(QWidget):
    """In der Mathe-QScrollArea verankerte rotationsmathematische Übersicht."""

    BASE_WIDTH = 1000
    BASE_HEIGHT = 1400

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('math_rotation_matrix_page')
        self._dark_mode = True
        self._colors = rotation_palette(True)
        self.setMinimumSize(940, self.BASE_HEIGHT)
        self.setToolTip('Verschieben 3-D: Rotationsmatrizen um die x-, y- und z-Achse')

    def set_dark_mode(self, enabled):
        self._dark_mode = bool(enabled)
        self._colors = rotation_palette(self._dark_mode)
        self.update()

    @staticmethod
    def _font(size, bold=False, family='Times New Roman', italic=False):
        result = QFont(family)
        result.setPixelSize(int(size))
        result.setBold(bool(bold))
        result.setItalic(bool(italic))
        return result

    def _write(self, painter, x, y, text, *, size=26, color=None,
               bold=False, width=None, align=Qt.AlignLeft, family='Times New Roman'):
        painter.setPen(QColor(color or self._colors['formula']))
        painter.setFont(self._font(size, bold=bold, family=family))
        if width is None:
            painter.drawText(QPointF(x, y), text)
        else:
            painter.drawText(QRectF(x, y-size*1.12, width, size*1.45),
                             Qt.AlignVCenter | align, text)

    def _formula_name(self, painter, x, y, name, *, size=29):
        """Index einer Matrixbezeichnung an der Grundlinie absenken."""
        if '_' not in name:
            self._write(painter, x, y, name, size=size, bold=True)
            return
        letter, suffix = name.split('_', 1)
        index, rest = suffix[0], suffix[1:]
        self._write(painter, x, y, letter, size=size, bold=True)
        self._write(painter, x+size*.70, y+size*.34, index, size=size*.65)
        self._write(painter, x+size*1.17, y, rest, size=size, bold=True)

    def _line(self, painter, p1, p2, color=None, thickness=3):
        pen = QPen(QColor(color or self._colors['formula']), thickness, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        painter.setPen(pen)
        painter.drawLine(QPointF(*p1), QPointF(*p2))

    def _arrow(self, painter, p1, p2, color=None, width=4, head=13):
        color = color or self._colors['axis']
        self._line(painter, p1, p2, color, width)
        theta = math.atan2(p2[1]-p1[1], p2[0]-p1[0])
        for side in (-0.52, 0.52):
            self._line(painter, p2,
                      (p2[0] - head*math.cos(theta+side),
                       p2[1] - head*math.sin(theta+side)),
                      color, width)

    def _curve_arrow(self, painter, start, middle, end, color=None, thickness=4):
        # Quadratische Bézierkurve, Pfeil am Ende.
        color = color or self._colors['curve']
        path = QPainterPath(QPointF(*start))
        path.quadTo(QPointF(*middle), QPointF(*end))
        painter.setPen(QPen(QColor(color), thickness, Qt.SolidLine, Qt.RoundCap))
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(path)
        theta = math.atan2(end[1]-middle[1], end[0]-middle[0])
        for delta in (-.55, .55):
            self._line(painter, end,
                      (end[0]-11*math.cos(theta+delta),
                       end[1]-11*math.sin(theta+delta)),
                      color, thickness)

    def _matrix(self, painter, name, rows, y, *, x=70, label_width=144,
                col_width=116, size=27, row_height=33):
        """Schreibt die 3x3-Matrix als echten Qt-Text mit gezeichneten Klammern."""
        top = y
        height = 3*row_height + 8
        bracket_x = x+label_width
        right_x = bracket_x + len(rows[0])*col_width + 12
        self._formula_name(painter, x, top+height/2+7, name, size=size+2)
        for sign in (-1, 1):
            xx = bracket_x if sign == -1 else right_x
            dx = 10 if sign == -1 else -10
            self._line(painter, (xx+dx, top), (xx, top), self._colors['bracket'], 2)
            self._line(painter, (xx, top), (xx, top+height), self._colors['bracket'], 2)
            self._line(painter, (xx, top+height), (xx+dx, top+height), self._colors['bracket'], 2)
        for r, row in enumerate(rows):
            for c, cell in enumerate(row):
                left = bracket_x+10+c*col_width
                self._write(painter, left, top+17+r*row_height+size/2,
                           cell, size=size, width=col_width-4, align=Qt.AlignHCenter)

    def _cube(self, painter):
        # Drahtwürfel nach Bildreferenz, ohne Wasserzeichen/Beschriftung unten.
        gold = self._colors['cube']
        front = ((760, 310), (919, 310), (919, 501), (760, 501))
        back = ((828, 252), (965, 252), (965, 446), (828, 446))
        for corners in (front, back):
            for i in range(4):
                self._line(painter, corners[i], corners[(i+1)%4], gold, 1.8)
        for a, b in ((0, 0), (1, 1), (2, 2), (3, 3)):
            self._line(painter, front[a], back[b], gold, 1.8)
        origin = (760, 520)
        self._arrow(painter, origin, (760, 340), self._colors['cube_z'], 5, 13)
        self._arrow(painter, origin, (930, 520), self._colors['cube_x'], 5, 12)
        self._arrow(painter, origin, (827, 455), self._colors['cube_y'], 4, 11)
        self._curve_arrow(painter, (724, 342), (750, 304), (794, 334))
        self._curve_arrow(painter, (793, 452), (850, 403), (829, 506))
        self._curve_arrow(painter, (915, 508), (967, 490), (960, 542))
        self._formula_name(painter, 680, 327, 'R_z(ψ)', size=23)
        self._formula_name(painter, 830, 437, 'R_y(θ)', size=23)
        self._formula_name(painter, 916, 571, 'R_x(φ)', size=23)

    def _axis(self, painter, origin, axis, theta='θ', size=1.0):
        x, y = origin
        blue = self._colors['axis']
        self._arrow(painter, (x, y), (x, y-105*size), blue, 4)
        self._arrow(painter, (x, y), (x+108*size, y), blue, 4)
        self._arrow(painter, (x, y), (x-66*size, y+62*size), blue, 4)
        self._write(painter, x-5, y-114*size, 'z', size=25)
        self._write(painter, x+119*size, y+6, 'y', size=25)
        self._write(painter, x-84*size, y+84*size, 'x', size=25)
        if axis == 'x':
            self._curve_arrow(painter, (x-40, y+9), (x-79, y-40), (x-24, y-43), blue, 3)
            self._curve_arrow(painter, (x-18, y+14), (x+23, y+33), (x+9, y+1), blue, 3)
            self._write(painter, x+15, y+65, theta, size=22)
        elif axis == 'y':
            self._curve_arrow(painter, (x+35, y-24), (x+61, y-85), (x+80, y-18), blue, 3)
            self._curve_arrow(painter, (x+73, y+13), (x+18, y+53), (x+27, y+11), blue, 3)
        else:
            self._curve_arrow(painter, (x-25, y-64), (x-69, y-111), (x-8, y-109), blue, 3)
            self._curve_arrow(painter, (x+8, y-106), (x+63, y-56), (x+13, y-56), blue, 3)
            self._write(painter, x-68, y-85, theta, size=22)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.TextAntialiasing, True)
        painter.fillRect(self.rect(), QColor(self._colors['canvas']))
        scale = min(self.width()/self.BASE_WIDTH, self.height()/self.BASE_HEIGHT)
        painter.translate((self.width()-self.BASE_WIDTH*scale)/2.0,
                          (self.height()-self.BASE_HEIGHT*scale)/2.0)
        painter.scale(scale, scale)
        paper = QLinearGradient(0, 0, self.BASE_WIDTH, self.BASE_HEIGHT)
        paper.setColorAt(0.0, QColor(self._colors['paper_top']))
        paper.setColorAt(0.52, QColor(self._colors['paper_mid']))
        paper.setColorAt(1.0, QColor(self._colors['paper_bottom']))
        painter.fillRect(QRectF(0, 0, self.BASE_WIDTH, self.BASE_HEIGHT), QBrush(paper))
        self._write(painter, 76, 114, 'Rotational Matrix', size=77, bold=True,
                    color=self._colors['title'], family='Arial')
        self._write(painter, 77, 173, 'Elementare Verschiebungen', size=38,
                    color=self._colors['heading'], bold=True)
        self._matrix(painter, 'R_x(φ) =', (
            ('1', '0', '0'),
            ('0', 'cos(φ)', '−sin(φ)'),
            ('0', 'sin(φ)', 'cos(φ)'),
        ), 224, x=68, col_width=104, label_width=136)
        self._matrix(painter, 'R_y(θ) =', (
            ('cos(θ)', '0', 'sin(θ)'),
            ('0', '1', '0'),
            ('−sin(θ)', '0', 'cos(θ)'),
        ), 355, x=68, col_width=104, label_width=136)
        self._matrix(painter, 'R_z(ψ) =', (
            ('cos(ψ)', '−sin(ψ)', '0'),
            ('sin(ψ)', 'cos(ψ)', '0'),
            ('0', '0', '1'),
        ), 486, x=68, col_width=104, label_width=136)
        self._cube(painter)

        sections = (
            ('Verschiebung um die x-Achse', 'P_x =', (
                ('1', '0', '0'),
                ('0', 'cos(θ)', '−sin(θ)'),
                ('0', 'sin(θ)', 'cos(θ)'),
            ), 651, 'x', 105, 115),
            ('Verschiebung um die y-Achse', 'P_y =', (
                ('cos(θ)', '0', 'sin(θ)'),
                ('0', '1', '0'),
                ('−sin(θ)', '0', 'cos(θ)'),
            ), 892, 'y', 105, 115),
            ('Verschiebung um die z-Achse', 'P_z =', (
                ('cos(θ)', '−sin(θ)', '0'),
                ('sin(θ)', 'cos(θ)', '0'),
                ('0', '0', '1'),
            ), 1133, 'z', 95, 125),
        )
        for heading, name, rows, y, axis, matrix_x, col_width in sections:
            self._write(painter, 252, y, heading, size=30, bold=True, color=self._colors['heading'])
            self._matrix(painter, name, rows, y+50, x=matrix_x,
                         col_width=col_width, label_width=115, size=28, row_height=37)
            self._axis(painter, (765, y+119), axis)
        painter.end()


if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication, QScrollArea
    app = QApplication(sys.argv)
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    widget = RotationMatrixFactWidget()
    scroll.setWidget(widget)
    scroll.resize(1200, 900)
    scroll.setWindowTitle('Verschieben 3-D – Stage 424')
    scroll.show()
    sys.exit(app.exec_())
