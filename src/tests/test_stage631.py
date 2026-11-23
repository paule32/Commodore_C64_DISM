"""Stage 631 – Turbo-Vision-Werkzeuge, Fenster-Menue und zentrale Dialogbox.

Die Qt5/Mingw32-Oberflaeche benoetigt weiterhin einen Windows-GUI-Test.
Der Rechenausdruck-Parser wird als echtes C++-Programm getestet.
"""
from pathlib import Path
import shutil
import subprocess

import pytest

ROOT = Path(__file__).resolve().parent
GUI = (ROOT / 'd64qt5/d64qt5_bridge.cpp').read_text(encoding='utf-8')
EDITOR = (ROOT / 'd64qt5/d64_turbo_editor.hpp').read_text(encoding='utf-8')
OUTPUT = (ROOT / 'd64qt5/d64_turbo_output.hpp').read_text(encoding='utf-8')
TOOL = (ROOT / 'd64qt5/d64_turbo_tools.hpp').read_text(encoding='utf-8')
DIALOG = (ROOT / 'd64qt5/d64_turbo_messagebox.hpp').read_text(encoding='utf-8')
EXPR = (ROOT / 'd64qt5/d64_turbo_calculator_expression.hpp').read_text(encoding='utf-8')


def test_scrollbars_keep_normal_cursor_editor_gets_ibeam():
    assert EDITOR.count('setCursor(Qt::ArrowCursor)') >= 2
    assert 'edit_->viewport()->setCursor(Qt::IBeamCursor)' in EDITOR
    assert 'edit_->setCursor(Qt::IBeamCursor)' in EDITOR
    assert 'grip_->setCursor(Qt::SizeFDiagCursor)' in EDITOR
    assert 'title_->setCursor(Qt::SizeAllCursor)' in EDITOR


def test_system_menu_equals_with_three_tools():
    for text in ['Taschenrechner', 'ASCII-Zeichentabelle', 'Puzzle']:
        assert f'QStringLiteral("{text}")' in GUI
    assert 'new AsciiPopupMenu(QStringLiteral("="), g_menu_bar)' in GUI
    assert 'create_turbo_tool(kind)' in GUI
    assert 'D64TurboToolWindow::Calculator' in GUI
    assert 'D64TurboToolWindow::AsciiTable' in GUI
    assert 'D64TurboToolWindow::Puzzle' in GUI


def test_tool_window_reuses_dos_grid_and_zoom():
    for marker in ['void setGridFont(const QFont &font)',
                   'void setGridGeometry(int column, int row, int cols, int rows)',
                   'void toggleMaximized()', 'void mousePressEvent(QMouseEvent *event)',
                   'void mouseMoveEvent(QMouseEvent *event)',
                   'void closeEvent(QCloseEvent *event)', 'shadow_ = 7']:
        assert marker in TOOL
    assert 'for (const QPointer<D64TurboToolWindow> &tool : g_turbo_tools)' in GUI
    assert 'if (tool) tool->setGridFont(font)' in GUI


def test_window_menu_cascade_tile_open_close_and_activate():
    for marker in ['QStringLiteral("Fenster")', 'QStringLiteral("Kaskadieren")',
                   'QStringLiteral("Nebeneinander")', 'visible_turbo_windows()',
                   'rebuild_turbo_windows_menu()', 'layout_turbo_windows(bool cascade)',
                   'activate_turbo_window(QWidget *window)',
                   'g_turbo_tools.append(QPointer<D64TurboToolWindow>(tool))',
                   'if (g_turbo_focused_window == closed) g_turbo_focused_window = nullptr']:
        assert marker in GUI
    assert 'tool->setClosedCallback' in GUI
    assert 'editor->setClosedCallback' in GUI
    assert 'QMenu::aboutToShow' in GUI


def test_grey_about_messagebox_is_reusable():
    assert 'QStringLiteral("Hilfe")' in GUI
    assert 'QStringLiteral("Über ...")' in GUI
    assert 'D64TurboMessageBox::information(g_console ? g_console->viewport() : g_window,' in GUI
    assert 'QStringLiteral("Information")' in GUI
    for marker in ['setWindowFlags(Qt::Widget);', 'setFocusPolicy(Qt::StrongFocus);',
                   'D64TurboModalLayer', '#bdbdbd', '#8c8c8c', 'color:#000000',
                   'class D64TurboMessageBox final : public QWidget',
                   'QList<ButtonSpec>', 'QStringLiteral("OK")']:
        assert marker in DIALOG
    assert 'D64TurboMessageBox::showMessage(' in EDITOR
    assert 'D64TurboMessageBox::Save' in EDITOR
    assert 'D64TurboMessageBox::Discard' in EDITOR
    assert 'D64TurboMessageBox::Cancel' in EDITOR


def test_dialog_button_press_offset_and_leave_restore():
    assert 'class D64TurboDialogButton final : public QPushButton' in DIALOG
    assert 'shift(3);' in DIALOG
    assert DIALOG.count('shift(-3)') >= 2
    assert 'void mouseReleaseEvent(QMouseEvent *event) override' in DIALOG
    assert 'void leaveEvent(QEvent *event) override' in DIALOG
    assert 'QPushButton::mouseReleaseEvent(&corrected);' in DIALOG


def test_ascii_table_uses_existing_full_cp437_mapping():
    assert 'QTableWidget(16,16,content_)' in TOOL
    assert 'for (int code = 0; code < 256; ++code)' in TOOL
    assert 'D64TurboOutputWidget::dosCharacter(code)' in TOOL
    assert 'QApplication::clipboard()->setText' in TOOL
    assert 'QTableWidget::cellDoubleClicked' in TOOL


def test_puzzle_shuffled_by_legal_sliding_moves():
    assert 'for (int step = 0; step < 180; ++step)' in TOOL
    assert 'QRandomGenerator::global()->bounded(choices.size())' in TOOL
    assert 'std::swap(puzzle_[blank],puzzle_[chosen])' in TOOL
    assert 'std::abs(index/4-blank/4)+std::abs(index%4-blank%4)!=1' in TOOL
    assert 'if (puzzleSolved())' in TOOL
    assert 'Neue mischen' not in TOOL  # korrekte Beschriftung: Neu mischen
    assert 'Neu mischen' in TOOL


def test_calculator_operations_and_errors_defined():
    for fragment in ["parseExpression()", "parseTerm()", "parseFactor()",
                     'Division durch Null', 'Schliessende Klammer fehlt',
                     'Zahl erwartet', 'std::isfinite']:
        assert fragment in EXPR
    assert 'D64CalculatorExpression::evaluate(' in TOOL
    assert 'calculatorEdit_->selectAll();' in TOOL


def test_calculator_parser_compiles_and_evaluates(tmp_path):
    compiler = shutil.which('g++')
    if not compiler:
        pytest.skip('g++ not available')
    source = tmp_path / 'test_calc.cpp'
    source.write_text(r'''
        #include "d64_turbo_calculator_expression.hpp"
        #include <cassert>
        #include <cmath>
        int main() {
            auto check=[](const char* text,double expected) {
                auto result=D64CalculatorExpression::evaluate(text);
                assert(result.ok);
                assert(std::fabs(result.value-expected) < 1e-9);
            };
            check("2+3*4",14);
            check("(2+3)*4",20);
            check("8/2*3",12);
            check("-2*(3+4)",-14);
            check("10--3",13);
            check("1/4+0.75",1);
            check(".125*8",1);
            check(" 4 + 8 / 2 ",8);
            assert(!D64CalculatorExpression::evaluate("1/0").ok);
            assert(!D64CalculatorExpression::evaluate("1+").ok);
            assert(!D64CalculatorExpression::evaluate("(2+3").ok);
            assert(!D64CalculatorExpression::evaluate("1+foo").ok);
            assert(!D64CalculatorExpression::evaluate("7)3").ok);
        }
    ''', encoding='utf-8')
    binary = tmp_path / 'test_calc'
    subprocess.run([compiler, '-std=c++17', '-Wall', '-Wextra', '-Werror',
                    '-I', str(ROOT / 'd64qt5'), str(source), '-o', str(binary)],
                   check=True, timeout=30, capture_output=True, text=True)
    subprocess.run([str(binary)], check=True, timeout=15, capture_output=True, text=True)


def test_vfs_remains_scoped_and_editor_can_open_multiple():
    assert 'D64ApplicationVfs' in EDITOR
    assert 'QDir::isAbsolutePath(source)' in EDITOR
    assert 'if (info.isSymLink()) return QString();' in EDITOR
    assert 'D64VirtualFileDialog dialog(' in EDITOR
    assert 'create_turbo_editor();' in GUI
    assert 'g_turbo_editors.append(QPointer<D64TurboEditorWidget>(editor))' in GUI


def test_stage631_build_script_exists():
    script = ROOT / 'build_and_deploy_dbase_editor_stage631.bat'
    assert script.is_file()
    data = script.read_text(encoding='utf-8')
    assert 'build_d64qt5_mingw32.bat' in data
    assert 'libd64_qt5.dll' in data
    assert 'runtime\\dbase\\pe32' in data
