# -*- coding: utf-8 -*-
"""Agent 0003 / dBASE-Startpfad: Offline-Logik- und Strukturtests.

Die native Qt5-GUI muss zusätzlich unter Windows / Python 3.15 getestet werden.
"""
from __future__ import annotations
import ast
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from typing import Optional

import cv2
import numpy as np

from agent_0003_core import detect_figures, load_image, matches_filter
from agent_0003_language import LanguageEngine, read_dbf, ensure_agent_databases

ROOT = Path(__file__).parent
SOURCE = (ROOT / 'd64_dism.py').read_text('utf8')
SOURCE_FOR_TEST = SOURCE.replace('lazy from app_lang.deu', 'from app_lang.deu').replace(
    'lazy from app_lang.enu', 'from app_lang.enu')
AST = ast.parse(SOURCE_FOR_TEST)


def load_method(name, env):
    nodes = [node for node in ast.walk(AST) if isinstance(node, ast.FunctionDef)
             and node.name == name]
    assert len(nodes) == 1, f'{name}: {len(nodes)} Methoden'
    fn = nodes[0]
    module = ast.fix_missing_locations(ast.Module(body=[fn], type_ignores=[]))
    namespace = dict(env)
    exec(compile(module, '<stage615>', 'exec'), namespace)
    return namespace[name]


class DocumentEditor:
    def __init__(self, path, target='pe32'):
        self.path = Path(path)
        self.build_target = target
        self.is_dbase_document = True
        self.assembled_program_path = None
        self.assembled_target = None


class TestDbaseStart(unittest.TestCase):
    def test_dbase_start_uses_project_output_directory(self):
        with tempfile.TemporaryDirectory() as root:
            project = Path(root)
            exe_dir = project / 'runtime' / 'dbase' / 'pe32'
            exe_dir.mkdir(parents=True)
            expected = exe_dir / 'probe.exe'
            expected.write_bytes(b'MZ\0\0')
            doc = DocumentEditor(project / 'probe.prg')
            class App:
                current_directory = project
                def __init__(self):
                    self.logs, self.errors = [], []
                def _document_windows_output_path(self, _doc): return exe_dir
                def show_error(self, *data): self.errors.append(data)
                def statusBar(self): return SimpleNamespace(showMessage=lambda *_: None)
                def log(self, message): self.logs.append(message)
                def _launch_assembled_document(self, doc): return doc.assembled_program_path == expected
            run = load_method('_start_existing_dbase_executable',
                              {'DocumentEditor': DocumentEditor, 'Path': Path})
            app = App()
            self.assertTrue(run(app, doc))
            self.assertEqual(doc.assembled_program_path, expected)
            self.assertEqual(doc.assembled_target, 'pe32')
            self.assertFalse(app.errors)
            self.assertIn('runtime', app.logs[-1])

    def test_dbase_start_does_not_build_or_search_wrong_directory(self):
        with tempfile.TemporaryDirectory() as root:
            project = Path(root)
            (project / 'probe.exe').write_bytes(b'MZ\0\0')
            exe_dir = project / 'runtime' / 'dbase' / 'pe32'
            exe_dir.mkdir(parents=True)
            doc = DocumentEditor(project / 'probe.prg')
            class App:
                current_directory = project
                def __init__(self): self.errors = []
                def _document_windows_output_path(self, _doc): return exe_dir
                def show_error(self, *data): self.errors.append(data)
                def statusBar(self): return SimpleNamespace(showMessage=lambda *_: None)
            run = load_method('_start_existing_dbase_executable',
                              {'DocumentEditor': DocumentEditor, 'Path': Path})
            app = App()
            self.assertFalse(run(app, doc))
            self.assertIn('runtime', app.errors[0][1])
            self.assertIsNone(doc.assembled_program_path)

    def test_relative_project_output_directory(self):
        with tempfile.TemporaryDirectory() as root:
            project = Path(root)
            class App:
                current_project_path = project / 'test.pro'
                current_directory = Path('/other/folder')
            base = load_method('_project_windows_base_directory', {'Path': Path, 'OSError': OSError})
            absolute = load_method('_project_windows_absolute_directory', {'Path': Path})
            App._project_windows_base_directory = base
            self.assertEqual(absolute(App(), 'runtime/dbase/pe32'),
                             str((project / 'runtime/dbase/pe32').resolve()))


class TestVision(unittest.TestCase):
    def synthetic(self):
        image = np.full((400, 650, 3), 255, np.uint8)
        cv2.circle(image, (90, 90), 48, (0, 0, 255), -1)
        cv2.rectangle(image, (230, 43), (400, 160), (255, 0, 0), -1)
        cv2.fillPoly(image, [np.array([(440, 180), (505, 35), (595, 180)])], (0, 180, 0))
        cv2.circle(image, (90, 290), 45, (0, 0, 0), -1)
        return image

    def test_mixed_color_and_black_shapes(self):
        figures = detect_figures(self.synthetic())
        self.assertEqual(len(figures), 4, [(f.kind, f.color) for f in figures])
        self.assertIn(('kreis', 'rot'), [(f.kind, f.color) for f in figures])
        self.assertIn(('kreis', 'schwarz'), [(f.kind, f.color) for f in figures])
        self.assertIn(('dreieck', 'grün'), [(f.kind, f.color) for f in figures])
        self.assertIn(('rechteck', 'blau'), [(f.kind, f.color) for f in figures])
        self.assertEqual(sum(matches_filter(f, 'zeige mir alle Kreise') for f in figures), 2)

    def test_black_background_white_shape(self):
        image = np.zeros((240, 240, 3), np.uint8)
        cv2.circle(image, (120, 120), 52, (255,255,255), -1)
        figures = detect_figures(image)
        self.assertEqual(len(figures), 1)
        self.assertEqual(figures[0].kind, 'kreis')
        self.assertEqual(figures[0].color, 'weiß')

    def test_reference_image(self):
        ref = ROOT.parent / 'recognition_ref' / 'Bild_Recognition-main' / 'src' / 'shapes.png'
        if not ref.is_file(): self.skipTest('Original-Referenzbild nicht im ZIP enthalten')
        figures = detect_figures(load_image(ref))
        self.assertGreaterEqual(len(figures), 12)
        kinds = {f.kind for f in figures}
        self.assertTrue({'kreis','dreieck','rechteck','polygon'} <= kinds)

    def test_unicode_image_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'grüner_kreis_äöü.png'
            self.assertTrue(cv2.imencode('.png', self.synthetic())[0])
            path.write_bytes(cv2.imencode('.png', self.synthetic())[1].tobytes())
            self.assertEqual(load_image(path).shape, (400, 650, 3))


class TestLanguage(unittest.TestCase):
    def setUp(self):
        self.words = ROOT / 'data' / 'woerter.dbf'
        self.questions = ROOT / 'data' / 'fragen.dbf'
        self.engine = LanguageEngine(self.words, self.questions)

    def test_dbf_and_word_features(self):
        rows = read_dbf(self.words)
        self.assertGreaterEqual(len(rows), 1000)
        entries = [row for row in rows if row['WORT'] == 'kreis' and row['SUBSTANTIV']]
        self.assertTrue(entries)
        self.assertTrue(any(row['SINGULAR'] and row['MALE'] and row['DER'] for row in entries))
        self.assertTrue(all(not row['FEMALE'] for row in entries))
        self.assertTrue(all('NOMINATIV' in row for row in entries))
        self.assertTrue(all(isinstance(row['NOMINATIV'], bool) for row in entries))

    def test_query_intents_from_dbf(self):
        for question, kind in (
            ('wo befindet sich der rote kreis?', 'position'),
            ('welcher kreis ist rot?', 'farbe'),
            ('zeige mir alle kreise', 'zeigen'),
            ('wie viele rote kreise sind im bild', 'anzahl'),
            ('welche farbe hat das rechteck', 'farbfrage'),
        ):
            q = self.engine.match_question(question)
            self.assertIsNotNone(q, question)
            self.assertEqual(q.intent, kind)
        self.assertIsNone(self.engine.match_question('wer ist gestern angekommen'))

    def test_answers_include_zero_and_yes_no(self):
        image = TestVision().synthetic()
        figs = detect_figures(image)
        answer, matches = self.engine.answer('wie viele gelbe kreise sind im bild', figs, 650, 400)
        self.assertIn('0', answer)
        answer, matches = self.engine.answer('welcher kreis ist rot', figs, 650, 400)
        self.assertTrue(answer.startswith('Ja,'))
        self.assertEqual(len(matches), 1)
        answer, matches = self.engine.answer('wo befindet sich der rote kreis', figs, 650, 400)
        self.assertIn('x=90', answer)

    def test_missing_dbf_generation(self):
        with tempfile.TemporaryDirectory() as directory:
            word_path, question_path = ensure_agent_databases(Path(directory))
            self.assertGreater(len(read_dbf(word_path)), 40)
            self.assertGreater(len(read_dbf(question_path)), 15)


class TestQtIntegrationStructure(unittest.TestCase):
    def test_menu_and_dock_connected(self):
        self.assertIn('QAction("0003 - Bild-Erkennung", self)', SOURCE)
        self.assertIn('self.show_agent_0003_dock', SOURCE)
        self.assertIn('self._activate_exclusive_tool_workspace(dock)', SOURCE)
        self.assertIn('self._expand_exclusive_tool_workspace(dock)', SOURCE)
        gui = (ROOT / 'agent_0003.py').read_text('utf8')
        for name in ('QGraphicsScene', 'QGraphicsView', 'QSplitter', 'load_picture',
                     'recognize', 'QComboBox', 'Bild laden ...', 'Erkennung ...'):
            self.assertIn(name, gui)
        self.assertIn('self.input_edit', gui)


if __name__ == '__main__': unittest.main()
