"""Stage 651: Python compiler/editor vs native C++ DEBUG help viewer."""
from __future__ import annotations

import gettext
import io
from pathlib import Path
import re
import struct

import pytest

from turbo_help_compiler import HelpCompiler, HelpCompileError, read_po, write_mo, write_po

ROOT = Path(__file__).resolve().parent
BRIDGE = (ROOT/'d64qt5/d64qt5_bridge.cpp').read_text('utf-8')
HEADER = (ROOT/'d64qt5/d64_turbo_help_window.hpp').read_text('utf-8')
GUI = (ROOT/'d64_dism.py').read_text('utf-8')
EDITOR = (ROOT/'turbo_help_gui.py').read_text('utf-8')


def test_compiler_source_includes_topics_refs_links_and_anchors(tmp_path):
    p = tmp_path/'help.thlp'
    ext = tmp_path/'section.thlp'
    p.write_text('''%topic "index"
<b>Hilfe</b>
%ref "Kapitel 2" #anker1
%link 'Kapitel 2'
%include "section.thlp"
''', encoding='utf-8')
    ext.write_text('''%topic 'Kapitel 2'
%anchor #anker1
Seite 2
%link "index"
''', encoding='utf-8')
    topics = HelpCompiler(p).compile()
    assert list(topics) == ['index', 'Kapitel 2']
    assert "<ref>'Kapitel 2' #anker1</ref>" in topics['index']
    assert "<link>'Kapitel 2'</link>" in topics['index']
    assert '<anchor id="anker1"></anchor>' in topics['Kapitel 2']
    po = write_po(topics)
    assert 'msgid "Kapitel 2"' in po
    assert 'msgstr ' in po
    assert read_po(po)['index'] == topics['index']
    mo = write_mo(read_po(po))
    assert struct.unpack_from('<I', mo)[0] == 0x950412DE
    translated = gettext.GNUTranslations(fp=io.BytesIO(mo))
    assert translated.gettext('Kapitel 2') == topics['Kapitel 2']
    assert translated.gettext('index') == topics['index']


def test_include_cycle_rejected(tmp_path):
    p = tmp_path/'main.thlp'
    p.write_text('%topic "index"\n%include "main.thlp"\n', encoding='utf-8')
    with pytest.raises(HelpCompileError, match='Zyklisches'):
        HelpCompiler(p).compile()


def test_unknown_topic_source_rejected(tmp_path):
    p = tmp_path/'empty.thlp'
    p.write_text('%topic "other"\nDaten\n', encoding='utf-8')
    with pytest.raises(HelpCompileError, match='index'):
        HelpCompiler(p).compile()


def test_ide_menu_editor_f2_and_no_python_viewer():
    assert 'QAction("Hilfecompiler", self)' in GUI
    assert 'tools_menu.addAction(self.turbo_help_compiler_action)' in GUI
    assert 'def show_turbo_help_compiler_dock(self' in GUI
    assert "QShortcut(QKeySequence('F2'), self)" in EDITOR
    assert 'self.compile_shortcut.activated.connect(self.compile_help)' in EDITOR
    assert 'self.compiled.emit(dict(topics), str(po_path), str(hlp_path))' in EDITOR
    assert 'class TurboHelpWindow(' not in EDITOR
    assert 'def _turbo_help_compiled(self, topics, po_path: str, mo_path: str)' in GUI
    assert 'launch_bridge_help(' not in GUI


def test_native_bridge_is_console_viewport_and_only_renders_mo():
    assert 'DBaseQtHelpShowMo(const char *utf8File)' in BRIDGE
    assert 'select_console();' in BRIDGE[BRIDGE.index('extern "C" D64QT5_API int DBaseQtHelpShowMo'):][:2500]
    assert 'new D64TurboHelpWindow(g_console->viewport())' in BRIDGE
    assert 'QFile file(filename);' in HEADER
    assert 'loaded.contains(QStringLiteral("index"))' in HEADER
    assert 'setOpenLinks(false)' in HEADER
    assert 'setOpenExternalLinks(false)' in HEADER
    assert 'browser_->clear(); // Replace the previous topic' in HEADER
    assert 'Qt::SizeAllCursor' in HEADER
    assert 'QEvent::MouseButtonDblClick' in HEADER
    assert 'toggleMaximized()' in HEADER
    assert 'QStringLiteral("Hilfe")' in HEADER
    assert 'Qt::NoContextMenu' in HEADER
    assert 'def compile_help' not in HEADER
    assert 'QAction("Hilfecompiler"' not in BRIDGE
    assert 'DBaseQtHelpShowMo @1017' in (ROOT/'d64qt5/d64qt5_bridge.def').read_text('utf-8')


def test_about_contextmenu_disabled_but_other_dialogs_keep_theirs():
    text = (ROOT/'d64qt5/d64_turbo_messagebox.hpp').read_text('utf-8')
    assert 'if (textAlignment & Qt::AlignHCenter)' in text
    assert text.count('setContextMenuPolicy(Qt::NoContextMenu);') >= 5
    assert 'Qt::Alignment textAlignment = Qt::AlignLeft | Qt::AlignVCenter' in text


def test_native_help_requires_no_separate_host_process():
    assert not (ROOT / 'turbo_help_bridge_host.py').exists()
    assert not (ROOT / 'd64qt5/turbo_help_host.cpp').exists()
    assert 'DBaseQtHelpShowMo(nullptr)' in BRIDGE
    assert 'QShortcut(QKeySequence(Qt::Key_F1), g_window)' in BRIDGE
    assert 'Qt::ApplicationShortcut' in BRIDGE
    for version in (651, 652, 653):
        script = (ROOT / f'build_and_deploy_dbase_editor_stage{version}.bat').read_text('utf-8')
        assert 'turbo_help_host.cpp' not in script
        assert 'g++ -std=c++17' not in script
        assert 'build_and_deploy_dbase_editor_stage653.bat' in script or version == 653


# Compatibility test updated for Stage 652/653 GNU-MO-format .hlp sidecars.
# Stage 651 sidecar deployment: the IDE writes the catalog beside each EXE;
# the native Qt5 bridge itself loads it at runtime, not the Python compiler.
def test_help_sidecar_companion_to_generated_exe(tmp_path, monkeypatch):
    from turbo_help_sidecar import install_help_catalog
    from turbo_help_compiler import write_mo
    path = tmp_path / "build" / "Hello World.exe"
    path.parent.mkdir()
    path.write_bytes(b"MZ")
    source_dir = tmp_path / "help"
    source_dir.mkdir()
    source = source_dir / "System.Help.hlp"
    source.write_bytes(write_mo({'index': 'Index Inhalt', 'topic2': '<b>Zwei</b>'}))
    monkeypatch.chdir(tmp_path)
    target = install_help_catalog(path, source)
    assert target == path.with_suffix('.hlp')
    assert target.read_bytes() == source.read_bytes()
    assert source.exists()
    assert target.name == 'Hello World.hlp'
    # A second deploy is repeatable, including direct self-installation.
    assert install_help_catalog(path, target) == target


def test_help_sidecar_rejects_invalid_catalog_without_overwriting(tmp_path):
    from turbo_help_sidecar import install_help_catalog
    from turbo_help_compiler import write_mo
    exe = tmp_path / 'Test.exe'
    exe.write_bytes(b'MZ')
    valid = tmp_path / 'valid.hlp'
    valid.write_bytes(write_mo({'index': 'Version A'}))
    installed = install_help_catalog(exe, valid)
    invalid = tmp_path / 'invalid.hlp'
    invalid.write_bytes(b'kein gueltiger Katalog')
    with pytest.raises(ValueError, match='GNU-MO/HLP-Header'):
        install_help_catalog(exe, invalid)
    assert installed.read_bytes() == valid.read_bytes()
    missing_index = tmp_path / 'missing.hlp'
    missing_index.write_bytes(write_mo({'anderes': 'unvollstaendig'}))
    with pytest.raises(ValueError, match='index'):
        install_help_catalog(exe, missing_index)
    assert installed.read_bytes() == valid.read_bytes()


def test_bridge_finds_sidecar_next_to_exe_not_cwd():
    code = BRIDGE[BRIDGE.index('extern "C" D64QT5_API int DBaseQtHelpShowMo'):]
    assert 'QCoreApplication::applicationFilePath()' in code
    assert 'exeDir.filePath(exeInfo.completeBaseName() + QStringLiteral(".hlp"))' in code
    assert 'QFileInfo(path).isFile()' in code
    assert 'D64TurboHelpWindow(g_console->viewport())' in code
    assert 'DBaseQtHelpShowMo(nullptr)' in BRIDGE  # Native runtime Help > Inhalt
    assert 'compile_project_help(_help_sources, output_path)' in GUI
    assert 'output_path.suffix.casefold() == ".exe"' in GUI
