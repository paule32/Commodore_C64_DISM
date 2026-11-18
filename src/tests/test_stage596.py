"""Stage 596: named project profiles, persistence, scope and Qt GUI contracts.

The pure unit tests deliberately do not require PyQt5: GUI callbacks are
isolated from their containing class with Python's AST and small Qt doubles.
"""
import ast
import configparser
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))
import project_named_targets as named


class FakeSignal:
    def __init__(self):
        self.handlers = []

    def connect(self, callback):
        self.handlers.append(callback)


class FakeCombo:
    def __init__(self, *_args):
        self.items = []
        self.index = -1
        self._signals_blocked = False
        self.currentIndexChanged = FakeSignal()

    def blockSignals(self, new):
        previous = self._signals_blocked
        self._signals_blocked = bool(new)
        return previous

    def clear(self):
        self.items = []
        self.index = -1

    def addItem(self, text, data=""):
        self.items.append([text, data])

    def setItemData(self, index, text, _role):
        pass

    def count(self):
        return len(self.items)

    def findData(self, data):
        return next((i for i, entry in enumerate(self.items) if entry[1] == data), -1)

    def setCurrentIndex(self, index):
        self.index = index

    def currentData(self):
        return self.items[self.index][1] if self.index >= 0 else None

    def setObjectName(self, name):
        pass

    def setSizePolicy(self, *args):
        pass

    def setToolTip(self, text):
        pass

    def setEnabled(self, enabled):
        self.enabled = enabled


class FakeNode:
    def __init__(self, text, path="", kind="file", parent=None):
        self.name = text
        self.path = path
        self.kind = kind
        self._parent = parent

    def data(self, column, role):
        if role == 302 + 32:  # unused
            return None
        if role == 300 + 32:
            return None
        if role == 302 + 256:
            return self.path
        return None

    def text(self, col):
        return self.name

    def childCount(self):
        return 0

    def parent(self):
        return self._parent


class FakeIterator:
    def __init__(self, tree):
        self.nodes = tree.items
        self.index = 0

    def value(self):
        return self.nodes[self.index] if self.index < len(self.nodes) else None

    def __iadd__(self, step):
        self.index += step
        return self


def extracted_class():
    code = (ROOT / "d64_dism.py").read_text(encoding="utf-8")
    code = code.replace("lazy import ", "import ").replace("lazy from ", "from ")
    tree = ast.parse(code)
    original = next(node for node in ast.walk(tree)
                    if isinstance(node, ast.ClassDef) and node.name == "ExplorerWindow")
    new_methods = [node for node in original.body if isinstance(node, ast.FunctionDef)
                   and node.name.startswith("_project_named_")]
    obj = ast.ClassDef(name="TestExplorer", bases=[], keywords=[], body=new_methods,
                       decorator_list=[])
    module = ast.Module(body=[ast.ImportFrom(module="__future__",
                       names=[ast.alias(name="annotations")], level=0), obj], type_ignores=[])
    ast.fix_missing_locations(module)

    class Qt:
        UserRole = 256
        ToolTipRole = 3

    env = {
        "Qt": Qt,
        "QComboBox": FakeCombo,
        "QTreeWidgetItemIterator": FakeIterator,
        "NAMED_PROJECT_LANGUAGES": named.LANGUAGES,
        "NAMED_PROJECT_LANGUAGE_IDS": named.LANGUAGE_IDS,
        "normalize_named_project_names": named.normalize_names,
        "normalize_named_project_selection": named.normalize_selection,
        "named_project_leaf_key": named.leaf_key,
        "PROJECT_NAMED_NAMES_KEY": named.NAMES_KEY,
        "PROJECT_NAMED_SELECTED_KEY": named.SELECTED_KEY,
        "PROJECT_NAMED_ASSIGNMENTS_KEY": named.ASSIGNMENTS_KEY,
        "PROJECT_NODE_MARKER_ROOT": "marker_root",
        "PROJECT_NODE_MARKER_FILE": "marker_file",
        "PROJECT_NODE_MARKER_LINE": "marker_line",
    }
    exec(compile(module, "test-explorer", "exec"), env)
    return env["TestExplorer"]


class Stage596Tests(unittest.TestCase):
    def test_legacy_ini_has_empty_named_profiles(self):
        parser = configparser.ConfigParser(interpolation=None)
        parser["Project"] = {"Version": "2"}
        names, selection, assignments = named.decode_names(parser)
        self.assertEqual(selection, ("", ""))
        self.assertFalse(assignments)
        self.assertTrue(all(not value for value in names.values()))

    def test_names_selection_assignments_roundtrip(self):
        parser = configparser.ConfigParser(interpolation=None)
        parser.optionxform = str
        names = {"basic": "Foo", "pascal": "Prüf DLL", "lisp": "Alpha"}
        assignment_key = named.leaf_key(r"C:\Quelle\Test.pas", "pascal_source",
                                        ["Pascal-Programme", "Windows PE32", "Module"])
        named.encode_names(parser, names, ("pascal", "library"), {assignment_key: "pascal"})
        contents = __import__("io").StringIO()
        parser.write(contents)
        restored = configparser.ConfigParser(interpolation=None)
        restored.optionxform = str
        restored.read_string(contents.getvalue())
        got_names, selected, assignments = named.decode_names(restored)
        self.assertEqual(got_names["pascal"], "Prüf DLL")
        self.assertEqual(selected, ("pascal", "library"))
        self.assertEqual(assignments[assignment_key], "pascal")

    def test_file_assignment_keys_are_project_relative_for_save_as(self):
        project = Path("/tmp/stage596/demo.pro")
        key = named.leaf_key("/tmp/stage596/src/Modul.pas", "pascal_source",
                             ["Pascal", "PE32", "Module"])
        encode_path = lambda path, project_path: str(Path(path).relative_to(project_path.parent))
        decode_path = lambda path, project_path: str(project_path.parent / path)
        stored = named.rebase_leaf_key(key, project, to_storage=True,
                                       path_converter=encode_path)
        self.assertIn("src/modul.pas", stored)
        restored = named.rebase_leaf_key(stored, project, to_storage=False,
                                         path_converter=decode_path)
        self.assertEqual(restored, key)

    def test_invalid_metadata_is_ignored(self):
        parser = configparser.ConfigParser(interpolation=None)
        parser.optionxform = str
        parser[named.NAMES_SECTION] = {"Names": "broken JSON", "Selection": "{}"}
        parser[named.ASSIGNMENTS_SECTION] = {
            "Item0001": '{"language":"untrusted", "key":"abc"}',
            "Item0002": 'not-json',
        }
        names, selected, assignments = named.decode_names(parser)
        self.assertEqual(selected, ("", ""))
        self.assertEqual(assignments, {})
        self.assertEqual(names["basic"], "")

    def test_duplicate_project_names_are_distinguished_by_language_id(self):
        names = named.normalize_names({"basic": "Foo", "pascal": "Foo"})
        self.assertEqual(names["basic"], names["pascal"])
        self.assertNotEqual(named.normalize_selection("basic|program"),
                            named.normalize_selection("pascal|program"))

    def test_assignment_key_is_stable_and_branch_specific(self):
        pe32 = named.leaf_key("C:/foo/test.pas", "pascal_source", ["Pascal", "PE32"])
        pe64 = named.leaf_key("C:/foo/test.pas", "pascal_source", ["Pascal", "PE64"])
        same = named.leaf_key(r"c:\foo\test.pas", "pascal_source", ["Pascal", "PE32"])
        self.assertNotEqual(pe32, pe64)
        self.assertEqual(pe32, same)

    def test_project_selection_list_displays_both_kinds(self):
        Explorer = extracted_class()
        state = Explorer()
        state.project_name_combo = FakeCombo()
        state._named_project_names = named.normalize_names({"basic": "Foo", "pascal": "Werkzeug"})
        state._named_project_selected = ("pascal", "library")
        state._project_named_refresh_selection()
        self.assertEqual(state.project_name_combo.items[1][0], "Programm: Foo")
        self.assertEqual(state.project_name_combo.items[2][0], "Bibliothek: Foo")
        self.assertEqual(state.project_name_combo.currentData(), "pascal|library")
        self.assertEqual(state._project_named_current_scope(), ("pascal", "library"))

    def test_save_names_and_assignments_on_project_entries(self):
        Explorer = extracted_class()
        state = Explorer()
        state._named_project_names = named.normalize_names({"basic": "Foo"})
        state._named_project_selected = ("basic", "program")
        # Leaf is fake and self._project_named_leaf_key is supplied to simplify Qt metadata.
        leaf = SimpleNamespace()
        state.project_tree = SimpleNamespace(items=[leaf])
        state._project_named_is_file_leaf = lambda item: True
        state._project_named_leaf_key = lambda item: "leaf-123"
        state._named_project_assignments = {"leaf-123": "basic", "deleted": "basic"}
        entries = {}
        state._project_named_entries(entries)
        self.assertEqual(entries[named.NAMES_KEY], [{"language": "basic", "name": "Foo"}])
        self.assertEqual(entries[named.SELECTED_KEY], [{"language": "basic", "kind": "program"}])
        self.assertEqual(entries[named.ASSIGNMENTS_KEY], [{"key": "leaf-123", "language": "basic"}])

    def test_dialog_cancel_leaves_existing_name_untouched(self):
        Explorer = extracted_class()
        state = Explorer()
        changes = []
        class Edit:
            def text(self): return "Foo"
            def setText(self, text): changes.append(text)
        state.project_name_edits = {"basic": Edit()}
        class QLineEdit:
            Normal = 0
        class Dialog:
            @staticmethod
            def getText(*_args): return ("Bar", False)
        Explorer._project_named_edit_dialog.__globals__["QInputDialog"] = Dialog
        Explorer._project_named_edit_dialog.__globals__["QLineEdit"] = QLineEdit
        state._project_named_edit_dialog("basic")
        self.assertEqual(changes, [])

    def test_selected_project_filters_unassigned_leaves(self):
        Explorer = extracted_class()
        state = Explorer()
        state._named_project_names = named.normalize_names({"basic": "Foo"})
        state._named_project_selected = ("basic", "program")
        state._named_project_assignments = {"basic-file": "basic", "pas-file": "pascal"}
        state._project_named_leaf_key = lambda item: item
        self.assertTrue(state._project_named_matches_item("basic-file"))
        self.assertFalse(state._project_named_matches_item("pas-file"))
        self.assertFalse(state._project_named_matches_item("missing"))
        state._named_project_selected = ("", "")
        self.assertTrue(state._project_named_matches_item("missing"))

    def test_source_has_required_editors_and_build_connections(self):
        source = (ROOT / "d64_dism.py").read_text(encoding="utf-8")
        self.assertIn("project_name_combo.currentIndexChanged.connect", source)
        self.assertIn("self.project_tree.setColumnCount(2)", source)
        self.assertIn("self.project_tree.header().setSectionResizeMode(0, QHeaderView.Interactive)", source)
        self.assertIn("self.project_tree.header().setSectionResizeMode(1, QHeaderView.Interactive)", source)
        self.assertIn("QInputDialog.getText(", source)
        self.assertIn("_project_named_matches_item(child)", source)
        self.assertIn("build_kind = _project_kind", source)


if __name__ == "__main__":
    unittest.main()
