# -*- coding: utf-8 -*-
"""Stage 573: Schutz gegen veraltete Agent-Module und native helle Header."""
from __future__ import annotations

import ast
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent


def test_widget_has_public_theme_method():
    tree = ast.parse((ROOT / "agent_0001.py").read_text(encoding="utf-8"))
    classes = {c.name: c for c in tree.body if isinstance(c, ast.ClassDef)}
    assert "GermanGrammarWidget" in classes
    methods = {f.name for f in classes["GermanGrammarWidget"].body if isinstance(f, ast.FunctionDef)}
    assert "set_dark_mode" in methods


def test_native_headers_are_custom_painted_and_dark_and_light():
    source = (ROOT / "agent_0001.py").read_text(encoding="utf-8")
    for required in (
        "class _GrammarHeader(QHeaderView)",
        "def paintSection(self, painter, rect, logical_index):",
        "painter.fillRect(rect, self._header_background)",
        "painter.drawText(rect.adjusted(8, 0, -6, -1), align, str(caption))",
        "self.token_table.setHorizontalHeader(_GrammarHeader(Qt.Horizontal, self.token_table))",
        "self.token_table.setVerticalHeader(_GrammarHeader(Qt.Vertical, self.token_table))",
        "header.set_dark_mode(self._dark)",
        "'#303030', '#f5f5f5', '#565656'",
        "'#e1e1e1', '#171717', '#999999'",
    ):
        assert required in source, required


def test_app_import_exact_local_agent_and_guards_theme_switch():
    source = (ROOT / "d64_dism.py").read_text(encoding="utf-8")
    for required in (
        'Path(__file__).resolve().with_name("agent_0001.py")',
        '_agent_importlib_util.spec_from_file_location(',
        'GermanGrammarWidget = _agent_module.GermanGrammarWidget',
        'agent_set_theme = getattr(agent_widget, "set_dark_mode", None)',
        'if callable(agent_set_theme):',
        'agent_set_theme(enabled)',
    ):
        assert required in source, required


def test_core_module_and_json_are_unmodified():
    import json
    payload = json.loads((ROOT / "data" / "agent_0001_example.json").read_text(encoding="utf-8"))
    assert payload.get("version") == 1
    assert isinstance(payload.get("examples"), list)


@pytest.mark.skipif(importlib.util.find_spec("PyQt5") is None,
                    reason="PyQt5 unter der aktuellen Linux-Umgebung nicht installiert")
def test_real_qt_header_palette_and_theme_switch():
    import os
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PyQt5.QtWidgets import QApplication
    from agent_0001 import GermanGrammarWidget, _GrammarHeader
    app = QApplication.instance() or QApplication([])
    w = GermanGrammarWidget()
    for enabled, bg in ((True, "#303030"), (False, "#e1e1e1"), (True, "#303030")):
        w.set_dark_mode(enabled)
        for header in (w.token_table.horizontalHeader(), w.token_table.verticalHeader()):
            assert isinstance(header, _GrammarHeader)
            assert header._header_background.name() == bg
    w.close()
