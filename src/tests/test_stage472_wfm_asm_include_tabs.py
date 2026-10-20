"""Stage 472: includes, tab layout and persistent file operations."""
from pathlib import Path
from wfm_asm_tab_support import include_at_position, resolve_wfm_include

SOURCE = (Path(__file__).parent / "d64_dism.py").read_text(encoding="utf-8")


def _method(name):
    start = SOURCE.index(f"        def {name}(")
    end = SOURCE.find("\n        def ", start + 12)
    return SOURCE[start:end] if end >= 0 else SOURCE[start:]


def test_include_right_click_inside_filename_only():
    line = '  %include "dir/file.extern.inc" ; extra'
    assert include_at_position(line, line.index('file')) == "dir/file.extern.inc"
    assert include_at_position(line, line.index('%')) is None
    assert include_at_position(line, line.index(';')) is None
    assert include_at_position('; %include "hidden.inc"', 16) is None
    assert include_at_position('%include <legacy.inc>', 12) is None
    assert include_at_position("%include 'nested.inc'", 12) == "nested.inc"


def test_include_resolution_priority_and_nested_project_directory(tmp_path):
    cwd = tmp_path / "cwd"
    inc1 = tmp_path / "inc1"
    inc2 = tmp_path / "inc2"
    for folder in (cwd, inc1, inc2):
        folder.mkdir()
    (inc1 / 'nested').mkdir()
    (inc2 / 'nested').mkdir()
    (inc1 / 'nested' / 'runtime.inc').write_text('one')
    (inc2 / 'nested' / 'runtime.inc').write_text('two')
    path, checked, err = resolve_wfm_include('nested/runtime.inc', cwd, (inc1, inc2))
    assert err is None
    assert path == (inc1 / 'nested' / 'runtime.inc').resolve()
    assert checked[0] == (cwd / 'nested' / 'runtime.inc').resolve()
    (cwd / 'nested').mkdir()
    (cwd / 'nested' / 'runtime.inc').write_text('local')
    path, _, err = resolve_wfm_include('nested/runtime.inc', cwd, (inc1, inc2))
    assert path == (cwd / 'nested' / 'runtime.inc').resolve()


def test_include_missing_and_invalid_filename(tmp_path):
    path, checked, err = resolve_wfm_include('missing.inc', tmp_path, ())
    assert path is None and err and len(checked) == 1
    assert resolve_wfm_include('bad\0name', tmp_path, ())[0] is None


def test_tabs_layout_and_buttons():
    ctor = _method('_ensure_dbase_form_designer')
    assert 'assembly_tabs = QTabWidget(assembly_host)' in ctor
    assert 'assembly_tabs.addTab(asm_container, "Generierter Assembler")' in ctor
    assert 'setTabButton(0, QTabBar.RightSide, None)' in ctor
    assert 'source_assembly_splitter = QSplitter(Qt.Vertical, source_page)' in ctor
    assert 'self.dbase_form_assembly_tabs = assembly_tabs' in ctor
    assert 'form_tabs.addTab(source_page, "Quellcode")' in ctor
    add = _method('_dbase_form_asm_add_tab')
    assert 'SourceEditorWithMiniMap(' in add
    assert 'QTabBar.RightSide, button' in add
    assert 'editor.viewport().installEventFilter(self)' in add
    assert 'self._dbase_form_asm_paths[container]' in add


def test_save_routes_and_new_assembler_behavior():
    assert 'return self._dbase_form_save_all_editors()' in _method('save_current_document')
    assert 'return self._dbase_form_asm_save_as()' in _method('save_current_document_as')
    assert 'self._dbase_form_asm_new_tab()' in _method('new_profile_source_document')
    save = _method('_dbase_form_asm_save_widget')
    for choice in ('"Umbenennen"', '"Beibehalten"', '"Abbrechen"'):
        assert choice in save
    assert 'os.replace(temporary_name, dest)' in save
    assert 'self._dbase_form_asm_new.discard(widget)' in save
    assert 'for idx in range(tabs.count())' in _method('_dbase_form_save_all_editors')
    assert 'if not self.save_dbase_form():' in _method('_dbase_form_save_all_editors')
    assert 'f"Unbenannt_{number}.asm"' in _method('_dbase_form_asm_new_tab')


def test_include_menu_theme_and_shortcuts():
    menu = SOURCE[SOURCE.index('        def contextMenuEvent(self, event) -> None:', SOURCE.index('    class SourceTextEdit(')):]
    assert '"In neuen Tab öffnen"' in menu
    assert 'wrapper.addSeparator()' in menu
    assert '"Hilfe"' in menu
    assert '"Neu Assembler"' in menu
    assert '_project_windows_asm_include_paths(target_name)' in _method('_dbase_form_asm_open_include')
    assert 'self.show_error(' in _method('_dbase_form_asm_open_include')
    assert 'self._apply_message_box_theme(box)' in _method('_dbase_form_asm_save_widget')
    final_filter = SOURCE[SOURCE.rfind('        def eventFilter(self, watched, event):'):]
    assert 'self._dbase_form_save_all_editors()' in final_filter
    assert 'self.save_dbase_form()' in final_filter
