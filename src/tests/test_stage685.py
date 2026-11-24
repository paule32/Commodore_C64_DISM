"""Stage 685: nested Turbo Help project, safe paths and F2 include resolver."""
from pathlib import Path

import pytest

from turbo_help_compiler import HelpCompiler, HelpCompileError
from turbo_help_sidecar import compile_help_sources
from turbo_help_project_tree import (
    checked_child, normalize_help_name, ordered_main_sources, resolve_include,
)

HERE = Path(__file__).resolve().parent


def test_nested_help_includes_main_first_and_link_sidecar(tmp_path):
    root = tmp_path / 'Help'
    sub = root / 'Tutorials' / 'Examples'
    sub.mkdir(parents=True)
    main = root / 'Main.thlp'
    chapter = sub / 'Chapter.thlp'
    linked = sub / 'Extra.thlp'
    main.write_text('%topic "index" 1\nStart\n%include "Chapter.thlp"\nFortsetzung\n', encoding='utf8')
    chapter.write_text('%topic "chapter" 20\nKapitel\n%include "Extra.thlp"\n', encoding='utf8')
    linked.write_text('%topic "extra" 30\nBeispiel\n', encoding='utf8')
    rows = [
        {'kind': 'folder', 'path': str(sub.parent)},
        {'kind': 'file', 'path': str(chapter)},
        {'kind': 'file', 'path': str(main), 'main': True},
        {'kind': 'file', 'path': str(linked)},
    ]
    sources = ordered_main_sources(rows)
    assert sources[0] == main
    assert set(sources) == {main, chapter, linked}
    topic_map = HelpCompiler.compile_files(sources, root=root, include_paths=(root,))
    assert list(topic_map) == ['index', 'chapter', 'extra']
    assert 'Fortsetzung' in topic_map['index']
    assert 'Fortsetzung' not in topic_map['chapter']
    assert topic_map.topic_numbers == {1: 'index', 20: 'chapter', 30: 'extra'}
    result, po, hlp = compile_help_sources(sources, tmp_path / 'App.exe', root=root,
                                            include_paths=(root,))
    assert len(result) == 3
    assert po.exists() and hlp.exists()
    assert hlp.read_bytes()[:4] in (b'\xde\x12\x04\x95', b'\x95\x04\x12\xde')


def test_no_main_blocks_compilation(tmp_path):
    with pytest.raises(ValueError, match='Haupt-Eintrag'):
        ordered_main_sources([{'kind':'file','path': str(tmp_path/'A.thlp')}])
    with pytest.raises(ValueError, match='genau einen'):
        ordered_main_sources([{'kind':'file','path': 'a.thlp','main':True},
                              {'kind':'file','path': 'b.thlp','main':True}])


def test_safe_names_and_root_boundaries(tmp_path):
    assert normalize_help_name('Test') == 'Test.thlp'
    assert normalize_help_name('Library', folder=True) == 'Library'
    for bad in ('../outside', '../evil.thlp', 'C:\\evil', 'CON', '.','hello.txt','a/b'):
        with pytest.raises(ValueError):
            normalize_help_name(bad)
    root = tmp_path/'root'
    root.mkdir()
    assert checked_child(root, root, 'Page.thlp') == root/'Page.thlp'
    with pytest.raises(ValueError):
        checked_child(root, tmp_path, 'Outside.thlp')


def test_ambiguous_duplicate_include_is_rejected(tmp_path):
    root = tmp_path/'Help'
    (root/'A').mkdir(parents=True)
    (root/'B').mkdir()
    one = root/'A'/'test.thlp'
    two = root/'B'/'test.thlp'
    for path in (one, two):
        path.write_text('%topic "one"\n', encoding='utf8')
    main = root/'Main.thlp'
    main.write_text('%topic "index"\n%include "test.thlp"\n', encoding='utf8')
    with pytest.raises(ValueError, match='Mehrdeutiges'):
        resolve_include('test.thlp', main, [main, one, two], (root,))
    with pytest.raises(HelpCompileError, match='Mehrdeutiges'):
        HelpCompiler.compile_files([main, one, two], root=root, include_paths=(root,))


def test_integration_in_project_ui_and_ini():
    src = (HERE/'d64_dism.py').read_text(encoding='utf8')
    assert '"Haupt-Eintrag", "Inhalt hinzufügen", "Datei hinzufügen"' in src
    assert '"Datei umbenennen", "Inhalt löschen", None' in src
    assert '"Ordner umbenennen", "Ordner hinzufügen", "Ordner löschen"' in src
    assert '"Ordner hinzufügen", "Ordner löschen"' in src
    assert 'PROJECT_NODE_TURBO_HELP_FOLDER = "turbo_help_folder"' in src
    assert 'PROJECT_TURBO_HELP_PATH_SECTIONS' in src
    assert '"parent": str(_item.get("parent", ""))' in src
    assert '"main": bool(_item.get("main", False))' in src
    assert 'self._turbo_help_restore_tree(values.get(PROJECT_TURBO_HELP_ENTRY_KEY, ()))' in src
    assert 'self._turbo_help_sources_for_compile(target)' in src
    assert 'self._turbo_help_sources_for_compile(' in src
    assert 'self._turbo_help_mark_main(item)' in src
    assert 'from turbo_help_path_widgets import TurboHelpPathGroup' in src
    assert 'self.development_group = QGroupBox("Entwicklung:", self.input_page)' in src
    assert 'self.turbo_help_group = TurboHelpPathGroup(owner, target, self.input_content)' in src


def test_nested_qtree_project_roundtrip_without_native_qt(tmp_path):
    """Exercise actual MainWindow methods via lightweight Qt tree fakes."""
    import textwrap
    import types

    source = (HERE/'d64_dism.py').read_text(encoding='utf-8')
    names = ('_turbo_help_tree_items', '_turbo_help_file_items', '_turbo_help_folder_key',
             '_turbo_help_add_folder_item', '_add_project_turbo_help_file',
             '_turbo_help_restore_tree', '_turbo_help_collect_entries',
             '_turbo_help_mark_main', '_turbo_help_sync_editor',
             '_turbo_help_remove_item')
    blocks = []
    for name in names:
        begin = source.index(f'        def {name}(')
        end = source.find('\n        def ', begin + 16)
        blocks.append(textwrap.dedent(source[begin:end]))

    class Qt:
        UserRole = 1000
        Checked = 2
        Unchecked = 0
        ItemIsUserCheckable = 16

    class TreeItem:
        def __init__(self, parent=None, text=None):
            self._parent = parent
            self._children = []
            self._text = text or ['']
            self._data = {}
            self._check = Qt.Unchecked
            if parent is not None:
                parent._children.append(self)
        def childCount(self): return len(self._children)
        def child(self, n): return self._children[n]
        def parent(self): return self._parent
        def text(self, col): return self._text[col]
        def setText(self, col, value): self._text[col] = value
        def data(self, col, key): return self._data.get((col,key))
        def setData(self, col, key, value): self._data[col,key] = value
        def setFlags(self, value): pass
        def flags(self): return 0
        def setCheckState(self, col, value): self._check = value
        def checkState(self, col): return self._check
        def setExpanded(self, value): pass
        def setIcon(self, col, value): pass
        def setToolTip(self, col, value): pass
        def indexOfChild(self, item): return self._children.index(item)
        def takeChild(self, index): return self._children.pop(index)

    ns = {'Path':Path, 'Qt':Qt, 'QTreeWidgetItem': TreeItem,
          'QFileInfo': lambda path: path,
          'PROJECT_NODE_TURBO_HELP_ROOT': 'root',
          'PROJECT_NODE_TURBO_HELP_FOLDER': 'folder',
          'PROJECT_NODE_TURBO_HELP_FILE': 'file',
          'QStyle':types.SimpleNamespace(SP_DirClosedIcon=1)}
    exec(compile('\n\n'.join(blocks), str(HERE/'d64_dism.py'), 'exec'),ns)
    class App:
        project_turbo_help_root = None
        _project_checkbox_guard = False
        current_project_path = None
        icon_provider = types.SimpleNamespace(icon=lambda x: 'file-icon')
        style = lambda self: types.SimpleNamespace(standardIcon=lambda _: 'folder-icon')
        _turbo_help_active_editor = lambda self: None
        _project_item_kind = lambda self,item: str(item.data(0,Qt.UserRole+303) or '')
        set_project_modified = lambda self, value: None
    for name in names:
        setattr(App, name, ns[name])

    root = tmp_path / 'help'
    file1 = root/'A'/'First.thlp'
    file2 = root/'A'/'Sub'/'Second.thlp'
    app = App()
    app.project_turbo_help_root = TreeItem(text=['Turbo Hilfe'])
    app.project_turbo_help_root.setData(0,Qt.UserRole+303,'root')
    original = [
        {'kind':'folder', 'path':str(root/'A'), 'title':'A', 'parent':'','main':False},
        {'kind':'file', 'path':str(file1),'title':'First.thlp','parent':'A','main':False},
        {'kind':'folder', 'path':str(root/'A'/'Sub'), 'title':'Sub','parent':'A','main':False},
        {'kind':'file', 'path':str(file2),'title':'Second.thlp','parent':'A/Sub','main':True},
    ]
    app._turbo_help_restore_tree(original)
    records = app._turbo_help_collect_entries()
    assert records == original
    files = list(app._turbo_help_file_items())
    assert len(files) == 2
    assert files[1].checkState(0) == Qt.Checked
    app._turbo_help_mark_main(files[0])
    updated = app._turbo_help_collect_entries()
    assert updated[1]['main'] is True and updated[3]['main'] is False
    folder = app.project_turbo_help_root.child(0)
    app._turbo_help_remove_item(folder)
    assert app.project_turbo_help_root.childCount() == 0


def test_include_historical_tlhp_spelling(tmp_path):
    root = tmp_path/'help'
    root.mkdir()
    main = root/'Main.thlp'
    chapter = root/'test.thlp'
    main.write_text('%topic "index"\n%include "test.tlhp"\n', encoding='utf8')
    chapter.write_text('%topic "test"\nText\n', encoding='utf8')
    result = HelpCompiler.compile_files([main, chapter], root=root, include_paths=(root,))
    assert list(result) == ['index', 'test']
