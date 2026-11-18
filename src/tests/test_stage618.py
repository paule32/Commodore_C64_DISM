# -*- coding: utf-8 -*-
"""Stage 618: nur die zur Bildfrage passenden Figuren markieren.

Die UI-Zeichenmethoden werden ohne Qt-Installation mit minimalen Grafik-Doubles
isoliert ausgeführt. Die Geometrie und die Satzantwort kommen aus den echten
OpenCV-/DBF-Modulen.
"""
from __future__ import annotations

import ast
from pathlib import Path
from types import SimpleNamespace
import unittest

from agent_0003_core import detect_figures, figures_for_overlay, load_image
from agent_0003_language import LanguageEngine

ROOT = Path(__file__).resolve().parent


class FakeRect:
    def __init__(self, *args):
        self.args = args
    def width(self):
        return self.args[2] if len(self.args) > 2 else 36
    def height(self):
        return self.args[3] if len(self.args) > 3 else 17


class FakeItem:
    def __init__(self, payload=None):
        self.payload = payload
        self.pen = None
        self.position = None
    def setPen(self, value):
        self.pen = value
    def setBrush(self, value):
        self.brush = value
    def setFlag(self, *args):
        pass
    def setToolTip(self, value):
        self.tooltip = value
    def setZValue(self, value):
        self.z = value
    def setFont(self, value):
        self.font = value
    def setAcceptedMouseButtons(self, value):
        pass
    def setPos(self, *value):
        self.position = value
    def boundingRect(self):
        return FakeRect(0, 0, len(self.payload) * 8, 17)


class FakeScene:
    def __init__(self):
        self.items = []
        self.pixmap = object()
        self.items.append(self.pixmap)
    def addItem(self, item):
        self.items.append(item)
    def removeItem(self, item):
        self.items.remove(item)


class Label:
    def __init__(self):
        self.text = ''
    def setText(self, text):
        self.text = text


class Combo:
    def __init__(self):
        self.text = 'Zeige mir alle Figuren'
    def currentText(self):
        return self.text


def load_drawer():
    source = ast.parse((ROOT / 'agent_0003.py').read_text(encoding='utf-8'))
    cls = next(item for item in source.body if isinstance(item, ast.ClassDef)
               and item.name == 'GermanImageRecognitionWidget')
    methods = {'show_filtered_shapes', '_on_filter_changed'}
    body = [item for item in cls.body if isinstance(item, ast.FunctionDef)
            and item.name in methods]
    assert len(body) == 2
    new_cls = ast.ClassDef(name='Drawer', bases=[], keywords=[], body=body,
                           decorator_list=[])
    namespace = dict(
        figures_for_overlay=figures_for_overlay,
        QColor=lambda *args: args,
        QPen=lambda *args: args,
        QBrush=lambda *args: args,
        QFont=type('FakeFont', (), {'Bold': 1, '__init__': lambda self, *args: None}),
        QPointF=lambda x, y: (x, y),
        QPolygonF=lambda pts: pts,
        QGraphicsPolygonItem=FakeItem,
        QGraphicsSimpleTextItem=FakeItem,
        QGraphicsRectItem=FakeItem,
        QRectF=FakeRect,
        QGraphicsItem=SimpleNamespace(ItemIsSelectable='selectable'),
        Qt=SimpleNamespace(NoBrush='none', NoPen='no-pen', NoButton='none'),
    )
    exec(compile(ast.fix_missing_locations(ast.Module(body=[new_cls], type_ignores=[])),
                 '<stage618-drawer>', 'exec'), namespace)
    return namespace['Drawer']


class TestExclusiveQuestionOverlay(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image = load_image(ROOT / 'examples' / 'agent_0003_testbild.png')
        cls.figures = detect_figures(cls.image)
        cls.language = LanguageEngine(ROOT / 'data' / 'woerter.dbf',
                                      ROOT / 'data' / 'fragen.dbf')
        cls.Drawer = load_drawer()

    def widget(self):
        w = self.Drawer()
        w.figures = self.figures
        w._overlay_items = []
        w._figures_by_item = {}
        w._highlighted_figures = set()
        w._show_query_only = False
        w._image_path = Path('testbild.png')
        w.figure_combo = Combo()
        w.scene = FakeScene()
        w.image_info = Label()
        return w

    def ask(self, widget, query):
        height, width = self.image.shape[:2]
        answer, selected = self.language.answer(query, widget.figures, width, height)
        widget._show_query_only = True
        widget._highlighted_figures = {id(f) for f in selected}
        widget.show_filtered_shapes()
        return answer, selected

    @staticmethod
    def labels(widget):
        return [item.payload for item in widget.scene.items
                if isinstance(item, FakeItem) and isinstance(item.payload, str)]

    def test_real_question_draws_only_red_circle_and_label(self):
        w = self.widget()
        answer, selected = self.ask(w, 'wo befindet sich der rote kreis')
        self.assertIn('rot Kreis: links / oben', answer)
        self.assertEqual(len(selected), 1)
        self.assertEqual(len(w._figures_by_item), 1)
        self.assertEqual(self.labels(w), ['Kreis'])
        self.assertEqual(len(w.scene.items), 4)  # Bild + Kontur + Text + Texthintergrund
        self.assertIs(w.scene.items[0], w.scene.pixmap)
        self.assertIn('1 markiert', w.image_info.text)
        figure = next(iter(w._figures_by_item.values()))
        self.assertEqual((figure.kind, figure.color), ('kreis', 'rot'))
        label = next(item for item in w.scene.items
                     if isinstance(item, FakeItem) and item.payload == 'Kreis')
        self.assertAlmostEqual(label.position[0] + len('Kreis') * 4, figure.center[0])

    def test_next_question_replaces_old_overlay_without_leftovers(self):
        w = self.widget()
        self.ask(w, 'wo befindet sich der rote kreis')
        self.ask(w, 'wo befindet sich das grüne dreieck')
        self.assertEqual(self.labels(w), ['Dreieck'])
        self.assertEqual(len(w._figures_by_item), 1)
        self.ask(w, 'wo befindet sich das blaue rechteck')
        self.assertEqual(self.labels(w), ['Rechteck'])
        self.assertEqual(len(w.scene.items), 4)

    def test_unmatched_question_does_not_show_other_figures(self):
        w = self.widget()
        self.ask(w, 'wo befindet sich der rote kreis')
        answer, selected = self.ask(w, 'wo befindet sich der gelbe kreis')
        self.assertIn('Keine passende Figur', answer)
        self.assertFalse(selected)
        self.assertEqual(w._figures_by_item, {})
        self.assertEqual(self.labels(w), [])
        self.assertEqual(w.scene.items, [w.scene.pixmap])

    def test_question_overrides_previous_combobox_filter(self):
        w = self.widget()
        w.figure_combo.text = 'zeige mir alle Dreiecke'
        w.show_filtered_shapes()
        self.assertEqual(self.labels(w), ['Dreieck'])
        self.ask(w, 'wo befindet sich der rote kreis')
        self.assertEqual(self.labels(w), ['Kreis'])

    def test_combobox_reenables_normal_filtering(self):
        w = self.widget()
        self.ask(w, 'wo befindet sich der rote kreis')
        w.figure_combo.text = 'Zeige mir alle Figuren'
        w._on_filter_changed()
        self.assertFalse(w._show_query_only)
        self.assertEqual(sorted(self.labels(w)), ['Dreieck', 'Kreis', 'Kreis', 'Rechteck'])
        w.figure_combo.text = 'zeige mir alle Rechtecke'
        w._on_filter_changed()
        self.assertEqual(self.labels(w), ['Rechteck'])

    def test_none_means_filtering_empty_set_means_no_overlay(self):
        self.assertEqual(len(figures_for_overlay(self.figures, 'Zeige mir alle Figuren')), len(self.figures))
        self.assertEqual(figures_for_overlay(self.figures, 'Zeige mir alle Figuren', set()), [])


if __name__ == '__main__':
    unittest.main()
