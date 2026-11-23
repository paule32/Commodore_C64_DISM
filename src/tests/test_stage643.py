"""Stage 643: Quelltext-/Integrationsprüfungen für internes Dateifenster und VFS.

Ohne Windows Qt5-Toolchain sind dies strukturelle Prüfungen, keine GUI-Tests.
"""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
ED = (ROOT/'d64qt5/d64_turbo_editor.hpp').read_text(encoding='utf-8')
BR = (ROOT/'d64qt5/d64qt5_bridge.cpp').read_text(encoding='utf-8')


def section(s, begin, end):
    return s.split(begin, 1)[1].split(end, 1)[0]


def test_menu_opens_file_dialog_before_constructing_editor():
    menu = section(BR, 'hookFile(QStringLiteral("Öffnen...")', 'hookFile(QStringLiteral("Speichern")')
    assert 'open_turbo_vfs_file()' in menu
    assert 'create_turbo_editor()' not in menu
    action = section(BR, 'void open_turbo_vfs_file()', 'void create_standard_menu()')
    assert action.index('dialog.exec()') < action.index('create_turbo_editor()')
    assert 'dialog.selectedVirtualPath()' in action
    assert 'editor->loadVirtualDocument(path)' in action
    assert 'QStringLiteral("prg")' in action and 'QStringLiteral("wfm")' in action


def test_file_dialog_embedded_and_modal():
    dialog = section(ED, 'class D64VirtualFileDialog final', '// Stage 628: Mehrfenster-Editor')
    assert 'public QWidget' in dialog.split('{',1)[0]
    for key in ('setParent(&layer, Qt::Widget)', 'D64TurboModalLayer layer(desktop)',
                'QEventLoop loop', 'layer.setEscapeHandler', 'layer.show()', 'loop.exec(',
                'QApplication::activePopupWidget()'):
        assert key in dialog
    assert 'QFileDialog' not in dialog and 'QMessageBox::' not in dialog


def test_layout_and_commands():
    for part in ('QSplitter(Qt::Horizontal', 'dbaseVirtualFolders', 'dbaseVirtualFiles',
                 'QStringLiteral("Name")', 'QStringLiteral("Datum")', 'QStringLiteral("Größe")',
                 'QStringLiteral("Suchen")', 'QStringLiteral("Dateiname")',
                 'QStringLiteral("Verz. Hinzufügen")', 'QStringLiteral("Löschen")',
                 'QStringLiteral("OK")', 'QStringLiteral("Abbrechen")',
                 'QStringLiteral("Hilfe")', 'dbaseVirtualFileStatus'):
        assert part in ED


def test_roots_and_private_identity():
    vfs = section(ED, 'class D64ApplicationVfs final', '// Reiner Qt::Widget-Dialog')
    for part in ('_Alle_Benutzer', '_Benutzer/', 'Dokumente', 'Alle Benutzer',
                 'QCryptographicHash::hash', 'setUserIdentity', 'hostRoot',
                 'mountPoints', 'QDir::isAbsolutePath', 'safeName',
                 'isInsideMount', 'info.isSymLink()', 'parentVirtual'):
        assert part in vfs
    assert 'root_ = QDir(root_).canonicalPath()' in vfs
    # Der private Hostpfad darf NICHT über direkte virtuelle Pfade erreichbar sein.
    assert 'if (parts.first() == shared())' in vfs
    assert 'else if (parts.first() == documents())' in vfs
    assert 'else return QString();' in vfs


def test_session_login_swaps_identity_before_success():
    impl = section(BR, 'extern "C" D64QT5_API int DBaseQtSessionLogin(',
                   'extern "C" D64QT5_API void *DBaseQtDatabaseCreate(')
    assert impl.index('if (!activate_turbo_vfs_identity(usernameText))') < impl.index('session->authenticated = true;')
    switch = section(BR, 'bool activate_turbo_vfs_identity(', 'void open_turbo_vfs_file()')
    assert '!editor->close()' in switch
    assert 'g_editor_vfs.setUserIdentity' in switch


def test_old_app_documents_migrated_only_to_host_user():
    vfs = section(ED, 'class D64ApplicationVfs final', '// Reiner Qt::Widget-Dialog')
    assert 'QStringLiteral("Dokumente")' in vfs
    assert 'setUserIdentity(QStringLiteral("Host:") + account)' in vfs
    assert 'QDir().rename(old.filePath(), dest)' in vfs


def test_virtual_parent_root_stop_and_mount_protection():
    vfs = section(ED, 'class D64ApplicationVfs final', '// Reiner Qt::Widget-Dialog')
    assert 'if (relative.isEmpty()) return QString();' in vfs
    assert 'if (virtualPath.isEmpty()) return root_;' in vfs
    assert 'if (virtualPath.isEmpty() || !virtualPath.contains(' in vfs
    assert 'virtualParent.isEmpty()) return false;' in vfs
    assert 'if (info.isDir()) return QDir().rmdir(path);' in vfs


def test_directory_and_file_double_click():
    dialog = section(ED, 'class D64VirtualFileDialog final', '// Stage 628: Mehrfenster-Editor')
    assert '&QTreeWidget::itemDoubleClicked' in dialog
    assert '&QListWidget::itemDoubleClicked' in dialog
    assert 'showDirectory(value)' in dialog
    assert 'acceptSelection()' in dialog
    assert 'addTreeEntry(QStringLiteral("..")' in dialog


def test_embedded_directory_input():
    d = section(ED, 'class D64VirtualFileDialog final', '// Stage 628: Mehrfenster-Editor')
    inputarea = section(d, 'bool inputPrompt(', 'void addDirectory()')
    assert 'QWidget blocker(this)' in inputarea
    assert 'QWidget panel(&blocker)' in inputarea
    assert 'QLineEdit *edit' in inputarea
    assert 'QEventLoop loop' in inputarea
    assert all(x in inputarea for x in ['QStringLiteral("OK")','QStringLiteral("Abbrechen")','QStringLiteral("Hilfe")'])
    assert 'QMessageBox' not in inputarea


def test_save_stays_within_vfs():
    part = section(ED, 'bool saveDocument(', 'void undo()')
    for x in ('vfs_->writableFile(destination)', 'QSaveFile file(host)',
              'file.commit()', 'D64VirtualFileDialog::SaveFile'):
        assert x in part


def test_no_regression_editor_and_window_system():
    assert 'g_turbo_editors.append(QPointer<D64TurboEditorWidget>(editor))' in BR
    assert 'rebuild_turbo_windows_menu()' in BR
    assert 'D64TurboMessageBox::showMessage(' in ED
    assert 'D64TurboArrowScrollBar(Qt::Vertical, edit_)' in ED
    assert 'D64TurboArrowScrollBar(Qt::Horizontal, this)' in ED
