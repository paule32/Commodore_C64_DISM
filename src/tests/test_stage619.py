"""Stage 619: dBASE ?/?? Debug-QDialog, explizite Console-Ausgabe."""
from pathlib import Path

from d64dbase.compiler import compile_dbase_to_assembly, dbase_uses_debug_output


def compiled(source, target="pe32"):
    return compile_dbase_to_assembly(
        source, filename="druck_test.prg", target=target
    )


def test_default_print_uses_debug_transcript():
    result = compiled('? "Hihi"')
    assert result.debug_transcript == 'Hihi\r\n'
    assert result.transcript == ''
    assert result.uses_debug_output
    assert dbase_uses_debug_output('? "Hihi"')


def test_default_output_has_initialized_data_flag_not_bss():
    result = compiled('? "Hihi"')
    asm = result.assembly
    assert '__dbase_output_format_screen:\n    dd 1' in asm
    assert '__dbase_output_format_screen:\n    resd 1' not in asm
    assert '__dbase_output_debug_override:\n    dd -1' in asm
    # Branch selecting DEBUG output must exist and call bridge's real output API.
    assert 'call DBaseQtSetDebugVisible' in asm
    assert 'call DBaseQtAppendDebug' in asm
    assert 'call DBaseConsoleWrite' in asm  # explicit CONSOLE runtime branch is retained


def test_question_mark_and_double_question_mark_newline():
    result = compiled('?? "Hallo "\n? "Welt"')
    assert result.debug_transcript == 'Hallo Welt\r\n'
    assert result.transcript == ''


def test_explicit_console_routes_to_native_console():
    result = compiled('SET FORMAT TO CONSOLE\n? "Konsole"\nSET FORMAT TO SCREEN\n? "Debug"')
    assert result.transcript == 'Konsole\r\n'
    assert result.debug_transcript == 'Debug\r\n'


def test_set_debug_off_and_on_override():
    result = compiled('SET DEBUG OFF\n? "A"\nSET DEBUG ON\n? "B"')
    assert result.transcript == 'A\r\n'
    assert result.debug_transcript == 'B\r\n'


def test_debug_off_overrides_format_screen():
    result = compiled('SET DEBUG OFF\nSET FORMAT TO SCREEN\n? "A"')
    assert result.transcript == 'A\r\n'
    assert result.debug_transcript == ''


def test_windows64_default_is_debug_too():
    result = compiled('? "Hihi"', 'pe64')
    assert result.debug_transcript == 'Hihi\r\n'
    assert '__dbase_output_format_screen:\n    dd 1' in result.assembly
    assert 'call DBaseQtAppendDebug' in result.assembly


def test_bridge_shows_separate_qdialog():
    source = (Path(__file__).resolve().parent / 'd64qt5' / 'd64qt5_bridge.cpp').read_text(encoding='utf-8')
    assert 'show_wfm_output_dialog(nullptr);' in source
    assert 'append_wfm_output(QString::fromLocal8Bit(text, length), false);' in source
    assert 'Normaler .prg-/Konsolenmodus behält den bestehenden DEBUG-Tab' not in source


def test_debug_on_preserves_workstation_pipe():
    source = (Path(__file__).resolve().parent / 'd64qt5' / 'd64qt5_bridge.cpp').read_text(encoding='utf-8')
    assert 'if (dbase_use_runner_debug_pipe() &&' in source
    assert 'send_wfm_output_to_workstation(QByteArray(text, length), false)' in source
