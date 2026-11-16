# -*- coding: utf-8 -*-
"""Stage 576: Agent 0002 muss ohne Import des gleichnamigen Agent-0001-Pakets starten."""
from __future__ import annotations

import ast
import importlib.util
import os
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parent


def test_agent0002_does_not_depend_on_agent0001_package():
    source = (ROOT / "agent_0002.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    package_imports = [
        node for node in ast.walk(tree)
        if (isinstance(node, ast.ImportFrom) and node.module == "agent_0001")
        or (isinstance(node, ast.Import) and any(x.name == "agent_0001" for x in node.names))
    ]
    assert not package_imports
    assert "class _GrammarHeader(QHeaderView):" in source
    assert "def paintSection(self, painter, rect, logical_index):" in source
    assert "def set_dark_mode(self, enabled):" in source
    assert "QPalette" in source
    assert "self.token_table.setHorizontalHeader(_GrammarHeader(" in source
    assert "self.token_table.setVerticalHeader(_GrammarHeader(" in source


def test_agent0002_import_with_shadowing_agent0001_package(tmp_path, monkeypatch):
    """Reproduktion des Benutzerfehlers (gleicher Dateiname als Datei/Paket)."""
    pytest.importorskip("PyQt5")
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    package = tmp_path / "agent_0001"
    package.mkdir()
    (package / "__init__.py").write_text("MARKER = 'shadow-package'\n", encoding="utf-8")
    monkeypatch.syspath_prepend(str(tmp_path))
    # Garantiert: import agent_0001 laedt ein anderes Modul, nicht die private Header-Klasse.
    imported = __import__("agent_0001")
    assert not hasattr(imported, "_GrammarHeader")
    import importlib.util
    source = ROOT / "agent_0002.py"
    spec = importlib.util.spec_from_file_location("_stage576_agent0002_test", source)
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
        assert issubclass(module._GrammarHeader, module.QHeaderView)
        from PyQt5.QtWidgets import QApplication
        app = QApplication.instance() or QApplication([])
        widget = module.GermanAssociationWidget()
        for dark in (True, False):
            widget.set_dark_mode(dark)
            for header in (widget.token_table.horizontalHeader(), widget.token_table.verticalHeader()):
                assert header._header_background.name() == ("#303030" if dark else "#e1e1e1")
        widget.input_edit.setPlainText("Zeige mir ein Dreieck")
        assert widget._run_analysis(widget.input_edit.toPlainText()).shape == "dreieck"
        widget.close()
    finally:
        # Modul hat einen eindeutigen, lokalen Namen.
        sys.modules.pop("_stage576_agent0002_test", None)

@pytest.mark.skipif(importlib.util.find_spec("PyQt5") is not None,
                    reason="Der echte Qt-Test prueft die Importkollision bereits")
def test_shadow_import_without_pyqt5_using_minimal_qt_stubs(tmp_path, monkeypatch):
    """Echtes Modul-Laden trotz kollidierendem agent_0001-Paket, ohne GUI."""
    import types

    package_dir = tmp_path / "agent_0001"
    package_dir.mkdir()
    (package_dir / "__init__.py").write_text("MARKER = 'package'\n", encoding="utf-8")
    monkeypatch.syspath_prepend(str(tmp_path))
    monkeypatch.delitem(sys.modules, "agent_0001", raising=False)
    shadow = __import__("agent_0001")
    assert shadow.__file__ == str(package_dir / "__init__.py")
    assert not hasattr(shadow, "_GrammarHeader")

    qt_pkg = types.ModuleType("PyQt5")
    qt_pkg.__path__ = []
    monkeypatch.setitem(sys.modules, "PyQt5", qt_pkg)
    names = {
        "QtCore": "Qt QPointF QRectF QSize",
        "QtGui": "QColor QFont QPainter QPen QPolygonF QBrush QPalette",
        "QtWidgets": "QAbstractItemView QComboBox QGroupBox QHeaderView QHBoxLayout QLabel "
                     "QPlainTextEdit QPushButton QSizePolicy QSplitter QTableWidget "
                     "QTableWidgetItem QVBoxLayout QWidget",
    }
    for submodule, imports in names.items():
        mod = types.ModuleType("PyQt5." + submodule)
        for name in imports.split():
            setattr(mod, name, type(name, (), {}))
        monkeypatch.setitem(sys.modules, mod.__name__, mod)

    spec = importlib.util.spec_from_file_location(
        "_stage576_agent_0002_stub_import", ROOT / "agent_0002.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert issubclass(module._GrammarHeader, module.QHeaderView)
    assert issubclass(module.GermanAssociationWidget, module.QWidget)
    assert sys.modules["agent_0001"] is shadow
