"""Stage 498: blue/yellow independent Qt5 terminal exists only on Linux."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WIN = (ROOT / 'd64qt5/d64qt5_bridge.cpp').read_text(encoding='utf-8')
LINUX = (ROOT / 'd64qt5/d64qt5_linux_form.cpp').read_text(encoding='utf-8')
PRO = (ROOT / 'd64qt5/d64qt5_bridge.pro').read_text(encoding='utf-8')


def func(source, start, end):
    return source[source.index(start):source.index(end, source.index(start))]


def test_linux_has_own_terminal_dialog_and_color_scheme():
    assert 'class DBaseTerminalDialog final : public QDialog' in LINUX
    assert 'dBASE Qt5 Terminal' in LINUX
    assert '#000080' in LINUX and '#ffff00' in LINUX
    assert 'QPlainTextEdit' in LINUX
    assert 'DBaseQtRunConsoleJson' in LINUX
    assert 'DBaseQtRunFormJson' in LINUX


def test_windows_never_constructs_linux_specific_terminal():
    for unwanted in ('append_dbase_qt_terminal', 'g_dbase_qt_terminal_dialog',
                     'g_dbase_qt_terminal_editor', 'dbaseTerminalDialog',
                     'dBASE Qt5 Terminal', '#000080; color: #ffff00'):
        assert unwanted not in WIN, unwanted


def test_windows_wfm_append_console_uses_existing_dialog_once():
    body = func(WIN, 'extern "C" D64QT5_API void DBaseQtAppendConsole(',
                'extern "C" D64QT5_API void DBaseQtAppendDebug(')
    assert 'dbase_use_runner_debug_pipe()' in body
    assert 'send_wfm_output_to_workstation(utf8, false)' in body
    assert body.count('append_wfm_output(') == 1
    assert 'append_text(g_console, text, length);' in body


def test_windows_wfm_console_write_uses_existing_dialog_and_preserves_newline():
    body = func(WIN, 'extern "C" D64QT5_API void DBaseQtConsoleWrite(',
                'extern "C" D64QT5_API void *DBaseQtFormCreate(')
    assert 'if (g_wfm_gui_mode)' in body
    assert 'send_wfm_output_to_workstation(utf8, newline != 0)' in body
    assert body.count('append_wfm_output(value, newline != 0)') == 1
    assert 'if (g_console)' in body
    assert 'if (newline)' in body


def test_windows_debug_and_focus_events_are_preserved():
    assert 'static void append_wfm_output(const QString &value, bool newline)' in WIN
    assert 'QEvent::FocusIn' in WIN and 'QEvent::FocusOut' in WIN
    assert 'ongotfocus' in WIN and 'onlostfocus' in WIN
    assert 'destroy_wfm_output_dialog();' in WIN


def test_qmake_builds_different_cpp_on_windows_and_linux():
    assert 'SOURCES += d64qt5_bridge.cpp' in PRO
    assert 'win32 {' in PRO
    assert 'unix:!macx {' in PRO
    assert 'SOURCES = d64qt5_linux_form.cpp' in PRO


def test_linux_cpp_is_original_stage497():
    # No source code change in the actual Linux runtime, only Windows routing.
    assert 'void appendJsonOutput(DBaseTerminalDialog *terminal' in LINUX
    assert 'terminal->writeText' in LINUX
