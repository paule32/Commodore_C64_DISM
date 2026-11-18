"""Stage 601: Pascal project tree flattening, legacy .pro IDs and build menus.

No GUI backend required; run the actual AST of the tree-building branches
against minimal Qt tree item doubles and verify the architecture metadata.
"""
import ast
import re
import unittest
from pathlib import Path

from project_named_targets import leaf_key, legacy_pascal_ancestry

SOURCE_PATH = Path(__file__).with_name("d64_dism.py")
SOURCE = SOURCE_PATH.read_text(encoding="utf-8")
# Python 3.15's soft-keyword lazy imports are unrelated to this Qt tree test.
MODULE = ast.parse(re.sub(r"(?m)^lazy from ", "from ", SOURCE))


def method_ast(name):
    return next(n for n in ast.walk(MODULE)
                if isinstance(n, ast.FunctionDef) and n.name == name)


def extracted_function(name, extra_globals=None):
    node = method_ast(name)
    namespace = dict(extra_globals or {})
    exec(compile(ast.Module(body=[node], type_ignores=[]),
                 str(SOURCE_PATH), "exec"), namespace)
    return namespace[name]


class Qt:
    UserRole = 256


class Item:
    def __init__(self, parent, texts):
        self._parent = parent if isinstance(parent, Item) else None
        self.title = texts[0]
        self.children = []
        self.metadata = {}
        if self._parent is not None:
            self._parent.children.append(self)

    def setData(self, col, role, value):
        self.metadata[(col, role)] = value

    def data(self, col, role):
        return self.metadata.get((col, role))

    def setIcon(self, *args):
        pass

    def setToolTip(self, *args):
        pass

    def setExpanded(self, *args):
        pass

    def text(self, col):
        return self.title

    def childCount(self):
        return len(self.children)

    def parent(self):
        return self._parent


class DummySelf:
    def __init__(self):
        self.project_pascal_group_nodes = {}
        self.project_pascal_table_nodes = {}
        self.project_windows_target_nodes = {}
        self.project_resource_nodes = {}
        self.added = []

    def _add_project_pascal_target_entry(self, parent, path, *, title, mark_modified):
        self.added.append(("source", parent.title, str(path), title, mark_modified))
        return Item(parent, [title or path.name])

    def _add_project_pascal_table_entry(self, parent, path, *, title, mark_modified):
        self.added.append(("table", parent.title, str(path), title, mark_modified))
        return Item(parent, [title or path.name])

    def _add_project_resource_entry(self, language, target, path, *, title, mark_modified):
        parent = self.project_resource_nodes[(language, target)]
        self.added.append(("resource", parent.title, str(path), title, mark_modified))
        return Item(parent, [title or path.name])


class Menu:
    def __init__(self):
        self.actions = []

    def addSeparator(self):
        self.actions.append("separator")

    def addMenu(self, name):
        child = Menu()
        self.actions.append((name, child))
        return child

    def addAction(self, name):
        action = object()
        self.actions.append((name, action))
        return action


class Stage601Tests(unittest.TestCase):
    def _build_branches(self, language):
        reset = method_ast("reset_project_tree")
        # Execute actual source AST, limited to the two language-specific
        # construction branches so the complete Qt application isn't needed.
        branches = [n for n in ast.walk(reset)
                    if isinstance(n, ast.If) and
                    ((isinstance(n.test, ast.Compare) and
                      isinstance(n.test.left, ast.Name) and
                      n.test.left.id == "key" and
                      isinstance(n.test.comparators[0], ast.Constant) and
                      n.test.comparators[0].value == "pascal") or
                     (isinstance(n.test, ast.BoolOp) and
                      "PROJECT_WINDOWS_RESOURCE_LANGUAGES" in ast.unparse(n.test)))]
        self.assertEqual(len(branches), 2)
        tree_code = compile(ast.Module(body=branches, type_ignores=[]),
                            str(SOURCE_PATH), "exec")
        root = Item(None, ["Pascal-Programme" if language == "pascal" else "dBASE Programme"])
        fake = DummySelf()
        values = {
            "pm32": [{"path": "/prj/m32.pas", "title": "m32.pas"}],
            "pu32": [{"path": "/prj/u32.pas", "title": "u32.pas"}],
            "pt32": [{"path": "/prj/t32.dbf", "title": "t32.dbf"}],
            "pr32": [{"path": "/prj/r32.rc", "title": "r32.rc"}],
            "pm64": [{"path": "/prj/m64.pas", "title": "m64.pas"}],
            "pu64": [{"path": "/prj/u64.pas", "title": "u64.pas"}],
            "pt64": [{"path": "/prj/t64.dbf", "title": "t64.dbf"}],
            "pr64": [{"path": "/prj/r64.rc", "title": "r64.rc"}],
        }
        ns = {
            "key": language, "title": language, "root": root,
            "self": fake, "Qt": Qt, "QTreeWidgetItem": Item,
            "Path": Path, "folder_icon": None, "values": values,
            "PROJECT_NODE_PASCAL_MODULE_ROOT": "pascal_module_root",
            "PROJECT_NODE_PASCAL_UNIT_ROOT": "pascal_unit_root",
            "PROJECT_NODE_PASCAL_TABLE_ROOT": "pascal_table_root",
            "PROJECT_NODE_RESOURCE_ROOT": "resource_root",
            "PROJECT_NODE_WINDOWS_TARGET": "windows_target",
            "PROJECT_PASCAL_TARGET_ENTRY_KEYS": {
                ("pe32", "modules"): "pm32", ("pe32", "units"): "pu32",
                ("pe64", "modules"): "pm64", ("pe64", "units"): "pu64"},
            "PROJECT_PASCAL_TABLE_ENTRY_KEYS": {"pe32": "pt32", "pe64": "pt64"},
            "PROJECT_WINDOWS_RESOURCE_ENTRY_KEYS": {
                ("pascal", "pe32"): "pr32", ("pascal", "pe64"): "pr64",
                ("dbase", "pe32"): "pr32", ("dbase", "pe64"): "pr64"},
            "PROJECT_WINDOWS_RESOURCE_LANGUAGES": {"pascal", "dbase"},
        }
        exec(tree_code, ns)
        return root, fake

    def test_pascal_eight_siblings_and_full_files(self):
        root, state = self._build_branches("pascal")
        self.assertEqual([n.title for n in root.children], [
            "Windows PE32 Module", "Windows PE32 Units",
            "Windows PE32 Tabellen", "Windows PE32 Ressourcen",
            "Windows PE32+ Module", "Windows PE32+ Units",
            "Windows PE32+ Tabellen", "Windows PE32+ Ressourcen",
        ])
        self.assertTrue(all(n.parent() is root for n in root.children))
        self.assertTrue(all(n.childCount() == 1 for n in root.children))
        self.assertEqual({n.data(0, Qt.UserRole + 305) for n in root.children[:4]}, {"pe32"})
        self.assertEqual({n.data(0, Qt.UserRole + 305) for n in root.children[4:]}, {"pe64"})
        self.assertEqual([record[0] for record in state.added],
                         ["source", "source", "table", "resource"] * 2)
        self.assertTrue(all(record[-1] is False for record in state.added))

    def test_non_pascal_resource_tree_unchanged(self):
        root, state = self._build_branches("dbase")
        self.assertEqual([n.title for n in root.children], ["Windows PE32", "Windows PE32+"])
        self.assertEqual([n.children[0].title for n in root.children], ["Resourcen", "Resourcen"])
        self.assertEqual(len(state.added), 2)

    def test_old_project_assignment_ids_identical_for_all_pascal_types(self):
        roles = [("Module", "Module"), ("Units", "Unit"),
                 ("Tabellen", "Tabellen"), ("Ressourcen", "Resourcen")]
        for target in ("Windows PE32", "Windows PE32+"):
            for new_role, old_role in roles:
                with self.subTest(target=target, role=new_role):
                    old = ["Pascal-Programme", target, old_role]
                    new = ["Pascal-Programme", target + " " + new_role]
                    self.assertEqual(legacy_pascal_ancestry(new), old)
                    self.assertEqual(
                        leaf_key("C:/test/Foo.pas", "pascal_target_source", old),
                        leaf_key("C:/test/Foo.pas", "pascal_target_source",
                                 legacy_pascal_ancestry(new)))

    def test_non_pascal_ancestry_and_namespaced_file_unchanged(self):
        other = ["dBASE Programme", "Windows PE32 Module"]
        self.assertEqual(legacy_pascal_ancestry(other), other)
        ns = ["Pascal-Programme", "Windows PE32+ Units", "System"]
        self.assertEqual(legacy_pascal_ancestry(ns),
                         ["Pascal-Programme", "Windows PE32+", "Unit", "System"])

    def test_pascal_build_menu_routed_to_correct_architecture(self):
        class Builder:
            def __init__(self): self.called = []
            def build_project_pascal_target(self, target, build_kind):
                self.called.append((target, build_kind))
            def start_project_pascal_target(self, target):
                self.called.append((target, "start"))
        obj = Builder()
        add = extracted_function("_project_pascal_flat_build_actions", {"Qt": Qt})
        invoke = extracted_function("_project_pascal_flat_build_chosen", {"Qt": Qt})
        for target in ("pe32", "pe64"):
            item = Item(None, ["Windows category"])
            item.setData(0, Qt.UserRole + 301, "pascal")
            item.setData(0, Qt.UserRole + 305, target)
            actions = add(obj, Menu(), item)
            self.assertEqual(len(actions), 3)
            for action, (arch, mode) in actions.items():
                self.assertTrue(invoke(obj, action, actions))
            self.assertEqual(obj.called[-3:], [(target, "program"),
                                               (target, "library"), (target, "start")])
        not_pascal = Item(None, ["dBASE"])
        not_pascal.setData(0, Qt.UserRole + 301, "dbase")
        not_pascal.setData(0, Qt.UserRole + 305, "pe32")
        self.assertEqual(add(obj, Menu(), not_pascal), {})

    def test_build_actions_in_all_relevant_context_menus(self):
        for name in ("_show_project_pascal_group_menu",
                     "_show_project_pascal_table_root_menu",
                     "_show_project_resource_root_menu"):
            node = method_ast(name)
            self.assertIn("_project_pascal_flat_build_actions", ast.unparse(node))
            self.assertIn("_project_pascal_flat_build_chosen", ast.unparse(node))

    def test_generic_delete_never_removes_new_direct_pascal_nodes(self):
        for name in ("clear_project_entries", "show_project_context_menu"):
            function = method_ast(name)
            source = ast.unparse(function)
            self.assertIn("PROJECT_NODE_PASCAL_MODULE_ROOT", source)
            self.assertIn("PROJECT_NODE_PASCAL_UNIT_ROOT", source)
            self.assertIn("PROJECT_NODE_RESOURCE_ROOT", source)
            self.assertIn("PROJECT_NODE_PASCAL_TABLE_ROOT", source)


if __name__ == "__main__":
    unittest.main()
