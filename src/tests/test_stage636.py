"""Stage 636 – Checks fuer Qt5-Ereignisweitergabe und Consolas-Font im internen Dialog.

Dies sind strukturelle Regressionstests; ein nativer Windows-/Qt5-Maustest ist
weiterhin noetig, um die gemeldeten Bedienprobleme abschliessend zu bestaetigen.
"""
from pathlib import Path

H = (Path(__file__).parent / 'd64qt5' / 'd64_turbo_messagebox.hpp').read_text(encoding='utf-8')


def test_native_qwindow_events_are_not_swallowed_before_widget_delivery():
    assert 'if (!watched || !watched->isWidgetType()) {' in H
    block = H.split('if (!watched || !watched->isWidgetType()) {', 1)[1].split('const bool viewportResized =', 1)[0]
    assert 'return QWidget::eventFilter(watched, event);' in block
    assert 'QEvent::MouseButtonPress' not in block
    assert 'QEvent::MouseButtonRelease' not in block
    assert 'QEvent::MouseMove' not in block
    assert 'event->accept();\n                return true;' in block  # Escape / Shortcut


def test_widget_events_outside_modal_layer_still_blocked():
    assert '!isAncestorOf(qobject_cast<QWidget *>(watched))' in H
    assert 'QEvent::MouseButtonPress' in H
    assert 'QEvent::KeyPress' in H
    assert 'QEvent::ShortcutOverride' in H


def test_escape_is_handled_before_native_widget_delivery_as_fallback():
    assert 'void setEscapeHandler(std::function<void()> handler)' in H
    assert 'if (key->key() == Qt::Key_Escape)' in H
    assert 'escapeHandler_();' in H
    assert 'layer.setEscapeHandler([&box]() { box.done(Cancel); });' in H


def test_escape_still_handled_inside_dialog_widget():
    assert 'void keyPressEvent(QKeyEvent *event) override' in H
    assert 'done(Cancel);' in H
    assert 'event->accept();' in H


def test_title_drag_has_mouse_grab_and_release():
    assert 'heading->installEventFilter(this)' in H
    assert 'title_->installEventFilter(this)' in H
    assert 'grabMouse();' in H
    assert 'void updateDragPosition(const QPoint &global)' in H
    assert 'void mouseMoveEvent(QMouseEvent *event) override' in H
    assert 'void mouseReleaseEvent(QMouseEvent *event) override' in H
    assert 'QWidget::mouseGrabber() == this' in H


def test_ok_and_x_controls_finish_embedded_event_loop():
    assert 'QObject::connect(closeButton, &QToolButton::clicked, this,' in H
    assert '[this]() { done(Cancel); }' in H
    assert 'QObject::connect(button, &QPushButton::clicked, this,' in H
    assert '[this, result = spec.second]() { done(result); }' in H
    assert 'box.setFinishedCallback([&modalLoop](int) { modalLoop.quit(); });' in H
    assert 'modalLoop.exec(QEventLoop::AllEvents)' in H


def test_font_family_preference_order_and_font_hint():
    f = H.split('QFontDatabase fonts;', 1)[1].split('setStyleSheet(', 1)[0]
    assert f.index('QStringLiteral("Consolas")') < f.index('QStringLiteral("Courier New")')
    assert f.index('QStringLiteral("Courier New")') < f.index('QStringLiteral("Courier")})')
    assert 'fonts.hasFamily(candidate)' in f
    assert 'QFont mono(family, 10);' in f
    assert 'setFont(mono);' in f


def test_font_family_qss_override_on_all_children():
    for ident in ['dbaseTurboMessageBox','dbaseTurboMessageFrame',
                  'dbaseTurboMessageHeading','dbaseTurboMessageTitle',
                  'dbaseTurboMessageText','dbaseTurboMessageClose',
                  'dbaseTurboDialogButton']:
        assert ident in H.split('const QString monoStyle', 1)[1].split(').arg(family);', 1)[0]
    assert 'setStyleSheet(monoStyle + QStringLiteral(' in H


def test_explicit_font_on_labels_buttons_and_title():
    assert 'title_->setFont(titleFont);' in H
    assert 'content->setFont(mono);' in H
    assert 'closeButton->setFont(mono);' in H
    assert 'button->setFont(mono);' in H


def test_modal_placement_and_border_unchanged():
    assert 'D64TurboModalLayer layer(desktop);' in H
    assert 'D64TurboMessageBox box(&layer,' in H
    assert 'QPen borderPen(QColor(0x52, 0x52, 0x52), 2);' in H
    assert 'setContentsMargins(2, 2, 4, 4);' in H
