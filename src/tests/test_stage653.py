# -*- coding: utf-8 -*-
"""Stage 653: no turbo_help_host executable; F1 opens HLP in native Qt5 DLL."""
from pathlib import Path
import gettext
import io
import re

from turbo_help_compiler import HelpCompiler, write_mo
from turbo_help_sidecar import compile_project_help

ROOT = Path(__file__).resolve().parent
MAIN = (ROOT/'d64_dism.py').read_text('utf-8')
BRIDGE = (ROOT/'d64qt5/d64qt5_bridge.cpp').read_text('utf-8')
VIEWER = (ROOT/'d64qt5/d64_turbo_help_window.hpp').read_text('utf-8')


def test_all_build_entrypoints_exclude_help_host():
    current = (ROOT/'build_and_deploy_dbase_editor_stage653.bat').read_text('utf-8')
    assert 'call "%BASE%d64qt5\\build_d64qt5_mingw32.bat"' in current
    assert 'copy /y "%SOURCE%" "%TARGET%\\libd64_qt5.dll"' in current
    assert 'g++ ' not in current
    for stage in (651, 652):
        legacy = (ROOT/f'build_and_deploy_dbase_editor_stage{stage}.bat').read_text('utf-8')
        assert 'call "%~dp0build_and_deploy_dbase_editor_stage653.bat" %*' in legacy
    assert not (ROOT/'d64qt5/turbo_help_host.cpp').exists()
    assert not (ROOT/'turbo_help_bridge_host.py').exists()
    assert not list(ROOT.rglob('turbo_help_host.exe'))


def test_f2_compiles_without_starting_a_new_process():
    section = MAIN[MAIN.index('def _turbo_help_compiled(self, topics'):]
    section = section[:section.index('# Stage ASM 10: grafischer dBase SQL Builder.')]
    assert 'self._turbo_help_catalog_path = Path(mo_path).resolve()' in section
    assert 'self._turbo_help_process' not in section
    assert 'subprocess' not in section
    assert 'launch_bridge_help' not in section
    assert 'F1' in section


def test_global_f1_for_both_console_and_debug_in_bridge():
    assert 'create_standard_menu();' in BRIDGE
    assert 'g_debug = new QPlainTextEdit(g_debug_frame)' in BRIDGE
    assert 'QShortcut(QKeySequence(Qt::Key_F1), g_window)' in BRIDGE
    assert 'helpF1->setContext(Qt::ApplicationShortcut)' in BRIDGE
    assert 'helpF1->setAutoRepeat(false)' in BRIDGE
    assert 'DBaseQtHelpShowMo(nullptr)' in BRIDGE
    implementation = BRIDGE[BRIDGE.index('extern "C" D64QT5_API int DBaseQtHelpShowMo'):]
    assert 'exeInfo.completeBaseName() + QStringLiteral(".hlp")' in implementation
    assert 'select_console();' in implementation
    assert 'new D64TurboHelpWindow(g_console->viewport())' in implementation
    assert 'g_turbo_help_window->openMo(resolved, &error)' in implementation
    assert 'g_turbo_help_window->raise();' in implementation
    assert 'browser_->clear(); // Replace the previous topic' in VIEWER
    assert 'dbaseTurboHelpResizeGrip' in VIEWER


def test_binary_hlp_compiled_next_to_generated_exe(tmp_path):
    source = tmp_path/'project'/'Help.thlp'
    source.parent.mkdir()
    source.write_text('%topic "index"\n<b>Welcome</b>\n', encoding='utf-8')
    exe = tmp_path/'output'/'ProjectApp.exe'
    exe.parent.mkdir()
    exe.write_bytes(b'MZ')
    dest = compile_project_help([source], exe)
    assert dest == exe.parent/'ProjectApp.hlp'
    translations = gettext.GNUTranslations(io.BytesIO(dest.read_bytes()))
    assert translations.gettext('index') == '<b>Welcome</b>'
