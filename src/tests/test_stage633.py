"""Stage 633: Turbo-Dialog, CP437-Scrollpfeile und graue Kontextmenues.

Statische GUI-Integrationspruefungen, da Qt5/MinGW32 im Linux-Runner fehlt.
"""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
DIALOG = (ROOT / 'd64qt5/d64_turbo_messagebox.hpp').read_text(encoding='utf-8')
TOOLS = (ROOT / 'd64qt5/d64_turbo_tools.hpp').read_text(encoding='utf-8')
EDITOR = (ROOT / 'd64qt5/d64_turbo_editor.hpp').read_text(encoding='utf-8')
STYLE = (ROOT / 'd64qt5/d64_turbo_context_menu.hpp').read_text(encoding='utf-8')
SCROLL = (ROOT / 'd64qt5/d64_turbo_scrollbar.hpp').read_text(encoding='utf-8')
BRIDGE = (ROOT / 'd64qt5/d64qt5_bridge.cpp').read_text(encoding='utf-8')


def test_messagebox_uses_priority_font_fallback():
    assert '#include <QFontDatabase>' in DIALOG
    assert re.search(r'Consolas.*Courier New.*Courier', DIALOG, re.S)
    assert 'fonts.hasFamily(candidate)' in DIALOG
    assert 'setFont(mono)' in DIALOG
    assert 'mono.setStyleHint(QFont::TypeWriter)' in DIALOG


def test_messagebox_has_two_pixel_frame_and_shadow():
    assert 'QPen borderPen(QColor(0x52, 0x52, 0x52), 2)' in DIALOG
    assert 'setContentsMargins(2, 2, 4, 4)' in DIALOG
    assert 'rect().adjusted(2, 2, 0, 0)' in DIALOG
    assert 'Qt::WA_NoSystemBackground, true' in DIALOG
    assert '#bdbdbd' in DIALOG
    assert '#8c8c8c' in DIALOG
    assert 'color:#000000' in DIALOG


def test_messagebox_can_be_dragged_by_title():
    assert 'heading->installEventFilter(this)' in DIALOG
    assert 'title_->installEventFilter(this)' in DIALOG
    for marker in ['QEvent::MouseButtonPress', 'QEvent::MouseMove',
                   'QEvent::MouseButtonRelease', 'dragStartGlobal_',
                   'dragStartWindow_', 'setGridPosition(', 'd64_turbo_message_grid::roundCells(']:
        assert marker in DIALOG


def test_messagebox_close_button_returns_cancel_and_is_right_aligned():
    assert 'dbaseTurboMessageClose' in DIALOG
    assert 'setText(QStringLiteral("×"))' in DIALOG
    assert 'titleRow->addWidget(title_, 1)' in DIALOG
    assert 'titleRow->addWidget(closeButton)' in DIALOG
    assert '[this]() { done(Cancel); }' in DIALOG
    assert 'setWindowFlags(Qt::Widget);' in DIALOG
    assert 'class D64TurboMessageBox final : public QWidget' in DIALOG


def test_messagebox_still_uses_reusable_buttons_and_press_offset():
    for fragment in ['static int showMessage', 'static void information',
                     'static int confirmSave', 'using ButtonSpec = QPair<QString, int>',
                     'shift(3)', 'shift(-3)', 'QPushButton::clicked']:
        assert fragment in DIALOG
    assert 'D64TurboMessageBox::information' in TOOLS
    assert 'D64TurboMessageBox::showMessage(' in EDITOR


def test_ascii_table_has_both_custom_scrollbars():
    assert 'QTableWidget(16,16,content_)' in TOOLS
    assert 'new D64TurboArrowScrollBar(Qt::Vertical, asciiTable_)' in TOOLS
    assert 'new D64TurboArrowScrollBar(Qt::Horizontal, asciiTable_)' in TOOLS
    assert 'asciiTable_->setVerticalScrollBar(asciiVertical)' in TOOLS
    assert 'asciiTable_->setHorizontalScrollBar(asciiHorizontal)' in TOOLS
    assert 'asciiVertical->setTurboEditorTheme()' in TOOLS
    assert 'asciiHorizontal->setTurboEditorTheme()' in TOOLS
    assert 'Qt::ScrollBarAlwaysOn' in TOOLS
    assert 'paintArrow(painter, arrowStartRect(g), true)' in SCROLL
    assert 'paintArrow(painter, arrowEndRect(g), false)' in SCROLL
    assert 'painter.setClipRect(groove)' in SCROLL


def test_both_context_menus_use_one_grey_style():
    assert 'menu.setStyleSheet(d64TurboGreyContextMenuStyle());' in EDITOR
    assert 'menu.setStyleSheet(d64TurboGreyContextMenuStyle());' in TOOLS
    for marker in ['background:#c6c6c6', 'color:#000000',
                   'background:#888888', 'QMenu::separator']:
        assert marker in STYLE
    assert '#171d35' not in EDITOR[EDITOR.index('void showGermanContextMenu'):]


def test_calculator_context_menu_german_and_shortcuts():
    assert 'calculatorEdit_->setContextMenuPolicy(Qt::CustomContextMenu)' in TOOLS
    assert 'content_->setContextMenuPolicy(Qt::CustomContextMenu)' in TOOLS
    for item in ['Rückgängig', 'Wiederherstellen', 'Ausschneiden', 'Kopieren',
                 'Einfügen', 'Löschen', 'Alles auswählen']:
        assert f'QStringLiteral("{item}")' in TOOLS
    for key in ['QKeySequence::Undo', 'Qt::Key_Y', 'QKeySequence::Cut',
                'QKeySequence::Copy', 'QKeySequence::Paste', 'Qt::Key_Delete',
                'QKeySequence::SelectAll']:
        assert key in TOOLS


def test_calculator_numeric_buttons_hand_cursor_no_hint():
    assert 'character.at(0).isDigit()' in TOOLS
    assert 'button->setCursor(Qt::PointingHandCursor)' in TOOLS
    assert 'button->setObjectName(QStringLiteral("dbaseTurboCalculatorButton"))' in TOOLS
    assert 'Punkt vor Strich · Klammern · Enter =' not in TOOLS
    assert 'outer->addLayout(keypad,1);' in TOOLS


def test_calculator_semantics_unchanged():
    assert 'D64CalculatorExpression::evaluate(' in TOOLS
    assert 'calculatorEdit_->selectAll();' in TOOLS
    assert 'create_turbo_tool(kind)' in BRIDGE
    assert 'rebuild_turbo_windows_menu()' in BRIDGE


def test_build_script_for_stage633_exists():
    p = ROOT / 'build_and_deploy_dbase_editor_stage633.bat'
    assert p.is_file()
    text = p.read_text(encoding='utf-8')
    assert 'build_d64qt5_mingw32.bat' in text
    assert 'libd64_qt5.dll' in text
    assert 'runtime\\dbase\\pe32' in text
