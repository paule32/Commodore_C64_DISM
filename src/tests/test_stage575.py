# -*- coding: utf-8 -*-
"""Stage 575: portable JSON-Ablage und neuer Form-Assoziationsagent."""
from __future__ import annotations

import ast
import json
import importlib.util
from pathlib import Path

import pytest

from agent_0001_data import (
    DATA_FILENAME, DEFAULT_EXAMPLES, ExampleStore, ExampleStoreError,
    default_user_path, application_directory,
)
from agent_0002_core import DEFAULT_EXAMPLES as SHAPE_EXAMPLES, recognize_association

ROOT = Path(__file__).resolve().parent


def test_data_basename_and_exe_path(monkeypatch, tmp_path):
    import agent_0001_data as module
    assert DATA_FILENAME == 'agent_0001_example.json'
    monkeypatch.setattr(module.sys, 'frozen', True, raising=False)
    monkeypatch.setattr(module.sys, 'executable', str(tmp_path / 'programm.exe'))
    assert module.default_user_path() == tmp_path / 'data' / DATA_FILENAME
    monkeypatch.delattr(module.sys, 'frozen')


def test_source_path_uses_module_directory(monkeypatch, tmp_path):
    import agent_0001_data as module
    monkeypatch.delattr(module.sys, 'frozen', raising=False)
    assert default_user_path() == application_directory() / 'data' / DATA_FILENAME
    assert not str(default_user_path()).startswith(str(tmp_path))


def test_initial_load_materializes_json_in_data_dir(monkeypatch, tmp_path):
    import agent_0001_data as module
    monkeypatch.setattr(module, 'application_directory', lambda: tmp_path)
    monkeypatch.setattr(module, 'legacy_user_path', lambda: tmp_path/'none.json')
    store = ExampleStore()
    examples = store.load()
    assert store.path == tmp_path/'data'/DATA_FILENAME
    assert store.path.is_file()
    assert len(examples) >= len(DEFAULT_EXAMPLES)
    assert store.path.read_text(encoding='utf8').find('Was ist heute') >= 0
    assert store.add('Der schöne Kreis ist rund.')
    assert ExampleStore().contains('Der schöne Kreis ist rund.')
    payload = json.loads(store.path.read_text(encoding='utf8'))
    assert payload['examples'][-1]['text'] == 'Der schöne Kreis ist rund.'


def test_legacy_profile_import_when_new_file_absent(monkeypatch, tmp_path):
    import agent_0001_data as module
    legacy = tmp_path / 'old' / 'agent_0001_examples.json'
    legacy.parent.mkdir()
    legacy.write_text(json.dumps({'version':1, 'examples':[{'text':'Alter eigener Beispielsatz.'}]}), encoding='utf8')
    monkeypatch.setattr(module, 'application_directory', lambda: tmp_path)
    monkeypatch.setattr(module, 'legacy_user_path', lambda: legacy)
    store = ExampleStore()
    assert store.load() == ['Alter eigener Beispielsatz.']
    assert store.path.exists()
    legacy.unlink()  # nach der Migration nicht mehr auf das Profil angewiesen
    assert store.load() == ['Alter eigener Beispielsatz.']


def test_packaged_default_file_merges_old_profile_once(monkeypatch, tmp_path):
    import agent_0001_data as module
    monkeypatch.setattr(module, 'application_directory', lambda: tmp_path)
    previous = tmp_path / 'old_examples.json'
    previous.write_text(json.dumps({'version':1, 'examples':[{'text':'Ein älterer eigener Satz.'}]}), encoding='utf8')
    monkeypatch.setattr(module, 'legacy_user_path', lambda: previous)
    path = tmp_path / 'data' / DATA_FILENAME
    path.parent.mkdir()
    path.write_text(json.dumps({'version':1, 'examples':[{'text':s} for s in DEFAULT_EXAMPLES]}), encoding='utf8')
    store = ExampleStore()
    current = store.load()
    assert len(current) == len(DEFAULT_EXAMPLES) + 1
    assert current[-1] == 'Ein älterer eigener Satz.'
    assert store.load() == current
    assert len(json.loads(path.read_text(encoding='utf8'))['examples']) == len(current)


def test_cannot_replace_corrupt_local_json(monkeypatch, tmp_path):
    import agent_0001_data as module
    monkeypatch.setattr(module, 'application_directory', lambda: tmp_path)
    path = tmp_path / 'data' / DATA_FILENAME
    path.parent.mkdir()
    path.write_text('{invalid-json', encoding='utf8')
    old = path.read_bytes()
    with pytest.raises(ExampleStoreError):
        ExampleStore().add('Ein neuer Satz.')
    assert path.read_bytes() == old


@pytest.mark.parametrize('sentence,shape,intent', [
    ('Was ist ein Kreis?', 'kreis', 'fragen'),
    ('Wie sieht ein Kreis aus?', 'kreis', 'fragen'),
    ('Zeige mir ein Dreieck', 'dreieck', 'zeichnen'),
    ('Zeichne ein Dreieck.', 'dreieck', 'zeichnen'),
    ('Ein Kreis', 'kreis', 'beschreiben'),
    ('Was ist ein Kreis und ein Dreieck?', None, 'mehrdeutig'),
    ('Zeige mir kein Dreieck', None, 'mehrdeutig'),
    ('Was ist ein Quader?', None, 'unbekannt'),
    ('', None, 'unbekannt'),
])
def test_association(sentence, shape, intent):
    r = recognize_association(sentence)
    assert (r.shape,r.intent)==(shape,intent)
    assert isinstance(r.tokens,tuple)
    assert r.message


def test_ui_layout_and_qpainter_drawing_present():
    src = (ROOT/'agent_0002.py').read_text(encoding='utf8')
    for mark in (
        'class AssociationCanvas(QWidget):', 'QPainter(self)',
        'p.drawEllipse(', 'p.drawPolygon(', 'Qt.Vertical', 'Qt.Horizontal',
        'self.main_splitter', 'self.upper_splitter',
        'self.token_table.setHorizontalHeader',
        'self.token_table.setVerticalHeader',
        'def set_dark_mode(self, enabled):',
        'class GermanAssociationWidget(QWidget):',
    ):
        assert mark in src, mark
    assert len(SHAPE_EXAMPLES)==3


def test_d64_application_menu_and_theme_hooks():
    src = (ROOT/'d64_dism.py').read_text(encoding='utf8')
    assert 'self.agent_menu.addAction(self.agent_0002_action)' in src
    assert 'self.agent_0002_action.triggered.connect(self.show_agent_0002_dock)' in src
    assert 'def show_agent_0002_dock(self):' in src
    assert 'self._activate_exclusive_tool_workspace(dock)' in src
    assert '"agent_0002_widget"' in src
    assert 'set_theme(enabled)' in src
    # PEP-810 lazy imports are supported by the intended application runtime;
    # test syntax of the added method independently on older test Python.
    start = src.index('        def show_agent_0002_dock(self):')
    end = src.index('        def _sync_formula_zoom_control_checks',start)
    ast.parse('class App:\n' + src[start:end])


@pytest.mark.skipif(importlib.util.find_spec('PyQt5') is None,
                    reason='PyQt5 fehlt in der Testumgebung')
def test_agent0002_native_qt_offscreen(monkeypatch):
    monkeypatch.setenv('QT_QPA_PLATFORM','offscreen')
    from PyQt5.QtWidgets import QApplication
    from agent_0002 import GermanAssociationWidget
    app = QApplication.instance() or QApplication([])
    w = GermanAssociationWidget()
    for dark in (True,False,True):
        w.set_dark_mode(dark)
        for header in (w.token_table.horizontalHeader(),w.token_table.verticalHeader()):
            assert header._header_background.name() == ('#303030' if dark else '#e1e1e1')
    w.input_edit.setPlainText('Zeige mir ein Dreieck')
    association = w._run_analysis(w.input_edit.toPlainText())
    assert association.shape == 'dreieck'
    assert w.canvas.shape == 'dreieck'
    w.close()
