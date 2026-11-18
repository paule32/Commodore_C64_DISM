"""Stage 626: statische Integrationspruefungen fuer Qt5-Editor/virtuelles FS.

Ein nativer Qt5/Windows-DLL-Build sowie Maus- und Dateidialogtests sind
zusaetzlich auf dem Zielsystem notwendig.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
BRIDGE = (ROOT / 'd64qt5/d64qt5_bridge.cpp').read_text(encoding='utf-8')
HEADER = (ROOT / 'd64qt5/d64_turbo_editor.hpp').read_text(encoding='utf-8')
PRO = (ROOT / 'd64qt5/d64qt5_bridge.pro').read_text(encoding='utf-8')


class Stage626EditorTests(unittest.TestCase):
    def test_shared_console_viewport(self):
        self.assertIn('new D64TurboEditorWidget(g_console->viewport(), &g_editor_vfs)', BRIDGE)
        self.assertIn('new D64TurboOutputWidget(g_console->viewport())', BRIDGE)
        self.assertIn('g_turbo_editor->raise()', BRIDGE)

    def test_qplain_text_editor_is_writable(self):
        self.assertIn('edit_ = new QPlainTextEdit(this)', HEADER)
        self.assertIn('edit_->setReadOnly(false)', HEADER)
        self.assertIn('edit_->setUndoRedoEnabled(true)', HEADER)

    def test_editor_palette_and_status(self):
        self.assertIn('background:#0000aa;color:#ffffff', HEADER)
        self.assertIn('color:#ffff55', HEADER)
        self.assertIn('dbaseTurboEditorPosition', HEADER)
        self.assertIn('cursor.blockNumber() + 1', HEADER)
        self.assertIn('cursor.positionInBlock() + 1', HEADER)
        self.assertIn('QStringLiteral("%1 : %2")', HEADER)

    def test_all_edit_menu_actions_and_shortcuts(self):
        for label, sequence in [('Rückgängig', 'Qt::Key_Z'), ('Wiederherstellen', 'Qt::Key_Y'),
                                ('Ausschneiden', 'Qt::Key_X'), ('Kopieren', 'Qt::Key_C'),
                                ('Einfügen', 'Qt::Key_V'), ('Löschen', 'Qt::Key_Delete'),
                                ('Alles auswählen', 'Qt::Key_A')]:
            with self.subTest(label=label):
                self.assertIn(f'QStringLiteral("{label}")', BRIDGE)
                self.assertIn(sequence, BRIDGE)
        self.assertIn('editMenu->addSeparator();', BRIDGE)

    def test_file_actions(self):
        for text in ('Neu', 'Öffnen...', 'Speichern', 'Speichern unter...'):
            self.assertIn(f'QStringLiteral("{text}")', BRIDGE)
        self.assertIn('g_turbo_editor->openDocument()', BRIDGE)
        self.assertIn('g_turbo_editor->saveDocument(true)', BRIDGE)
        self.assertIn('create_standard_menu();', BRIDGE)

    def test_save_and_open_safely(self):
        self.assertIn('QSaveFile file(host)', HEADER)
        self.assertIn('file.commit()', HEADER)
        self.assertIn('QFile file(host)', HEADER)
        self.assertIn('vfs_->readableFile(relative)', HEADER)
        self.assertIn('vfs_->writableFile(destination)', HEADER)
        self.assertIn('edit_->document()->isModified()', HEADER)
        self.assertIn('confirmDiscard()', HEADER)

    def test_own_mapping_per_executable(self):
        self.assertIn('QCoreApplication::applicationFilePath()', HEADER)
        self.assertIn('QCryptographicHash::Sha256', HEADER)
        self.assertIn('QStandardPaths::AppLocalDataLocation', HEADER)
        self.assertIn('dBase2Many/Anwendungen/', HEADER)
        self.assertIn('g_editor_vfs.initialize()', BRIDGE)

    def test_vfs_blocks_escape(self):
        for check in ('QDir::isAbsolutePath(source)', "source.contains(QLatin1Char('\\\\'))",
                      'component == QLatin1String("..")', 'info.isSymLink()',
                      'info.canonicalFilePath()', 'isInside(canonical)',
                      'isInside(candidate)', 'existingDirectory(parentVirtual(virtualPath))'):
            with self.subTest(check=check):
                self.assertIn(check, HEADER)

    def test_two_panel_dialog(self):
        self.assertIn('QSplitter(Qt::Horizontal, this)', HEADER)
        self.assertIn('setStretchFactor(0, 1)', HEADER)
        self.assertIn('setStretchFactor(1, 3)', HEADER)
        self.assertIn('new QListWidget(splitter_)', HEADER)
        self.assertIn('new QTreeWidget(splitter_)', HEADER)
        self.assertIn('QStyle::SP_DirIcon', HEADER)
        self.assertIn('QStyle::SP_FileIcon', HEADER)
        self.assertIn('QStringLiteral("Meine Dokumente")', HEADER)
        self.assertIn('dbaseVirtualFileSearch', HEADER)

    def test_dialog_actions(self):
        for text in ('OK', 'Abbrechen', 'Hilfe', 'Dateiname:'):
            self.assertIn(f'QStringLiteral("{text}")', HEADER)
        self.assertIn('D64VirtualFileDialog::SaveFile', HEADER)
        self.assertIn('D64VirtualFileDialog::OpenFile', HEADER)
        self.assertIn('QMessageBox::Yes | QMessageBox::No', HEADER)

    def test_font_and_movement_in_cells(self):
        self.assertIn('g_turbo_editor->setGridFont(font)', BRIDGE)
        self.assertIn('const QFontMetrics fm(font)', HEADER)
        self.assertIn('qRound(static_cast<double>(delta.x()) / cw_)', HEADER)
        self.assertIn('qRound(static_cast<double>(delta.y()) / ch_)', HEADER)
        self.assertIn('setGeometry(xCol_ * cw_, yRow_ * ch_, cols * cw_, rows * ch_)', HEADER)

    def test_no_extra_qt_moc(self):
        self.assertNotIn('Q_OBJECT', HEADER.split('class D64ApplicationVfs', 1)[1])
        self.assertIn('HEADERS += d64_turbo_editor.hpp', PRO)

    def test_existing_background_untouched(self):
        self.assertIn('render_console_character_pattern(code, foreground, background)', BRIDGE)
        self.assertIn('g_turbo_output->appendOutput(QString::fromLocal8Bit(text, length))', BRIDGE)


if __name__ == '__main__':
    unittest.main()
