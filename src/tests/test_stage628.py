"""Stage 628: statische Qt5-Integrations- und Regressionstests (ohne native Qt-DLL)."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EDITOR = (ROOT / 'd64qt5' / 'd64_turbo_editor.hpp').read_text(encoding='utf-8')
OUTPUT = (ROOT / 'd64qt5' / 'd64_turbo_output.hpp').read_text(encoding='utf-8')
BRIDGE = (ROOT / 'd64qt5' / 'd64qt5_bridge.cpp').read_text(encoding='utf-8')
SCROLL = (ROOT / 'd64qt5' / 'd64_turbo_scrollbar.hpp').read_text(encoding='utf-8')


def test_multi_editor_registry():
    assert 'QList<QPointer<D64TurboEditorWidget>> g_turbo_editors' in BRIDGE
    assert 'g_turbo_editors.append(QPointer<D64TurboEditorWidget>(editor))' in BRIDGE
    assert 'active_turbo_editor()' in BRIDGE


def test_new_always_creates_window_without_resetting_old_document():
    assert 'hookFile(QStringLiteral("Neu"), QKeySequence::New, []() {\n        create_turbo_editor();' in BRIDGE
    assert 'g_turbo_editor->newDocument()' not in BRIDGE


def test_open_creates_separate_editor_after_file_selection():
    # Stage 643: Das Menü darf keinen leeren Editor vor dem VFS-Dialog erzeugen.
    assert 'open_turbo_vfs_file();' in BRIDGE
    assert 'if (dialog.exec() != D64VirtualFileDialog::Accepted) return;' in BRIDGE
    assert 'if (D64TurboEditorWidget *editor = create_turbo_editor())' in BRIDGE
    assert 'editor->loadVirtualDocument(path)' in BRIDGE


def test_main_window_confirms_all_dirty_editors():
    assert 'for (const QPointer<D64TurboEditorWidget> &editor : g_turbo_editors)' in BRIDGE
    assert 'editor && editor->isVisible() && editor->isModified()' in BRIDGE
    assert '!editor->confirmClose()' in BRIDGE


def test_window_close_guard_even_without_title_button():
    assert 'void closeEvent(QCloseEvent *event) override' in EDITOR
    assert 'if (!confirmDiscard())' in EDITOR
    assert 'event->ignore();' in EDITOR
    assert 'QWidget::closeEvent(event);' in EDITOR


def test_close_button_requires_double_click():
    assert 'dbaseTurboEditorCloseButton' in EDITOR
    assert 'watched == closeButton_ && event->type() == QEvent::MouseButtonDblClick' in EDITOR
    assert 'close(); // closeEvent fuehrt IMMER' in EDITOR


def test_maximize_restore_state_preserved():
    for name in ('toggleMaximized()', 'restoreCol_', 'restoreRow_',
                 'restoreCols_', 'restoreRows_', 'fitMaximizedToViewport()',
                 'grip_->hide()', 'grip_->show()'):
        assert name in EDITOR


def test_resize_and_move_grid_units():
    for marker in ('roundToCells(delta.x(), cw_)', 'roundToCells(delta.y(), ch_)',
                   'preferredCols_ = qMax(26', 'preferredRows_ = qMax(8',
                   'xCol_*cw_', 'yRow_*ch_'):
        assert marker in EDITOR


def test_editor_blue_colors_and_yellow_frame():
    for color in ('#0000aa', '#ffffff', '#ffff55', '#2256cf'):
        assert color in EDITOR
    assert 'p.drawRect(1, 1, right-2, bottom-2)' in EDITOR
    assert 'p.drawRect(4, 4, right-8, bottom-8)' in EDITOR


def test_cursor_position_on_same_footer_line_as_scroll_and_grip():
    assert 'QStringLiteral("%1 : %2")' in EDITOR
    assert 'status_->setGeometry(8,footerY' in EDITOR
    assert 'horizontalBar_->setGeometry(barX,footerY' in EDITOR
    assert 'grip_->setGeometry(qMax(0,right-25),footerY' in EDITOR


def test_vertical_horizontal_scrollers_have_visible_arrow_components():
    assert 'D64TurboArrowScrollBar(Qt::Vertical, edit_)' in EDITOR
    assert 'D64TurboArrowScrollBar(Qt::Horizontal, this)' in EDITOR
    assert 'QScrollBar::sub-line:vertical' in EDITOR
    assert 'QScrollBar::add-line:vertical' in EDITOR
    assert 'QScrollBar::sub-line:horizontal' in EDITOR
    assert 'QScrollBar::add-line:horizontal' in EDITOR
    assert 'painter.drawPolygon(polygon)' in SCROLL and 'paintArrow(painter,' in SCROLL


def test_green_window_also_has_vertical_and_horizontal_arrows():
    assert 'D64TurboArrowScrollBar(Qt::Vertical, editor_)' in OUTPUT
    assert 'D64TurboArrowScrollBar(Qt::Horizontal, editor_)' in OUTPUT
    assert '#076b30' in OUTPUT
    assert 'g_turbo_output->appendOutput' in BRIDGE


def test_footer_horizontal_bar_is_linked_to_document_scrolling():
    assert 'edit_->setHorizontalScrollBarPolicy(Qt::ScrollBarAlwaysOff)' in EDITOR
    assert 'internalH, &QScrollBar::rangeChanged' in EDITOR
    assert 'horizontalBar_, &QScrollBar::setValue' in EDITOR
    assert 'internalH, &QScrollBar::setValue' in EDITOR


def test_german_context_menu_and_shortcut_keys():
    for text in ('Rückgängig', 'Wiederherstellen', 'Ausschneiden', 'Kopieren',
                 'Einfügen', 'Löschen', 'Alles auswählen'):
        assert f'QStringLiteral("{text}")' in EDITOR
    assert 'QKeySequence::Undo' in EDITOR
    assert 'QKeySequence::Paste' in EDITOR
    assert 'QKeySequence::SelectAll' in EDITOR
    assert 'setShortcutVisibleInContextMenu(true)' in EDITOR


def test_active_editor_receives_menu_edits():
    assert 'if (active_turbo_editor() && slot) slot();' in BRIDGE
    assert 'g_turbo_editor->undo();' in BRIDGE
    assert 'g_turbo_editor->paste();' in BRIDGE


def test_modal_close_prompts_and_vfs_dialog_for_saving():
    assert 'D64TurboMessageBox::showMessage(' in EDITOR
    for marker in ('Speichern', 'Verwerfen', 'Abbrechen',
                   'return saveDocument(true)', 'D64VirtualFileDialog dialog('):
        assert marker in EDITOR


def test_save_is_atomic_and_confined_to_vfs():
    for marker in ('vfs_->writableFile(destination)', 'QSaveFile file(host)',
                   'file.commit()', 'info.isSymLink()', 'QSplitter(Qt::Horizontal',
                   'dbaseVirtualFolders', 'dbaseVirtualFiles'):
        assert marker in EDITOR


def test_close_all_respects_cancel():
    assert 'fileMenu->addAction(QStringLiteral("Alle Schließen"))' in BRIDGE
    assert 'if (editor && !editor->close()) break;' in BRIDGE


def test_zoom_updates_all_open_editors():
    assert 'for (const QPointer<D64TurboEditorWidget> &editor : g_turbo_editors)' in BRIDGE
    assert 'if (editor) editor->setGridFont(font);' in BRIDGE


def test_build_script():
    text = (ROOT / 'build_and_deploy_dbase_editor_stage628.bat').read_text(encoding='utf-8')
    assert 'build_d64qt5_mingw32.bat' in text
    assert 'libd64_qt5.dll' in text
