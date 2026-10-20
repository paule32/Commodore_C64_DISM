"""Stage 469: WFM source-ASM pane must not reuse hidden QTabWidget page."""
from pathlib import Path

SOURCE = (Path(__file__).parent / 'd64_dism.py').read_text(encoding='utf-8')


def _constructor():
    begin = SOURCE.index('        def _ensure_dbase_form_designer(self) -> None:')
    end = SOURCE.index('        def _apply_dbase_form_source_outline_theme(', begin)
    return SOURCE[begin:end]


def test_assembler_editor_reparented_to_visible_host_instead_of_hidden_tab():
    method = _constructor()
    assert 'build_document.views.removeTab(assembly_index)' in method
    assert 'assembly_page.setParent(build_document)' in method
    assert 'assembly_page.hide()' in method
    assert 'source_assembly_splitter = QSplitter(Qt.Vertical, source_page)' in method
    assert 'source_splitter = QSplitter(Qt.Horizontal, source_page)' in method
    assert 'source_assembly_splitter.addWidget(source_splitter)' in method
    assert 'assembly_host = QWidget(source_assembly_splitter)' in method
    assert 'assembly_host.setObjectName("dbase_form_assembly_host")' in method
    assert 'assembly_layout.removeWidget(asm_container)' in method
    assert 'asm_container = build_document.generated_assembly_editor_container' in method
    assert 'asm_container.setParent(assembly_host)' in method
    # Stage 472: der permanente ASM-Editor lebt nun im TabWidget im gleichen Host.
    assert ('assembly_host_layout.addWidget(asm_container, 1)' in method
            or 'assembly_tabs.addTab(asm_container, "Generierter Assembler")' in method)
    assert 'source_assembly_splitter.addWidget(assembly_host)' in method
    assert 'asm_container.show()' in method
    assert 'assembly_host.show()' in method
    assert 'source_layout.addWidget(source_assembly_splitter, 1)' in method
    assert 'self.dbase_form_assembly_page = assembly_host' in method
    assert 'source_assembly_splitter.addWidget(assembly_page)' not in method
    assert 'form_tabs.addTab(assembly_page' not in method


def test_splitter_stays_resizable_and_asm_is_kept_visible_on_source_tab_switch():
    method = _constructor()
    assert 'source_assembly_splitter.setChildrenCollapsible(False)' in method
    assert 'source_assembly_splitter.setHandleWidth(7)' in method
    assert 'source_assembly_splitter.setStretchFactor(0, 2)' in method
    assert 'source_assembly_splitter.setStretchFactor(1, 1)' in method
    assert 'source_assembly_splitter.setSizes([620, 300])' in method
    assert 'form_tabs.addTab(source_page, "Quellcode")' in method
    start = SOURCE.index('        def _dbase_form_tab_changed(self, index: int) -> None:')
    end = SOURCE.index('        def _merge_dbase_form_source_methods_events(', start)
    handler = SOURCE[start:end]
    assert 'generated_assembly_editor_container.show()' in handler
    assert 'self.dbase_form_assembly_page.show()' in handler
    # Tabwechsel darf die manuell eingestellten Splittergroessen nicht zuruecksetzen.
    assert 'setSizes(' not in handler


def test_old_assembler_tab_is_still_absent_and_compiler_targets_source_tab():
    method = _constructor()
    assert 'form_tabs.addTab(source_page, "Quellcode")' in method
    assert 'form_tabs.addTab(assembly_page' not in method
    start = SOURCE.index('        def compile_dbase_form(self) -> bool:')
    end = SOURCE.index('        def assemble_dbase_form(self) -> bool:', start)
    compile_method = SOURCE[start:end]
    assert 'setCurrentWidget(self.dbase_form_source_page)' in compile_method
    assert 'setCurrentWidget(self.dbase_form_assembly_page)' not in compile_method
