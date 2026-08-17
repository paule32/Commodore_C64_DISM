from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "d64_dism.py").read_text(encoding="utf-8")


class Stage68CloseDialogEmbeddedAlternativesTests(unittest.TestCase):
    def test_project_close_prompt_uses_common_themed_message_box_layer(self):
        marker = SOURCE.index("def _confirm_project_replacement")
        block = SOURCE[marker:marker + 2400]
        self.assertIn("self._apply_message_box_theme(box)", block)
        self.assertLess(block.index("self._apply_message_box_theme(box)"), block.index("box.exec_()"))
        self.assertIn('box.addButton("Ja, speichern", QMessageBox.AcceptRole)', block)
        self.assertIn('"Nein, nicht speichern", QMessageBox.DestructiveRole', block)
        self.assertIn('box.addButton("Abbrechen", QMessageBox.RejectRole)', block)

    def test_message_box_dark_palette_is_dark_with_white_text(self):
        marker = SOURCE.index("def _message_box_palette")
        block = SOURCE[marker:marker + 1800]
        self.assertIn("QColor(32, 38, 48)", block)
        self.assertIn("QColor(255, 255, 255)", block)

    def test_message_box_light_palette_is_light_gray_with_black_text(self):
        marker = SOURCE.index("def _message_box_palette")
        block = SOURCE[marker:marker + 2300]
        self.assertIn("QColor(240, 240, 240)", block)
        self.assertIn("QColor(0, 0, 0)", block)
        self.assertIn("QColor(245, 245, 245)", block)

    def test_message_box_theme_is_applied_to_child_widgets(self):
        marker = SOURCE.index("def _apply_message_box_theme")
        block = SOURCE[marker:marker + 1500]
        self.assertIn('dialog.setObjectName("themed_message_box")', block)
        self.assertIn("dialog.setAutoFillBackground(True)", block)
        self.assertIn("for child in dialog.findChildren(QWidget):", block)
        self.assertIn("child.setPalette(dialog.palette())", block)

    def test_each_level_owns_a_permanent_embedded_alternative_combo(self):
        marker = SOURCE.index("class KnowledgeLevelButton(QWidget):")
        block = SOURCE[marker:marker + 11000]
        self.assertIn("self.embedded_alternative_combo = QComboBox(self.alternative_host)", block)
        self.assertIn('"prolog_knowledge_embedded_alternative_combo"', block)
        self.assertIn("outer_layout.addLayout(button_row)", block)
        self.assertIn("outer_layout.addWidget(self.alternative_host)", block)
        self.assertLess(block.index("outer_layout.addLayout(button_row)"), block.index("outer_layout.addWidget(self.alternative_host)"))

    def test_embedded_combo_has_requested_monospace_font_and_check_button_below(self):
        marker = SOURCE.index("self.embedded_alternative_combo = QComboBox")
        block = SOURCE[marker:marker + 4200]
        self.assertIn('embedded_font.setFamilies(["Consolas", "Courier New"])', block)
        self.assertIn("embedded_font.setPointSize(9)", block)
        combo_add = block.index("self.alternative_host_layout.addWidget(self.embedded_alternative_combo)")
        check_add = block.index("self.alternative_host_layout.addWidget(\n                self.embedded_alternative_check_button")
        self.assertLess(combo_add, check_add)

    def test_arrow_populates_clicked_buttons_own_visible_combo(self):
        marker = SOURCE.index("def _populate_alternative_combo(")
        block = SOURCE[marker:marker + 7200]
        self.assertIn("parent_button.show_embedded_alternatives(", block)
        self.assertIn("values, parent_text=parent_text", block)
        self.assertIn("self.alternative_combo.setVisible(False)", block)

    def test_local_check_uses_existing_prolog_validation_and_success_clears_controls(self):
        marker = SOURCE.index("def _check_embedded_alternative")
        block = SOURCE[marker:marker + 1800]
        self.assertIn("self.query_edit.setText(value)", block)
        self.assertIn("self.add_query_level()", block)
        add_marker = SOURCE.index("self.level_values = base_prefix + [value]", SOURCE.index("def add_query_level"))
        add_block = SOURCE[add_marker:add_marker + 700]
        self.assertIn("self._clear_alternative_controls()", add_block)
        self.assertIn("self._rebuild_level_buttons()", add_block)


if __name__ == "__main__":
    unittest.main()
