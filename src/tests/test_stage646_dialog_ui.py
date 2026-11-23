"""Stage 646: in-app file dialog font, drag cursor, +24px first-column gap.

Qt GUI rendering requires a native Windows Qt5 test environment. This suite
checks the integration contracts without substituting a fake GUI result.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent
HEADER = (ROOT / 'd64qt5/d64_turbo_editor.hpp').read_text('utf-8')
DIALOG = HEADER.split('class D64VirtualFileDialog final : public QWidget', 1)[1].split('// Stage 628: Mehrfenster-Editor.', 1)[0]


def test_preferred_font_order_and_monospaced_fallback():
    assert '#include <QFontDatabase>' in HEADER
    assert 'QFontDatabase availableFonts;' in DIALOG
    first = DIALOG.split('for (const QString &candidate : {', 1)[1].split('}) {', 1)[0]
    i = [first.index('QStringLiteral("' + f + '")') for f in
         ('Consolas', 'Courier New', 'Courier')]
    assert i == sorted(i)
    assert 'availableFonts.hasFamily(candidate)' in DIALOG
    assert 'fileFont.setStyleHint(QFont::TypeWriter)' in DIALOG
    assert 'fileFont.setStyleStrategy(QFont::PreferMatch)' in DIALOG


def test_path_and_both_lists_and_header_share_exact_family():
    assert 'location_->setObjectName(QStringLiteral("dbaseVirtualFilePath"))' in DIALOG
    assert 'files_->header()->setObjectName(QStringLiteral("dbaseVirtualFileHeader"))' in DIALOG
    for obj in ('location_', 'folders_', 'files_', 'files_->header()'):
        assert 'static_cast<QWidget *>(' + obj + ')' in DIALOG
    assert 'item->setFont(fileFont);' in DIALOG
    assert 'item->setStyleSheet(fileFontStyle);' in DIALOG
    assert "font-family:'%1';" in DIALOG


def test_drag_cursor_only_on_title_not_close_button():
    assert 'dragSurface->setCursor(Qt::SizeAllCursor);' in DIALOG
    assert 'for (QWidget *dragSurface : {titleBar_, static_cast<QWidget *>(title_), titleBalance_})' in DIALOG
    assert DIALOG.index('for (QWidget *widget : findChildren<QWidget *>())') < DIALOG.index('dragSurface->setCursor(Qt::SizeAllCursor);')
    assert 'closeButton_->setCursor(Qt::PointingHandCursor);' in DIALOG
    assert 'dragWidget_->grabMouse()' in DIALOG


def test_first_column_exact_extra_24px_at_each_folder_change():
    assert 'files_->resizeColumnToContents(0);' in DIALOG
    assert 'files_->setColumnWidth(0, files_->columnWidth(0) + 24);' in DIALOG
    assert DIALOG.index('files_->resizeColumnToContents(0);') < DIALOG.index('files_->setColumnWidth(0, files_->columnWidth(0) + 24);')
    assert 'void showDirectory(const QString &virtualDirectory)' in DIALOG


def test_existing_cursors_and_vfs_are_untouched():
    assert 'handle->setCursor(Qt::SplitHCursor)' in DIALOG
    assert 'area->setCursor(atDivider ? Qt::SplitHCursor : Qt::ArrowCursor)' in DIALOG
    assert 'area->setCursor(overEntry ? Qt::PointingHandCursor : Qt::ArrowCursor)' in DIALOG
    assert 'button->setCursor(Qt::PointingHandCursor);' in DIALOG
    assert 'D64ApplicationVfs::join(currentDirectory_, name)' in DIALOG
    assert 'new D64TurboArrowScrollBar(Qt::Vertical, view)' in DIALOG
    assert 'new D64TurboArrowScrollBar(Qt::Horizontal, view)' in DIALOG
