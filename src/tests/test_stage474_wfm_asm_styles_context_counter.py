"""Stage 474: ASM appearance, native context menus and numbered new tabs."""
from pathlib import Path
import textwrap

SOURCE = (Path(__file__).parent / 'd64_dism.py').read_text(encoding='utf-8')


def method(name):
    start = SOURCE.index(f'        def {name}(')
    end = SOURCE.find('\n        def ', start + 12)
    return SOURCE[start:end] if end >= 0 else SOURCE[start:]


class FakeTabs:
    def __init__(self):
        self.titles = ['Generierter Assembler']
    def count(self):
        return len(self.titles)
    def tabText(self, index):
        return self.titles[index]


class FakeForm:
    def __init__(self):
        self._dbase_form_asm_new_counter = 1
        self.dbase_form_assembly_tabs = FakeTabs()
        self.dbase_form_source_page = object()
        self.dbase_form_tabs = self
        self.created = []
        self.messages = []
    def _ensure_dbase_form_designer(self):
        pass
    def setCurrentWidget(self, w):
        pass
    def _dbase_form_asm_add_tab(self, name, text, new=False):
        assert new and text == ''
        self.created.append(name)
        self.dbase_form_assembly_tabs.titles.append(name)
        return name
    def statusBar(self):
        return self
    def showMessage(self, text, timeout):
        self.messages.append(text)


def test_numbered_unsaved_tabs_and_no_duplicate_after_reset():
    namespace = {}
    exec(textwrap.dedent(method('_dbase_form_asm_new_tab')), namespace)
    create = namespace['_dbase_form_asm_new_tab']
    form = FakeForm()
    assert create(form) == 'Unbenannt_1.asm'
    assert create(form) == 'Unbenannt_2.asm'
    assert form._dbase_form_asm_new_counter == 3
    form._dbase_form_asm_new_counter = 1  # close and reopen the same designer
    assert create(form) == 'Unbenannt_3.asm'  # old tabs still exist, no collision
    form.dbase_form_assembly_tabs.titles = ['Generierter Assembler']
    form._dbase_form_asm_new_counter = 1
    assert create(form) == 'Unbenannt_1.asm'


def test_counter_initial_state_and_reset_on_form_close():
    assert 'self._dbase_form_asm_new_counter = 1' in SOURCE
    assert 'self._dbase_form_asm_new_counter = 1' in method('_close_dbase_form_designer_pair')
    assert 'self._dbase_form_asm_new_counter = 1' in method('_dbase_form_dock_visibility_changed')
    assert 'self._dbase_form_asm_new.add(container)' in method('_dbase_form_asm_add_tab')
    assert 'fresh = widget in self._dbase_form_asm_new or old_path is None' in method('_dbase_form_asm_save_widget')
    assert 'initial.name' in method('_dbase_form_asm_save_widget')


def test_all_tabs_copy_main_asm_palette_and_gutter():
    ctor = method('_ensure_dbase_form_designer')
    assert 'self._dbase_form_asm_bind_editor(build_document.generated_assembly_editor)' in ctor
    binder = method('_dbase_form_asm_bind_editor')
    assert 'QPalette(original.palette())' in binder
    assert 'QPalette(original.viewport().palette())' in binder
    assert 'editor.set_gutter_dark_mode(True)' in binder
    assert '_wfm_asm_new_callback' in binder
    assert '_wfm_asm_include_callback' in binder
    add = method('_dbase_form_asm_add_tab')
    assert 'highlighter = AssemblerSyntaxHighlighter(editor.document())' in add
    assert 'highlighter.set_enabled(True)' in add
    assert 'self._dbase_form_asm_bind_editor(editor)' in add
    assert 'for editor in getattr(self, "_dbase_form_asm_editors", {}).values():' in SOURCE


def test_editor_menu_preserves_existing_items_with_new_first():
    source_edit = SOURCE[SOURCE.index('    class SourceTextEdit('):]
    context = source_edit[source_edit.index('        def contextMenuEvent(self, event) -> None:'):]
    # A separate wrapper prefixes actions from the native editor menu.
    assert context.index('wrapper.addAction("Neu Assembler")') < context.index('wrapper.addSeparator()')
    assert 'for existing_action in menu.actions():' in context
    assert 'wrapper.addAction(existing_action)' in context
    assert 'include_at_position(' in context
    assert 'wrapper.addAction("In neuen Tab öffnen")' in context
    assert 'wrapper.addAction("Hilfe")' in context
    assert 'new_asm()' in context
    assert 'include_handler(include_name, False)' in context
    assert 'include_handler(include_name, True)' in context
    # No earlier viewport event filter may hijack the native editor context.
    event_filter = SOURCE[SOURCE.rfind('        def eventFilter(self, watched, event):'):]
    assert '_dbase_form_include_context_menu(' not in event_filter


def test_close_icon_red_small_right_side_and_main_tab_without_close():
    add = method('_dbase_form_asm_add_tab')
    assert 'button.setIcon(self._dbase_form_asm_red_close_icon())' in add
    assert 'button.setIconSize(QSize(12, 12))' in add
    assert 'QTabBar.RightSide, button' in add
    icon = method('_dbase_form_asm_red_close_icon')
    assert 'QColor("#e44646")' in icon
    assert 'QPixmap(12, 12)' in icon
    assert 'pixmap.fill(Qt.transparent)' in icon
    assert 'QTabBar.RightSide, None' in method('_ensure_dbase_form_designer')
