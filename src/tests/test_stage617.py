# -*- coding: utf-8 -*-
"""Stage 617: Regressionschecks für Bildfrage -> Figurenerkennung -> Antwort.

Qt5-Bindings werden für den Logikfluss nicht benötigt; die echte
QGraphicsView muss zusätzlich auf dem Zielsystem geprüft werden.
"""
from __future__ import annotations
import ast
from pathlib import Path
from types import SimpleNamespace
import unittest

from agent_0003_core import detect_figures, load_image, figures_for_overlay
from agent_0003_language import LanguageEngine, read_dbf

HERE = Path(__file__).resolve().parent
ROOT = HERE


class DummyLabel:
    def __init__(self):
        self.content = ''
    def setText(self, text):
        self.content = text
    def text(self):
        return self.content


class DummyDiagnostics:
    def __init__(self):
        self.content = ''
    def setPlainText(self, text):
        self.content = text


class DummyEdit:
    def __init__(self, text):
        self.content = text
    def toPlainText(self):
        return self.content


class DummyTable:
    def __init__(self):
        self.rows = []
    def setRowCount(self, count):
        self.rows = [None] * count
    def setItem(self, row, column, item):
        if self.rows[row] is None:
            self.rows[row] = [None] * 3
        self.rows[row][column] = item


class TableItem:
    def __init__(self, value):
        self.value = value
    def setTextAlignment(self, _align):
        pass


class SceneItem:
    def __init__(self):
        self.pen = None
    def setPen(self, pen):
        self.pen = pen


class ParentAssociation:
    def analyze(self):
        self.analysis_runs += 1
        return self._run_analysis(self.input_edit.toPlainText())


def load_gui_logic():
    text = (HERE / 'agent_0003.py').read_text(encoding='utf-8')
    module = ast.parse(text)
    cls = next(c for c in module.body if isinstance(c, ast.ClassDef)
               and c.name == 'GermanImageRecognitionWidget')
    methods = {'analyze', 'recognize', '_detect_current_image', '_run_analysis'}
    import copy
    body = [copy.deepcopy(f) for f in cls.body if isinstance(f, ast.FunctionDef)
            and f.name in methods]
    assert len(body) == len(methods)
    temp_class = ast.ClassDef(name='TestedGuiLogic', bases=[ast.Name(id='ParentAssociation', ctx=ast.Load())],
                              keywords=[], body=body, decorator_list=[])
    compiled = ast.fix_missing_locations(ast.Module(body=[temp_class], type_ignores=[]))
    namespace = dict(ParentAssociation=ParentAssociation, detect_figures=detect_figures,
                     cv2=__import__('cv2'), ValueError=ValueError,
                     QTableWidgetItem=TableItem,
                     Qt=SimpleNamespace(AlignCenter=1),
                     QPen=lambda color, width: (color, width),
                     QColor=lambda col: col)
    exec(compile(compiled, '<stage617-gui-logic>', 'exec'), namespace)
    return namespace['TestedGuiLogic']


class TestVisionQuestionFlow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.Gui = load_gui_logic()
        cls.img = load_image(HERE / 'examples' / 'agent_0003_testbild.png')
        cls.language = LanguageEngine(HERE / 'data' / 'woerter.dbf',
                                      HERE / 'data' / 'fragen.dbf')

    def make_widget(self, question):
        w = self.Gui()
        w._image_bgr = self.img
        w.figures = []
        w._recognition_done = False
        w._recognition_error = ''
        w._highlighted_figures = set()
        w._show_query_only = False
        w._figures_by_item = {}
        w._log = lambda message: None
        def draw_overlays():
            chosen = (w._highlighted_figures if w._show_query_only else None)
            visible = figures_for_overlay(w.figures, 'Zeige mir alle Figuren', chosen)
            w._figures_by_item.clear()
            for f in visible:
                item = SceneItem()
                match = id(f) in w._highlighted_figures
                item.setPen(('#ffad36', 3.0) if match else ('#10ff40', 2.3))
                w._figures_by_item[item] = f
        w.show_filtered_shapes = draw_overlays
        w.result_label = DummyLabel()
        w.diagnostics = DummyDiagnostics()
        w.input_edit = DummyEdit(question)
        w.token_table = DummyTable()
        w.language_engine = self.language
        w.analysis_runs = 0
        return w

    def test_button_automatically_detects_red_circle_and_outputs_position(self):
        w = self.make_widget('wo befindet sich der rote kreis')
        w.analyze()  # Im Agenten mit "Satz / Bild prüfen" verbunden
        self.assertTrue(w._recognition_done)
        self.assertGreaterEqual(len(w.figures), 3)
        self.assertEqual(w.analysis_runs, 1)
        self.assertIn('Absicht: position', w.result_label.text())
        self.assertIn('rot Kreis: links / oben', w.result_label.text())
        self.assertIn('x=90', w.result_label.text())
        self.assertIn('y=90', w.result_label.text())
        red = next(f for f in w.figures if f.color == 'rot' and f.kind == 'kreis')
        self.assertIn(id(red), w._highlighted_figures)
        selected = [(item.pen, figure) for item, figure in w._figures_by_item.items()
                    if figure == red]
        self.assertEqual(selected[0][0], ('#ffad36', 3.0))

    def test_second_question_reuses_cached_recognition(self):
        w = self.make_widget('wo befindet sich der rote kreis')
        w.analyze()
        first_figures = w.figures
        w.input_edit.content = 'wo befindet sich das grüne dreieck'
        w.analyze()
        self.assertIs(w.figures, first_figures)
        self.assertIn('grün Dreieck', w.result_label.text())
        self.assertEqual(w.analysis_runs, 2)
        w.input_edit.content = 'wo befindet sich das blaue rechteck'
        w.analyze()
        self.assertIn('blau Rechteck', w.result_label.text())

    def test_explicit_button_reruns_recognition(self):
        w = self.make_widget('wo befindet sich der rote kreis')
        a = w.recognize()
        self.assertTrue(a)
        self.assertIn('Kreis', w.result_label.text())
        self.assertEqual(w.analysis_runs, 1)
        b = w.recognize()
        self.assertTrue(b)
        self.assertIsNot(a, b)
        self.assertEqual(w.analysis_runs, 2)

    def test_no_image_does_not_auto_recognize(self):
        w = self.make_widget('wo befindet sich der rote kreis')
        w._image_bgr = None
        w.analyze()
        self.assertFalse(w._recognition_done)
        self.assertIn('Bild laden', w.result_label.text())

    def test_wrong_color_yields_no_match_after_real_detection(self):
        w = self.make_widget('wo befindet sich der gelbe kreis')
        w.analyze()
        self.assertIn('Keine passende Figur', w.result_label.text())
        self.assertFalse(w._highlighted_figures)

    def test_question_dbf_includes_grammatical_articles(self):
        patterns = [r['FRAGE'] for r in read_dbf(HERE / 'data' / 'fragen.dbf')]
        for pattern in ('wo befindet sich der {farbe} {form}',
                        'wo befindet sich das {farbe} {form}',
                        'wo befindet sich die {farbe} {form}'):
            self.assertIn(pattern, patterns)

    def test_graphics_label_marked_as_figure(self):
        text = (HERE / 'agent_0003.py').read_text(encoding='utf-8')
        self.assertIn('QGraphicsSimpleTextItem(figure.label)', text)
        self.assertIn('self._highlighted_figures = {id(fig) for fig in chosen}', text)
        self.assertIn('self._recognition_done = False', text)


if __name__ == '__main__':
    unittest.main()
