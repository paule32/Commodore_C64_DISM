# -*- coding: utf-8 -*-
"""Stage 427 – Mathematik / Grundwissen / Zahlen-Mengen.

QPainter-Neuzeichnung nach der vom Benutzer bereitgestellten Mengenübersicht.
Die Anordnung folgt deren drei horizontalen Ebenen (komplex, algebraisch,
reell) und den sechs *nebeneinanderliegenden* unteren Beispielspalten.
Das Schema dient der Einordnung der Beispiele und ist kein Venn-Diagramm,
das die vollständigen Mengeninklusionen geometrisch beweisen soll.

Keine Bitmap, kein pixelweises Kopieren: Flächen entstehen durch
QPainter.fillPath()/fillRect(), Beschriftungen durch QPainter.drawText().
"""
from __future__ import annotations

from PyQt5.QtCore import QPointF, QRectF, Qt
from PyQt5.QtGui import QBrush, QColor, QFont, QPainter, QPainterPath, QPen
from PyQt5.QtWidgets import QWidget


class NumberSetsFactWidget(QWidget):
    """Skalierbare Zahlenmengen-Grafik mit echten Dark-/Light-Mode-Farben."""

    BASE_WIDTH = 1040
    BASE_HEIGHT = 580

    # Fixe Spaltengrenzen – auf diese Koordinaten beziehen sich *alle*
    # Überschriften, Zahlenbeispiele und Mengensymbole. Dadurch können die
    # untersten Felder nicht mehr gegeneinander verrutschen oder überlappen.
    COLUMN_EDGES = (56, 225, 371, 507, 654, 846, 1016)
    TOP = 20
    ALGEBRAIC_TOP = 132
    REAL_TOP = 250
    BOTTOM = 458

    # Untere Spalten in der Reihenfolge der vom Benutzer gezeigten Referenz:
    # 0 | natürliche | ganze | rationale | reell-algebraische | reelle
    COLUMNS = (
        ('zero', '', '0'),
        ('natural', 'natürliche\nZahlen', 'ℕ'),
        ('integer', 'ganze\nZahlen', 'ℤ'),
        ('rational', 'rationale\nZahlen', 'ℚ'),
        ('real_algebraic', 'reelle\nalgebraische\nZahlen', 'Aᵣ'),
        ('real', 'reelle Zahlen', 'ℝ'),
    )

    # Die Beispiele sind bewusst als (x, y, Beschriftung, Größe)-Daten
    # abgelegt. Jeder Wert gehört zurjenigen Spalte, in der er steht.
    EXAMPLES = {
        'zero': (
            (130, 409, '0', 49),
        ),
        'natural': (
            (247, 374, '3', 22), (323, 390, '9', 22),
            (249, 439, '15', 21), (304, 444, '256', 21),
        ),
        'integer': (
            (381, 373, '-411', 21),
            (381, 418, '-1854', 20), (470, 420, '-9', 20),
            (382, 449, '-2', 19), (425, 450, '-100', 19),
            (483, 449, '-1', 18),
        ),
        'rational': (
            (522, 377, '¼', 23), (586, 377, '3,5', 20),
            (521, 416, '-15,7889', 20),
            (522, 449, '4,85', 20), (604, 448, '-½', 20),
            (635, 418, '¾', 19),
        ),
        'real_algebraic': (
            (673, 379, '√5', 25), (758, 379, '∛¼', 23),
            (675, 443, '∛22', 24), (777, 443, '-√8', 23),
        ),
        'real': (
            (861, 374, 'log(4)', 21), (987, 374, 'e', 23),
            (868, 416, 'e²', 23), (984, 414, 'π', 22),
            (869, 447, '-4π', 21), (982, 448, 'e³', 22),
        ),
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('math_number_sets_page')
        self._dark_mode = True
        self._colors = self._palette(True)
        self.setMinimumSize(920, self.BASE_HEIGHT)
        self.setToolTip('Zahlen-Mengen: Anordnung nach der Übersicht über komplexe, algebraische und reelle Zahlen')

    @staticmethod
    def _palette(dark_mode: bool) -> dict:
        if dark_mode:
            return {
                'canvas': '#0c1624',
                'page': '#142033',
                'text': '#f4f8ff',
                'axis': '#eaf0f8',
                'border': '#7492a9',
                'divider': '#8ab5cc',
                'complex': '#47792f',
                'imaginary': '#558e3d',
                'algebraic': '#377769',
                'blue_zero': '#366d9c',
                'blue_natural': '#3b76a7',
                'blue_integer': '#356f9d',
                'blue_rational': '#337399',
                'blue_real_algebraic': '#327c90',
                'real': '#417d51',
            }
        return {
            'canvas': '#f2f1ee',
            'page': '#ffffff',
            'text': '#101923',
            'axis': '#151d2a',
            'border': '#a3b5ad',
            'divider': '#8eacbd',
            'complex': '#b4ef79',
            'imaginary': '#a9e86e',
            'algebraic': '#9fd3c4',
            'blue_zero': '#93c3e7',
            'blue_natural': '#95c5e7',
            'blue_integer': '#90bfdf',
            'blue_rational': '#8fc9e3',
            'blue_real_algebraic': '#9dd5d6',
            'real': '#a1dba2',
        }

    def set_dark_mode(self, enabled: bool):
        self._dark_mode = bool(enabled)
        self._colors = self._palette(self._dark_mode)
        self.update()

    @staticmethod
    def _font(size: int, bold: bool = False,
              family: str = 'Times New Roman', italic: bool = False):
        font = QFont(family)
        font.setPixelSize(int(size))
        font.setBold(bool(bold))
        font.setItalic(bool(italic))
        return font

    def _write(self, painter, x, y, text, *, size=22, bold=False,
               color=None, italic=False, family='Times New Roman'):
        painter.setPen(QColor(color or self._colors['text']))
        painter.setFont(self._font(size, bold, family, italic))
        painter.drawText(QPointF(x, y), text)

    def _center(self, painter, rect, text, *, size=24, bold=False,
                color=None, family='Times New Roman'):
        """In ein festes Textfeld zeichnen – auch bei mehrzeiligen Überschriften."""
        painter.setPen(QColor(color or self._colors['text']))
        painter.setFont(self._font(size, bold, family))
        painter.drawText(QRectF(*rect), Qt.AlignCenter | Qt.TextWordWrap, text)

    def _regions(self, painter):
        """Flächen ohne Überlagerungen: ein ClipPath, dann saubere Zellfüllungen."""
        left, right = self.COLUMN_EDGES[0], self.COLUMN_EDGES[-1]
        outer = QPainterPath()
        outer.addRoundedRect(
            QRectF(left, self.TOP, right-left, self.BOTTOM-self.TOP), 9, 9
        )
        painter.save()
        painter.setClipPath(outer)
        painter.fillPath(outer, QBrush(QColor(self._colors['complex'])))
        painter.fillRect(QRectF(left, self.TOP, self.COLUMN_EDGES[1]-left,
                               self.ALGEBRAIC_TOP-self.TOP),
                         QColor(self._colors['imaginary']))
        painter.fillRect(QRectF(left, self.ALGEBRAIC_TOP,
                               self.COLUMN_EDGES[5]-left,
                               self.REAL_TOP-self.ALGEBRAIC_TOP),
                         QColor(self._colors['algebraic']))

        for index, (key, _name, _symbol) in enumerate(self.COLUMNS):
            c_left = self.COLUMN_EDGES[index]
            c_right = self.COLUMN_EDGES[index+1]
            color_key = 'blue_' + key if key != 'real' else 'real'
            painter.fillRect(QRectF(c_left, self.REAL_TOP,
                                   c_right-c_left, self.BOTTOM-self.REAL_TOP),
                             QColor(self._colors[color_key]))
        painter.restore()

        painter.setPen(QPen(QColor(self._colors['border']), 1))
        painter.drawPath(outer)
        painter.setPen(QPen(QColor(self._colors['divider']), 1))
        # Segmentgrenzen sind nur in der unteren Reihe sichtbar.
        for edge in self.COLUMN_EDGES[1:-1]:
            painter.drawLine(QPointF(edge, self.REAL_TOP+2),
                             QPointF(edge, self.BOTTOM-2))

    def _upper_labels(self, painter):
        c = self._colors['text']
        self._center(painter, (60, 27, 161, 49), 'imaginäre\nZahlen', size=25, bold=True)
        self._center(painter, (336, 23, 446, 37), 'komplexe Zahlen', size=28, bold=True)
        self._center(painter, (421, 56, 80, 52), 'ℂ', size=44, family='Cambria Math')
        self._center(painter, (331, 139, 413, 36), 'algebraische Zahlen', size=27, bold=True)
        self._center(painter, (419, 170, 88, 59), 'A', size=41, family='Cambria Math')

        # Beispiele in den oberen komplexen bzw. imaginären Regionen.
        for x, y, value, size in (
            (92, 115, 'ei', 21), (171, 115, 'πi', 21),
            (307, 102, '5+9πi', 21),
            (550, 109, 'e − 7πi', 22),
            (740, 82, 'e + i√5', 23),
            (911, 108, 'π − ei', 22),
            (75, 209, 'i', 24), (177, 217, '4i', 23),
            (109, 243, '√−1', 23),
            (280, 211, '5+9i', 22), (308, 242, '−25+i', 22),
            (515, 235, '521+85i', 23),
            (694, 207, '1−i', 23), (730, 241, '−9+14i', 22),
            (869, 219, 'π + i√3', 22),
        ):
            self._write(painter, x, y, value, size=size,
                        color=c, italic=('i' in value or 'π' in value))

    def _lower_labels_and_examples(self, painter):
        for index, (key, heading, symbol) in enumerate(self.COLUMNS):
            x0, x1 = self.COLUMN_EDGES[index:index+2]
            center = (x0+x1)/2
            if heading:
                font_size = 22 if key in ('natural', 'real_algebraic', 'real') else 24
                self._center(painter, (x0+4, 261, x1-x0-8, 69), heading,
                             size=font_size, bold=True)
            for x, y, value, size in self.EXAMPLES[key]:
                self._write(painter, x, y, value, size=size)
            if key == 'zero':
                self._center(painter, (center-32, 480, 64, 42), '0', size=22)
            else:
                self._center(painter, (center-60, 476, 120, 57), symbol,
                             size=44, family='Cambria Math')
        self._center(painter, (319, 540, 420, 31), 'reeller Teil',
                     size=23, bold=True, color=self._colors['axis'])

    def _imaginary_axis_label(self, painter):
        """Nur einmal zeichnen, gedreht an der linken Diagrammkante."""
        painter.save()
        painter.translate(27, 247)
        painter.rotate(-90)
        self._center(painter, (-109, -18, 218, 36), 'imaginärer Teil',
                     size=21, bold=True, color=self._colors['axis'])
        painter.restore()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.TextAntialiasing, True)
        painter.fillRect(self.rect(), QColor(self._colors['canvas']))
        scale = min(self.width()/self.BASE_WIDTH, self.height()/self.BASE_HEIGHT)
        painter.translate((self.width()-self.BASE_WIDTH*scale)/2.0,
                          (self.height()-self.BASE_HEIGHT*scale)/2.0)
        painter.scale(scale, scale)
        painter.fillRect(QRectF(0, 0, self.BASE_WIDTH, self.BASE_HEIGHT),
                         QColor(self._colors['page']))
        self._regions(painter)
        self._upper_labels(painter)
        self._lower_labels_and_examples(painter)
        self._imaginary_axis_label(painter)
        painter.end()


if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication, QScrollArea
    app = QApplication(sys.argv)
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    widget = NumberSetsFactWidget()
    scroll.setWidget(widget)
    scroll.resize(1210, 740)
    scroll.setWindowTitle('Zahlen-Mengen – Stage 427')
    scroll.show()
    sys.exit(app.exec_())
