# -*- coding: utf-8 -*-
"""Stage 652: GNU-format HLP, project sources and Qt5 DEBUG viewer integration."""
from pathlib import Path
import gettext
import io
import re

import pytest
from turbo_help_compiler import HelpCompiler, HelpCompileError, write_mo
from turbo_help_sidecar import install_help_catalog, compile_project_help

ROOT = Path(__file__).resolve().parent
GUI = (ROOT/'turbo_help_gui.py').read_text(encoding='utf-8')
MAIN = (ROOT/'d64_dism.py').read_text(encoding='utf-8')
CPP = (ROOT/'d64qt5/d64qt5_bridge.cpp').read_text(encoding='utf-8')
HEADER = (ROOT/'d64qt5/d64_turbo_help_window.hpp').read_text(encoding='utf-8')


def test_multiple_project_sources_and_duplicate_includes(tmp_path):
    first = tmp_path/'main.thlp'
    second = tmp_path/'other.thlp'
    first.write_text('%topic "index"\nStart\n%include "other.thlp"\n', encoding='utf-8')
    second.write_text('%topic "Kapitel"\n<b>Text</b>\n', encoding='utf-8')
    result = HelpCompiler.compile_files([first, second])
    assert list(result) == ['index', 'Kapitel']
    assert result['Kapitel'] == '<b>Text</b>'


def test_duplicate_topics_rejected_across_sources(tmp_path):
    first = tmp_path/'main.thlp'
    second = tmp_path/'other.thlp'
    first.write_text('%topic "index"\nStart', encoding='utf-8')
    second.write_text('%topic "index"\nAgain', encoding='utf-8')
    with pytest.raises(HelpCompileError, match='schon'):
        HelpCompiler.compile_files([first, second])


def test_compiler_from_project_outputs_exe_stem_hlp(tmp_path):
    source = tmp_path/'sources'/'Help.thlp'
    source.parent.mkdir()
    source.write_text('%topic "index"\nWillkommen\n', encoding='utf-8')
    exe = tmp_path/'output'/'App.exe'
    exe.parent.mkdir()
    exe.write_bytes(b'MZ')
    hlp = compile_project_help([source], exe)
    assert hlp == exe.parent/'App.hlp'
    assert (source.parent/'App.po').is_file()
    catalog = gettext.GNUTranslations(fp=io.BytesIO(hlp.read_bytes()))
    assert catalog.gettext('index') == 'Willkommen'


def test_install_hlp_sidecar_validates_and_preserves_old_when_invalid(tmp_path):
    exe = tmp_path/'App.exe'
    exe.write_bytes(b'MZ')
    target = tmp_path/'App.hlp'
    target.write_bytes(b'previous')
    invalid = tmp_path/'invalid.hlp'
    invalid.write_bytes(b'garbage')
    with pytest.raises(ValueError):
        install_help_catalog(exe, invalid)
    assert target.read_bytes() == b'previous'
    valid = tmp_path/'valid.hlp'
    valid.write_bytes(write_mo({'index':'OK'}))
    assert install_help_catalog(exe, valid) == target
    assert gettext.GNUTranslations(io.BytesIO(target.read_bytes())).gettext('index') == 'OK'


def test_project_root_source_persistence_and_menu():
    for fragment in (
        'PROJECT_TURBO_HELP_ENTRY_KEY', 'PROJECT_TURBO_HELP_SECTION',
        'PROJECT_NODE_TURBO_HELP_ROOT', 'PROJECT_NODE_TURBO_HELP_FILE',
        'QTreeWidgetItem(self.project_tree, ["Turbo Help"])',
        'def _project_turbo_help_context', '"Neu:  Inhalt"',
        '"Hinzufügen"', '"Entfernen"', 'self._project_turbo_help_open(item)',
        'def _turbo_help_document_saved', 'PROJECT_TURBO_HELP_ENTRY_KEY].append',
        'compile_project_help(_help_sources, output_path)',
    ):
        assert fragment in MAIN, fragment
    assert 'Category.TurboHelp' in MAIN


def test_tabbed_editor_closes_only_after_successful_save():
    assert 'QTabWidget(self)' in GUI
    assert "setObjectName('turbo_help_source_tabs')" in GUI
    assert 'setTabButton(index' in GUI
    assert "color:#e93232" in GUI
    assert 'edit.document().isModified() or self._path_for(edit) is None' in GUI
    assert 'if not self._save_edit(edit):' in GUI
    assert 'self.tabs.removeTab(index)' in GUI
    assert "QShortcut(QKeySequence('F2'), self)" in GUI
    assert 'compile_help_sources(paths, executable)' in GUI


def test_bridge_loads_executable_named_hlp_f1_and_resize():
    assert 'QStringLiteral(".hlp")' in CPP
    assert 'exeInfo.completeBaseName()' in CPP
    assert 'DBaseQtHelpShowMo(nullptr)' in CPP
    assert 'QShortcut(QKeySequence(Qt::Key_F1), g_window)' in CPP
    assert 'Qt::ApplicationShortcut' in CPP
    assert 'new D64TurboHelpWindow(g_console->viewport())' in CPP
    assert 'dbaseTurboHelpResizeGrip' in HEADER
    assert 'Qt::SizeFDiagCursor' in HEADER
    assert 'bool resizing_ = false;' in HEADER
    assert 'void resizeEvent(QResizeEvent *event) override' in HEADER
    assert 'toggleMaximized()' in HEADER
    assert 'browser_->clear()' in HEADER
    assert '<EXE-Stamm>.hlp' in CPP


def test_main_syntax_with_lazy_soft_keyword_normalized_only_for_test():
    # The original source requires Python 3.15 lazy-import support.
    source = re.sub(r'(?m)^([ \t]*)lazy[ \t]+from[ \t]+', r'\1from ', MAIN)
    source = re.sub(r'(?m)^([ \t]*)lazy[ \t]+import[ \t]+', r'\1import ', source)
    compile(source, 'd64_dism.py', 'exec')
