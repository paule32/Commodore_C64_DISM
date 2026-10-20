# -*- coding: utf-8 -*-
"""Stage 427: fixed, reference-based numerical-set layout without Qt dependency."""
from __future__ import annotations

import ast
from pathlib import Path

HERE = Path(__file__).parent
SOURCE = (HERE / 'number_sets_fact.py').read_text(encoding='utf-8')
MAIN = (HERE / 'd64_dism.py').read_text(encoding='utf-8')


def _number_sets_class():
    return next(node for node in ast.parse(SOURCE).body
                if isinstance(node, ast.ClassDef) and node.name == 'NumberSetsFactWidget')


def _constant(name):
    for node in _number_sets_class().body:
        if isinstance(node, ast.Assign):
            if any(isinstance(target, ast.Name) and target.id == name for target in node.targets):
                return ast.literal_eval(node.value)
    raise AssertionError(name)


def test_fixed_six_column_order_matches_reference():
    edges = _constant('COLUMN_EDGES')
    columns = _constant('COLUMNS')
    assert len(edges) == 7
    assert tuple(key for key, *_ in columns) == (
        'zero', 'natural', 'integer', 'rational', 'real_algebraic', 'real'
    )
    assert all(b > a for a, b in zip(edges, edges[1:]))
    assert edges[0] == 56 and edges[-1] == 1016


def test_examples_are_in_own_column_and_below_headers():
    # Check the exact data assignments via AST, without importing PyQt5.
    edges = _constant('COLUMN_EDGES')
    cols = _constant('COLUMNS')
    examples = _constant('EXAMPLES')
    y_min = _constant('REAL_TOP') + 100
    y_max = _constant('BOTTOM')
    for i, (key, *_rest) in enumerate(cols):
        for x, y, text, size in examples[key]:
            assert edges[i] + 8 <= x < edges[i+1] - 8, (key, text, x)
            assert y_min <= y <= y_max, (key, text, y)
            assert text and 17 <= size <= 55
    assert set(examples) == {row[0] for row in cols}
    assert '0' in {entry[2] for entry in examples['zero']}
    assert '√5' in {entry[2] for entry in examples['real_algebraic']}
    assert 'π' in {entry[2] for entry in examples['real']}


def test_three_layer_fill_clipped_and_vertical_label_not_duplicated():
    assert 'painter.setClipPath(outer)' in SOURCE
    assert 'painter.fillPath(outer' in SOURCE
    assert 'painter.fillRect(' in SOURCE
    assert 'painter.drawText(' in SOURCE
    assert 'painter.translate(27, 247)' in SOURCE
    assert 'painter.rotate(-90)' in SOURCE
    assert SOURCE.count("'imaginärer Teil'") == 1
    assert 'QPixmap' not in SOURCE
    assert '.png' not in SOURCE
    assert '.jpg' not in SOURCE


def test_theme_switch_and_navigation_preserved():
    assert "'complex': '#47792f'" in SOURCE
    assert "'complex': '#b4ef79'" in SOURCE
    assert 'self._colors = self._palette(self._dark_mode)' in SOURCE
    assert "self.facts_tree.itemClicked.connect(self._handle_fact_click)" in MAIN
    assert "self.content_stack.setCurrentWidget(self.number_sets_scroll)" in MAIN
    assert "self.number_sets_widget.set_dark_mode(enabled)" in MAIN


def test_headless_qpainter_dark_light_dark_roundtrip():
    """Run the actual paintEvent with a recording Qt stub (no Qt on CI)."""
    from importlib import util
    from unittest.mock import patch
    import sys
    import types

    class FakeColor:
        def __init__(self, color):
            self.value = color

    class FakeBrush:
        def __init__(self, color):
            self.color = color

    class FakePoint:
        def __init__(self, x, y):
            self.x, self.y = x, y

    class FakeRect:
        def __init__(self, x, y, w, h):
            self.x, self.y, self.w, self.h = x, y, w, h

    class FakeFont:
        def __init__(self, *args):
            pass
        def setPixelSize(self, value):
            pass
        def setBold(self, value):
            pass
        def setItalic(self, value):
            pass

    class FakePen:
        def __init__(self, color, width=1):
            self.color = color

    class FakePath:
        def __init__(self):
            pass
        def addRoundedRect(self, *args):
            pass

    class FakeWidget:
        def __init__(self, *args):
            self.repaints = 0
        def setObjectName(self, *args):
            pass
        def setMinimumSize(self, *args):
            pass
        def setToolTip(self, *args):
            pass
        def update(self):
            self.repaints += 1
        def rect(self):
            return FakeRect(0, 0, 1040, 580)
        def width(self):
            return 1040
        def height(self):
            return 580

    class FakePainter:
        Antialiasing = 1
        TextAntialiasing = 2
        def __init__(self, widget):
            self.trace = []
            widget._last_painter = self
        def setRenderHint(self, *args):
            pass
        def fillRect(self, _rect, color):
            self.trace.append(('fill', color.value))
        def setClipPath(self, path):
            self.trace.append(('clip',))
        def fillPath(self, path, brush):
            self.trace.append(('fill', brush.color.value))
        def setPen(self, pen):
            pass
        def drawPath(self, *args):
            pass
        def drawLine(self, *args):
            pass
        def setFont(self, *args):
            pass
        def drawText(self, *args):
            self.trace.append(('text', args[-1]))
        def translate(self, *args):
            pass
        def rotate(self, *args):
            pass
        def scale(self, *args):
            pass
        def save(self):
            pass
        def restore(self):
            pass
        def end(self):
            pass

    qtcore = types.ModuleType('PyQt5.QtCore')
    qtcore.QPointF, qtcore.QRectF = FakePoint, FakeRect
    qtcore.Qt = types.SimpleNamespace(AlignLeft=1, AlignCenter=2, TextWordWrap=4)
    qtgui = types.ModuleType('PyQt5.QtGui')
    qtgui.QBrush = FakeBrush
    qtgui.QColor = FakeColor
    qtgui.QFont = FakeFont
    qtgui.QPainter = FakePainter
    qtgui.QPainterPath = FakePath
    qtgui.QPen = FakePen
    qtwidgets = types.ModuleType('PyQt5.QtWidgets')
    qtwidgets.QWidget = FakeWidget
    qt5 = types.ModuleType('PyQt5')

    with patch.dict(sys.modules, {
        'PyQt5': qt5, 'PyQt5.QtCore': qtcore,
        'PyQt5.QtGui': qtgui, 'PyQt5.QtWidgets': qtwidgets,
    }):
        spec = util.spec_from_file_location('_stage427_numbers_widget', HERE/'number_sets_fact.py')
        module = util.module_from_spec(spec)
        spec.loader.exec_module(module)
        widget = module.NumberSetsFactWidget()
        traces = []
        for enabled in (True, False, True):
            widget.set_dark_mode(enabled)
            widget.paintEvent(None)
            traces.append(widget._last_painter.trace)
        assert widget.repaints == 3
        assert traces[0] == traces[2]
        assert traces[0] != traces[1]
        assert ('fill', '#47792f') in traces[0]
        assert ('fill', '#b4ef79') in traces[1]
        for expected in ('natürliche\nZahlen', 'ganze\nZahlen', 'rationale\nZahlen',
                         'reelle Zahlen', 'imaginärer Teil', 'reeller Teil'):
            assert ('text', expected) in traces[0]
