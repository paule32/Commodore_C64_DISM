"""Stage 473: keyboard-scoped ASM New action, unsaved tabs and Save As title."""
from pathlib import Path
import textwrap

SOURCE = (Path(__file__).parent / "d64_dism.py").read_text(encoding="utf-8")


def method(name):
    start = SOURCE.index(f"        def {name}(")
    end = SOURCE.find("\n        def ", start + 12)
    return SOURCE[start:end] if end >= 0 else SOURCE[start:]


class _Qt:
    ControlModifier = 1
    AltModifier = 2
    ShiftModifier = 4
    MetaModifier = 8
    Key_N = 78
    Key_S = 83


class _QEvent:
    ShortcutOverride = 1
    KeyPress = 2


class _Event:
    def __init__(self, kind, key, modifiers):
        self.kind = kind
        self.key_value = key
        self.mods = modifiers
        self.accepted = False

    def type(self):
        return self.kind

    def key(self):
        return self.key_value

    def modifiers(self):
        return self.mods

    def accept(self):
        self.accepted = True


class _Editor:
    def __init__(self):
        self._viewport = object()

    def viewport(self):
        return self._viewport


class _FakeForm:
    def __init__(self):
        self.raw_editor = _Editor()


class _FakeMain:
    def __init__(self):
        self.dbase_form_build_document = _FakeForm()
        self.main_editor = _Editor()
        self.include_editor = _Editor()
        self._dbase_form_asm_editors = {
            object(): self.main_editor,
            object(): self.include_editor,
        }
        self.new_calls = 0
        self.save_wfm_calls = 0
        self.save_all_calls = 0
        self.active = True

    def _dbase_form_is_active(self):
        return self.active

    def _dbase_form_asm_new_tab(self):
        self.new_calls += 1

    def save_dbase_form(self):
        self.save_wfm_calls += 1

    def _dbase_form_save_all_editors(self):
        self.save_all_calls += 1


def _keyboard_handler():
    # Execute the actual Stage 473 event-filter branch, without the Qt GUI or
    # the unrelated, very large rest of eventFilter().
    start = SOURCE.index('            # Stage 472/473: Tastenkombinationen gelten nur fuer ihren Editor.')
    end = SOURCE.index('            if self._dbase_form_is_active() and event.type() in (QEvent.FocusIn', start)
    branch = SOURCE[start:end]
    prefix = '''def keyboard_handler(self, watched, event):\n    document = getattr(self, "dbase_form_build_document", None)\n'''
    code = prefix + textwrap.dedent(branch).replace('\n', '\n    ')
    # dedent + prefix indent loses first line indentation unless restored
    code = prefix + textwrap.indent(textwrap.dedent(branch), '    ')
    ns = {'Qt': _Qt, 'QEvent': _QEvent}
    exec(compile(code, '<stage473-shortcut-test>', 'exec'), ns)
    return ns['keyboard_handler']


def test_ctrl_n_in_generated_and_included_asm_editor():
    handler = _keyboard_handler()
    ui = _FakeMain()
    for editor in (ui.main_editor, ui.include_editor):
        override = _Event(_QEvent.ShortcutOverride, _Qt.Key_N, _Qt.ControlModifier)
        assert handler(ui, editor, override) is False
        assert override.accepted  # prevents the global new-text-file action
        press = _Event(_QEvent.KeyPress, _Qt.Key_N, _Qt.ControlModifier)
        assert handler(ui, editor, press) is True
        assert press.accepted
    assert ui.new_calls == 2


def test_ctrl_n_viewport_handled_and_does_not_affect_wfm():
    handler = _keyboard_handler()
    ui = _FakeMain()
    event = _Event(_QEvent.KeyPress, _Qt.Key_N, _Qt.ControlModifier)
    assert handler(ui, ui.main_editor.viewport(), event) is True
    assert ui.new_calls == 1
    event = _Event(_QEvent.ShortcutOverride, _Qt.Key_N, _Qt.ControlModifier)
    assert handler(ui, ui.dbase_form_build_document.raw_editor, event) is None
    assert not event.accepted
    event = _Event(_QEvent.KeyPress, _Qt.Key_N, _Qt.ControlModifier)
    assert handler(ui, ui.dbase_form_build_document.raw_editor, event) is None
    assert ui.new_calls == 1


def test_ctrl_n_does_not_fire_with_other_modifiers_or_in_inactive_workspace():
    handler = _keyboard_handler()
    ui = _FakeMain()
    for mods in (_Qt.ControlModifier | _Qt.AltModifier, _Qt.ControlModifier | _Qt.ShiftModifier, 0):
        event = _Event(_QEvent.KeyPress, _Qt.Key_N, mods)
        assert handler(ui, ui.include_editor, event) is None
    ui.active = False
    event = _Event(_QEvent.KeyPress, _Qt.Key_N, _Qt.ControlModifier)
    assert handler(ui, ui.include_editor, event) is None
    assert ui.new_calls == 0


def test_existing_ctrl_s_shortcuts_remain_intact():
    handler = _keyboard_handler()
    ui = _FakeMain()
    event = _Event(_QEvent.KeyPress, _Qt.Key_S, _Qt.ControlModifier)
    assert handler(ui, ui.main_editor, event) is True
    assert ui.save_all_calls == 1
    event = _Event(_QEvent.KeyPress, _Qt.Key_S, _Qt.ControlModifier)
    assert handler(ui, ui.dbase_form_build_document.raw_editor, event) is True
    assert ui.save_wfm_calls == 1


def test_new_tab_is_unsaved_and_main_editor_receives_events():
    ctor = method('_ensure_dbase_form_designer')
    assert 'build_document.generated_assembly_editor.installEventFilter(self)' in ctor
    add = method('_dbase_form_asm_add_tab')
    assert 'self._dbase_form_asm_new.add(container)' in add
    assert 'editor.installEventFilter(self)' in add
    assert 'tabs.setTabToolTip(' in add
    new = method('_dbase_form_asm_new_tab')
    assert 'self._dbase_form_asm_add_tab(name, "", new=True)' in new
    assert 'f"Unbenannt_{number}.asm"' in new
    save = method('_dbase_form_asm_save_widget')
    assert 'fresh = widget in self._dbase_form_asm_new or old_path is None' in save
    assert 'if save_as or fresh:' in save
    assert '"Neue Assembler-Datei speichern unter – {initial.name}"' in save
    assert 'QFileDialog.getSaveFileName(' in save
    assert 'self._dbase_form_asm_new.discard(widget)' in save
    assert 'tabs.setTabText(index, dest.name)' in save
