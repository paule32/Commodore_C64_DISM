"""Stage 635: regressions for interactive, embedded Turbo-Vision MessageBox.

These are C++ interface/source tests; they do NOT substitute for a native Qt5
Windows GUI test. They specifically target the four observed failures.
"""
from pathlib import Path

HEADER = (Path(__file__).parent/'d64qt5/d64_turbo_messagebox.hpp').read_text('utf-8')


def test_is_real_embedded_qwidget_not_qdialog():
    assert 'class D64TurboMessageBox final : public QWidget' in HEADER
    assert ': QWidget(parent)' in HEADER
    assert 'setWindowFlags(Qt::Widget);' in HEADER
    assert 'class D64TurboMessageBox final : public QDialog' not in HEADER
    assert 'QDialog::finished' not in HEADER.split('static int showMessage')[1].split('static void information')[0]
    assert 'box.exec()' not in HEADER


def test_frame_two_pixels_and_shadow_two_pixels_explicit_painting():
    for marker in ('const QRect face = rect().adjusted(0, 0, -2, -2);',
                   'setContentsMargins(2, 2, 4, 4)',
                   'painter.fillRect(rect().adjusted(2, 2, 0, 0)',
                   'QPen borderPen(QColor(0x52, 0x52, 0x52), 2)',
                   'painter.drawRect(face.adjusted(1, 1, -1, -1))'):
        assert marker in HEADER
    assert 'QWidget::paintEvent(' not in HEADER


def test_title_drag_press_move_release_with_cell_grid_clamp():
    for marker in ('heading->installEventFilter(this)',
                   'title_->installEventFilter(this)',
                   'dragStartGlobal_ = mouse->globalPos()',
                   'dragStartWindow_ = pos()',
                   'dragStartColumn_ = gridColumn_',
                   'dragStartRow_ = gridRow_',
                   'const QPoint delta = global - dragStartGlobal_',
                   'd64_turbo_message_grid::roundCells(delta.x()',
                   'd64_turbo_message_grid::roundCells(delta.y()',
                   'setGridPosition(', 'dragging_ = false'):
        assert marker in HEADER


def test_ok_button_and_close_button_complete_local_modal_loop():
    assert 'QObject::connect(closeButton, &QToolButton::clicked, this,' in HEADER
    assert '[this]() { done(Cancel); }' in HEADER
    assert 'QObject::connect(button, &QPushButton::clicked, this,' in HEADER
    assert '[this, result = spec.second]() { done(result); }' in HEADER
    assert 'if (finished_) return;' in HEADER
    assert 'result_ = answer;' in HEADER
    assert 'if (onFinished_) onFinished_(answer);' in HEADER
    assert 'box.setFinishedCallback([&modalLoop](int) { modalLoop.quit(); });' in HEADER
    assert 'modalLoop.exec(QEventLoop::AllEvents);' in HEADER
    assert 'void closeEvent(QCloseEvent *event) override' in HEADER
    assert 'if (event->key() == Qt::Key_Escape) {\n            done(Cancel);' in HEADER


def test_mouse_release_after_button_press_uses_original_hit_target():
    assert 'QPushButton::mousePressEvent(event);' in HEADER
    assert 'shift(3)' in HEADER
    assert 'shift(-3)' in HEADER
    assert 'const QPoint global = event->globalPos()' in HEADER
    assert 'QMouseEvent corrected(QEvent::MouseButtonRelease,' in HEADER
    assert 'QPointF(mapFromGlobal(global))' in HEADER
    assert 'QPushButton::mouseReleaseEvent(&corrected);' in HEADER


def test_menu_mouse_grab_is_released_and_overlay_keeps_mouse_events_inside():
    assert 'QApplication::activePopupWidget()' in HEADER
    assert 'popup->close();' in HEADER
    assert 'D64TurboModalLayer layer(desktop);' in HEADER
    assert 'D64TurboMessageBox box(&layer,' in HEADER
    assert '!isAncestorOf(qobject_cast<QWidget *>(watched))' in HEADER
    assert 'layer.raise();' in HEADER
    assert 'box.raise();' in HEADER


def test_dialog_built_on_console_viewport_and_keeps_vfs_decisions():
    assert 'qobject_cast<QAbstractScrollArea *>(candidate)' in HEADER
    assert 'area->viewport()' in HEADER
    for token in ('QStringLiteral("Speichern")', 'QStringLiteral("Verwerfen")',
                  'QStringLiteral("Abbrechen")', 'QStringLiteral("OK")',
                  'QStringLiteral("Information")'):
        assert token in HEADER
