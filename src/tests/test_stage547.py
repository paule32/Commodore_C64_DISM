"""Stage 547: Regressionstests der zentralen Speicherroutine, ohne Qt-Bedarf.

Die relevanten Methoden werden unmittelbar aus d64_dism.py extrahiert, damit
kein zweites, abweichendes Speichermodell getestet wird. Die IDE benutzt PyQt5;
diese Tests ersetzen keinen nativen GUI-Test unter Windows.
"""
from __future__ import annotations

import ast
import os
from pathlib import Path
import re
import tempfile
from types import SimpleNamespace
import unittest


class TextBuffer:
    def __init__(self, text="", modified=False):
        self.text = text
        self.modified = modified

    def document(self):
        return self

    def isModified(self):
        return self.modified

    def setModified(self, value):
        self.modified = value

    def toPlainText(self):
        return self.text


class FakeDocument:
    def __init__(self, path, text, *, modified=True, asm=None, asm_modified=False):
        self.path = path
        self.display_name = path.name if path is not None else "Ohne Name"
        self.raw_editor = TextBuffer(text, modified)
        self.hex_editor = SimpleNamespace(is_modified=False)
        self.generated_assembly_editor = TextBuffer(asm or "", asm_modified)
        self.generated_assembly_path = None
        self.build_target = "pe32"
        self._is_new_c64_project_file = False
        self._last_modified_state = True

    @property
    def source_is_modified(self):
        return self.raw_editor.isModified() or self.hex_editor.is_modified

    @property
    def is_modified(self):
        return self.source_is_modified or self.generated_assembly_editor.isModified()

    def _view_modification_changed(self, _value):
        self._last_modified_state = self.is_modified


class FakeTabs:
    def __init__(self, documents, current_index=0):
        self.documents = documents
        self.current = documents[current_index] if documents else None

    def count(self):
        return len(self.documents)

    def widget(self, index):
        return self.documents[index]

    def currentWidget(self):
        return self.current

    def indexOf(self, document):
        try:
            return self.documents.index(document)
        except ValueError:
            return -1

    def setCurrentWidget(self, document):
        self.current = document


class FakeStatus:
    def __init__(self):
        self.messages = []

    def showMessage(self, text, *_):
        self.messages.append(text)


def load_real_save_methods():
    path = Path(__file__).with_name("d64_dism.py")
    source = re.sub(r"(?m)^(\s*)lazy from ", r"\1from ", path.read_text(encoding="utf-8"))
    module = ast.parse(source, filename=str(path))
    explorer = next(node for node in ast.walk(module) if isinstance(node, ast.ClassDef) and node.name == "ExplorerWindow")
    names = {
        "_write_editor_bytes_verified",
        "_save_generated_assembly_editor",
        "_save_editor_document_parts",
        "save_all_open_documents",
        "_save_project_close_changes",
    }
    selected = [node for node in explorer.body if isinstance(node, ast.FunctionDef) and node.name in names]
    assert {n.name for n in selected} == names
    synthetic = ast.Module(body=[ast.ClassDef(name="ActualSaveMethods", bases=[], keywords=[], body=selected, decorator_list=[])], type_ignores=[])
    ast.fix_missing_locations(synthetic)
    namespace = {
        "Path": Path,
        "os": os,
        "tempfile": tempfile,
        "DocumentEditor": FakeDocument,
    }
    exec(compile(synthetic, str(path), "exec"), namespace)
    return namespace["ActualSaveMethods"]


ActualSaveMethods = load_real_save_methods()


class Harness(ActualSaveMethods):
    def __init__(self, documents):
        self.document_tabs = FakeTabs(documents)
        self._save_all_in_progress = False
        self.messages = []
        self.errors = []
        self.status = FakeStatus()
        self.project_modified = False
        self.current_project_path = None
        self.dbase_form_modified = False
        self._dbase_form_asm_editors = {}
        self.dbase_form_assembly_tabs = None
        self.html_editor_widget = None
        self.windows_resource_editor_widget = None
        self.apache_server_widget = None
        self.e_baukasten_widget = None
        self.save_project_calls = 0
        self.fail_paths = set()
        self.saved_tabs = []

    def log(self, text):
        self.messages.append(text)

    def show_error(self, title, text):
        self.errors.append((title, text))

    def statusBar(self):
        return self.status

    def _update_document_tab(self, document):
        self.saved_tabs.append(document)

    def _find_open_document(self, target):
        for doc in self.document_tabs.documents:
            if doc.path is not None and doc.path.resolve() == Path(target).resolve():
                return doc
        return None

    def _save_document(self, document, *, save_as=False):
        assert not save_as
        if document.path in self.fail_paths:
            self.show_error("Speichern fehlgeschlagen", str(document.path))
            return False
        self._write_editor_bytes_verified(document.path, document.raw_editor.toPlainText().encode("utf-8"))
        document.raw_editor.setModified(False)
        return True

    def save_project(self):
        self.save_project_calls += 1
        self.project_modified = False
        return True

    def project_has_entries(self):
        return False


class SaveAllTests(unittest.TestCase):
    def test_two_open_pascal_documents_save_both(self):
        with tempfile.TemporaryDirectory() as root:
            path1 = Path(root) / "unitA.pas"
            path2 = Path(root) / "unitB.pas"
            path1.write_text("alt 1", encoding="utf-8")
            path2.write_text("alt 2", encoding="utf-8")
            a, b = FakeDocument(path1, "neu 1"), FakeDocument(path2, "neu 2")
            host = Harness([a, b])
            self.assertTrue(host.save_all_open_documents())
            self.assertEqual(path1.read_text(encoding="utf-8"), "neu 1")
            self.assertEqual(path2.read_text(encoding="utf-8"), "neu 2")
            self.assertFalse(a.is_modified or b.is_modified)
            self.assertIs(host.document_tabs.currentWidget(), a)
            self.assertIn("2 Dokument(e)", host.status.messages[-1])

    def test_background_tab_modified_without_switching(self):
        with tempfile.TemporaryDirectory() as root:
            path1, path2 = Path(root)/"front.pas", Path(root)/"back.pas"
            path1.write_text("unverändert", encoding="utf-8")
            path2.write_text("alt", encoding="utf-8")
            a = FakeDocument(path1, "unverändert", modified=False)
            b = FakeDocument(path2, "aus anderem Tab", modified=True)
            host = Harness([a,b])
            self.assertTrue(host.save_all_open_documents())
            self.assertEqual(path1.read_text(encoding="utf-8"), "unverändert")
            self.assertEqual(path2.read_text(encoding="utf-8"), "aus anderem Tab")
            self.assertIn("1 Dokument(e)", host.status.messages[-1])

    def test_failed_file_does_not_prevent_other_files(self):
        with tempfile.TemporaryDirectory() as root:
            a_path, b_path = Path(root)/"a.pas", Path(root)/"b.pas"
            a_path.write_text("alte a", encoding="utf-8")
            b_path.write_text("alte b", encoding="utf-8")
            a, b = FakeDocument(a_path, "NEU A"), FakeDocument(b_path, "NEU B")
            host = Harness([a,b])
            host.fail_paths.add(a_path)
            self.assertFalse(host.save_all_open_documents())
            self.assertEqual(a_path.read_text(encoding="utf-8"), "alte a")
            self.assertEqual(b_path.read_text(encoding="utf-8"), "NEU B")
            self.assertTrue(a.is_modified)
            self.assertFalse(b.is_modified)
            self.assertIn("1 fehlgeschlagen", host.status.messages[-1])

    def test_generated_asm_is_separate_from_pascal(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root)/"main.pas"
            path.write_text("program Keep; begin end.", encoding="utf-8")
            doc = FakeDocument(path, "program Keep; begin end.", modified=False,
                               asm="mov eax, 42\n", asm_modified=True)
            host = Harness([doc])
            self.assertTrue(host.save_all_open_documents())
            self.assertEqual(path.read_text(encoding="utf-8"), "program Keep; begin end.")
            self.assertEqual((Path(root)/"main.generated.pe32.asm").read_text(encoding="utf-8"), "mov eax, 42\n")
            self.assertFalse(doc.is_modified)

    def test_project_html_resource_apache_circuit(self):
        with tempfile.TemporaryDirectory():
            host = Harness([])
            html = TextBuffer("<p>neu</p>", True)
            config = TextBuffer("Listen 80", True)
            called = []
            host.html_editor_widget = SimpleNamespace(editor=html, save_document=lambda: called.append("html") or html.setModified(False) or True)
            host.windows_resource_editor_widget = SimpleNamespace(_dirty=True, save=lambda: called.append("resource") or True)
            host.apache_server_widget = SimpleNamespace(apache_config_editor=config, save_current_config=lambda: called.append("apache") or config.setModified(False) or True)
            host.e_baukasten_widget = SimpleNamespace(dirty=True, save_file=lambda _: called.append("circuit") or True)
            host.project_modified = True
            self.assertTrue(host.save_all_open_documents())
            self.assertEqual(called, ["html", "resource", "apache", "circuit"])
            self.assertEqual(host.save_project_calls, 1)
            self.assertIn("5 Dokument(e)",host.status.messages[-1])

    def test_reentrant_save_is_rejected(self):
        host = Harness([])
        host._save_all_in_progress = True
        self.assertFalse(host.save_all_open_documents())

    def test_verified_write_keeps_exact_bytes(self):
        with tempfile.TemporaryDirectory() as root:
            file = Path(root)/"example.pas"
            bytestr = "äöü\nzweite Zeile".encode("utf-8")
            Harness._write_editor_bytes_verified(file, bytestr)
            self.assertEqual(file.read_bytes(), bytestr)
            self.assertEqual(len(list(Path(root).glob("*.tmp"))), 0)

    def test_save_on_project_close_uses_shared_routine(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root)/"unit.pas"
            d = FakeDocument(path,"test")
            host = Harness([d])
            host.current_project_path = Path(root)/"project.pro"
            self.assertTrue(host._save_project_close_changes())
            self.assertEqual(host.save_project_calls, 1)
            self.assertEqual(path.read_text(encoding="utf-8"), "test")

    def test_both_source_and_generated_asm_are_saved(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root)/"both.pas"
            path.write_text("alter Pascal-Code", encoding="utf-8")
            doc = FakeDocument(path, "neuer Pascal-Code", modified=True, asm="mov eax, 7", asm_modified=True)
            host = Harness([doc])
            self.assertTrue(host.save_all_open_documents())
            self.assertEqual(path.read_text(encoding="utf-8"), "neuer Pascal-Code")
            self.assertEqual(doc.generated_assembly_path.read_text(encoding="utf-8"), "mov eax, 7")
            self.assertFalse(doc.is_modified)

    def test_failed_asm_write_keeps_asm_modified(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root)/"both.pas"
            path.write_text("alt", encoding="utf-8")
            blocker = Path(root)/"no_directory"
            blocker.write_text("ordinary file", encoding="utf-8")
            doc = FakeDocument(path, "neu", modified=True, asm="mov eax, 7", asm_modified=True)
            doc.generated_assembly_path = blocker/"test.asm"
            host = Harness([doc])
            self.assertFalse(host.save_all_open_documents())
            self.assertEqual(path.read_text(encoding="utf-8"), "neu")
            self.assertTrue(doc.generated_assembly_editor.isModified())
            self.assertIn("1 fehlgeschlagen", host.status.messages[-1])

    def test_empty_save_does_not_write_anything(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root)/"already_saved.pas"
            path.write_text("unverändert", encoding="utf-8")
            host = Harness([FakeDocument(path, "unverändert", modified=False)])
            self.assertTrue(host.save_all_open_documents())
            self.assertEqual(host.status.messages[-1], "Keine ungespeicherten Änderungen gefunden.")

    def test_external_dbf_error_is_not_reported_as_success(self):
        host = Harness([])
        self.assertFalse(host.save_all_open_documents(additional_failures=("dBase-Tabelle",)))
        self.assertIn("dBase-Tabelle", host.status.messages[-1])
        self.assertTrue(host.save_all_open_documents(additional_saved=1))
        self.assertIn("1 Dokument(e)", host.status.messages[-1])

    def test_multiple_dbase_assembler_tabs(self):
        host = Harness([])
        widgets = [object(), object()]
        editors = [TextBuffer("a", True), TextBuffer("b", True)]
        host.dbase_form_assembly_tabs = FakeTabs(widgets)
        host._dbase_form_asm_editors = dict(zip(widgets, editors))
        visited = []
        def save_asm(widget):
            visited.append(widget)
            host._dbase_form_asm_editors[widget].setModified(False)
            return True
        host._dbase_form_asm_save_widget = save_asm
        self.assertTrue(host.save_all_open_documents())
        self.assertEqual(visited, widgets)
        self.assertTrue(all(not editor.isModified() for editor in editors))

    def test_main_action_routes_to_save_all(self):
        source=Path(__file__).with_name("d64_dism.py").read_text(encoding="utf-8")
        self.assertIn('self.save_file_action.triggered.connect(self._save_file_contextual)',source)
        self.assertIn('self.save_all_open_documents()\n\n        def _ensure_dbase_table_designer',source)
        self.assertNotIn('shortcut=QKeySequence.Save, object_name="html_editor_save_action"',source)


if __name__ == "__main__":
    unittest.main(verbosity=2)
