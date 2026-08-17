from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / 'd64_dism.py').read_text(encoding='utf-8')


class PrologKnowledgeWidgetHelpDockComboStage67Tests(unittest.TestCase):
    def test_every_visible_widget_gets_dynamic_property(self):
        self.assertIn('WIDGET_PROPERTY_NAME = "d64WidgetPropertyId"', SOURCE)
        self.assertIn('def _assign_widget_property_ids(self, root=None) -> None:', SOURCE)
        self.assertIn('for widget in root.findChildren(QWidget):', SOURCE)
        self.assertIn('if widget.isVisible():', SOURCE)
        self.assertIn('widget.setProperty(self.WIDGET_PROPERTY_NAME, property_id)', SOURCE)
        self.assertIn('QTimer.singleShot(0, self._assign_widget_property_ids)', SOURCE)

    def test_dynamic_widgets_receive_property_on_show(self):
        marker = SOURCE.index('def eventFilter(self, watched, event):', SOURCE.index('class ExplorerWindow'))
        block = SOURCE[marker:marker + 1800]
        self.assertIn('event.type() == QEvent.Show', block)
        self.assertIn('self._assign_widget_property_id(watched)', block)

    def test_f1_uses_widget_under_mouse_and_logs_property_id(self):
        self.assertIn('QCursor,', SOURCE)
        self.assertIn('QApplication.widgetAt(QCursor.pos())', SOURCE)
        self.assertIn('event.key() == Qt.Key_F1', SOURCE)
        self.assertIn('self._log_f1_widget_property()', SOURCE)
        self.assertIn('self.log(f"F1 Widget-Property-ID: {property_id}")', SOURCE)
        self.assertIn('self.statusBar().showMessage(', SOURCE)

    def test_property_id_prefers_object_name_without_changing_qss_object_name(self):
        marker = SOURCE.index('def _widget_property_segment(widget: QWidget)')
        block = SOURCE[marker:marker + 2100]
        self.assertIn('widget.objectName()', block)
        self.assertIn('return object_name', block)
        self.assertIn('class_name = widget.metaObject().className()', block)
        self.assertIn('siblings.index(widget) + 1', block)
        self.assertNotIn('widget.setObjectName(', block)

    def test_knowledge_widgets_have_semantic_object_names_for_future_chm(self):
        for name in (
            'prolog_knowledge_directory_edit',
            'prolog_knowledge_directory_button',
            'prolog_knowledge_database_combo',
            'prolog_knowledge_open_button',
            'prolog_knowledge_fact_tree',
            'prolog_knowledge_query_edit',
            'prolog_knowledge_query_check_add',
            'prolog_knowledge_level_main',
            'prolog_knowledge_level_arrow',
            'prolog_knowledge_alternative_combo',
            'prolog_knowledge_alternative_check_button',
        ):
            self.assertIn(name, SOURCE)

    def test_knowledge_dock_hides_central_widget_to_fill_free_area(self):
        marker = SOURCE.index('def _prolog_knowledge_dock_visibility_changed')
        block = SOURCE[marker:marker + 4300]
        self.assertIn('central = self.centralWidget()', block)
        self.assertIn('central.hide()', block)
        self.assertIn('central.show()', block)
        self.assertIn('_knowledge_replaced_central_widget', block)
        self.assertIn('def _expand_prolog_knowledge_dock', block)
        self.assertIn('self.resizeDocks([dock], [100000], Qt.Horizontal)', block)
        self.assertIn('self.resizeDocks([dock], [100000], Qt.Vertical)', block)

    def test_embedded_dialog_has_no_artificial_minimum_size(self):
        marker = SOURCE.index('if self._embedded:')
        block = SOURCE[marker:marker + 700]
        self.assertIn('self.setMinimumSize(0, 0)', block)
        self.assertIn('QSizePolicy.Expanding, QSizePolicy.Expanding', block)

    def test_alternative_combo_is_embedded_below_clicked_arrow_button(self):
        marker = SOURCE.index('class KnowledgeLevelButton(QWidget):')
        block = SOURCE[marker:marker + 9000]
        self.assertLess(block.index('outer_layout.addLayout(button_row)'), block.index('outer_layout.addWidget(self.alternative_host)'))
        self.assertIn('self.alternative_host_layout.addWidget(combo)', block)
        self.assertIn('self.alternative_host_layout.addWidget(check_button)', block)
        self.assertIn('combo.show()', block)
        self.assertIn('self.alternative_host.show()', block)

    def test_flow_layout_geometry_is_refreshed_after_combo_show(self):
        marker = SOURCE.index('def _refresh_embedded_alternative_geometry')
        block = SOURCE[marker:marker + 4200]
        self.assertIn('layout.invalidate()', block)
        self.assertIn('layout.activate()', block)
        self.assertIn('self.setMinimumSize(', block)
        self.assertIn('self.updateGeometry()', block)
        self.assertIn('QTimer.singleShot(0, self._refresh_embedded_alternative_geometry)', block)

    def test_combo_is_not_forced_into_popup_during_relayout(self):
        marker = SOURCE.index('def _populate_alternative_combo(')
        block = SOURCE[marker:marker + 6200]
        self.assertIn('parent_button.attach_alternative_controls(', block)
        self.assertIn('self.alternative_combo.setFocus(Qt.OtherFocusReason)', block)
        self.assertNotIn('self.alternative_combo.showPopup()', block)

    def test_stage66_combo_font_requirement_remains(self):
        self.assertIn('alternative_font.setFamilies(["Consolas", "Courier New"])', SOURCE)
        self.assertIn('alternative_font.setPointSize(9)', SOURCE)
        self.assertIn('self.alternative_combo.view().setFont(alternative_font)', SOURCE)


if __name__ == '__main__':
    unittest.main()
