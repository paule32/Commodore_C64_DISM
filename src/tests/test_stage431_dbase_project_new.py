# -*- coding: utf-8 -*-
"""Stage 431: ohne PyQt5 ausführbare Prüfungen für dBASE-Neu-Dateien."""
from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

from dbase_project_new import (
    DBASE_NEW_MENU,
    create_dbase_project_file,
    is_dbase_program_text,
)

ROOT = Path(__file__).parent
MAIN = (ROOT / "d64_dism.py").read_text(encoding="utf-8")


def test_eight_actions_exactly_and_unique_targets():
    assert [entry[0] for entry in DBASE_NEW_MENU] == [
        "Neu:  Formular", "Neu:  Programm", "Neu:  Tabelle",
        "Neu:  Abfrage", "Neu:  Bericht", "Neu:  Etikett",
        "Neu:  Windows PE32 Ressource", "Neu:  Windows PE32+ Ressource",
    ]
    assert len({(role, target) for _, role, _, _, target in DBASE_NEW_MENU}) == 8
    assert DBASE_NEW_MENU[-2][-1] == "pe32"
    assert DBASE_NEW_MENU[-1][-1] == "pe64"


def test_binary_detection_text_and_embedded_control_bytes(tmp_path):
    samples = {
        "empty.prg": (b"", True),
        "latin.prg": ("größer = 7\r\n? größer\n".encode("cp1252"), True),
        "utf8.prg": ("Ä = 2\n".encode("utf-8-sig"), True),
        "mz_text.prg": (b"MZ = 123\n", True),
        "c64.prg": (b"\x01\x08\x0a\x00\x9e2064\x00", False),
        "null.prg": (b"? 1\x00? 2", False),
        "late_null.prg": (b"? 42\r\n" * 12000 + b"\x00", False),
        "exe.prg": (b"MZ\x90\x00\x00\x00", False),
        "utf16.prg": (b"\xff\xfe?\x00 \x001\x00", False),
        "esc.prg": (b"? 1\x1b[31m", False),
        "del.prg": (b"? 1\x7f", False),
    }
    for filename, (content, expected) in samples.items():
        path = tmp_path / filename
        path.write_bytes(content)
        assert is_dbase_program_text(path) == expected, filename
    assert is_dbase_program_text(tmp_path / "missing.prg") is False


def test_new_base_documents_are_readable_and_existing_not_overwritten(tmp_path):
    for _, role, _exts, name, target in DBASE_NEW_MENU:
        if role == "tables":
            continue  # DBF wird über den vorhandenen write_dbase_dbf geschrieben.
        path = tmp_path / name
        assert create_dbase_project_file(path, role) == path
        assert path.is_file()
        assert path.stat().st_size >= 0
        if role == "programs":
            assert is_dbase_program_text(path)
        if role in {"queries", "reports", "labels"}:
            data = json.loads(path.read_text(encoding="utf-8"))
            assert isinstance(data, dict)
            assert data["format"].startswith("d64-")
        before = path.read_bytes()
        with pytest.raises(FileExistsError):
            create_dbase_project_file(path, role)
        assert path.read_bytes() == before


def test_wfm_uses_existing_form_parser(tmp_path):
    from d64dbase.wfm import parse_dbase_wfm
    path = tmp_path / "Formular1.wfm"
    create_dbase_project_file(path, "forms")
    form = parse_dbase_wfm(path.read_text(encoding="utf-8"))
    assert form.class_name == "Formular1"
    numeric = tmp_path / "123-Formular.wfm"
    create_dbase_project_file(numeric, "forms")
    form2 = parse_dbase_wfm(numeric.read_text(encoding="utf-8"))
    assert form2.class_name == "Form1"


def test_table_writer_called_once(tmp_path):
    path = tmp_path / "Tabelle.dbf"
    def stub_writer(p):
        Path(p).write_bytes(b"DBF-FORMAT-TEST")
    create_dbase_project_file(path, "tables", table_writer=stub_writer)
    assert path.is_file()
    with pytest.raises(FileExistsError):
        create_dbase_project_file(path, "tables", table_writer=stub_writer)


def test_res_not_created_as_fake_text(tmp_path):
    with pytest.raises(ValueError):
        create_dbase_project_file(tmp_path / "binary.res", "resources")
    assert not (tmp_path / "binary.res").exists()


def test_integrated_paths_in_main_project_tree():
    # Beschränkt auf einfache Quelltext-/AST-Checks, da Qt5 hier nicht installiert ist.
    ast.parse(MAIN)
    for line in (
        "self._show_project_dbase_root_menu(item, position)",
        "self._new_dbase_project_file(role, target)",
        "QFileDialog.AcceptOpen", "QFileDialog.AnyFile",
        "self._add_project_dbase_entry(role, path, title=path.name)",
        'self._add_project_resource_entry(\n                    "dbase", target, path, title=path.name',
        'self.open_project_item(child)',
        'self.project_tree.itemClicked.connect(self._on_project_c64_leaf_clicked)',
        'self.open_document(path, language_override="dbase")',
        '"Datei ist keine gültige Programm-Datei"',
    ):
        assert line in MAIN, line
