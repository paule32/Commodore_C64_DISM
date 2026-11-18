#pragma once

// Stage 626: Turbo-Vision-Editor in der dBASE-Qt5-Konsole.
// Eigenstaendiger, zeichenraster-basierter Editor mit auf die Anwendung
// beschraenktem virtuellem Dateisystem und zweispaltigem Dateidialog.
// Keine MOC-/Q_OBJECT-Abhaengigkeit.

#include <QApplication>
#include <QCoreApplication>
#include <QKeySequence>
#include <QPaintEvent>
#include <QRegularExpression>
#include <QResizeEvent>
#include <functional>
#include <QCryptographicHash>
#include <QDialog>
#include <QDir>
#include <QFile>
#include <QFileInfo>
#include <QFontMetrics>
#include <QHBoxLayout>
#include <QLabel>
#include <QLineEdit>
#include <QListWidget>
#include <QMessageBox>
#include <QMouseEvent>
#include <QPainter>
#include <QPlainTextEdit>
#include <QPointer>
#include <QPushButton>
#include <QSaveFile>
#include <QScrollBar>
#include <QSplitter>
#include <QStandardPaths>
#include <QStyle>
#include <QTextBlock>
#include <QTextCursor>
#include <QTextDocument>
#include <QTreeWidget>
#include <QVBoxLayout>
#include <QWidget>
#include <QMenu>
#include <QToolButton>
#include <QCloseEvent>
#include <QTimer>
#include <QAction>
#include <QPalette>
#include <utility>
#include "d64_turbo_scrollbar.hpp"
#include "d64_turbo_messagebox.hpp"
#include "d64_turbo_context_menu.hpp"

class D64ApplicationVfs final
{
public:
    bool initialize()
    {
        // Derselbe EXE-Pfad bekommt ueber Programmstarts hinweg dasselbe
        // eigene Host-Verzeichnis; verschiedene EXEs werden getrennt.
        const QString exe = QDir::cleanPath(QCoreApplication::applicationFilePath());
        const QByteArray digest = QCryptographicHash::hash(
            exe.toUtf8(), QCryptographicHash::Sha256).toHex().left(16);
        QString appName = QFileInfo(exe).completeBaseName();
        appName.replace(QRegularExpression(QStringLiteral("[^A-Za-z0-9_-]")), QStringLiteral("_"));
        if (appName.isEmpty()) appName = QStringLiteral("Programm");
        const QString local = QStandardPaths::writableLocation(QStandardPaths::AppLocalDataLocation);
        if (local.isEmpty()) return false;
        root_ = QDir(local).filePath(QStringLiteral("dBase2Many/Anwendungen/")
                                     + appName + QLatin1Char('-') + QString::fromLatin1(digest));
        if (!QDir().mkpath(QDir(root_).filePath(QStringLiteral("Dokumente")))) {
            root_.clear();
            return false;
        }
        root_ = QDir(root_).canonicalPath();
        return !root_.isEmpty();
    }

    QString hostRoot() const { return root_; }
    QString documents() const { return QStringLiteral("Dokumente"); }

    // Nur virtuelle, relative Pfade. Keine absoluten Host-Pfade, kein '..',
    // keine Symlinks/Junctions innerhalb des gemappten Baums.
    QString hostPath(const QString &virtualPath) const
    {
        if (root_.isEmpty()) return QString();
        const QString source = virtualPath.trimmed();
        if (QDir::isAbsolutePath(source) || source.contains(QLatin1Char('\\'))
            || source.contains(QLatin1Char(':')) || source.contains(QChar(0)))
            return QString();
        const QStringList components = source.split(QLatin1Char('/'), Qt::SkipEmptyParts);
        QString probe = root_;
        for (const QString &component : components) {
            if (component == QLatin1String(".") || component == QLatin1String("..")
                || component.isEmpty())
                return QString();
            probe = QDir(probe).filePath(component);
            const QFileInfo info(probe);
            if (info.isSymLink()) return QString();
            if (info.exists()) {
                const QString canonical = info.canonicalFilePath();
                if (!isInside(canonical)) return QString();
            }
        }
        const QString candidate = QDir::cleanPath(probe);
        if (!isInside(candidate)) return QString();
        return candidate;
    }

    QString existingDirectory(const QString &virtualPath) const
    {
        const QString path = hostPath(virtualPath);
        return !path.isEmpty() && QFileInfo(path).isDir() ? path : QString();
    }

    QString readableFile(const QString &virtualPath) const
    {
        const QString path = hostPath(virtualPath);
        const QFileInfo info(path);
        return !path.isEmpty() && info.isFile() && !info.isSymLink()
            ? path : QString();
    }

    QString writableFile(const QString &virtualPath) const
    {
        const QString path = hostPath(virtualPath);
        if (path.isEmpty()) return QString();
        const QFileInfo info(path);
        if (info.exists() && (!info.isFile() || info.isSymLink())) return QString();
        if (info.isSymLink() || existingDirectory(parentVirtual(virtualPath)).isEmpty())
            return QString();
        return path;
    }

    static QString parentVirtual(const QString &relative)
    {
        const QString result = QFileInfo(relative).path();
        return result == QLatin1String(".") ? QString() : result;
    }

    static QString join(const QString &directory, const QString &name)
    {
        return directory.isEmpty() ? name : directory + QLatin1Char('/') + name;
    }

private:
    bool isInside(const QString &path) const
    {
        if (root_.isEmpty()) return false;
#ifdef _WIN32
        const Qt::CaseSensitivity sensitivity = Qt::CaseInsensitive;
#else
        const Qt::CaseSensitivity sensitivity = Qt::CaseSensitive;
#endif
        return path.compare(root_, sensitivity) == 0
            || path.startsWith(root_ + QLatin1Char('/'), sensitivity);
    }
    QString root_;
};

class D64VirtualFileDialog final : public QDialog
{
public:
    enum Mode { OpenFile, SaveFile };

    explicit D64VirtualFileDialog(D64ApplicationVfs *vfs, Mode mode,
                                   const QString &previousFile, QWidget *parent, bool darkMode = true)
        : QDialog(parent), vfs_(vfs), mode_(mode)
    {
        setObjectName(QStringLiteral("dbaseVirtualFileDialog"));
        setWindowTitle(mode == SaveFile ? QStringLiteral("Datei speichern unter")
                                         : QStringLiteral("Datei öffnen"));
        setMinimumSize(600, 370);
        resize(820, 510);
        setStyleSheet(QStringLiteral(
            "QDialog#dbaseVirtualFileDialog{background:#0000aa;color:white;}"
            "QLabel{color:white;}"
            "QListWidget,QTreeWidget,QLineEdit{background:#000080;color:white;"
            "border:1px solid #ffff55;selection-background-color:#aaaa00;selection-color:black;}"
            "QHeaderView::section{background:#0000aa;color:#ffff55;border:1px solid #ffff55;}"
            "QPushButton{background:#0000aa;color:#ffff55;border:1px solid #ffff55;"
            "padding:5px 15px;min-width:80px;}"
            "QPushButton:hover{background:#3333cc;}"
            "QSplitter::handle{background:#ffff55;}"));
        if (!darkMode) {
            setStyleSheet(QStringLiteral(
                "QDialog#dbaseVirtualFileDialog{background:#f0f2f8;color:#1e2130;}"
                "QLabel{color:#1e2130;}"
                "QListWidget,QTreeWidget,QLineEdit{background:#ffffff;color:#182440;"
                "border:1px solid #5474ae;selection-background-color:#acc1ed;}"
                "QHeaderView::section{background:#dfe7f7;color:#233b66;border:1px solid #5474ae;}"
                "QPushButton{background:#dfe7f7;color:#233b66;border:1px solid #5474ae;"
                "padding:5px 15px;min-width:80px;}"
                "QSplitter::handle{background:#5474ae;}"));
        }
        auto *outer = new QVBoxLayout(this);
        auto *intro = new QLabel(QStringLiteral("Virtuelles Dateisystem – Zugriff nur innerhalb der Anwendung"), this);
        outer->addWidget(intro);
        location_ = new QLabel(this);
        location_->setObjectName(QStringLiteral("dbaseVirtualFileLocation"));
        outer->addWidget(location_);
        auto *searchRow = new QHBoxLayout();
        searchRow->addWidget(new QLabel(QStringLiteral("Suche:"), this));
        search_ = new QLineEdit(this);
        search_->setObjectName(QStringLiteral("dbaseVirtualFileSearch"));
        search_->setPlaceholderText(QStringLiteral("Dateinamen im aktuellen Verzeichnis suchen ..."));
        searchRow->addWidget(search_, 1);
        outer->addLayout(searchRow);

        splitter_ = new QSplitter(Qt::Horizontal, this);
        splitter_->setObjectName(QStringLiteral("dbaseVirtualFileSplitter"));
        splitter_->setChildrenCollapsible(false);
        folders_ = new QListWidget(splitter_);
        folders_->setObjectName(QStringLiteral("dbaseVirtualFolders"));
        folders_->setMinimumWidth(170);
        folders_->setCursor(Qt::PointingHandCursor);
        files_ = new QTreeWidget(splitter_);
        files_->setObjectName(QStringLiteral("dbaseVirtualFiles"));
        files_->setHeaderLabels({QStringLiteral("Dateiname"), QStringLiteral("Typ"),
                                 QStringLiteral("Groesse")});
        files_->setRootIsDecorated(false);
        files_->setAlternatingRowColors(false);
        files_->setMinimumWidth(250);
        splitter_->addWidget(folders_);
        splitter_->addWidget(files_);
        splitter_->setStretchFactor(0, 1);
        splitter_->setStretchFactor(1, 3);
        splitter_->setSizes({230, 590});
        outer->addWidget(splitter_, 1);

        auto *filenameRow = new QHBoxLayout();
        filenameRow->addWidget(new QLabel(QStringLiteral("Dateiname:"), this));
        filename_ = new QLineEdit(this);
        filename_->setObjectName(QStringLiteral("dbaseVirtualFilename"));
        filenameRow->addWidget(filename_, 1);
        outer->addLayout(filenameRow);

        auto *buttons = new QHBoxLayout();
        buttons->addStretch(1);
        auto *ok = new QPushButton(QStringLiteral("OK"), this);
        auto *cancel = new QPushButton(QStringLiteral("Abbrechen"), this);
        auto *help = new QPushButton(QStringLiteral("Hilfe"), this);
        ok->setObjectName(QStringLiteral("dbaseVirtualFileOK"));
        cancel->setObjectName(QStringLiteral("dbaseVirtualFileCancel"));
        help->setObjectName(QStringLiteral("dbaseVirtualFileHelp"));
        buttons->addWidget(ok);
        buttons->addWidget(cancel);
        buttons->addWidget(help);
        outer->addLayout(buttons);

        QObject::connect(ok, &QPushButton::clicked, this, [this]() { acceptSelection(); });
        QObject::connect(cancel, &QPushButton::clicked, this, &QDialog::reject);
        QObject::connect(help, &QPushButton::clicked, this, [this]() {
            QMessageBox::information(this, QStringLiteral("Hilfe – Dateiauswahl"),
                QStringLiteral("Links: Meine Dokumente und Verzeichnisse oeffnen. "
                               "Rechts: Dateien ansehen und per Doppelklick auswaehlen. "
                               "Die Suche filtert Dateinamen im aktuellen Ordner. "
                               "Der Trenner zwischen beiden Listen ist verschiebbar. "
                               "Dateinamen unten eingeben und mit OK bestaetigen. "
                               "Dateien duerfen nur innerhalb des dieser Anwendung fest zugeordneten "
                               "virtuellen Verzeichnisses geoeffnet und gespeichert werden.\n\nHost-Verzeichnis:\n%1")
                    .arg(vfs_ ? vfs_->hostRoot() : QString()));
        });
        QObject::connect(folders_, &QListWidget::itemClicked, this, [this](QListWidgetItem *item) {
            if (item) showDirectory(item->data(Qt::UserRole).toString());
        });
        QObject::connect(files_, &QTreeWidget::itemClicked, this, [this](QTreeWidgetItem *item, int) {
            if (item) filename_->setText(item->data(0, Qt::UserRole).toString());
        });
        QObject::connect(files_, &QTreeWidget::itemDoubleClicked, this, [this](QTreeWidgetItem *item, int) {
            if (item) {
                filename_->setText(item->data(0, Qt::UserRole).toString());
                acceptSelection();
            }
        });
        QObject::connect(search_, &QLineEdit::textChanged, this, [this](const QString &value) {
            if (!files_) return;
            for (int i = 0; i < files_->topLevelItemCount(); ++i) {
                QTreeWidgetItem *item = files_->topLevelItem(i);
                if (item)
                    item->setHidden(!item->text(0).contains(value, Qt::CaseInsensitive));
            }
        });
        QObject::connect(filename_, &QLineEdit::returnPressed, this, [this]() { acceptSelection(); });
        const QString priorDirectory = D64ApplicationVfs::parentVirtual(previousFile);
        const QString initial = vfs_ && !vfs_->existingDirectory(priorDirectory).isEmpty()
            ? priorDirectory : (vfs_ ? vfs_->documents() : QString());
        showDirectory(initial);
        if (!previousFile.isEmpty()) filename_->setText(QFileInfo(previousFile).fileName());
    }

    QString selectedVirtualPath() const { return selected_; }

private:
    void showDirectory(const QString &virtualDirectory)
    {
        if (!vfs_) return;
        const QString host = vfs_->existingDirectory(virtualDirectory);
        if (host.isEmpty()) return;
        currentDirectory_ = virtualDirectory;
        location_->setText(QStringLiteral("Pfad: /") + virtualDirectory);
        folders_->clear();
        files_->clear();
        auto addFolder = [this](const QString &label, const QString &path, QStyle::StandardPixmap icon) {
            auto *entry = new QListWidgetItem(style()->standardIcon(icon), label, folders_);
            entry->setData(Qt::UserRole, path);
            entry->setToolTip(QStringLiteral("Verzeichnis öffnen: /") + path);
        };
        addFolder(QStringLiteral("Meine Dokumente"), vfs_->documents(), QStyle::SP_DirHomeIcon);
        if (!virtualDirectory.isEmpty()) {
            addFolder(QStringLiteral(".. (Übergeordnet)"),
                      D64ApplicationVfs::parentVirtual(virtualDirectory), QStyle::SP_ArrowUp);
        }
        const QFileInfoList dirs = QDir(host).entryInfoList(QDir::Dirs | QDir::NoDotAndDotDot
                                                           | QDir::Readable, QDir::Name);
        for (const QFileInfo &dir : dirs) {
            const QString virtualChild = D64ApplicationVfs::join(virtualDirectory, dir.fileName());
            if (dir.isSymLink() || vfs_->existingDirectory(virtualChild).isEmpty()) continue;
            addFolder(dir.fileName(), virtualChild, QStyle::SP_DirIcon);
        }
        const QFileInfoList entries = QDir(host).entryInfoList(QDir::Files | QDir::Readable,
                                                                QDir::Name | QDir::IgnoreCase);
        for (const QFileInfo &file : entries) {
            if (file.isSymLink() || vfs_->readableFile(
                D64ApplicationVfs::join(virtualDirectory, file.fileName())).isEmpty()) continue;
            auto *item = new QTreeWidgetItem(files_);
            item->setText(0, file.fileName());
            item->setIcon(0, style()->standardIcon(QStyle::SP_FileIcon));
            item->setText(1, file.suffix().isEmpty() ? QStringLiteral("Datei")
                                                       : file.suffix().toUpper());
            item->setText(2, QString::number(file.size()));
            item->setData(0, Qt::UserRole, file.fileName());
        }
        files_->resizeColumnToContents(0);
        search_->clear();
        filename_->clear();
    }

    void acceptSelection()
    {
        if (!vfs_) return;
        const QString name = filename_->text().trimmed();
        if (name.isEmpty() || name == QLatin1String(".") || name == QLatin1String("..")
            || name.contains(QLatin1Char('/')) || name.contains(QLatin1Char('\\'))
            || name.contains(QLatin1Char(':'))) {
            QMessageBox::warning(this, QStringLiteral("Ungueltiger Name"),
                                 QStringLiteral("Bitte einen Dateinamen ohne Pfadtrenner angeben."));
            return;
        }
#ifdef _WIN32
        // Win32-Geraetenamen sind keine regulaeren Dateien, auch mit Suffix.
        const QString base = name.section(QLatin1Char('.'), 0, 0).toUpper();
        if (base == QLatin1String("CON") || base == QLatin1String("PRN")
            || base == QLatin1String("AUX") || base == QLatin1String("NUL")
            || QRegularExpression(QStringLiteral("^(COM|LPT)[1-9]$")).match(base).hasMatch()
            || name.endsWith(QLatin1Char('.'))) {
            QMessageBox::warning(this, QStringLiteral("Reservierter Dateiname"),
                QStringLiteral("Der gewaehlte Name ist unter Windows reserviert."));
            return;
        }
#endif
        const QString relative = D64ApplicationVfs::join(currentDirectory_, name);
        const QString host = mode_ == OpenFile ? vfs_->readableFile(relative)
                                                : vfs_->writableFile(relative);
        if (host.isEmpty()) {
            QMessageBox::warning(this, QStringLiteral("Dateizugriff nicht erlaubt"),
                QStringLiteral("Die Datei ist nicht vorhanden oder liegt ausserhalb des "
                               "zugeordneten Verzeichnisses."));
            return;
        }
        if (mode_ == SaveFile && QFileInfo::exists(host)
            && QMessageBox::question(this, QStringLiteral("Datei ueberschreiben"),
                 QStringLiteral("Die Datei existiert bereits. Ueberschreiben?"),
                 QMessageBox::Yes | QMessageBox::No, QMessageBox::No) != QMessageBox::Yes)
            return;
        selected_ = relative;
        accept();
    }

    D64ApplicationVfs *vfs_ = nullptr;
    Mode mode_ = OpenFile;
    QSplitter *splitter_ = nullptr;
    QListWidget *folders_ = nullptr;
    QTreeWidget *files_ = nullptr;
    QLineEdit *filename_ = nullptr;
    QLineEdit *search_ = nullptr;
    QLabel *location_ = nullptr;
    QString currentDirectory_;
    QString selected_;
};

// Stage 628: Mehrfenster-Editor. Jedes Dokument besitzt sein eigenes Widget,
// seinen eigenen QPlainTextEdit, Cursor, Undo-Stack und virtuellen Dateipfad.
// Kein Q_OBJECT, somit kein zusätzlicher MOC-Schritt.
class D64TurboEditorWidget final : public QWidget
{
public:
    explicit D64TurboEditorWidget(QWidget *viewport, D64ApplicationVfs *vfs)
        : QWidget(viewport), vfs_(vfs)
    {
        setObjectName(QStringLiteral("dbaseTurboVisionEditor"));
        setAttribute(Qt::WA_StyledBackground, true);
        setAttribute(Qt::WA_DeleteOnClose, true);
        setMouseTracking(true);
        setFocusPolicy(Qt::StrongFocus);

        title_ = new QLabel(this);
        title_->setObjectName(QStringLiteral("dbaseTurboEditorTitle"));
        title_->setAlignment(Qt::AlignCenter);
        title_->setCursor(Qt::SizeAllCursor);
        title_->setStyleSheet(QStringLiteral("color:#ffff55;background:#2256cf;font-weight:bold;"));
        title_->installEventFilter(this);

        closeButton_ = new QToolButton(this);
        closeButton_->setObjectName(QStringLiteral("dbaseTurboEditorCloseButton"));
        closeButton_->setText(QStringLiteral("×"));
        closeButton_->setToolTip(QStringLiteral("Zum Schließen doppelklicken"));
        closeButton_->setFocusPolicy(Qt::NoFocus);
        closeButton_->setCursor(Qt::PointingHandCursor);
        closeButton_->setStyleSheet(QStringLiteral(
            "QToolButton#dbaseTurboEditorCloseButton{color:#ffff55;background:#163b9c;"
            "border:1px solid #ffff55;font-weight:bold;padding:0;}"
            "QToolButton#dbaseTurboEditorCloseButton:hover{background:#355de0;}"));
        closeButton_->installEventFilter(this);

        maximizeButton_ = new QToolButton(this);
        maximizeButton_->setObjectName(QStringLiteral("dbaseTurboEditorMaximizeButton"));
        maximizeButton_->setText(QStringLiteral("□"));
        maximizeButton_->setToolTip(QStringLiteral("Editor maximieren"));
        maximizeButton_->setFocusPolicy(Qt::NoFocus);
        maximizeButton_->setCursor(Qt::PointingHandCursor);
        maximizeButton_->setStyleSheet(QStringLiteral(
            "QToolButton#dbaseTurboEditorMaximizeButton{color:#ffff55;background:#163b9c;"
            "border:1px solid #ffff55;font-weight:bold;padding:0;}"
            "QToolButton#dbaseTurboEditorMaximizeButton:hover{background:#355de0;}"));
        QObject::connect(maximizeButton_, &QToolButton::clicked, this,
                         [this]() { toggleMaximized(); });
        maximizeButton_->installEventFilter(this);

        edit_ = new QPlainTextEdit(this);
        edit_->setObjectName(QStringLiteral("dbaseTurboEditorText"));
        edit_->setReadOnly(false);
        edit_->setUndoRedoEnabled(true);
        edit_->setFrameShape(QFrame::NoFrame);
        edit_->setLineWrapMode(QPlainTextEdit::NoWrap);
        edit_->document()->setDocumentMargin(0.0);
        edit_->setHorizontalScrollBarPolicy(Qt::ScrollBarAlwaysOff);
        edit_->setVerticalScrollBarPolicy(Qt::ScrollBarAlwaysOn);
        auto *verticalBar = new D64TurboArrowScrollBar(Qt::Vertical, edit_);
        verticalBar->setTurboEditorTheme();
        verticalBar->setCursor(Qt::ArrowCursor);
        edit_->setVerticalScrollBar(verticalBar);
        verticalBar->installEventFilter(this);
        edit_->setStyleSheet(QStringLiteral(
            "QPlainTextEdit#dbaseTurboEditorText{background:#0000aa;color:#ffffff;"
            "selection-background-color:#aaaa00;selection-color:#000080;border:0;padding:2px;}"
            // 15px Endfelder liegen IN den CSS-Margins, die Rille nur dazwischen.
            "QScrollBar:vertical{background:#000080;width:15px;"
            "margin:15px 0px 15px 0px;border:1px solid #ffff55;}"
            "QScrollBar::groove:vertical{background:#000080;}"
            "QScrollBar::handle:vertical{background:#686868;min-height:15px;"
            "border:1px solid #bababa;}"
            "QScrollBar::sub-line:vertical{background:#0000aa;height:15px;"
            "subcontrol-position:top;subcontrol-origin:margin;border:1px solid #ffff55;}"
            "QScrollBar::add-line:vertical{background:#0000aa;height:15px;"
            "subcontrol-position:bottom;subcontrol-origin:margin;border:1px solid #ffff55;}"
            "QScrollBar::add-page:vertical,QScrollBar::sub-page:vertical{background:#000080;}"));
        edit_->setContextMenuPolicy(Qt::CustomContextMenu);
        edit_->installEventFilter(this);
        edit_->viewport()->setCursor(Qt::IBeamCursor);
        edit_->setCursor(Qt::IBeamCursor);
        edit_->viewport()->installEventFilter(this);
        QObject::connect(edit_, &QWidget::customContextMenuRequested,
                         this, [this](const QPoint &where) { showGermanContextMenu(where); });

        // Die horizontale Leiste liegt in der *letzten Fensterzeile*, neben
        // dem Cursor-Indikator; die interne QTextEdit-Leiste bleibt unsichtbar.
        horizontalBar_ = new D64TurboArrowScrollBar(Qt::Horizontal, this);
        horizontalBar_->setObjectName(QStringLiteral("dbaseTurboEditorHorizontalScroll"));
        horizontalBar_->setTurboEditorTheme();
        horizontalBar_->setCursor(Qt::ArrowCursor);
        horizontalBar_->setStyleSheet(QStringLiteral(
            // Gleiche Rille, Thumb-Form und Pfeilfelder wie die vertikale Leiste.
            "QScrollBar:horizontal{background:#000080;height:15px;"
            "margin:0px 15px 0px 15px;border:1px solid #ffff55;}"
            "QScrollBar::groove:horizontal{background:#000080;}"
            "QScrollBar::handle:horizontal{background:#686868;min-width:15px;"
            "border:1px solid #bababa;}"
            "QScrollBar::sub-line:horizontal{background:#0000aa;width:15px;"
            "subcontrol-position:left;subcontrol-origin:margin;border:1px solid #ffff55;}"
            "QScrollBar::add-line:horizontal{background:#0000aa;width:15px;"
            "subcontrol-position:right;subcontrol-origin:margin;border:1px solid #ffff55;}"
            "QScrollBar::add-page:horizontal,QScrollBar::sub-page:horizontal{background:#000080;}"));
        QScrollBar *internalH = edit_->horizontalScrollBar();
        QObject::connect(internalH, &QScrollBar::rangeChanged, this,
                         [this, internalH](int min, int max) {
            horizontalBar_->setRange(min, max);
            horizontalBar_->setPageStep(internalH->pageStep());
            horizontalBar_->setSingleStep(internalH->singleStep());
            horizontalBar_->setValue(internalH->value());
        });
        QObject::connect(internalH, &QScrollBar::valueChanged,
                         horizontalBar_, &QScrollBar::setValue);
        QObject::connect(horizontalBar_, &QScrollBar::valueChanged,
                         internalH, &QScrollBar::setValue);
        horizontalBar_->installEventFilter(this);

        status_ = new QLabel(QStringLiteral("1 : 1"), this);
        status_->setObjectName(QStringLiteral("dbaseTurboEditorPosition"));
        status_->setStyleSheet(QStringLiteral("background:#0000aa;color:#ffff55;"));
        status_->setAlignment(Qt::AlignLeft | Qt::AlignVCenter);
        status_->installEventFilter(this);

        grip_ = new QLabel(QStringLiteral("◢"), this);
        grip_->setObjectName(QStringLiteral("dbaseTurboEditorGridGrip"));
        grip_->setAlignment(Qt::AlignCenter);
        grip_->setCursor(Qt::SizeFDiagCursor);
        grip_->setStyleSheet(QStringLiteral(
            "color:#ffff55;background:#2455cc;border:1px solid #ffff55;"));
        grip_->setMouseTracking(true);
        grip_->installEventFilter(this);

        QObject::connect(edit_, &QPlainTextEdit::cursorPositionChanged, this,
                         [this]() { updateStatus(); });
        QObject::connect(edit_->document(), &QTextDocument::modificationChanged, this,
                         [this](bool) { updateTitle(); });
        if (viewport) viewport->installEventFilter(this);
        updateTitle();
        hide();
    }

    void setActivationCallback(std::function<void(D64TurboEditorWidget *)> callback)
    { onActivated_ = std::move(callback); }
    void setClosedCallback(std::function<void(D64TurboEditorWidget *)> callback)
    { onClosed_ = std::move(callback); }
    void setDarkMode(bool dark) { darkMode_ = dark; }

    void setGridFont(const QFont &font)
    {
        edit_->setFont(font);
        title_->setFont(font);
        status_->setFont(font);
        grip_->setFont(font);
        horizontalBar_->setFont(font);
        closeButton_->setFont(font);
        maximizeButton_->setFont(font);
        const QFontMetrics fm(font);
        cw_ = qMax(1, fm.horizontalAdvance(QLatin1Char('M')));
        ch_ = qMax(1, fm.lineSpacing());
        applyGridGeometry();
    }

    void setInitialGridPosition(int col, int row)
    {
        xCol_ = qMax(0, col);
        yRow_ = qMax(0, row);
        applyGridGeometry();
    }
    QPlainTextEdit *textEditor() const { return edit_; }
    bool isModified() const { return edit_ && edit_->document()->isModified(); }
    // Stage 632: Der Fenstermanager verwendet diese oeffentliche API fuer
    // die Fensterliste. Gleicher Name und Aenderungsmarker wie in der Titelleiste.
    QString windowCaption() const
    {
        const QString name = relativeFile_.isEmpty()
            ? QStringLiteral("Unbenannt")
            : QFileInfo(relativeFile_).fileName();
        return name + (isModified() ? QStringLiteral(" *") : QString());
    }
    bool confirmClose() { return confirmDiscard(); }
    bool isMaximizedInViewport() const { return maximized_; }
    int gridColumns() const { return preferredCols_; }
    int gridRows() const { return preferredRows_; }

    // Stage 631: Kaskadieren/Nebeneinander über das gemeinsame Fenster-Menü.
    // Fenstergrößen bleiben als DOS-Zeichen, nicht als Pixel gespeichert.
    void setGridGeometry(int column, int row, int columns, int rows)
    {
        if (maximized_) toggleMaximized();
        xCol_ = column;
        yRow_ = row;
        preferredCols_ = qMax(26, columns);
        preferredRows_ = qMax(8, rows);
        applyGridGeometry();
    }

    void activate()
    {
        if (!parentWidget()) return;
        applyGridGeometry();
        show();
        raise();
        if (onActivated_) onActivated_(this);
        edit_->setFocus(Qt::OtherFocusReason);
    }

    bool newDocument()
    {
        if (!confirmDiscard()) return false;
        edit_->clear();
        relativeFile_.clear();
        edit_->document()->setModified(false);
        updateTitle();
        activate();
        return true;
    }

    bool openDocument()
    {
        if (!confirmDiscard() || !vfs_) return false;
        D64VirtualFileDialog dialog(vfs_, D64VirtualFileDialog::OpenFile,
                                    relativeFile_, this, darkMode_);
        if (dialog.exec() != QDialog::Accepted) return false;
        const QString relative = dialog.selectedVirtualPath();
        const QString host = vfs_->readableFile(relative);
        if (host.isEmpty()) return false;
        QFile file(host);
        if (!file.open(QIODevice::ReadOnly)) {
            showError(QStringLiteral("Öffnen fehlgeschlagen"), file.errorString());
            return false;
        }
        const QByteArray data = file.readAll();
        if (file.error() != QFile::NoError) {
            showError(QStringLiteral("Lesefehler"), file.errorString());
            return false;
        }
        edit_->setPlainText(QString::fromUtf8(data));
        relativeFile_ = relative;
        edit_->document()->setModified(false);
        updateTitle();
        activate();
        return true;
    }

    bool saveDocument(bool forceDialog = false)
    {
        if (!vfs_) return false;
        QString destination = relativeFile_;
        if (forceDialog || destination.isEmpty()) {
            D64VirtualFileDialog dialog(vfs_, D64VirtualFileDialog::SaveFile,
                                        relativeFile_, this, darkMode_);
            if (dialog.exec() != QDialog::Accepted) return false;
            destination = dialog.selectedVirtualPath();
        }
        const QString host = vfs_->writableFile(destination);
        if (host.isEmpty()) {
            showError(QStringLiteral("Zugriff verweigert"),
                      QStringLiteral("Speichern ist nur im virtuellen Dateisystem erlaubt."));
            return false;
        }
        QSaveFile file(host);
        if (!file.open(QIODevice::WriteOnly)) {
            showError(QStringLiteral("Speichern fehlgeschlagen"), file.errorString());
            return false;
        }
        const QByteArray data = edit_->toPlainText().toUtf8();
        if (file.write(data) != data.size() || !file.commit()) {
            showError(QStringLiteral("Speichern fehlgeschlagen"), file.errorString());
            return false;
        }
        relativeFile_ = destination;
        edit_->document()->setModified(false);
        updateTitle();
        return true;
    }

    void undo() { edit_->undo(); }
    void redo() { edit_->redo(); }
    void cut() { edit_->cut(); }
    void copy() { edit_->copy(); }
    void paste() { edit_->paste(); }
    void deleteSelection()
    {
        QTextCursor cursor = edit_->textCursor();
        if (cursor.hasSelection()) cursor.removeSelectedText();
        else cursor.deleteChar();
        edit_->setTextCursor(cursor);
    }
    void selectAll() { edit_->selectAll(); }

    void toggleMaximized()
    {
        if (!parentWidget()) return;
        moving_ = resizing_ = false;
        if (!maximized_) {
            restoreCol_ = xCol_;
            restoreRow_ = yRow_;
            restoreCols_ = preferredCols_;
            restoreRows_ = preferredRows_;
            maximized_ = true;
            maximizeButton_->setText(QStringLiteral("❐"));
            maximizeButton_->setToolTip(QStringLiteral("Editor wiederherstellen"));
            grip_->hide();
            fitMaximizedToViewport();
        } else {
            maximized_ = false;
            maximizeButton_->setText(QStringLiteral("□"));
            maximizeButton_->setToolTip(QStringLiteral("Editor maximieren"));
            xCol_ = restoreCol_;
            yRow_ = restoreRow_;
            preferredCols_ = restoreCols_;
            preferredRows_ = restoreRows_;
            applyGridGeometry();
            grip_->show();
        }
        update();
    }

protected:
    void closeEvent(QCloseEvent *event) override
    {
        if (!confirmDiscard()) {
            event->ignore();
            return;
        }
        if (onClosed_) onClosed_(this);
        QWidget::closeEvent(event);
    }

    void paintEvent(QPaintEvent *) override
    {
        QPainter p(this);
        const int right = width() - shadow_ - 1;
        const int bottom = height() - shadow_ - 1;
        p.fillRect(QRect(shadow_, shadow_, width()-shadow_, height()-shadow_), QColor("#05051a"));
        p.fillRect(QRect(0, 0, right+1, bottom+1), QColor("#0000aa"));
        p.setPen(QPen(QColor("#ffff55"), 2));
        p.drawRect(1, 1, right-2, bottom-2);
        p.setPen(QPen(QColor("#d8c840"), 1));
        p.drawRect(4, 4, right-8, bottom-8);
        p.fillRect(QRect(6, 6, right-11, titleHeight()-7), QColor("#2256cf"));
    }

    void resizeEvent(QResizeEvent *event) override
    {
        QWidget::resizeEvent(event);
        layoutChildren();
    }

    // Die gezeichnete blaue Titelleiste besitzt neben dem QLabel auch
    // kleine freie Flaechen. Dort gelten dieselben Fokus-/Drag-Regeln.
    void mousePressEvent(QMouseEvent *event) override
    {
        if (event->button() == Qt::LeftButton && isTitleBarPoint(event->pos())) {
            raise();
            if (onActivated_) onActivated_(this);
            edit_->setFocus(Qt::MouseFocusReason);
            if (!maximized_) {
                moving_ = true;
                pressGlobal_ = event->globalPos();
                startCol_ = xCol_;
                startRow_ = yRow_;
            }
            event->accept();
            return;
        }
        QWidget::mousePressEvent(event);
    }

    void mouseMoveEvent(QMouseEvent *event) override
    {
        if (moving_ && !maximized_ && (event->buttons() & Qt::LeftButton)) {
            const QPoint delta = event->globalPos() - pressGlobal_;
            xCol_ = startCol_ + roundToCells(delta.x(), cw_);
            yRow_ = startRow_ + roundToCells(delta.y(), ch_);
            applyGridGeometry();
            event->accept();
            return;
        }
        QWidget::mouseMoveEvent(event);
    }

    void mouseReleaseEvent(QMouseEvent *event) override
    {
        if (event->button() == Qt::LeftButton && moving_) {
            moving_ = false;
            event->accept();
            return;
        }
        QWidget::mouseReleaseEvent(event);
    }

    void mouseDoubleClickEvent(QMouseEvent *event) override
    {
        if (event->button() == Qt::LeftButton && isTitleBarPoint(event->pos())) {
            raise();
            if (onActivated_) onActivated_(this);
            toggleMaximized();
            event->accept();
            return;
        }
        QWidget::mouseDoubleClickEvent(event);
    }

    bool eventFilter(QObject *watched, QEvent *event) override
    {
        if (watched == parentWidget() && event->type() == QEvent::Resize) {
            // Warte auf das Ende der aktuellen Qt-Layoutphase.
            QTimer::singleShot(0, this, [this]() {
                if (maximized_) fitMaximizedToViewport();
                else applyGridGeometry();
            });
        }
        // Fensteranhebung auch bei maximiertem Editor und beim Anklicken
        // der Bedienelemente. Der Textcursor bleibt nach Titelleistenklick aktiv.
        if (event->type() == QEvent::MouseButtonPress &&
            (watched == title_ || watched == closeButton_ ||
             watched == maximizeButton_ || watched == grip_ ||
             watched == status_ || watched == horizontalBar_ ||
             watched == edit_->verticalScrollBar())) {
            auto *mouse = static_cast<QMouseEvent *>(event);
            if (mouse->button() == Qt::LeftButton) {
                raise();
                if (onActivated_) onActivated_(this);
                if (watched == title_) edit_->setFocus(Qt::MouseFocusReason);
            }
        }
        if (watched == closeButton_ && event->type() == QEvent::MouseButtonDblClick) {
            auto *mouse = static_cast<QMouseEvent *>(event);
            if (mouse->button() == Qt::LeftButton) {
                close(); // closeEvent fuehrt IMMER die Aenderungspruefung aus.
                return true;
            }
        }
        if (watched == title_) {
            if (event->type() == QEvent::MouseButtonDblClick) {
                auto *mouse = static_cast<QMouseEvent *>(event);
                if (mouse->button() == Qt::LeftButton) {
                    toggleMaximized();
                    return true;
                }
            }
            if (event->type() == QEvent::MouseButtonPress) {
                auto *mouse = static_cast<QMouseEvent *>(event);
                if (mouse->button() == Qt::LeftButton && !maximized_) {
                    moving_ = true;
                    pressGlobal_ = mouse->globalPos();
                    startCol_ = xCol_;
                    startRow_ = yRow_;
                    return true;
                }
            }
            if (event->type() == QEvent::MouseMove && moving_) {
                auto *mouse = static_cast<QMouseEvent *>(event);
                const QPoint delta = mouse->globalPos() - pressGlobal_;
                xCol_ = startCol_ + roundToCells(delta.x(), cw_);
                yRow_ = startRow_ + roundToCells(delta.y(), ch_);
                applyGridGeometry();
                return true;
            }
            if (event->type() == QEvent::MouseButtonRelease && moving_) {
                moving_ = false;
                return true;
            }
        }
        if (watched == grip_ && !maximized_) {
            if (event->type() == QEvent::MouseButtonPress) {
                auto *mouse = static_cast<QMouseEvent *>(event);
                if (mouse->button() == Qt::LeftButton) {
                    if (onActivated_) onActivated_(this);
                    raise();
                    resizing_ = true;
                    pressGlobal_ = mouse->globalPos();
                    startCols_ = preferredCols_;
                    startRows_ = preferredRows_;
                    return true;
                }
            }
            if (event->type() == QEvent::MouseMove && resizing_) {
                auto *mouse = static_cast<QMouseEvent *>(event);
                const QPoint delta = mouse->globalPos() - pressGlobal_;
                preferredCols_ = qMax(26, startCols_ + roundToCells(delta.x(), cw_));
                preferredRows_ = qMax(8, startRows_ + roundToCells(delta.y(), ch_));
                applyGridGeometry();
                return true;
            }
            if (event->type() == QEvent::MouseButtonRelease && resizing_) {
                resizing_ = false;
                return true;
            }
        }
        if ((watched == edit_ || watched == edit_->viewport())
            && (event->type() == QEvent::MouseButtonPress
                || event->type() == QEvent::FocusIn)) {
            if (onActivated_) onActivated_(this);
            raise();
        }
        return QWidget::eventFilter(watched, event);
    }

private:
    bool isTitleBarPoint(const QPoint &point) const
    {
        return point.x() >= 5 && point.y() >= 5 &&
               point.x() < width() - shadow_ - 5 &&
               point.y() < titleHeight();
    }

    static int roundToCells(int delta, int cell)
    {
        cell = qMax(1, cell);
        return delta >= 0 ? (delta + cell / 2) / cell
                          : -((-delta + cell / 2) / cell);
    }

    QString modalStyle() const
    {
        if (darkMode_) return QStringLiteral(
            "QMessageBox,QDialog{background:#1e2230;color:#f4f4f4;}"
            "QLabel{color:#f4f4f4;}"
            "QPushButton{background:#303b56;color:#ffffff;border:1px solid #adbada;"
            "padding:5px 12px;min-width:80px;}"
            "QPushButton:hover{background:#475d89;}");
        return QStringLiteral(
            "QMessageBox,QDialog{background:#f3f4f8;color:#202530;}"
            "QLabel{color:#202530;}"
            "QPushButton{background:#e2e6ee;color:#202530;border:1px solid #777f94;"
            "padding:5px 12px;min-width:80px;}");
    }

    void showError(const QString &title, const QString &description)
    {
        QMessageBox box(QMessageBox::Warning, title, description,
                        QMessageBox::Ok, this);
        box.setStyleSheet(modalStyle());
        box.exec();
    }

    bool confirmDiscard()
    {
        if (!isModified()) return true;
        const int answer = D64TurboMessageBox::showMessage(
            this, QStringLiteral("Information"),
            QStringLiteral("Der Text wurde geändert. Vor dem Schließen speichern?"),
            {{QStringLiteral("Speichern"), D64TurboMessageBox::Save},
             {QStringLiteral("Verwerfen"), D64TurboMessageBox::Discard},
             {QStringLiteral("Abbrechen"), D64TurboMessageBox::Cancel}});
        if (answer == D64TurboMessageBox::Save)
            return saveDocument(true); // weiterhin der bestehende zweispaltige VFS-Dialog
        return answer == D64TurboMessageBox::Discard;
    }

    void showGermanContextMenu(const QPoint &localPosition)
    {
        if (onActivated_) onActivated_(this);
        QMenu menu(edit_);
        menu.setObjectName(QStringLiteral("dbaseTurboEditorContextMenu"));
        menu.setStyleSheet(d64TurboGreyContextMenuStyle());
        auto addEntry = [&menu](const QString &name, const QKeySequence &key,
                                const std::function<void()> &callback) {
            QAction *action = menu.addAction(name);
            action->setShortcut(key);
            action->setShortcutVisibleInContextMenu(true);
            QObject::connect(action, &QAction::triggered, &menu,
                             [callback](bool) { callback(); });
            return action;
        };
        QAction *undoAction = addEntry(QStringLiteral("Rückgängig"), QKeySequence::Undo,
                                      [this]() { undo(); });
        undoAction->setEnabled(edit_->document()->isUndoAvailable());
        QAction *redoAction = addEntry(QStringLiteral("Wiederherstellen"),
            QKeySequence(static_cast<int>(Qt::CTRL) | static_cast<int>(Qt::Key_Y)),
            [this]() { redo(); });
        redoAction->setEnabled(edit_->document()->isRedoAvailable());
        menu.addSeparator();
        const bool selection = edit_->textCursor().hasSelection();
        addEntry(QStringLiteral("Ausschneiden"), QKeySequence::Cut, [this]() { cut(); })
            ->setEnabled(selection);
        addEntry(QStringLiteral("Kopieren"), QKeySequence::Copy, [this]() { copy(); })
            ->setEnabled(selection);
        addEntry(QStringLiteral("Einfügen"), QKeySequence::Paste, [this]() { paste(); });
        addEntry(QStringLiteral("Löschen"), QKeySequence(Qt::Key_Delete),
                 [this]() { deleteSelection(); })->setEnabled(selection);
        menu.addSeparator();
        addEntry(QStringLiteral("Alles auswählen"), QKeySequence::SelectAll,
                 [this]() { selectAll(); });
        menu.exec(edit_->mapToGlobal(localPosition));
    }

    void updateStatus()
    {
        const QTextCursor cursor = edit_->textCursor();
        status_->setText(QStringLiteral("%1 : %2")
                         .arg(cursor.blockNumber() + 1)
                         .arg(cursor.positionInBlock() + 1));
    }
    void updateTitle()
    {
        title_->setText(QStringLiteral(" Editor – %1 ").arg(windowCaption()));
    }

    int titleHeight() const { return ch_ + 14; }
    int footerHeight() const { return ch_ + 10; }
    int buttonWidth() const { return qMax(20, cw_ * 3); }
    void layoutChildren()
    {
        if (!edit_) return;
        const int right = qMax(0, width() - shadow_);
        const int bottom = qMax(0, height() - shadow_);
        const int titleH = titleHeight();
        const int buttonH = qMax(14, ch_);
        closeButton_->setGeometry(8, qMax(5, (titleH-buttonH)/2), buttonWidth(), buttonH);
        maximizeButton_->setGeometry(qMax(5,right-buttonWidth()-8),
                                     qMax(5,(titleH-buttonH)/2), buttonWidth(), buttonH);
        title_->setGeometry(8+buttonWidth()+3, 6,
                            qMax(1,right-2*buttonWidth()-27), qMax(1,titleH-10));
        edit_->setGeometry(7, titleH, qMax(1,right-14),
                           qMax(1,bottom-titleH-footerHeight()-6));
        const int footerY = qMax(0,bottom-footerHeight()+2);
        const int footerH = qMax(1,footerHeight()-5);
        const int statusWidth = qMin(qMax(cw_*11, 75), qMax(1,right-65));
        status_->setGeometry(8,footerY,statusWidth,footerH);
        const int barX = 8+statusWidth;
        horizontalBar_->setGeometry(barX,footerY,
                                   qMax(1,right-barX-27),footerH);
        grip_->setGeometry(qMax(0,right-25),footerY,20,footerH);
        closeButton_->raise();
        maximizeButton_->raise();
    }

    void fitMaximizedToViewport()
    {
        if (!maximized_ || !parentWidget()) return;
        setGeometry(QRect(QPoint(0, 0), parentWidget()->size()));
        layoutChildren();
    }

    void applyGridGeometry()
    {
        QWidget *viewport = parentWidget();
        if (!viewport) return;
        if (maximized_) { fitMaximizedToViewport(); return; }
        const int availCols = qMax(1, viewport->width() / cw_);
        const int availRows = qMax(1, viewport->height() / ch_);
        // Die Fensterduerfen ueber den sichtbaren DOS-Bereich hinausragen.
        // Nur der anklickbare linke Titelleistenteil (mind. 10 Zellen)
        // und die Titelleistenreihe (max. Zeile 24, 0-basiert) bleiben drin.
        const int visibleTitleCols = qMin(availCols, 10);
        xCol_ = qBound(0, xCol_, qMin(79, qMax(0, availCols-visibleTitleCols)));
        yRow_ = qBound(0, yRow_, qMin(24, availRows-1));
        setGeometry(xCol_*cw_, yRow_*ch_, preferredCols_*cw_, preferredRows_*ch_);
        layoutChildren();
    }

    D64ApplicationVfs *vfs_ = nullptr;
    QPlainTextEdit *edit_ = nullptr;
    QLabel *title_ = nullptr;
    QLabel *status_ = nullptr;
    QLabel *grip_ = nullptr;
    QToolButton *closeButton_ = nullptr;
    QToolButton *maximizeButton_ = nullptr;
    D64TurboArrowScrollBar *horizontalBar_ = nullptr;
    QString relativeFile_;
    std::function<void(D64TurboEditorWidget *)> onActivated_;
    std::function<void(D64TurboEditorWidget *)> onClosed_;
    bool darkMode_ = true;
    int cw_ = 9;
    int ch_ = 16;
    int preferredCols_ = 66;
    int preferredRows_ = 19;
    int xCol_ = 4;
    int yRow_ = 2;
    static constexpr int shadow_ = 7;
    bool moving_ = false;
    bool resizing_ = false;
    bool maximized_ = false;
    QPoint pressGlobal_;
    int startCol_ = 0;
    int startRow_ = 0;
    int startCols_ = 66;
    int startRows_ = 19;
    int restoreCol_ = 4;
    int restoreRow_ = 2;
    int restoreCols_ = 66;
    int restoreRows_ = 19;
};
