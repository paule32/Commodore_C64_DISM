"""Stage 644: statische Qt5-Integrationsprüfungen (kein Windows-GUI-Lauf)."""
from pathlib import Path
import re

BASE = Path(__file__).resolve().parent
source = (BASE / 'd64qt5' / 'd64_turbo_editor.hpp').read_text(encoding='utf-8')
bridge = (BASE / 'd64qt5' / 'd64qt5_bridge.cpp').read_text(encoding='utf-8')
file_dialog = source.split('class D64VirtualFileDialog final : public QWidget', 1)[1].split('// Stage 628: Mehrfenster-Editor.', 1)[0]


def test_stays_embedded_in_console():
    assert 'setWindowFlags(Qt::Widget)' in file_dialog
    assert 'D64TurboModalLayer layer(desktop)' in file_dialog
    assert 'setParent(&layer, Qt::Widget)' in file_dialog
    assert 'QFileDialog' not in file_dialog


def test_blue_title_and_three_pixel_reduction():
    assert 'dbaseVirtualFileTitleBar{background:#2256cf;}' in file_dialog
    assert 'setMinimumSize(557, 330)' in file_dialog
    assert 'resize(767, 490)' in file_dialog
    assert 'desktop->width() - 20), 820) - 3' in file_dialog


def test_left_close_is_cancel_not_accept():
    assert 'closeButton_ = new QToolButton(titleBar_)' in file_dialog
    assert 'closeButton_->setText(QStringLiteral("×"))' in file_dialog
    assert re.search(r'connect\(closeButton_.*?finish\(Rejected\)', file_dialog, re.S)
    assert 'cancel, &QPushButton::clicked' in file_dialog
    assert 'if (dialog.exec() != D64VirtualFileDialog::Accepted) return;' in bridge


def test_drag_uses_character_cells_and_visible_title_limits():
    for snippet in ('titleBar_->installEventFilter(this)',
                    'title_->installEventFilter(this)',
                    'titleBalance_->installEventFilter(this)',
                    'dragWidget_->grabMouse()',
                    'dragStartGlobal_', 'dragStartCells_',
                    'updateDragPosition(mouse->globalPos())',
                    'd64_turbo_message_grid::roundCells(delta.x(), cell.width())',
                    'd64_turbo_message_grid::roundCells(delta.y(), cell.height())',
                    'd64_turbo_message_grid::clampCells(',
                    'setProperty("d64GridCol", gridColumn_)',
                    'setProperty("d64GridRow", gridRow_)'):
        assert snippet in file_dialog, snippet


def test_drag_ends_with_mouse_release_and_on_dialog_finish():
    assert 'case QEvent::MouseButtonRelease:' in file_dialog
    assert 'endTitleDrag();' in file_dialog
    assert 'dragWidget_->releaseMouse();' in file_dialog
    assert 'if (dragging_) endTitleDrag();' in file_dialog


def test_context_menus_disabled_even_in_child_inputs():
    assert 'void contextMenuEvent(QContextMenuEvent *event)' in file_dialog
    assert 'if (event->type() == QEvent::ContextMenu)' in file_dialog
    assert 'for (QWidget *widget : findChildren<QWidget *>())' in file_dialog
    assert 'widget->setContextMenuPolicy(Qt::NoContextMenu)' in file_dialog
    assert 'for (QWidget *widget : blocker.findChildren<QWidget *>())' in file_dialog


def test_normal_arrow_everywhere_except_entries_and_buttons():
    assert 'setCursor(Qt::ArrowCursor)' in file_dialog
    assert 'folders_->viewport()->setMouseTracking(true)' in file_dialog
    assert 'files_->viewport()->setMouseTracking(true)' in file_dialog
    assert 'folders_->itemAt(pos) != nullptr' in file_dialog
    assert 'files_->itemAt(pos) != nullptr' in file_dialog
    assert 'area->setCursor(overEntry ? Qt::PointingHandCursor : Qt::ArrowCursor)' in file_dialog
    assert 'for (QPushButton *button : {add, remove, ok, cancel, help})' in file_dialog
    assert 'button->setCursor(Qt::PointingHandCursor)' in file_dialog
    assert 'closeButton_->setCursor(Qt::PointingHandCursor)' in file_dialog


def test_vfs_and_file_opening_unchanged():
    assert 'mountPoints() const' in source
    assert 'readableFile(' in file_dialog
    assert 'writableFile(' in file_dialog
    assert 'createDirectory(' in file_dialog
    assert 'itemDoubleClicked' in file_dialog
    assert 'dialog.selectedVirtualPath()' in bridge
