"""Stage 554: Regressionen der Ein-Dock-Installer-Architektur (Qt-frei)."""
import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MODULE = (ROOT / 'software_installer.py').read_text(encoding='utf-8')
IDE = (ROOT / 'd64_dism.py').read_text(encoding='utf-8')


class SingleInstallerDockSourceTests(unittest.TestCase):
    def test_installer_module_is_syntactically_valid(self):
        ast.parse(MODULE)

    def test_workbench_is_a_plain_widget(self):
        tree = ast.parse(MODULE)
        matches = [node for node in tree.body if isinstance(node, ast.ClassDef)
                   and node.name == 'SoftwareInstallerWorkbench']
        self.assertEqual(len(matches), 1)
        self.assertEqual(ast.unparse(matches[0].bases[0]), 'QWidget')
        self.assertNotIn('QMainWindow', [ast.unparse(base) for base in matches[0].bases])

    def test_no_nested_docking_widgets_or_dock_management(self):
        self.assertNotIn('QDockWidget(', MODULE)
        self.assertNotIn('addDockWidget(', MODULE)
        self.assertNotIn('splitDockWidget(', MODULE)
        self.assertNotIn('addToolBar(', MODULE)
        self.assertNotIn('setCentralWidget(', MODULE)

    def test_exactly_one_outer_ide_dock(self):
        start = IDE.index('def show_software_installer_dock(')
        end = IDE.index('def show_agent_0001_dock(', start)
        method = IDE[start:end]
        self.assertEqual(method.count('QDockWidget("Software Installer", self)'), 1)
        self.assertIn('dock.setWidget(self.software_installer_widget)', method)
        self.assertNotIn('files_dock', method)
        self.assertNotIn('entries_dock', method)
        self.assertIn('Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea', method)
        self.assertIn('self._activate_exclusive_tool_workspace(dock)', method)
        self.assertIn('self._expand_exclusive_tool_workspace(dock)', method)
        self.assertIn('self._exclusive_tool_workspace_visibility_changed(', method)

    def test_toolbar_is_fixed_and_above_splitter(self):
        self.assertIn('self.filter_bar = QToolBar(', MODULE)
        self.assertIn('self.filter_bar.setMovable(False)', MODULE)
        self.assertIn('self.filter_bar.setFloatable(False)', MODULE)
        self.assertIn('main_layout.addWidget(self.filter_bar, 0)', MODULE)
        self.assertIn('main_layout.addWidget(self.splitter, 1)', MODULE)
        self.assertLess(MODULE.index('main_layout.addWidget(self.filter_bar, 0)'),
                        MODULE.index('main_layout.addWidget(self.splitter, 1)'))
        self.assertIn('self.filter_combo.currentIndexChanged.connect(self.apply_filter)', MODULE)

    def test_splitter_contains_only_left_and_right_widgets(self):
        self.assertIn('self.splitter = QSplitter(Qt.Horizontal, self)', MODULE)
        self.assertIn('self.splitter.setChildrenCollapsible(False)', MODULE)
        self.assertEqual(MODULE.count('self.splitter.addWidget('), 2)
        self.assertIn('self.splitter.addWidget(self.files_scroll)', MODULE)
        self.assertIn('self.splitter.addWidget(self.tabs)', MODULE)
        self.assertLess(MODULE.index('self.splitter.addWidget(self.files_scroll)'),
                        MODULE.index('self.splitter.addWidget(self.tabs)'))

    def test_initial_ratio_only_applied_once(self):
        self.assertIn('self._initial_split_applied = False', MODULE)
        self.assertIn('width // 4', MODULE)
        self.assertIn('self._initial_split_applied = True', MODULE)
        self.assertIn('if self._initial_split_applied:', MODULE)
        self.assertIn('self.splitter.setSizes([left, right])', MODULE)

    def test_all_four_panels_and_both_tables_remain(self):
        self.assertIn('for title, buttons in INSTALLER_GROUPS:', MODULE)
        self.assertIn('self.panels[title] = panel', MODULE)
        self.assertIn('for title, key in (("Archiv", "archive"), ("Extern", "external")):', MODULE)
        self.assertIn('self.tabs.addTab(table, title)', MODULE)
        self.assertIn('self.setHorizontalHeaderLabels(list(INSTALLER_COLUMNS))', MODULE)
        self.assertIn('self.setContextMenuPolicy(Qt.CustomContextMenu)', MODULE)

    def test_theme_handles_splitter_and_filter_bar(self):
        self.assertIn('QSplitter#softwareInstallerSplitter::handle', MODULE)
        self.assertIn('QToolBar#softwareInstallerFilterBar', MODULE)
        self.assertIn('QFrame#installerPanelHeader', MODULE)
        self.assertIn('QTableWidget#installerTable', MODULE)
        self.assertIn('installer_widget.set_dark_mode(enabled)', IDE)

    def test_no_model_modifications(self):
        model = (ROOT / 'software_installer_model.py').read_text(encoding='utf-8')
        self.assertIn('INSTALLER_GROUPS = (', model)
        self.assertIn('INSTALLER_FILTERS = (', model)
        self.assertIn('class InstallerProject:', model)


if __name__ == '__main__':
    unittest.main()
