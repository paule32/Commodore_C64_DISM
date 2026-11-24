"""Stage 693: safe overwrite-confirmation of Turbo Help files and folders."""
from pathlib import Path
import textwrap
from types import SimpleNamespace

import pytest

from turbo_help_project_tree import rename_help_path

HERE = Path(__file__).resolve().parent
SOURCE = (HERE / 'd64_dism.py').read_text(encoding='utf8')


def method(name):
    begin = SOURCE.index(f'        def {name}(')
    end = SOURCE.find('\n        def ', begin + 16)
    return textwrap.dedent(SOURCE[begin:end])


def test_file_rename_rejects_existing_unless_confirmed(tmp_path):
    src, dest = tmp_path / 'a.thlp', tmp_path / 'b.thlp'
    src.write_text('NEU', encoding='utf8')
    dest.write_text('ALT', encoding='utf8')
    with pytest.raises(FileExistsError):
        rename_help_path(src, dest)
    assert src.read_text() == 'NEU' and dest.read_text() == 'ALT'
    assert rename_help_path(src, dest, overwrite=True) is True
    assert not src.exists() and dest.read_text() == 'NEU'
    assert not list(tmp_path.glob('.*.d64-rename-*.bak'))


def test_existing_folder_replaced_with_whole_tree(tmp_path):
    src, dest = tmp_path / 'Old', tmp_path / 'New'
    (src / 'Sub').mkdir(parents=True)
    (dest / 'Other').mkdir(parents=True)
    (src / 'Sub' / 'one.thlp').write_text('source', encoding='utf8')
    (dest / 'Other' / 'two.thlp').write_text('destination', encoding='utf8')
    assert rename_help_path(src, dest, overwrite=True)
    assert not src.exists()
    assert (dest / 'Sub' / 'one.thlp').read_text() == 'source'
    assert not (dest / 'Other').exists()


def test_type_mismatch_prevents_replacement(tmp_path):
    src, dest = tmp_path / 'Old', tmp_path / 'New'
    src.mkdir()
    dest.write_text('keep')
    with pytest.raises(ValueError, match='Datei und Verzeichnis'):
        rename_help_path(src, dest, overwrite=True)
    assert src.is_dir() and dest.read_text() == 'keep'


def test_failed_rename_restores_existing_target(tmp_path, monkeypatch):
    src, dest = tmp_path / 'a.thlp', tmp_path / 'b.thlp'
    src.write_text('NEW')
    dest.write_text('OLD')
    rename_original = Path.rename

    def failing_rename(self, to):
        if self == src and Path(to) == dest:
            raise OSError('simulierter Dateisystemfehler')
        return rename_original(self, to)

    monkeypatch.setattr(Path, 'rename', failing_rename)
    with pytest.raises(OSError, match='simulierter'):
        rename_help_path(src, dest, overwrite=True)
    assert src.read_text() == 'NEW'
    assert dest.read_text() == 'OLD'
    assert not list(tmp_path.glob('.*.d64-rename-*.bak'))


def test_simple_rename_and_absent_source(tmp_path):
    src, dest = tmp_path / 'a.thlp', tmp_path / 'b.thlp'
    with pytest.raises(FileNotFoundError):
        rename_help_path(src, dest)
    src.write_text('TEST')
    assert rename_help_path(src, dest) is False
    assert dest.read_text() == 'TEST'


class FakeQt:
    UserRole = 1000
    Checked = 2
    Unchecked = 0


class FakeMessageBox:
    Warning = 5
    Ok = 1
    Cancel = 2
    Help = 4


class FakeDialog:
    def __init__(self, answer):
        self.answer = answer
        self.clicked = None
        self.buttons = FakeMessageBox.Ok | FakeMessageBox.Cancel | FakeMessageBox.Help
        self.default = FakeMessageBox.Cancel
        self.help_button = SimpleNamespace(clicked=SimpleNamespace(connect=self.connect))

    def connect(self, fn):
        self.clicked = fn

    def button(self, value):
        return self.help_button if value == FakeMessageBox.Help else None

    def exec_(self):
        return self.answer


class FakeNode:
    def __init__(self, path, kind, parent=None, checked=False):
        self.path, self.kind, self._parent = Path(path), kind, parent
        self.children = []
        self.text_value = Path(path).name
        self.tooltip = str(path)
        self.folder_key = self.text_value if kind == 'folder' else ''
        self.checked = checked
        if parent is not None:
            parent.children.append(self)

    def data(self, col, key):
        return {1302: str(self.path), 1303: self.kind,
                1315: self.folder_key}.get(key)

    def setData(self, col, key, value):
        if key == 1302:
            self.path = Path(value)
        elif key == 1315:
            self.folder_key = value

    def setToolTip(self, col, value):
        self.tooltip = value

    def setText(self, col, value):
        self.text_value = value

    def parent(self):
        return self._parent

    def indexOfChild(self, node):
        return self.children.index(node)

    def takeChild(self, index):
        node = self.children.pop(index)
        node._parent = None
        return node

    def checkState(self, col):
        return FakeQt.Checked if self.checked else FakeQt.Unchecked


@pytest.fixture
def ui_methods():
    ns = {'Path': Path, 'Qt': FakeQt, 'QMessageBox': FakeMessageBox,
          'PROJECT_NODE_TURBO_HELP_FOLDER': 'folder',
          'PROJECT_NODE_TURBO_HELP_FILE': 'file'}

    class FakeInput:
        result = None

        @staticmethod
        def getText(*args, **kwargs):
            return FakeInput.result

    ns['QInputDialog'] = FakeInput
    for name in ('_turbo_help_rename', '_turbo_help_confirm_rename_replace'):
        exec(compile(method(name), str(HERE / 'd64_dism.py'), 'exec'), ns)
    return ns


def build_app(ns, tmp_path, *, folder=False, collision=True):
    src = tmp_path / ('Before' if folder else 'before.thlp')
    dest = tmp_path / ('After' if folder else 'after.thlp')
    if folder:
        src.mkdir()
        (src / 'child.thlp').write_text('NEW')
        if collision:
            dest.mkdir()
            (dest / 'old.thlp').write_text('OLD')
    else:
        src.write_text('NEW')
        if collision:
            dest.write_text('OLD')
    root = FakeNode(tmp_path, 'root')
    node = FakeNode(src, 'folder' if folder else 'file', root)
    if folder:
        FakeNode(src / 'child.thlp', 'file', node)
    target = FakeNode(dest, 'folder' if folder else 'file', root) if collision else None
    if folder and collision:
        FakeNode(dest / 'old.thlp', 'file', target)

    class App:
        _project_item_kind = lambda self, item: item.kind
        _turbo_help_root_directory = lambda self, **kw: tmp_path
        _turbo_help_active_editor = lambda self: None
        _turbo_help_sync_editor = lambda self: None
        _turbo_help_mark_main = lambda self, item: setattr(item, 'checked', True)
        _turbo_help_folder_key = lambda self, item: '' if item is root else item.folder_key
        _turbo_help_warning = lambda self, msg: self.warnings.append(msg)
        set_project_modified = lambda self, value: self.modified.append(value)

        def _turbo_help_tree_items(self, parent=None):
            parent = parent or root
            for child in parent.children:
                yield child
                yield from self._turbo_help_tree_items(child)

        _create_message_box = lambda self, *args, **kwargs: self.make_dialog(args, kwargs)
        show_chm_viewer = lambda self, **kwargs: self.chm_calls.append(kwargs)

    App._turbo_help_rename = ns['_turbo_help_rename']
    App._turbo_help_confirm_rename_replace = ns['_turbo_help_confirm_rename_replace']
    app = App()
    app.warnings, app.modified, app.chm_calls, app.dialogs = [], [], [], []

    def make_dialog(args, kwargs):
        dialog = FakeDialog(app.answer)
        app.dialogs.append((args, kwargs, dialog))
        return dialog

    app.make_dialog = make_dialog
    return app, ns['QInputDialog'], root, node, target, src, dest


def test_ui_cancel_keeps_tree_and_disk_untouched(ui_methods, tmp_path):
    app, inp, root, node, target, src, dest = build_app(ui_methods, tmp_path)
    inp.result = (dest.name, True)
    app.answer = FakeMessageBox.Cancel
    app._turbo_help_rename(node)
    assert src.read_text() == 'NEW'
    assert dest.read_text() == 'OLD'
    assert root.children == [node, target]
    assert not app.modified and not app.warnings
    args, kwargs, dialog = app.dialogs[0]
    assert kwargs['buttons'] == 7
    assert kwargs['default_button'] == FakeMessageBox.Cancel
    assert 'überschrieben' in args[2]
    assert dialog.clicked is not None
    dialog.clicked()
    assert app.chm_calls[0]['context_word'] == 'Datei umbenennen'


def test_ui_ok_replaces_file_and_removes_old_tree_node(ui_methods, tmp_path):
    app, inp, root, node, target, src, dest = build_app(ui_methods, tmp_path)
    inp.result = (dest.name, True)
    app.answer = FakeMessageBox.Ok
    app._turbo_help_rename(node)
    assert not src.exists() and dest.read_text() == 'NEW'
    assert root.children == [node]
    assert node.path == dest and node.text_value == dest.name
    assert app.modified == [True]


def test_ui_ok_replaces_folder_recursively(ui_methods, tmp_path):
    app, inp, root, node, target, src, dest = build_app(ui_methods, tmp_path, folder=True)
    inp.result = (dest.name, True)
    app.answer = FakeMessageBox.Ok
    app._turbo_help_rename(node)
    assert not src.exists()
    assert (dest / 'child.thlp').read_text() == 'NEW'
    assert not (dest / 'old.thlp').exists()
    assert root.children == [node]
    assert node.path == dest and node.children[0].path == dest / 'child.thlp'
    assert app.modified == [True]


def test_ui_original_name_dialog_cancel_never_prompts(ui_methods, tmp_path):
    app, inp, root, node, target, src, dest = build_app(ui_methods, tmp_path)
    inp.result = (dest.name, False)
    app._turbo_help_rename(node)
    assert not app.dialogs
    assert src.exists() and dest.exists()


def test_ui_no_conflict_renames_without_prompt(ui_methods, tmp_path):
    app, inp, root, node, target, src, dest = build_app(ui_methods, tmp_path, collision=False)
    inp.result = (dest.name, True)
    app._turbo_help_rename(node)
    assert dest.exists() and not src.exists()
    assert not app.dialogs


def test_ui_conflict_uses_central_theme_and_chm():
    assert 'self._create_message_box(' in method('_turbo_help_confirm_rename_replace')
    assert 'QMessageBox.Ok | QMessageBox.Cancel | QMessageBox.Help' in method('_turbo_help_confirm_rename_replace')
    assert 'self.show_chm_viewer(' in method('_turbo_help_confirm_rename_replace')
    assert 'QMessageBox.Cancel' in method('_turbo_help_confirm_rename_replace')


def test_overwritten_main_file_transfers_main_mark_to_renamed_source(ui_methods, tmp_path):
    app, inp, root, node, target, src, dest = build_app(ui_methods, tmp_path)
    target.checked = True
    inp.result = (dest.name, True)
    app.answer = FakeMessageBox.Ok
    app._turbo_help_rename(node)
    assert node.checked is True
    assert root.children == [node]


def test_modified_destination_tab_blocks_overwrite(ui_methods, tmp_path):
    app, inp, root, node, target, src, dest = build_app(ui_methods, tmp_path)
    inp.result = (dest.name, True)
    app.answer = FakeMessageBox.Ok
    edit = SimpleNamespace(document=lambda: SimpleNamespace(isModified=lambda: True))
    tabs = SimpleNamespace(count=lambda: 1, widget=lambda _i: edit)
    editor = SimpleNamespace(tabs=tabs, _path_for=lambda _edit: dest)
    app._turbo_help_active_editor = lambda: editor
    app._turbo_help_rename(node)
    assert src.read_text() == 'NEW'
    assert dest.read_text() == 'OLD'
    assert app.warnings and 'ungespeicherte Änderungen' in app.warnings[-1]
    assert not app.modified
