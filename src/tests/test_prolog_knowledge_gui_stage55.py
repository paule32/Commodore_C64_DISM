from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / 'd64_dism.py').read_text(encoding='utf-8')


class ProjectKnowledgeDatabaseTests(unittest.TestCase):
    def test_project_persistence_has_separate_knowledge_section(self):
        self.assertIn('PROJECT_PROLOG_KNOWLEDGE_KEY = "__prolog_knowledge_databases__"', SOURCE)
        self.assertIn('knowledge_section = "Category.prolog.knowledge"', SOURCE)
        self.assertIn('entries[PROJECT_PROLOG_KNOWLEDGE_KEY].append({', SOURCE)

    def test_project_tree_has_protected_knowledge_node(self):
        self.assertIn('PROJECT_NODE_PROLOG_KNOWLEDGE_ROOT', SOURCE)
        self.assertIn('QTreeWidgetItem(root, ["Wissen-Datenbanken"])', SOURCE)
        self.assertIn('Wissensdatenbank hinzufügen …', SOURCE)

    def test_knowledge_root_is_skipped_by_link_input_collection(self):
        self.assertIn('PROJECT_NODE_PROLOG_KNOWLEDGE_ROOT,', SOURCE)
        self.assertIn('PROJECT_PROLOG_KNOWLEDGE_KEY', SOURCE)


class KnowledgeBrowserGuiSourceTests(unittest.TestCase):
    def test_combo_open_button_and_fact_tree_exist(self):
        for marker in (
            'class PrologKnowledgeDialog(QDialog):',
            'self.database_combo = QComboBox',
            'self.open_button = QPushButton("Öffnen"',
            'self.fact_tree = QTreeWidget',
            'self.level_scroll = QScrollArea',
            'self.query_edit = QLineEdit',
            'self.add_level_button = QPushButton("Prüfen +"',
        ):
            self.assertIn(marker, SOURCE)

    def test_flow_wrap_and_green_active_border(self):
        self.assertIn('class KnowledgeFlowLayout(QLayout):', SOURCE)
        self.assertIn('border = "#2ea043" if self._active else normal', SOURCE)

    def test_parent_arrow_and_search_threshold(self):
        self.assertIn('searchable = len(values) > 10', SOURCE)
        self.assertIn('self.arrow_button.setVisible(bool(self.alternatives))', SOURCE)
        self.assertIn('self.alternative_combo.showPopup()', SOURCE)

    def test_delete_removes_selected_level_and_descendants(self):
        self.assertIn('self.level_values = self.level_values[:level_index]', SOURCE)
        self.assertIn('alle Sub-Level', SOURCE)

    def test_parent_bound_alternative_restarts_from_prefix(self):
        self.assertIn('base_prefix = list(self._alternative_parent_prefix)', SOURCE)
        self.assertIn('self.level_values = base_prefix + [value]', SOURCE)
        self.assertIn('self._restart_decision()', SOURCE)

    def test_dark_and_light_styles_are_present(self):
        self.assertIn('#0d1117', SOURCE)
        self.assertIn('#ffffff', SOURCE)


if __name__ == '__main__':
    unittest.main()
