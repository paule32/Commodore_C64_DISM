# -*- coding: utf-8 -*-
"""Stage 687: THLP imports, directive highlighter, global F1 loading prelude.

Qt-free functional tests supplement native Qt visual verification on Windows.
"""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
import ast
import textwrap

from dock_opening_prelude import DOCK_OPENING_TITLES, install_dock_opening_preludes
from turbo_help_syntax import HELP_DIRECTIVE_PATTERN

HERE = Path(__file__).resolve().parent
SOURCE = (HERE / 'd64_dism.py').read_text(encoding='utf-8')


def extract_method(name):
    start = SOURCE.index(f'        def {name}(')
    end = SOURCE.find('\n        def ', start + 16)
    return textwrap.dedent(SOURCE[start:end if end >= 0 else None])


def test_highlighter_matches_exact_five_keywords_case_insensitively():
    for item in ('%topic', '%include', '%ref', '%anchor', '%link'):
        assert [m.group() for m in HELP_DIRECTIVE_PATTERN.finditer(item + ' "Hello"')] == [item]
        assert [m.group() for m in HELP_DIRECTIVE_PATTERN.finditer(item.upper())] == [item.upper()]
    assert not list(HELP_DIRECTIVE_PATTERN.finditer('topic include %reference %includes %topic_extra %'))
    assert [m.group() for m in HELP_DIRECTIVE_PATTERN.finditer('%topic "x" %ref 12')] == ['%topic', '%ref']


def test_actual_qsyntax_highlighter_formats_only_directive_spans():
    source = (HERE/'turbo_help_editor_widgets.py').read_text(encoding='utf-8')
    begin = source.index('class TurboHelpDirectiveHighlighter(')
    end = source.index('\nclass TurboHelpLineNumberArea(', begin)

    class FakeHighlighter:
        def __init__(self, document):
            self.doc = document
            self.spans = []
        def setFormat(self, start, length, fmt):
            self.spans.append((start, length, fmt.color))

    class FakeFormat:
        def setForeground(self, color):
            self.color = color

    # Execute actual class using only lightweight Qt stand-ins.
    namespace = {'QSyntaxHighlighter': FakeHighlighter,
                 'QTextCharFormat': FakeFormat, 'QColor': lambda value: value}
    exec(compile(source[begin:end], 'turbo_help_editor_widgets.py', 'exec'), namespace)
    # turbo_help_syntax is a real import in the class constructor.
    highlight = namespace['TurboHelpDirectiveHighlighter'](object())
    line = '%topic "foo" %include "bar" %ref X %anchor Y %link Z'
    highlight.highlightBlock(line)
    assert [line[pos:pos+size] for pos,size,_ in highlight.spans] == [
        '%topic', '%include', '%ref', '%anchor', '%link']
    assert all(color == '#ff981f' for _,_,color in highlight.spans)


def test_import_existing_thlp_under_selected_folder_or_leaf(tmp_path):
    root_dir = tmp_path/'root'; root_dir.mkdir()
    nested = root_dir/'Nested'; nested.mkdir()
    src = tmp_path/'existing.thlp'; src.write_text('%topic "old"\n', encoding='utf-8')
    wrong = tmp_path/'bad.txt'; wrong.write_text('no',encoding='utf-8')
    duplicates = []

    class Qt:
        UserRole = 100

    class FakeItem:
        def __init__(self, kind, directory, parent=None):
            self.kind, self.directory, self._parent = kind, directory, parent
        def parent(self):
            return self._parent
        def data(self, column, role):
            return str(self.directory)

    root = FakeItem('root', root_dir)
    folder = FakeItem('folder', nested, root)
    leaf = FakeItem('file', nested/'Chapter.thlp', folder)
    ns = {
        'Path': Path, 'Qt': Qt,
        'PROJECT_NODE_TURBO_HELP_ROOT': 'root',
        'PROJECT_NODE_TURBO_HELP_FOLDER': 'folder',
        'PROJECT_NODE_TURBO_HELP_FILE': 'file',
        'QFileDialog': SimpleNamespace(getOpenFileNames=lambda *_args: ([str(src), str(wrong)], '')),
    }
    exec(compile(extract_method('_project_turbo_help_add'), 'd64_dism.py', 'exec'), ns)

    class FakeWindow:
        project_turbo_help_root = root
        current_project_path = None
        current_directory = root_dir
        def _project_item_kind(self, item):
            return item.kind if item else ''
        def _turbo_help_root_directory(self):
            return root_dir
        def _add_project_turbo_help_file(self, path, *, parent=None):
            duplicates.append((Path(path),parent))
        def _turbo_help_sync_editor(self):
            self.synced = True

    window = FakeWindow()
    window._project_turbo_help_add = ns['_project_turbo_help_add'].__get__(window)
    window._project_turbo_help_add(root)
    window._project_turbo_help_add(folder)
    window._project_turbo_help_add(leaf)
    assert duplicates == [(src,root),(src,folder),(src,folder)]
    assert window.synced
    assert src.read_text(encoding='utf-8') == '%topic "old"\n'


def test_context_menu_places_file_import_immediately_after_content_creation():
    menu = extract_method('_project_turbo_help_context')
    assert '"Inhalt hinzufügen", "Datei hinzufügen"' in menu
    assert 'elif choice is actions["Datei hinzufügen"]:' in menu
    assert 'self._project_turbo_help_add(item)' in menu
    assert '"Ordner hinzufügen", "Ordner löschen"' in menu
    assert 'menu.addSeparator()' in menu
    ast.parse(menu)


def test_f1_uses_existing_splash_before_viewer_modal():
    assert DOCK_OPENING_TITLES['show_chm_viewer'] == 'Hilfe'

    class Window:
        _dock_prelude_ready = True
        _dock_prelude_dispatching = False
        _operation_prelude = None
        _operation_prelude_executing = False
        def __init__(self):
            self.events = []
        def run_with_operation_prelude(self, title, message, operation):
            self.events.append(('splash', title, message))
            self.pending = operation
            return True
        def show_chm_viewer(self, _checked=False, *, context_word=''):
            self.events.append(('open', _checked, context_word))

    cls = type('RuntimeWindow', (Window,), {'show_chm_viewer': Window.show_chm_viewer})
    assert 'show_chm_viewer' in install_dock_opening_preludes(cls)
    obj = cls()
    assert obj.show_chm_viewer(False, context_word='index') is True
    assert obj.events == [('splash', 'Hilfe', 'Hilfe wird geladen …')]
    assert obj.pending() is True
    assert obj.events[-1] == ('open', False, 'index')

    body = SOURCE[SOURCE.index('        def show_chm_viewer('):SOURCE.index('        def show_system_information_dialog(')]
    assert body.index('prelude.hide()') < body.index('dialog.exec_()')
    assert body.index('dialog.open_chm(') < body.index('prelude.hide()')
    assert 'install_dock_opening_preludes(ExplorerWindow)' in SOURCE
    assert SOURCE.index('install_dock_opening_preludes(ExplorerWindow)') < SOURCE.index('window = ExplorerWindow(initial_directory)')


def test_changed_python_modules_compile():
    for name in ('turbo_help_editor_widgets.py', 'turbo_help_syntax.py', 'dock_opening_prelude.py'):
        ast.parse((HERE/name).read_text('utf-8'))
