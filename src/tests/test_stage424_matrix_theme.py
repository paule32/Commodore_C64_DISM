# -*- coding: utf-8 -*-
"""Stage 424: beide Matrizen-Seiten schalten alle Zeichenfarben mit dem Theme um.

Der QPainter-Smoke-Test verwendet kleine Python-Dummys. Ein wirklicher Qt-
Fenstertest muss weiterhin auf Windows mit installiertem PyQt5 erfolgen.
"""
from __future__ import annotations

from importlib import util
from pathlib import Path
import ast
import sys
import types
from unittest.mock import patch

from math_matrix_theme import (
    ROTATION_DARK, ROTATION_LIGHT, MULTIPLICATION_DARK, MULTIPLICATION_LIGHT,
    rotation_palette, multiplication_palette,
)

ROOT = Path(__file__).parent


def _luminance(hex_rgb):
    rgb = [int(hex_rgb[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    rgb = [v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4 for v in rgb]
    return .2126 * rgb[0] + .7152 * rgb[1] + .0722 * rgb[2]


def test_palettes_are_distinct_and_readable():
    for dark, light, base, foreground in (
        (ROTATION_DARK, ROTATION_LIGHT, 'paper_mid', 'formula'),
        (MULTIPLICATION_DARK, MULTIPLICATION_LIGHT, 'panel', 'text'),
    ):
        assert set(dark) == set(light)
        assert _luminance(dark[base]) < .12
        assert _luminance(dark[foreground]) > .55
        assert _luminance(light[base]) > .70
        assert _luminance(light[foreground]) < .16
        assert dark[base] != light[base]
        assert dark[foreground] != light[foreground]
    assert rotation_palette(True) == ROTATION_DARK
    assert rotation_palette(False) == ROTATION_LIGHT
    assert multiplication_palette(True) == MULTIPLICATION_DARK
    assert multiplication_palette(False) == MULTIPLICATION_LIGHT
    assert rotation_palette(True) is not rotation_palette(True)


def test_theme_is_connected_to_application_and_both_pages():
    src = (ROOT / 'd64_dism.py').read_text(encoding='utf-8')
    assert 'widget.set_dark_mode(self.dark_mode_enabled)' in src
    assert 'elif isinstance(widget, MathematicsLearningDockWidget):' in src
    assert 'self.multiplication_matrix_widget.set_dark_mode(enabled)' in src
    assert 'self.rotation_matrix_widget.set_dark_mode(enabled)' in src
    assert 'self._dark_mode = True' in src
    for name in ('rotation_matrix_fact.py', 'multiplication_matrix_fact.py'):
        text = (ROOT / name).read_text(encoding='utf-8')
        ast.parse(text)
        assert 'self._colors = ' in text
        assert 'self._dark_mode = bool(enabled)' in text
        assert 'self.update()' in text


def _render_with_fake_qt(filename, classname):
    """Execute the *entire* paintEvent in both themes without installing Qt."""
    class FakeColor:
        def __init__(self, *args):
            self.value = args
    class FakePoint:
        def __init__(self, x, y):
            self.x, self.y = x, y
    class FakeRect:
        def __init__(self, x, y, w, h):
            self.xvalue, self.yvalue = x, y
            self.width, self.height = w, h
        def x(self): return self.xvalue
        def y(self): return self.yvalue
        def adjusted(self, *args): return self
    class FakeFont:
        def __init__(self, *args): pass
        def setPixelSize(self, *args): pass
        def setBold(self, *args): pass
        def setItalic(self, *args): pass
    class FakePen:
        def __init__(self, color, *args):
            self.color = color
    class FakeBrush:
        def __init__(self, *args): pass
    class FakeGradient:
        def __init__(self, *args): pass
        def setColorAt(self, *args): pass
    class FakePath:
        def __init__(self, *args): pass
        def quadTo(self, *args): pass
    class FakeWidget:
        def __init__(self, *args):
            self._width = 1200
            self._height = 1600
            self.repaints = 0
        def setObjectName(self, *args): pass
        def setMinimumSize(self, *args): pass
        def setToolTip(self, *args): pass
        def update(self): self.repaints += 1
        def rect(self): return FakeRect(0, 0, self._width, self._height)
        def width(self): return self._width
        def height(self): return self._height

    class FakeMetrics:
        def horizontalAdvance(self, text): return len(text) * 12

    class FakePainter:
        Antialiasing = 1
        TextAntialiasing = 2
        def __init__(self, owner):
            owner._painter = self
            self.fills = []
            self.pens = []
        def setRenderHint(self, *args): pass
        def fillRect(self, rect, color):
            if isinstance(color, FakeColor):
                self.fills.append(color.value)
        def translate(self, *args): pass
        def scale(self, *args): pass
        def setPen(self, pen):
            self.pens.append(pen.color.value if isinstance(pen, FakePen) else pen.value)
        def setFont(self, *args): pass
        def fontMetrics(self): return FakeMetrics()
        def drawText(self, *args): pass
        def drawLine(self, *args): pass
        def drawPath(self, *args): pass
        def drawRect(self, *args): pass
        def setBrush(self, *args): pass
        def end(self): pass

    qtcore = types.ModuleType('PyQt5.QtCore')
    qtcore.QPointF, qtcore.QRectF = FakePoint, FakeRect
    qtcore.Qt = types.SimpleNamespace(AlignLeft=0, AlignVCenter=1, AlignHCenter=2,
                                      SolidLine=3, RoundCap=4, RoundJoin=5, NoBrush=6)
    qtgui = types.ModuleType('PyQt5.QtGui')
    qtgui.QColor, qtgui.QFont, qtgui.QPainter, qtgui.QPen = FakeColor, FakeFont, FakePainter, FakePen
    qtgui.QBrush, qtgui.QLinearGradient, qtgui.QPainterPath = FakeBrush, FakeGradient, FakePath
    qtwidgets = types.ModuleType('PyQt5.QtWidgets')
    qtwidgets.QWidget = FakeWidget
    qt5 = types.ModuleType('PyQt5')

    with patch.dict(sys.modules, {'PyQt5': qt5, 'PyQt5.QtCore': qtcore,
                                  'PyQt5.QtGui': qtgui, 'PyQt5.QtWidgets': qtwidgets}):
        spec = util.spec_from_file_location('_stage424_' + filename.replace('.', '_'), ROOT / filename)
        module = util.module_from_spec(spec)
        spec.loader.exec_module(module)
        widget = getattr(module, classname)()
        traces = []
        for enabled in (True, False, True):
            widget.set_dark_mode(enabled)
            widget.paintEvent(None)
            traces.append((widget._painter.fills, widget._painter.pens))
        assert widget.repaints == 3
        assert traces[0] == traces[2], 'Wechsel zurück in Dark-Mode muss identisch zeichnen'
        assert traces[0] != traces[1]
        return traces


def test_rotation_paint_full_dark_light_dark_roundtrip():
    traces = _render_with_fake_qt('rotation_matrix_fact.py', 'RotationMatrixFactWidget')
    assert (ROTATION_DARK['canvas'],) in traces[0][0]
    assert (ROTATION_LIGHT['canvas'],) in traces[1][0]
    assert (ROTATION_DARK['title'],) in traces[0][1]
    assert (ROTATION_LIGHT['title'],) in traces[1][1]
    assert (ROTATION_DARK['axis'],) in traces[0][1]
    assert (ROTATION_LIGHT['axis'],) in traces[1][1]


def test_multiplication_paint_full_dark_light_dark_roundtrip():
    traces = _render_with_fake_qt('multiplication_matrix_fact.py', 'MultiplicationMatrixFactWidget')
    assert (MULTIPLICATION_DARK['page'],) in traces[0][0]
    assert (MULTIPLICATION_LIGHT['page'],) in traces[1][0]
    assert (MULTIPLICATION_DARK['panel'],) in traces[0][0]
    assert (MULTIPLICATION_LIGHT['panel'],) in traces[1][0]
    assert (MULTIPLICATION_DARK['token_normal'],) in traces[0][1]
    assert (MULTIPLICATION_LIGHT['token_normal'],) in traces[1][1]
    assert (MULTIPLICATION_DARK['token_red'],) in traces[0][1]
    assert (MULTIPLICATION_LIGHT['token_red'],) in traces[1][1]
