# -*- coding: utf-8 -*-
"""Stage 368: Vektorbasierte Mathehilfen zu Bruechen mit PyQt5/QPainter.

Dieses Modul wird im bestehenden Mathematik-Dock verwendet und kann fuer
Sichtpruefungen auch einzeln gestartet werden:

    python fraction_math_help.py --page fraction_multiply --dark

Keine Referenzbilder werden eingebettet: Saemtliche Tabellen, Balken, Brueche,
Erklaerungen und Formeln werden per QPainter gezeichnet.
"""
from __future__ import annotations

import argparse
from typing import Sequence, Union, Tuple

from PyQt5.QtCore import QPointF, QRectF, Qt
from PyQt5.QtGui import QBrush, QColor, QFont, QPainter, QPainterPath, QPen
from PyQt5.QtWidgets import QApplication, QDockWidget, QMainWindow, QScrollArea, QWidget

FractionCell = Tuple[str, str]
EquationCell = Union[str, FractionCell]


class FractionHelpWidget(QWidget):
    """Fuenf Unterrichtsseiten fuer den rechten Bereich des Mathe-Docks."""

    MODES = (
        'fraction_overview', 'fraction_add', 'fraction_subtract',
        'fraction_multiply', 'fraction_divide',
    )

    # Dezimal-/Prozentwerte bewusst als Naeherung fuer periodische Brueche.
    OVERVIEW = (
        ('1', '10', '0,1', '10 %', 0.10),
        ('1', '5', '0,2', '20 %', 0.20),
        ('1', '4', '0,25', '25 %', 0.25),
        ('1', '3', '0,333…', '≈ 33,3 %', 1.0 / 3.0),
        ('1', '2', '0,5', '50 %', 0.50),
        ('3', '4', '0,75', '75 %', 0.75),
        ('5', '10', '0,5', '50 %', 0.50),
        ('2', '3', '0,666…', '≈ 66,7 %', 2.0 / 3.0),
        ('1', '1', '1', '100 %', 1.0),
    )

    # Titel, Erklaerung und Rechenwege entsprechend den Referenzvorlagen.
    RULES = {
        'fraction_add': {
            'title': 'Brüche addieren',
            'first': (('2', '3'), '+', ('1', '5')),
            'description': (
                'Brüche mit unterschiedlichen Nennern auf einen gemeinsamen Nenner '
                'erweitern. Anschließend die Zähler addieren.'
            ),
            'working': (
                ('2', '3'), '+', ('1', '5'), '=', ('10', '15'), '+',
                ('3', '15'), '=', ('13', '15')
            ),
            'rule': 'Bei gleichem Nenner nur die Zähler addieren; der Nenner bleibt gleich.',
            'second': (('1', '4'), '+', ('2', '4'), '=', ('3', '4')),
        },
        'fraction_subtract': {
            'title': 'Brüche subtrahieren',
            'first': (('5', '6'), '−', ('1', '4')),
            'description': (
                'Zuerst beide Brüche auf einen gemeinsamen Nenner bringen. '
                'Danach den zweiten Zähler vom ersten abziehen.'
            ),
            'working': (
                ('5', '6'), '−', ('1', '4'), '=', ('10', '12'), '−',
                ('3', '12'), '=', ('7', '12')
            ),
            'rule': 'Bei gleichem Nenner nur die Zähler subtrahieren.',
            'second': (('7', '9'), '−', ('2', '9'), '=', ('5', '9')),
        },
        'fraction_multiply': {
            'title': 'Brüche multiplizieren',
            'first': (('2', '3'), '·', ('1', '5')),
            'description': (
                'Die Zähler miteinander multiplizieren und die Nenner '
                'miteinander multiplizieren.'
            ),
            'working': (
                ('2', '3'), '·', ('1', '5'), '=', ('2 · 1', '3 · 5'),
                '=', ('2', '15')
            ),
            'rule': (
                'Vor dem Multiplizieren kann man über Kreuz kürzen: '
                '6 und 4 jeweils durch 2 teilen.'
            ),
            'second': (
                ('3', '4'), '·', ('6', '5'), '=', ('3', '2'), '·',
                ('3', '5'), '=', ('9', '10')
            ),
        },
        'fraction_divide': {
            'title': 'Brüche dividieren',
            'first': (('2', '3'), '÷', ('1', '5')),
            'description': (
                'Den Kehrwert des zweiten Bruchs bilden: Zähler und Nenner '
                'vertauschen. Danach mit dem ersten Bruch multiplizieren.'
            ),
            'working': (
                ('2', '3'), '÷', ('1', '5'), '=', ('2', '3'), '·',
                ('5', '1'), '=', ('10', '3')
            ),
            'rule': 'Weiteres Beispiel: Nach der Kehrwertbildung das Ergebnis kürzen.',
            'second': (
                ('3', '4'), '÷', ('6', '5'), '=', ('3', '4'), '·',
                ('5', '6'), '=', ('15', '24'), '=', ('5', '8')
            ),
        },
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('fraction_math_help')
        self._mode = 'fraction_overview'
        self._dark_mode = False
        self._content_width = 890
        self.setMinimumSize(930, 1000)

    def activate_fact(self, fact_key: str, title: str = '') -> None:
        if fact_key not in self.MODES:
            raise ValueError('Unbekanntes Bruch-Thema: ' + str(fact_key))
        self._mode = fact_key
        self.setMinimumHeight(1100 if fact_key == 'fraction_overview' else 1060)
        self.updateGeometry()
        self.update()

    def set_dark_mode(self, enabled: bool) -> None:
        self._dark_mode = bool(enabled)
        self.update()

    def _palette(self):
        if self._dark_mode:
            return {
                'bg': QColor('#0e1720'), 'card': QColor('#1a2a35'),
                'heading': QColor('#d2f7ef'), 'text': QColor('#edf5f7'),
                'sub': QColor('#bfd3dc'), 'line': QColor('#466774'),
                'accent': QColor('#65d0b9'), 'numerator': QColor('#ff8585'),
                'denominator': QColor('#86c9ff'), 'bar': QColor('#f65d65'),
                'barbg': QColor('#2a4552'), 'panel': QColor('#1e343f'),
                'table_header': QColor('#23515a'),
            }
        return {
            'bg': QColor('#f6f9f9'), 'card': QColor('#ffffff'),
            'heading': QColor('#105f63'), 'text': QColor('#202e37'),
            'sub': QColor('#486372'), 'line': QColor('#96b3b9'),
            'accent': QColor('#087c79'), 'numerator': QColor('#c9303a'),
            'denominator': QColor('#166ca5'), 'bar': QColor('#ea4351'),
            'barbg': QColor('#e5eff2'), 'panel': QColor('#ebf4f4'),
            'table_header': QColor('#067b78'),
        }

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.TextAntialiasing, True)
        colors = self._palette()
        painter.fillRect(self.rect(), colors['bg'])
        # Der Lernbogen bleibt linksbuendig im rechten Inhaltsbereich und
        # erzwingt auch bei schmalem Dock keine verzerrte Grafik.
        if self._mode == 'fraction_overview':
            self._paint_overview(painter, colors)
        else:
            self._paint_operation(painter, colors, self.RULES[self._mode])
        painter.end()

    @staticmethod
    def _font(painter: QPainter, px: int, bold: bool = False):
        font = QFont('Segoe UI', 11)
        font.setPixelSize(px)
        font.setBold(bold)
        painter.setFont(font)

    def _card(self, painter: QPainter, rect: QRectF, colors):
        path = QPainterPath()
        path.addRoundedRect(rect, 14, 14)
        painter.fillPath(path, QBrush(colors['card']))
        painter.setPen(QPen(colors['line'], 1.4))
        painter.drawPath(path)

    def _text(self, painter: QPainter, text: str, rect: QRectF, colors, px=24,
              bold=False, align=Qt.AlignCenter, role='text', wrap=False):
        self._font(painter, px, bold)
        painter.setPen(colors[role])
        flags = align | (Qt.TextWordWrap if wrap else 0)
        painter.drawText(rect, flags, text)

    def _fraction(self, painter: QPainter, rect: QRectF,
                  numerator: str, denominator: str, colors,
                  size=27, colored=True):
        # Echte Bruchstriche statt typografischer Schraegstriche.
        center_x = rect.center().x()
        y = rect.center().y()
        ncol = colors['numerator'] if colored else colors['text']
        dcol = colors['denominator'] if colored else colors['text']
        self._font(painter, size, False)
        painter.setPen(ncol)
        painter.drawText(QRectF(rect.x(), y - size - 8, rect.width(), size + 8),
                         Qt.AlignCenter, str(numerator))
        painter.setPen(QPen(colors['text'], 2.1))
        line_half = max(19, min(rect.width() / 2 - 8, 11 * max(len(str(numerator)), len(str(denominator))) + 8))
        painter.drawLine(QPointF(center_x - line_half, y + 2),
                         QPointF(center_x + line_half, y + 2))
        painter.setPen(dcol)
        painter.drawText(QRectF(rect.x(), y + 6, rect.width(), size + 8),
                         Qt.AlignCenter, str(denominator))

    def _equation(self, painter: QPainter, sequence: Sequence[EquationCell],
                  center_x: float, center_y: float, colors, font_px=27,
                  max_width=824, colored=True):
        widths = []
        for cell in sequence:
            if isinstance(cell, tuple):
                widths.append(max(62, 12 * max(len(str(cell[0])), len(str(cell[1]))) + 32))
            else:
                widths.append(39)
        gap = 6
        total_width = sum(widths) + (len(widths) - 1) * gap
        scale = min(1.0, max_width / total_width)
        painter.save()
        painter.translate(center_x - total_width * scale / 2.0, center_y)
        painter.scale(scale, scale)
        x = 0.0
        for cell, w in zip(sequence, widths):
            rect = QRectF(x, -58, w, 116)
            if isinstance(cell, tuple):
                self._fraction(painter, rect, str(cell[0]), str(cell[1]),
                               colors, font_px, colored)
            else:
                self._text(painter, str(cell), QRectF(x, -16, w, 35), colors,
                           px=font_px + 3, bold=False)
            x += w + gap
        painter.restore()

    def _paint_overview(self, painter: QPainter, colors):
        x, width = 24.0, 870.0
        self._text(painter, 'BRÜCHE – MERKBLATT', QRectF(x, 22, width, 58),
                   colors, px=34, bold=True, role='heading')
        self._text(painter, 'Bruch  ·  Dezimal  ·  Prozent  ·  Bild',
                   QRectF(x, 81, width, 40), colors, px=20, role='sub')
        col = (140, 230, 160, 340)
        row_h = 86
        table_top = 146.0
        self._card(painter, QRectF(x, table_top - 2, width, row_h * 10 + 4), colors)
        widths = [col[0], col[1], col[2], col[3]]
        labels = ('Bruch', 'Dezimal', 'Prozent', 'Bild')
        cx = x
        painter.fillRect(QRectF(x + 1, table_top, width - 2, row_h),
                         colors['table_header'])
        for label, col_w in zip(labels, widths):
            self._font(painter, 20, True)
            painter.setPen(QColor('#ffffff'))
            painter.drawText(QRectF(cx, table_top, col_w, row_h), Qt.AlignCenter, label)
            cx += col_w
        for i, (num, den, decimal, percent, portion) in enumerate(self.OVERVIEW):
            ry = table_top + row_h * (i + 1)
            if i % 2:
                painter.fillRect(QRectF(x + 2, ry, width - 4, row_h), colors['panel'])
            self._fraction(painter, QRectF(x + 21, ry + 3, 96, row_h - 7),
                           num, den, colors, size=23, colored=False)
            if den == '1':
                # Ganze Eins rechts als Zahl, nicht als 1/1, wie auf Merkblatt.
                pass
            self._text(painter, decimal,
                       QRectF(x + col[0], ry, col[1], row_h),
                       colors, px=24)
            self._text(painter, percent,
                       QRectF(x + col[0] + col[1], ry, col[2], row_h),
                       colors, px=21)
            bx = x + col[0] + col[1] + col[2] + 17
            bar_w = col[3] - 36
            by = ry + 25
            painter.setPen(QPen(colors['line'], 1.5))
            painter.setBrush(QBrush(colors['barbg']))
            painter.drawRect(QRectF(bx, by, bar_w, 35))
            painter.fillRect(QRectF(bx + 2, by + 2,
                                    max(0.0, (bar_w - 4) * portion), 31),
                             colors['bar'])
            parts = 10 if den == '10' else int(den)
            painter.setPen(QPen(colors['line'], 1))
            for boundary in range(1, parts):
                gx = bx + bar_w * boundary / parts
                painter.drawLine(QPointF(gx, by), QPointF(gx, by + 35))
        painter.setPen(QPen(colors['line'], 1.4))
        for i in range(11):
            yy = table_top + row_h * i
            painter.drawLine(QPointF(x, yy), QPointF(x + width, yy))
        off = x
        for w in widths[:-1]:
            off += w
            painter.drawLine(QPointF(off, table_top),
                             QPointF(off, table_top + 10 * row_h))
        self._text(painter, 'Bei 1/3 und 2/3 sind die Dezimalwerte periodisch.',
                   QRectF(x, 1015, width, 28), colors, px=16, role='sub')

    def _paint_operation(self, painter: QPainter, colors, rule: dict):
        x, width = 24.0, 870.0
        # Breiter dunkler Titelstreifen wie bei den Referenzkarten.
        header = QRectF(x, 18, width, 88)
        painter.fillRect(header, colors['table_header'])
        self._font(painter, 31, True)
        painter.setPen(QColor('#ffffff'))
        painter.drawText(header, Qt.AlignCenter, rule['title'])
        self._card(painter, QRectF(x, 125, width, 885), colors)
        self._text(painter, 'Ausgangsaufgabe', QRectF(x + 18, 151, width - 36, 34),
                   colors, px=20, bold=True, role='heading')
        self._equation(painter, rule['first'], x + width / 2, 236, colors,
                       font_px=37, colored=False)
        self._text(painter, rule['description'],
                   QRectF(x + 52, 307, width - 104, 94), colors,
                   px=21, wrap=True)
        self._text(painter, 'Rechenweg', QRectF(x + 40, 418, width - 80, 40),
                   colors, px=22, bold=True, role='heading')
        self._equation(painter, rule['working'], x + width / 2, 546, colors,
                       font_px=28, max_width=824)
        painter.setPen(QPen(colors['line'], 1.6))
        painter.drawLine(QPointF(x + 72, 633), QPointF(x + width - 72, 633))
        self._text(painter, rule['rule'], QRectF(x + 64, 665, width - 128, 100),
                   colors, px=21, wrap=True)
        self._text(painter, 'Weiteres Beispiel',
                   QRectF(x + 40, 797, width - 80, 40),
                   colors, px=20, bold=True, role='heading')
        self._equation(painter, rule['second'], x + width / 2, 907, colors,
                       font_px=27, max_width=830)
        if self._mode == 'fraction_multiply':
            self._text(painter, 'Kürzen: 6 : 2 = 3 und 4 : 2 = 2',
                       QRectF(x + 70, 960, width - 140, 30),
                       colors, px=16, role='sub')


def _demo():
    parser = argparse.ArgumentParser(description='Mathehilfen: QPainter-Bruchseiten')
    parser.add_argument('--page', choices=FractionHelpWidget.MODES,
                        default='fraction_overview')
    parser.add_argument('--dark', action='store_true')
    args = parser.parse_args()
    app = QApplication([])
    window = QMainWindow()
    window.setWindowTitle('Mathematik – Bruchhilfen')
    widget = FractionHelpWidget()
    widget.activate_fact(args.page)
    widget.set_dark_mode(args.dark)
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setWidget(widget)
    window.setCentralWidget(scroll)
    window.resize(990, 800)
    window.show()
    return app.exec_()


if __name__ == '__main__':
    raise SystemExit(_demo())
