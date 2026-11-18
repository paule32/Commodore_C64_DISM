from pathlib import Path

ROOT = Path(__file__).resolve().parent
BRIDGE = (ROOT / 'd64qt5' / 'd64qt5_bridge.cpp').read_text(encoding='utf-8')
TURBO = (ROOT / 'd64qt5' / 'd64_turbo_output.hpp').read_text(encoding='utf-8')
COMPILER = (ROOT / 'd64dbase' / 'compiler.py').read_text(encoding='utf-8')


def test_turbo_is_child_of_existing_console_viewport():
    assert 'new D64TurboOutputWidget(g_console->viewport())' in BRIDGE
    assert 'g_turbo_output->setGridFont(make_console_grid_font())' in BRIDGE


def test_normal_programs_write_debug_into_turbo_and_not_wfm_dialog():
    assert 'g_turbo_output->appendOutput(QString::fromLocal8Bit(text, length))' in BRIDGE
    assert '!g_wfm_gui_mode && !g_workstation_mode_enabled && g_turbo_output' in BRIDGE
    assert 'g_turbo_output->show()' in BRIDGE
    assert 'g_turbo_output->hide()' in BRIDGE


def test_workstation_and_wfm_paths_remain_present():
    assert 'dbase_use_runner_debug_pipe()' in BRIDGE
    assert 'append_wfm_output(QString::fromUtf8' in BRIDGE
    assert 'DBaseQtAppendConsole' in BRIDGE


def test_turbo_grip_uses_current_character_grid():
    assert 'QFontMetrics fm(font)' in TURBO
    assert 'cellWidth_ = qMax(1, fm.horizontalAdvance' in TURBO
    assert 'cellHeight_ = qMax(1, fm.lineSpacing())' in TURBO
    assert 'dragColumns_ + dx, dragRows_ + dy' in TURBO
    assert 'requestedColumns_' in TURBO
    assert 'requestedRows_' in TURBO
    assert 'resizeInCharacters(requestedColumns_, requestedRows_)' in TURBO


def test_green_frame_scroll_and_indicator():
    for marker in ('#a6ffac', '#076b30', '#e8ffcb',
                   'Qt::ScrollBarAlwaysOn', 'Qt::ScrollBarAsNeeded',
                   'dbaseTurboVisionGridGrip', 'Zeichenraster',
                   'p.fillRect(QRect(shadow_, shadow_',
                   'cursor.insertText(text)'):
        assert marker in TURBO


def test_zoom_updates_embedded_window_font():
    assert 'g_turbo_output->setGridFont(font)' in BRIDGE


def test_compiler_emits_debug_visibility_and_print_runtime():
    assert 'self.emit_qt_call1_int("DBaseQtSetDebugVisible", 1)' in COMPILER
    assert 'self.emit_print_expression(statement.expression, "runtime")' in COMPILER
    assert 'return "DBaseQtAppendDebug" if target in {"screen", "debug"}' in COMPILER


def test_build_script_exists():
    script = ROOT / 'build_and_deploy_dbase_debug_stage622.bat'
    assert 'build_d64qt5_mingw32.bat' in script.read_text(encoding='utf-8')
