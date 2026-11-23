"""Stage 634: MessageBox als echtes internes Turbo-Vision-Widget.

Statische Qt5-Integrationspruefungen. Ein nativer Win32-/Qt5-GUI-Build
ist fuer die vollstaendige Laufzeitbestaetigung weiterhin erforderlich.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MSG = (ROOT/'d64qt5/d64_turbo_messagebox.hpp').read_text('utf-8')
ED = (ROOT/'d64qt5/d64_turbo_editor.hpp').read_text('utf-8')
TOOLS = (ROOT/'d64qt5/d64_turbo_tools.hpp').read_text('utf-8')
BR = (ROOT/'d64qt5/d64qt5_bridge.cpp').read_text('utf-8')


def test_messagebox_not_a_native_top_level_dialog():
    assert 'class D64TurboMessageBox final : public QWidget' in MSG
    assert ': QWidget(parent)' in MSG
    assert 'setWindowFlags(Qt::Widget);' in MSG
    assert 'class D64TurboMessageBox final : public QDialog' not in MSG


def test_console_viewport_is_the_desktop_for_every_call_site():
    assert 'QStringLiteral("dbaseConsole")' in MSG
    assert 'qobject_cast<QAbstractScrollArea *>(candidate)' in MSG
    assert 'area->viewport()' in MSG
    assert 'D64TurboMessageBox::information(g_console ? g_console->viewport() : g_window,' in BR
    assert 'D64TurboMessageBox::information(this,' in TOOLS
    assert 'D64TurboMessageBox::showMessage(' in ED


def test_modal_layer_is_inside_console_viewport_not_desktop_window():
    assert 'D64TurboModalLayer layer(desktop);' in MSG
    assert 'setGeometry(desktop->rect())' in MSG
    assert 'layer.show();' in MSG and 'layer.raise();' in MSG
    assert 'D64TurboMessageBox box(&layer,' in MSG
    assert 'box.setFinishedCallback([&modalLoop](int) { modalLoop.quit(); });' in MSG
    assert 'modalLoop.exec(QEventLoop::AllEvents)' in MSG
    assert 'return box.result();' in MSG
    assert 'return box.exec();' not in MSG


def test_modal_layer_blocks_underlying_windows_and_actions():
    assert 'QCoreApplication::instance()->installEventFilter(this)' in MSG
    for type_name in ('MouseButtonPress', 'MouseButtonRelease', 'Wheel',
                      'KeyPress', 'KeyRelease', 'Shortcut', 'ShortcutOverride'):
        assert 'QEvent::'+type_name in MSG
    assert '!isAncestorOf(qobject_cast<QWidget *>(watched))' in MSG


def test_messagebox_title_can_reach_row_24_and_extend_right():
    assert 'const int maxRow = qMin(24, qMax(0, viewportRows - 1));' in MSG
    assert 'const int maxCol = qMin(79, qMax(0, viewportCols - visibleTitleCols));' in MSG
    assert 'const int visibleTitleCols = qMin(10, viewportCols);' in MSG
    assert 'void updateDragPosition(const QPoint &global)' in MSG
    assert 'setGridPosition(' in MSG
    assert 'void paintEvent(QPaintEvent *) override' in MSG
    assert 'watched == parentWidget()' in MSG


def test_existing_turbo_dialog_look_and_close_behavior_retained():
    for phrase in ('Consolas', 'Courier New', 'Courier', 'QPen borderPen(QColor(0x52, 0x52, 0x52), 2)',
                   'setContentsMargins(2, 2, 4, 4)', 'dbaseTurboMessageClose',
                   '[this]() { done(Cancel); }', 'shift(3)', 'shift(-3)',
                   'QStringLiteral("Information")'):
        assert phrase in MSG


def test_editor_unsaved_close_still_has_all_decisions():
    assert 'if (!isModified()) return true;' in ED
    for name in ('Speichern', 'Verwerfen', 'Abbrechen'):
        assert 'QStringLiteral("'+name+'")' in ED
    assert 'return saveDocument(true);' in ED
    assert 'return answer == D64TurboMessageBox::Discard;' in ED


def test_no_new_runtime_exports_or_relinked_dbase_program_needed():
    assert 'DBaseQtFillBackground' in BR
    assert 'create_turbo_editor()' in BR
    assert 'rebuild_turbo_windows_menu()' in BR
