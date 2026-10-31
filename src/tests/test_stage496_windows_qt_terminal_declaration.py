"""Stage 496 regression adapted for Stage 498: obsolete Windows dialog removed.

The former forward declaration is no longer needed, because the Windows
bridge no longer creates the Linux-specific dBASE Qt5 Terminal.
"""
from pathlib import Path

ROOT = Path(__file__).parent
CPP = (ROOT / "d64qt5" / "d64qt5_bridge.cpp").read_text(encoding="utf-8")
PRO = (ROOT / "d64qt5" / "d64qt5_bridge.pro").read_text(encoding="utf-8")


def test_no_obsolete_terminal_declaration_or_definition():
    assert "append_dbase_qt_terminal" not in CPP
    assert "g_dbase_qt_terminal_dialog" not in CPP


def test_windows_output_uses_existing_wfm_dialog():
    start = CPP.index('extern "C" D64QT5_API void DBaseQtAppendConsole(')
    end = CPP.index('extern "C" D64QT5_API void DBaseQtAppendDebug(', start)
    body = CPP[start:end]
    assert "append_wfm_output(" in body
    assert "append_text(g_console, text, length)" in body


def test_windows_console_write_keeps_original_console_tab():
    start = CPP.index('extern "C" D64QT5_API void DBaseQtConsoleWrite(')
    end = CPP.index('extern "C" D64QT5_API void *DBaseQtFormCreate(', start)
    body = CPP[start:end]
    assert "append_wfm_output(value, newline != 0);" in body
    assert "append_text(g_console, bytes.constData(), bytes.size());" in body


def test_platform_specific_qt_source_files_remain_in_build():
    assert 'SOURCES += d64qt5_bridge.cpp' in PRO
    assert 'win32 {' in PRO
    assert 'unix:!macx {' in PRO
    assert 'SOURCES = d64qt5_linux_form.cpp' in PRO


def test_single_windows_console_export_remains():
    assert CPP.count('extern "C" D64QT5_API void DBaseQtConsoleWrite(') == 1
