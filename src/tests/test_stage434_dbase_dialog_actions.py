# -*- coding: utf-8 -*-
"""Stage 434: explizite Open/Create-Entscheidung und Dark-Mode-Warnungen."""
from __future__ import annotations

import ast
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import pytest

from dbase_project_new import can_open_dbase_project_file, create_dbase_project_file

BASE = Path(__file__).parent
SOURCE = (BASE / 'd64_dism.py').read_text(encoding='utf-8')


def _class_source(name):
    start = SOURCE.index('    class ' + name + '(')
    end = SOURCE.find('\n    class ', start + 7)
    return SOURCE[start:end if end >= 0 else None]


def _method_source(name):
    start = SOURCE.index('        def ' + name + '(')
    end = SOURCE.find('\n        def ', start + 5)
    return SOURCE[start:end if end >= 0 else None]


def test_initial_geometry_large_icons_three_visible_buttons():
    cls = _class_source('DBaseProjectOpenFileDialog')
    assert 'self.setMinimumSize(640, 480)' in cls
    assert 'self.setGeometry(x, y, 640, 480)' in cls
    assert 'self.title_bar.close_button.setIconSize(QSize(36, 36))' in cls
    assert 'self.title_bar.close_button.setIcon(self._close_icon(self._dark_mode, 36))' in cls
    assert 'tool_button.setIconSize(QSize(34, 34))' in cls
    assert 'for button_box in self.file_dialog.findChildren(QDialogButtonBox):' in cls
    assert 'button_box.hide()' in cls
    for attr, name in [('create_button', 'Erstellen'), ('open_button', 'Öffnen'), ('cancel_button', 'Abbrechen')]:
        assert f'self.{attr} = QPushButton("{name}", controls)' in cls
    assert 'self.file_dialog.accepted.connect(self._open_selected_file)' in cls
    assert 'self.cancel_button.clicked.connect(self.reject)' in cls


def test_warning_uses_3px_frame_gradient_titlebar_close_icon_and_ok():
    cls = _class_source('DBaseProjectWarningDialog')
    assert 'Qt.FramelessWindowHint' in cls
    assert 'border:3px solid {frame}' in cls
    assert 'DBaseTableDialogTitleBar(' in cls
    assert 'self.title_bar.close_button.setIcon(' in cls
    assert 'QPushButton("OK", self)' in cls
    assert 'self.ok_button.clicked.connect(self.accept)' in cls
    source = _class_source('DBaseTableDialogTitleBar')
    assert 'QLinearGradient(0, 0, self.width(), 0)' in source
    assert 'QColor("#000000")' in source
    assert 'QColor("#707070")' in source


def test_user_messages_and_distinct_operations():
    cls = _class_source('DBaseProjectOpenFileDialog')
    assert 'Die angegebene Datei existiert bereits' in cls
    assert 'Sie haben nicht die benötigten Rechte um die ausgewählte Datei zu öffnen/bearbeiten' in cls
    assert 'self.operation = "create"' in cls
    assert 'self.operation = "open"' in cls
    workflow = _method_source('_new_dbase_project_file')
    assert 'operation = dialog.operation' in workflow
    assert 'if operation not in ("create", "open"):' in workflow
    assert 'if operation == "create" and (path.exists() or path.is_symlink()):' in workflow
    assert 'if operation == "open" and not can_open_dbase_project_file(path):' in workflow
    assert 'if operation == "create":' in workflow
    assert 'self.open_project_item(child)' in workflow
    assert 'is_dbase_program_text(path)' in workflow


def test_can_open_access_check_read_and_write(tmp_path):
    existing = tmp_path / 'Programm.prg'
    create_dbase_project_file(existing, 'programs')
    assert can_open_dbase_project_file(existing)
    assert not can_open_dbase_project_file(tmp_path / 'missing.prg')
    assert not can_open_dbase_project_file(tmp_path)
    real_open = Path.open

    def deny_read(path, mode='r', *args, **kwargs):
        if mode == 'rb':
            raise PermissionError('read denied')
        return real_open(path, mode, *args, **kwargs)

    def deny_write(path, mode='r', *args, **kwargs):
        if mode == 'r+b':
            raise PermissionError('write denied')
        return real_open(path, mode, *args, **kwargs)

    with patch.object(Path, 'open', deny_read):
        assert not can_open_dbase_project_file(existing)
    with patch.object(Path, 'open', deny_write):
        assert not can_open_dbase_project_file(existing)


def _selection_method(name):
    method_src = _method_source(name)
    node = ast.parse('class C:\n'+method_src).body[0].body[0]
    ns = {'can_open_dbase_project_file': can_open_dbase_project_file}
    exec(compile(ast.Module(body=[node], type_ignores=[]), '<stage434>', 'exec'), ns)
    return ns[name]


def test_create_existing_file_warns_and_does_not_accept(tmp_path):
    path = tmp_path / 'exists.prg'
    path.write_text('HELLO', encoding='utf-8')
    warnings = []
    host = SimpleNamespace(_candidate_path=lambda: path,
                           _warn=warnings.append, operation=None,
                           _selected_file='', accept=lambda: pytest.fail('should not accept'))
    _selection_method('_create_selected_file')(host)
    assert warnings == ['Die angegebene Datei existiert bereits']
    assert host.operation is None


def test_create_fresh_name_accepts_and_sets_create(tmp_path):
    path = tmp_path / 'new.prg'
    accepted = []
    host = SimpleNamespace(_candidate_path=lambda: path,
                           _warn=lambda *_: pytest.fail('unexpected warning'),
                           operation=None, _selected_file='',
                           accept=lambda: accepted.append(True))
    _selection_method('_create_selected_file')(host)
    assert accepted == [True]
    assert host.operation == 'create'
    assert host._selected_file == str(path)
    assert not path.exists(), 'the dialog must not create the file before the workflow validates it'


def test_open_valid_file_accepts_and_denied_file_warns(tmp_path):
    path = tmp_path / 'yes.prg'
    path.write_text('? 1\n', encoding='utf-8')
    accepted, warnings = [], []
    host = SimpleNamespace(_candidate_path=lambda: path,
                           _warn=warnings.append,
                           operation=None, _selected_file='',
                           accept=lambda: accepted.append(True))
    method = _selection_method('_open_selected_file')
    method(host)
    assert host.operation == 'open'
    assert accepted == [True]
    host.operation = None
    host._candidate_path = lambda: tmp_path / 'no.prg'
    method(host)
    assert warnings == ['Sie haben nicht die benötigten Rechte um die ausgewählte Datei zu öffnen/bearbeiten']
    assert host.operation is None


def _simulate_project_workflow(tmp_path, filename, operation, *, allow_access=True):
    """Fuehrt die echte Projektbaum-Methode mit kleinen Qt-Dummys aus."""
    from dbase_project_new import (
        DBASE_NEW_MENU, DBASE_GROUP_NEW_MENU, is_dbase_program_text,
    )
    calls = []
    notices = []

    class Dialog:
        def __init__(self, *args, **kwargs):
            self.operation = operation
        def exec_(self): return 1
        def selectedFiles(self): return [str(filename)]

    class Warning:
        def __init__(self, _parent, msg, **kwargs):
            notices.append(msg)
        def exec_(self): return 1

    class Child:
        def parent(self): return None
        def setSelected(self, selected): pass

    tree = SimpleNamespace(setCurrentItem=lambda child: None,
                           scrollToItem=lambda child: None)
    child = Child()
    host = SimpleNamespace(
        current_project_path=None, current_directory=str(tmp_path),
        dark_mode_enabled=True, project_tree=tree,
        show_error=lambda *args: calls.append(('error', args)),
        _ensure_project_for_new_document=lambda: None,
        _add_project_dbase_entry=lambda role, path, title: calls.append(('added', role, path)) or child,
        _add_project_resource_entry=lambda *args, **kw: child,
        open_project_item=lambda item: calls.append(('opened', item)),
        save_project=lambda: calls.append(('saved',)),
        statusBar=lambda: SimpleNamespace(showMessage=lambda *args: None),
    )
    ns = {
        'DBASE_NEW_MENU': DBASE_NEW_MENU, 'DBASE_GROUP_NEW_MENU': DBASE_GROUP_NEW_MENU,
        'DBaseProjectOpenFileDialog': Dialog, 'DBaseProjectWarningDialog': Warning,
        'QDialog': SimpleNamespace(Accepted=1), 'Path': Path,
        'can_open_dbase_project_file': lambda p: allow_access and can_open_dbase_project_file(p),
        'is_dbase_program_text': is_dbase_program_text,
        'create_dbase_project_file': create_dbase_project_file,
    }
    node = ast.parse('class Host:\n' + _method_source('_new_dbase_project_file')).body[0].body[0]
    exec(compile(ast.Module(body=[node], type_ignores=[]), '<stage434 workflow>', 'exec'), ns)
    ns['_new_dbase_project_file'](host, 'programs')
    return calls, notices


def test_end_to_end_create_and_open_do_not_overwrite(tmp_path):
    name = tmp_path / 'Programm1.prg'
    calls, notices = _simulate_project_workflow(tmp_path, name, 'create')
    assert name.is_file() and name.read_bytes() == b''
    assert not notices
    assert [c[0] for c in calls] == ['added', 'opened']
    name.write_bytes(b'? 123\n')
    calls, notices = _simulate_project_workflow(tmp_path, name, 'open')
    assert name.read_bytes() == b'? 123\n'
    assert not notices
    assert [c[0] for c in calls] == ['added', 'opened']
    calls, notices = _simulate_project_workflow(tmp_path, name, 'create')
    assert calls == []
    assert notices == ['Die angegebene Datei existiert bereits']
    assert name.read_bytes() == b'? 123\n'


def test_end_to_end_denied_open_does_not_add_file(tmp_path):
    name = tmp_path / 'NoRead.prg'
    name.write_bytes(b'? 123\n')
    calls, notices = _simulate_project_workflow(tmp_path, name, 'open', allow_access=False)
    assert calls == []
    assert notices == ['Sie haben nicht die benötigten Rechte um die ausgewählte Datei zu öffnen/bearbeiten']
