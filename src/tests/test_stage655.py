# -*- coding: utf-8 -*-
"""Stage 655: project-profile F2 HLP output and native console help viewer."""
from __future__ import annotations
import ast
import gettext
import io
import re
import textwrap
from pathlib import Path
from types import SimpleNamespace

import pytest
from turbo_help_sidecar import compile_help_sources, compile_project_help

ROOT = Path(__file__).resolve().parent
MAIN = (ROOT / 'd64_dism.py').read_text('utf-8')
EDITOR = (ROOT / 'turbo_help_gui.py').read_text('utf-8')
BRIDGE = (ROOT / 'd64qt5/d64qt5_bridge.cpp').read_text('utf-8')
VIEWER = (ROOT / 'd64qt5/d64_turbo_help_window.hpp').read_text('utf-8')


def test_f2_creates_project_named_hlp_without_existing_exe(tmp_path):
    source = tmp_path / 'src' / 'NotTheOutputName.thlp'
    source.parent.mkdir()
    source.write_text('%topic "index"\nHallo\n', encoding='utf-8')
    exe = tmp_path / 'bin' / 'AppDB.exe'
    assert not exe.exists()
    topics, po, hlp = compile_help_sources([source], exe)
    assert topics == {'index': 'Hallo'}
    assert po == source.parent / 'AppDB.po'
    assert hlp == exe.with_suffix('.hlp')
    assert hlp.is_file() and not exe.exists()
    assert not source.with_suffix('.hlp').exists()
    assert gettext.GNUTranslations(io.BytesIO(hlp.read_bytes())).gettext('index') == 'Hallo'


def test_multiple_tabs_do_not_determine_output_name(tmp_path):
    src = tmp_path / 'sources'
    src.mkdir()
    a, b = src / 'alpha.thlp', src / 'beta.thlp'
    a.write_text('%topic "index"\nStart\n', encoding='utf-8')
    b.write_text('%topic "Details"\nNoch mehr\n', encoding='utf-8')
    topics, po, hlp = compile_help_sources([a,b], tmp_path / 'build' / 'OtherApp.exe')
    assert set(topics) == {'index', 'Details'}
    assert po.name == 'OtherApp.po' and hlp.name == 'OtherApp.hlp'
    reader = gettext.GNUTranslations(io.BytesIO(hlp.read_bytes()))
    assert reader.gettext('Details') == 'Noch mehr'


def test_link_mode_still_requires_exe(tmp_path):
    source = tmp_path/'source.thlp'
    source.write_text('%topic "index"\nText\n', encoding='utf-8')
    with pytest.raises(FileNotFoundError):
        compile_project_help([source], tmp_path/'output'/'NotYet.exe')
    exe = tmp_path/'output'/'NamedApp.exe'
    exe.parent.mkdir()
    exe.write_bytes(b'MZ')
    assert compile_project_help([source], exe) == exe.with_suffix('.hlp')


def _make_resolver():
    name = '_turbo_help_project_executable'
    begin = MAIN.index(f'        def {name}(')
    end = MAIN.index('\n        def ', begin + 14)
    method = textwrap.dedent(MAIN[begin:end])
    scope = {'Path': Path, 're': re}
    exec(compile(method, 'd64_dism.py', 'exec'), scope)
    return scope[name]


class StubWindow:
    def __init__(self, dir32, dir64=None, target=None):
        self._named_project_names = {'dbase_program': 'AppDB', 'dbase_library': 'Runtime'}
        self.current_directory = dir32
        self.dir32 = dir32
        self.dir64 = dir64
        self.target = target
    def _project_named_current_scope(self): return ('dbase','program')
    def _project_windows_language_output_path(self, target, lang):
        assert lang == 'dbase'
        return self.dir32 if target == 'pe32' else self.dir64
    def current_document(self):
        if self.target:
            return SimpleNamespace(is_dbase_document=True, build_target=self.target)
        return None


def test_named_project_combo_and_output_dir(tmp_path):
    run = _make_resolver()
    win = StubWindow(tmp_path / 'out32', tmp_path / 'out64', 'pe64')
    assert run(win) == tmp_path/'out64'/'AppDB.exe'
    win.target = 'pe32'
    assert run(win) == tmp_path/'out32'/'AppDB.exe'
    win.target = None
    win.dir64 = None
    assert run(win) == tmp_path/'out32'/'AppDB.exe'
    win._named_project_names['dbase_program'] = 'MyCustom.exe'
    assert run(win) == tmp_path/'out32'/'MyCustom.exe'
    win._named_project_names['dbase_program'] = '../insecure'
    with pytest.raises(ValueError, match='Ungültiger'):
        run(win)
    win._named_project_names['dbase_program'] = 'AppDB'
    win._project_named_current_scope = lambda: ('pascal','program')
    with pytest.raises(ValueError, match='dBASE-Programm'):
        run(win)


def test_f2_uses_project_profile_callback_not_thlp_tab_name():
    assert 'editor.resolve_output_executable = self._turbo_help_project_executable' in MAIN
    assert 'executable = Path(self.resolve_output_executable())' in EDITOR
    assert 'compile_help_sources(paths, executable)' in EDITOR
    assert "hlp_path = main.parent" not in EDITOR


def test_qt_bridge_help_on_console_and_scrollbars_always_visible():
    fragment = BRIDGE[BRIDGE.index('extern "C" D64QT5_API int DBaseQtHelpShowMo'):]
    assert 'select_console();' in fragment
    assert 'new D64TurboHelpWindow(g_console->viewport())' in fragment
    assert 'new D64TurboHelpWindow(g_debug->viewport())' not in fragment
    assert 'install_debug_tab(true)' not in fragment[:1300]
    # Stage 656: only the console's child windows show scrollbars.
    assert 'g_console->setHorizontalScrollBarPolicy(Qt::ScrollBarAlwaysOff);' in BRIDGE
    assert 'g_console->setVerticalScrollBarPolicy(Qt::ScrollBarAlwaysOff);' in BRIDGE
    assert 'g_debug->setHorizontalScrollBarPolicy(Qt::ScrollBarAlwaysOn);' in BRIDGE
    assert 'g_debug->setVerticalScrollBarPolicy(Qt::ScrollBarAlwaysOn);' in BRIDGE
    assert 'browser_->setHorizontalScrollBarPolicy(Qt::ScrollBarAlwaysOn);' in VIEWER
    assert 'browser_->setVerticalScrollBarPolicy(Qt::ScrollBarAlwaysOn);' in VIEWER
    assert 'editor == g_debug ? QColor(QStringLiteral("#d3d3d3"))' in BRIDGE
    assert 'QPlainTextEdit#dbaseDebug{color:#d3d3d3;' in BRIDGE
    assert 'QShortcut(QKeySequence(Qt::Key_F1), g_window)' in BRIDGE
