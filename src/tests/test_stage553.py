"""Stage 553/554 – Software-Installer-Model- und aktuelle Integrations-Regressionen.

PyQt5 ist in der Linux-Pruefumgebung nicht installiert. Native Widget-Tests
muessen zusaetzlich auf einem Windows/Qt5-System ausgefuehrt werden.
"""
import ast
import tempfile
import unittest
from pathlib import Path

from software_installer_model import (
    INSTALLER_COLUMNS, INSTALLER_FILTERS, INSTALLER_GROUPS,
    InstallerEntry, InstallerProject, entry_visible,
)


ROOT = Path(__file__).resolve().parent


class InstallerModelTests(unittest.TestCase):
    def test_exact_columns(self):
        self.assertEqual(INSTALLER_COLUMNS, (
            "Name", "Ziel", "Lokaler Pfad", "Größe", "Datum",
            "Datei Version", "Status", "Package", "Short Cut",
        ))

    def test_exact_group_actions_and_order(self):
        self.assertEqual([name for name, _ in INSTALLER_GROUPS],
                         ["Dateien", "Einstellungen", "Bildschirme", "Aktionen"])
        self.assertEqual(INSTALLER_GROUPS[0][1], (
            "Datei hinzufügen", "Pfad hinzufügen", "Elemente Löschen", "Datei Eigenschaften"
        ))
        self.assertEqual(len(INSTALLER_GROUPS[1][1]), 7)
        self.assertEqual(len(INSTALLER_GROUPS[2][1]), 4)
        self.assertEqual(len(INSTALLER_GROUPS[3][1]), 4)

    def test_filter_all_tabs_and_status(self):
        for tab in ("archive", "external"):
            self.assertTrue(entry_visible("all", tab, "Neu"))
            self.assertEqual(entry_visible("archive", tab, "Neu"), tab == "archive")
            self.assertEqual(entry_visible("external", tab, "Neu"), tab == "external")
        self.assertTrue(entry_visible("exists", "archive", "Vorhanden"))
        self.assertFalse(entry_visible("exists", "archive", "Fehlt"))
        self.assertTrue(entry_visible("missing", "external", "Fehlt"))
        self.assertFalse(entry_visible("missing", "archive", "Neu"))

    def test_add_paths_deduplicates_by_tab(self):
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory) / "test.exe"
            file.write_bytes(b"hello")
            model = InstallerProject()
            self.assertEqual(model.add_paths("archive", [str(file), str(file)]), 1)
            self.assertEqual(model.add_paths("archive", [str(file)]), 0)
            self.assertEqual(model.add_paths("external", [str(file)]), 1)
            entry = model.entries["archive"][0]
            self.assertEqual(entry.name, "test.exe")
            self.assertEqual(entry.status, "Vorhanden")
            self.assertEqual(entry.size, "5")

    def test_missing_status_and_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            missing = InstallerEntry.from_path(str(Path(directory) / "absent.o"))
            self.assertEqual(missing.status, "Fehlt")
            folder = InstallerEntry.from_path(directory)
            self.assertEqual(folder.size, "<DIR>")

    def test_delete_multiple_rows_stably(self):
        project = InstallerProject()
        project.entries["archive"] = [InstallerEntry(name=str(i)) for i in range(5)]
        self.assertEqual(project.delete_rows("archive", [1, 3, 3]), 2)
        self.assertEqual([entry.name for entry in project.entries["archive"]],
                         ["0", "2", "4"])

    def test_table_update_fields(self):
        entry = InstallerEntry()
        entry.update_from_values(list(INSTALLER_COLUMNS))
        self.assertEqual(entry.name, "Name")
        self.assertEqual(entry.shortcut, "Short Cut")
        with self.assertRaises(ValueError):
            entry.update_from_values(["only one"])

    def test_json_project_roundtrip(self):
        with tempfile.TemporaryDirectory() as directory:
            filename = Path(directory) / "demo.installer.json"
            project = InstallerProject()
            project.entries["archive"].append(
                InstallerEntry(name="main.exe", local_path=r"T:\\source\\main.exe")
            )
            project.entries["external"].append(InstallerEntry(name="readme.txt"))
            project.sections["OnStartup"] = "writeln('hello')"
            project.save(str(filename))
            restored = InstallerProject.load(str(filename))
            self.assertEqual(restored.to_dict(), project.to_dict())
            self.assertIn("d64-software-installer", filename.read_text("utf-8"))

    def test_reject_invalid_json_format_without_data_loss(self):
        with self.assertRaises(ValueError):
            InstallerProject.from_dict({"format": "other", "version": 1})
        with self.assertRaises(ValueError):
            InstallerProject.from_dict({"format": "d64-software-installer", "version": 55})


class InstallerIntegrationTests(unittest.TestCase):
    def test_widget_source_syntax(self):
        ast.parse((ROOT / "software_installer.py").read_text(encoding="utf-8"))

    def test_single_dock_splitter_and_toolbar(self):
        source = (ROOT / "software_installer.py").read_text(encoding="utf-8")
        self.assertIn('class SoftwareInstallerWorkbench(QWidget):', source)
        self.assertNotIn('class SoftwareInstallerWorkbench(QMainWindow):', source)
        self.assertNotIn('QDockWidget(', source)
        self.assertIn('self.splitter = QSplitter(Qt.Horizontal, self)', source)
        self.assertIn('self.splitter.addWidget(self.files_scroll)', source)
        self.assertIn('self.splitter.addWidget(self.tabs)', source)
        self.assertIn('main_layout.addWidget(self.filter_bar, 0)', source)
        self.assertIn('main_layout.addWidget(self.splitter, 1)', source)
        self.assertIn('width // 4', source)
        self.assertIn('self.tabs.addTab(table, title)', source)

    def test_main_menu_order_and_exclusive_lifecycle(self):
        source = (ROOT / "d64_dism.py").read_text(encoding="utf-8")
        p = source.index('self.build_menu.addAction(self.build_start_action)')
        self.assertLess(p, source.index('self.build_menu.addSeparator()', p))
        self.assertLess(source.index('self.build_menu.addSeparator()', p),
                        source.index('QAction("Software Installer", self)', p))
        self.assertIn('self._activate_exclusive_tool_workspace(dock)', source)
        self.assertIn('self._exclusive_tool_workspace_visibility_changed(', source)
        self.assertIn('installer_widget.set_dark_mode(enabled)', source)

    def test_compact_panels_two_tabs_and_context_menu(self):
        source = (ROOT / "software_installer.py").read_text(encoding="utf-8")
        self.assertIn('Qt.DownArrow', source)
        self.assertIn('Qt.UpArrow', source)
        self.assertIn('"Archiv", "archive"', source)
        self.assertIn('"Extern", "external"', source)
        self.assertIn('"Zeile hinzufügen"', source)
        self.assertIn('"Ausgewählte Zeilen löschen"', source)


if __name__ == "__main__":
    unittest.main()
