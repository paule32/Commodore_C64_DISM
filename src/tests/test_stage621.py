"""Stage 621: realer dBASE-Ausgabepfad + lokaler DEBUG-QDialog."""
from pathlib import Path
import re
from d64dbase import compile_dbase_to_assembly

ROOT = Path(__file__).resolve().parent
BRIDGE = (ROOT / 'd64qt5' / 'd64qt5_bridge.cpp').read_text(encoding='utf-8')


def compiled(source: str, target: str = 'pe32'):
    return compile_dbase_to_assembly(source, target=target, filename='stage621.prg')


def test_dbase_default_uses_debug():
    result = compiled('? "Hihi"')
    assert result.debug_transcript == 'Hihi\r\n'
    assert result.transcript == ''
    assert '__dbase_output_format_screen:\n    dd 1' in result.assembly
    assert 'call DBaseQtAppendDebug' in result.assembly


def test_dbase_pe64_uses_debug_too():
    result = compiled('? "Hihi"', 'pe64')
    assert result.debug_transcript == 'Hihi\r\n'
    assert 'call DBaseQtAppendDebug' in result.assembly


def test_double_question_mark_preserves_no_newline():
    assert compiled('?? "Hi"').debug_transcript == 'Hi'


def test_explicit_console_is_kept():
    result = compiled('SET FORMAT TO CONSOLE\n? "Konsole"\nSET FORMAT TO SCREEN\n? "Debug"')
    assert result.transcript == 'Konsole\r\n'
    assert result.debug_transcript == 'Debug\r\n'


def test_set_debug_off_is_kept():
    result = compiled('SET DEBUG OFF\n? "Konsole"\nSET DEBUG ON\n? "Debug"')
    assert result.transcript == 'Konsole\r\n'
    assert result.debug_transcript == 'Debug\r\n'


def test_ensure_dialog_has_no_prg_guard():
    section = BRIDGE.split('static void ensure_wfm_output_dialog()\n{',1)[1].split('static void show_wfm_output_dialog(',1)[0]
    # Exakt die bisherige Abbruchbedingung im Code darf nicht mehr existieren.
    assert 'if (!g_wfm_gui_mode && !g_workstation_mode_enabled)' not in re.sub(r'//[^\n]*', '', section)
    assert 'if (!g_wfm_gui_mode)\n        return;' not in section
    assert 'new DBaseDebugOutputDialog(nullptr)' in section


def test_debug_writes_to_dialog_in_prg_mode():
    section = BRIDGE.split('extern "C" D64QT5_API void DBaseQtAppendDebug(',1)[1].split('extern "C" D64QT5_API int DBaseQtSetColorNormal(',1)[0]
    assert 'append_wfm_output(QString::fromLocal8Bit(text, length), false);' in section
    assert 'send_wfm_output_to_workstation(QByteArray(text, length), false)' in section


def test_debug_writer_shows_dialog_when_visible():
    section = BRIDGE.split('static void append_wfm_output(const QString &value, bool newline)\n{',1)[1].split('// Stage 498:',1)[0]
    assert 'if (g_debug_visible)' in section
    assert 'show_wfm_output_dialog(nullptr);' in section


def test_visible_grey_foreground_both_themes():
    section = BRIDGE.split('static void apply_wfm_debug_theme()\n{',1)[1].split('static bool g_wfm_debug_context_menu_active',1)[0]
    assert 'color:#d0d0d0' in section
    assert 'color:#454545' in section
    assert 'palette.setColor(QPalette::Text' in section


def test_build_deploy_script_matches_runtime_dll_name():
    bat = (ROOT / 'build_and_deploy_dbase_debug_stage621.bat').read_text(encoding='utf-8')
    assert 'build_d64qt5_mingw32.bat' in bat
    assert 'runtime\\dbase\\pe32' in bat
    assert 'libd64_qt5.dll' in bat
