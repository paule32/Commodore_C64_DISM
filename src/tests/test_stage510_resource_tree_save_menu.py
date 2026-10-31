# -*- coding: utf-8 -*-
"""Stage 510 – new save/save-as entries in the resource tree context menu."""
from pathlib import Path
from types import SimpleNamespace
import textwrap

from test_stage509_resource_tree_context_menu import Menu, FakeHost, _method

SOURCE = Path(__file__).with_name('d64_dism.py').read_text(encoding='utf-8')


def test_save_menu_is_topmost_and_has_shortcut():
    namespace = {
        'QMenu': Menu,
        'QKeySequence': SimpleNamespace(Save='Ctrl+S'),
    }
    exec(_method('_show_resource_tree_context_menu'), namespace)
    host = FakeHost()
    namespace['_show_resource_tree_context_menu'](host, (0, 0))
    actions = Menu.last.items
    assert [a.text if a else None for a in actions[:4]] == [
        'Speichern', 'Speichern unter ...', None, 'Neu:  Dialog',
    ]
    assert actions[0].shortcut == 'Ctrl+S'
    actions[0].triggered.fire()
    actions[1].triggered.fire()
    assert host.calls == ['save', 'save_as']
    assert not any(a.shortcut == 'Ctrl+S' for a in actions[3:] if a and hasattr(a, 'shortcut'))


def test_resource_save_methods_are_preserved_and_global_save_routes_to_editor():
    editor = SOURCE.split('class WindowsResourceEditorWidget(QWidget):', 1)[1]
    assert 'def save(self):' in editor and 'def save_as(self):' in editor
    assert 'return bool(self.windows_resource_editor_widget.save())' in SOURCE
    assert 'return bool(self.windows_resource_editor_widget.save_as())' in SOURCE
    assert 'self.save_file_action.setShortcut(QKeySequence.Save)' in SOURCE


def test_resource_save_writes_rc_document_to_existing_path(tmp_path):
    ns = {'Path': Path}
    exec(_method('save'), ns)
    target = tmp_path / 'demo.rc'
    status = []
    host = SimpleNamespace(
        current_path=target,
        source_edit=SimpleNamespace(toPlainText=lambda: '101 MENU\nBEGIN\nEND\n'),
        _dirty=True,
        _set_status=status.append,
    )
    assert ns['save'](host)
    assert target.read_text(encoding='utf-8') == '101 MENU\nBEGIN\nEND\n'
    assert not host._dirty
    assert 'Gespeichert:' in status[-1]


def test_resource_save_as_uses_existing_file_dialog(tmp_path):
    ns = {'Path': Path}
    exec(_method('save_as'), ns)
    chosen = tmp_path / 'new-menu.rc'
    class Recorder:
        def __init__(self): self.messages=[]
        def emit(self, message): self.messages.append(message)
    class Label:
        def __init__(self): self.text=''
        def setText(self, text): self.text=text
    signal = Recorder()
    label = Label()
    host = SimpleNamespace(
        current_path=None,
        source_edit=SimpleNamespace(toPlainText=lambda: '102 MENU\nBEGIN\nEND\n'),
        _file_dialog=lambda *args, **kwargs: str(chosen),
        file_changed=signal,
        file_label=label,
        _dirty=True,
        _set_status=lambda text: None,
    )
    assert ns['save_as'](host)
    assert chosen.read_text(encoding='utf-8') == '102 MENU\nBEGIN\nEND\n'
    assert host.current_path == chosen.resolve()
    assert label.text == str(chosen.resolve())
    assert signal.messages == [str(chosen.resolve())]
    assert not host._dirty
