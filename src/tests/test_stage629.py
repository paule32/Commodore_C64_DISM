"""Stage 629: DOS-Scrollleisten, Fenstergrenzen und Vordergrund-Fokus.

Statische Sicherheits-/Integrationspruefungen; der native Qt5/Mingw32-
Fenstertest bleibt bewusst ein separater Schritt auf Windows.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EDITOR = (ROOT / 'd64qt5/d64_turbo_editor.hpp').read_text(encoding='utf-8')
OUTPUT = (ROOT / 'd64qt5/d64_turbo_output.hpp').read_text(encoding='utf-8')
BAR = (ROOT / 'd64qt5/d64_turbo_scrollbar.hpp').read_text(encoding='utf-8')
BRIDGE = (ROOT / 'd64qt5/d64qt5_bridge.cpp').read_text(encoding='utf-8')


def test_editor_vertical_groove_with_reserved_end_buttons():
    assert 'margin:15px 0px 15px 0px;' in EDITOR
    assert 'QScrollBar::groove:vertical' in EDITOR
    assert 'QScrollBar::sub-line:vertical' in EDITOR
    assert 'QScrollBar::add-line:vertical' in EDITOR
    assert EDITOR.count('subcontrol-origin:margin;') >= 4


def test_editor_horizontal_groove_same_gray_thumb_and_end_buttons():
    assert 'margin:0px 15px 0px 15px;' in EDITOR
    assert 'QScrollBar::groove:horizontal' in EDITOR
    assert 'QScrollBar::handle:horizontal{background:#686868;min-width:15px;' in EDITOR
    assert 'QScrollBar::handle:vertical{background:#686868;min-height:15px;' in EDITOR
    assert 'QScrollBar::sub-line:horizontal' in EDITOR
    assert 'QScrollBar::add-line:horizontal' in EDITOR


def test_both_arrow_button_backgrounds_match_blue_text_area():
    assert 'verticalBar->setTurboEditorTheme();' in EDITOR
    assert 'horizontalBar_->setTurboEditorTheme();' in EDITOR
    assert 'arrowBackground_ = QColor(QStringLiteral("#0000aa"))' in BAR
    assert 'QScrollBar::sub-line:vertical{background:#0000aa;' in EDITOR
    assert 'QScrollBar::add-line:vertical{background:#0000aa;' in EDITOR
    assert 'QScrollBar::sub-line:horizontal{background:#0000aa;' in EDITOR
    assert 'QScrollBar::add-line:horizontal{background:#0000aa;' in EDITOR


def test_arrow_paint_uses_fixed_shared_geometry_not_qt_subcontrols():
    # Stage 630 fixes the Stage-629 subcontrol overlap by replacing
    # QStyleSheet geometry with a common paint-and-hit-test geometry.
    assert 'd64TurboScrollGeometry(' in BAR
    assert 'painter.setClipRect(groove)' in BAR
    assert 'style()->subControlRect(' not in BAR
    assert 'geometryForCurrentValue()' in BAR
    assert 'mousePressEvent(QMouseEvent *event) override' in BAR
    assert 'setTurboEditorTheme()' in BAR


def test_green_scrollbars_use_reserved_grooves_too():
    for style in ('margin:15px 0px 15px 0px;', 'margin:0px 15px 0px 15px;',
                  'QScrollBar::groove:horizontal', 'QScrollBar::groove:vertical'):
        assert OUTPUT.count(style) == 2, style  # initial CSS and patterned CSS


def test_editor_preserves_geometry_outside_viewport_instead_of_shrinking():
    assert 'preferredCols_*cw_, preferredRows_*ch_' in EDITOR
    assert 'qMin(preferredCols_, availCols)' not in EDITOR
    assert 'qMin(preferredRows_, availRows)' not in EDITOR
    assert 'yRow_ = qBound(0, yRow_, qMin(24, availRows-1))' in EDITOR
    assert 'xCol_ = qBound(0, xCol_, qMin(79,' in EDITOR


def test_output_preserves_requested_grid_size_and_limits_title_row():
    assert 'columns_ = requestedColumns_' in OUTPUT
    assert 'rows_ = requestedRows_' in OUTPUT
    assert 'qBound(0, roundToCell(y, cellHeight_)/cellHeight_, maxRow)' in OUTPUT
    assert 'const int maxRow = qMin(24, viewportRows-1)' in OUTPUT
    assert 'const int maxCol = qMin(79,' in OUTPUT


def test_editor_title_click_activates_and_raises_also_maximized():
    assert 'watched == title_ || watched == closeButton_' in EDITOR
    assert 'if (mouse->button() == Qt::LeftButton) {' in EDITOR
    assert 'if (onActivated_) onActivated_(this);' in EDITOR
    assert 'if (watched == title_) edit_->setFocus(Qt::MouseFocusReason);' in EDITOR
    assert 'if (watched == title_)' in EDITOR
    assert 'void mousePressEvent(QMouseEvent *event) override' in EDITOR
    assert 'void mouseDoubleClickEvent(QMouseEvent *event) override' in EDITOR
    assert 'raise();' in EDITOR


def test_output_title_click_raises_even_maximized():
    assert 'if (event->button() == Qt::LeftButton && isTitleBarPoint(event->pos())) {' in OUTPUT
    assert 'raise();' in OUTPUT
    assert 'setFocus(Qt::MouseFocusReason)' in OUTPUT


def test_multi_editor_and_file_dialog_untouched():
    assert 'QList<QPointer<D64TurboEditorWidget>> g_turbo_editors' in BRIDGE
    assert 'D64VirtualFileDialog dialog' in EDITOR
    assert 'D64TurboMessageBox::showMessage(' in EDITOR


def test_build_script():
    script = (ROOT / 'build_and_deploy_dbase_editor_stage629.bat').read_text(encoding='utf-8')
    assert 'build_d64qt5_mingw32.bat' in script
    assert 'libd64_qt5.dll' in script


def test_limits_for_viewport_80_by_25_and_smaller_zoom():
    # Mathematische Gegenprobe zur in C++ verwendeten DOS-Raster-Berechnung.
    def clamp_position(x, y, cols, rows):
        visible = min(10, cols)
        return min(max(x, 0), min(79, max(0, cols-visible))), min(max(y, 0), min(24, rows-1))
    assert clamp_position(90, 40, 80, 25) == (70, 24)
    assert clamp_position(65, 24, 40, 15) == (30, 14)
    assert clamp_position(100, 100, 8, 5) == (0, 4)
    assert clamp_position(-5, -3, 80, 25) == (0, 0)
