#pragma once

// Stage 626: Turbo-Vision-Editor in der dBASE-Qt5-Konsole.
// Eigenstaendiger, zeichenraster-basierter Editor mit auf die Anwendung
// beschraenktem virtuellem Dateisystem und zweispaltigem Dateidialog.
// Keine MOC-/Q_OBJECT-Abhaengigkeit.

#include <QApplication>
#include <QAbstractScrollArea>
#include <QCoreApplication>
#include <QKeySequence>
#include <QKeyEvent>
#include <QPaintEvent>
#include <QRegularExpression>
#include <QResizeEvent>
#include <functional>
#include <QCryptographicHash>
#include <QDialog>
#include <QDir>
#include <QDateTime>
#include <QEventLoop>
#include <QHeaderView>
#include <QFrame>
#include <QTimer>
#include <QFile>
#include <QFileInfo>
#include <QFontMetrics>
#include <QFontDatabase>
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
#include <QSplitterHandle>
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
#include <QContextMenuEvent>
#include <QTimer>
#include <QAction>
#include <QPalette>
#include <utility>
#include "d64_turbo_scrollbar.hpp"
#include "d64_turbo_messagebox.hpp"
#include "d64_turbo_context_menu.hpp"

// Stage 643: Die Dateisystem-Wurzel ist virtuell. Ausschliesslich
// /Alle Benutzer und /Dokumente sind sichtbar. Host-Benutzernamen oder
// die echten /Benutzer/<hash>-Verzeichnisse sind nie navigierbar.
class D64ApplicationVfs final
{
public:
    bool initialize()
    {
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
        if (!QDir().mkpath(root_)) { root_.clear(); return false; }
        root_ = QDir(root_).canonicalPath();
        if (root_.isEmpty()) return false;
        const QString account = qEnvironmentVariable("USERDOMAIN") + QLatin1Char('\\')
                              + qEnvironmentVariable("USERNAME") + QLatin1Char(':')
                              + QDir::homePath();
        if (!setUserIdentity(QStringLiteral("Host:") + account)) return false;
        // Stage-626-Altdaten aus dem bisherigen EXE-Verzeichnis gehen nicht
        // verloren: nur beim Host-Fallback in das private Dokumente-Mount
        // migrieren, nicht fuer spaetere dBASE-SESSION-Identitaeten freigeben.
        const QString legacy = QDir(root_).filePath(QStringLiteral("Dokumente"));
        QDir oldFiles(legacy);
        if (oldFiles.exists()) {
            const QFileInfoList entries = oldFiles.entryInfoList(
                QDir::Files | QDir::Dirs | QDir::NoDotAndDotDot, QDir::Name);
            for (const QFileInfo &old : entries) {
                if (old.isSymLink()) continue;
                const QString dest = QDir(personalRoot_).filePath(old.fileName());
                if (!QFileInfo::exists(dest)) QDir().rename(old.filePath(), dest);
            }
        }
        return true;
    }

    bool setUserIdentity(const QString &identity)
    {
        if (root_.isEmpty() || identity.trimmed().isEmpty()) return false;
        const QByteArray hash = QCryptographicHash::hash(
            identity.trimmed().toCaseFolded().toUtf8(), QCryptographicHash::Sha256).toHex();
        const QString shared = QDir(root_).filePath(QStringLiteral("_Alle_Benutzer"));
        const QString personal = QDir(root_).filePath(QStringLiteral("_Benutzer/")
                                + QString::fromLatin1(hash) + QStringLiteral("/Dokumente"));
        if (!QDir().mkpath(shared) || !QDir().mkpath(personal)) return false;
        const QString canonShared = QDir(shared).canonicalPath();
        const QString canonPersonal = QDir(personal).canonicalPath();
        if (!isInsideRoot(canonShared) || !isInsideRoot(canonPersonal)) return false;
        sharedRoot_ = canonShared;
        personalRoot_ = canonPersonal;
        identityHash_ = QString::fromLatin1(hash);
        return true;
    }

    QString userToken() const { return identityHash_; }
    QString hostRoot() const { return root_; }
    QString documents() const { return QStringLiteral("Dokumente"); }
    QString shared() const { return QStringLiteral("Alle Benutzer"); }

    // Virtuelle Wurzel: ausschliesslich zwei sichtbare Mountpoints.
    QStringList mountPoints() const
    { return {shared(), documents()}; }

    static bool safeName(const QString &name)
    {
        if (name.isEmpty() || name == QLatin1String(".") || name == QLatin1String("..")
            || name.endsWith(QLatin1Char(' ')) || name.endsWith(QLatin1Char('.'))
            || name.contains(QLatin1Char('/')) || name.contains(QLatin1Char('\\'))
            || name.contains(QLatin1Char(':')) || name.contains(QChar(0))
            || name.contains(QRegularExpression(QStringLiteral("[<>\\\"|?*\\x00-\\x1f]"))))
            return false;
        const QString stem = name.section(QLatin1Char('.'), 0, 0).toUpper();
        return stem != QLatin1String("CON") && stem != QLatin1String("PRN")
            && stem != QLatin1String("AUX") && stem != QLatin1String("NUL")
            && !QRegularExpression(QStringLiteral("^(COM|LPT)[1-9]$")).match(stem).hasMatch();
    }

    QString hostPath(const QString &virtualPath) const
    {
        if (root_.isEmpty() || virtualPath.startsWith(QLatin1Char('/'))
            || QDir::isAbsolutePath(virtualPath)) return QString();
        if (virtualPath.isEmpty()) return root_;
        const QString &source = virtualPath;
        if (QDir::isAbsolutePath(source)) return QString();
        const QStringList parts = source.split(QLatin1Char('/'), Qt::KeepEmptyParts);
        if (parts.isEmpty()) return QString();
        QString base;
        if (parts.first() == shared()) base = sharedRoot_;
        else if (parts.first() == documents()) base = personalRoot_;
        else return QString();
        if (base.isEmpty()) return QString();
        QString probe = base;
        for (int i=1; i<parts.size(); ++i) {
            if (!safeName(parts.at(i))) return QString();
            probe = QDir(probe).filePath(parts.at(i));
            const QFileInfo info(probe);
            if (info.isSymLink()) return QString();
            if (info.exists()) {
                const QString canonical = info.canonicalFilePath();
                if (!isInsideMount(canonical, base)) return QString();
            }
        }
        const QString result = QDir::cleanPath(probe);
        return isInsideMount(result, base) ? result : QString();
    }

    QString existingDirectory(const QString &virtualPath) const
    {
        if (virtualPath.isEmpty()) return root_;
        const QString path = hostPath(virtualPath);
        return !path.isEmpty() && QFileInfo(path).isDir() ? path : QString();
    }

    QString readableFile(const QString &virtualPath) const
    {
        if (virtualPath.isEmpty() || !virtualPath.contains(QLatin1Char('/')))
            return QString();
        const QString path = hostPath(virtualPath);
        const QFileInfo info(path);
        return !path.isEmpty() && info.isFile() && !info.isSymLink() ? path : QString();
    }

    QString writableFile(const QString &virtualPath) const
    {
        if (virtualPath.isEmpty() || !virtualPath.contains(QLatin1Char('/')))
            return QString();
        const QString path = hostPath(virtualPath);
        if (path.isEmpty()) return QString();
        const QFileInfo info(path);
        if (info.exists() && (!info.isFile() || info.isSymLink())) return QString();
        if (info.isSymLink() || existingDirectory(parentVirtual(virtualPath)).isEmpty())
            return QString();
        return path;
    }

    bool createDirectory(const QString &virtualParent, const QString &name)
    {
        if (!safeName(name) || virtualParent.isEmpty()) return false;
        if (existingDirectory(virtualParent).isEmpty()) return false;
        const QString child = join(virtualParent, name);
        const QString path = hostPath(child);
        if (path.isEmpty() || QFileInfo::exists(path)) return false;
        return QDir().mkdir(path);
    }

    bool removeEntry(const QString &virtualPath)
    {
        if (virtualPath.isEmpty() || !virtualPath.contains(QLatin1Char('/')))
            return false; // Mountpoints bleiben unveraenderlich.
        const QString path = hostPath(virtualPath);
        if (path.isEmpty()) return false;
        const QFileInfo info(path);
        if (info.isSymLink()) return false;
        if (info.isDir()) return QDir().rmdir(path); // nur leere Ordner
        if (info.isFile()) return QFile::remove(path);
        return false;
    }

    static QString parentVirtual(const QString &relative)
    {
        if (relative.isEmpty()) return QString();
        const int slash = relative.lastIndexOf(QLatin1Char('/'));
        return slash < 0 ? QString() : relative.left(slash);
    }
    static QString join(const QString &directory, const QString &name)
    { return directory.isEmpty() ? name : directory + QLatin1Char('/') + name; }

private:
    bool isInsideRoot(const QString &path) const { return isInsideMount(path, root_); }
    static bool isInsideMount(const QString &path, const QString &base)
    {
        if (base.isEmpty() || path.isEmpty()) return false;
#ifdef _WIN32
        const Qt::CaseSensitivity cs = Qt::CaseInsensitive;
#else
        const Qt::CaseSensitivity cs = Qt::CaseSensitive;
#endif
        return path.compare(base, cs) == 0 || path.startsWith(base + QLatin1Char('/'), cs);
    }
    QString root_;
    QString sharedRoot_;
    QString personalRoot_;
    QString identityHash_;
};

// Reiner Qt::Widget-Dialog im DOS-Viewport: nie ein eigenes Windows-Fenster.
class D64VirtualFileDialog final : public QWidget
{
public:
    enum Mode { OpenFile, SaveFile };
    enum { Rejected=0, Accepted=1 };

    explicit D64VirtualFileDialog(D64ApplicationVfs *vfs, Mode mode,
                                   const QString &previousFile, QWidget *parent, bool darkMode = true)
        : QWidget(parent), vfs_(vfs), mode_(mode), darkMode_(darkMode)
    {
        setWindowFlags(Qt::Widget);
        setObjectName(QStringLiteral("dbaseVirtualFileDialog"));
        setFocusPolicy(Qt::StrongFocus);
        setContextMenuPolicy(Qt::NoContextMenu);
        setCursor(Qt::ArrowCursor);
        setMouseTracking(true);
        // Stage 644: exakt drei Pixel schmaler als Stage 643.
        setMinimumSize(557, 330);
        resize(767, 490);
        setStyleSheet(darkMode ? QStringLiteral(
            "QWidget#dbaseVirtualFileDialog{background:#0000aa;color:#ffffff;border:2px solid #ffff55;}"
            "QLabel{color:#ffffff;}"
            "QListWidget,QTreeWidget,QLineEdit{background:#000080;color:white;"
            "border:1px solid #ffff55;selection-background-color:#aaaa00;selection-color:black;}"
            "QHeaderView::section{background:#0000aa;color:#ffff55;border:1px solid #ffff55;}"
            "QPushButton{background:#0000aa;color:#ffff55;border:1px solid #ffff55;"
            "padding:5px 11px;min-width:60px;}"
            "QPushButton:hover{background:#3333cc;}"
            "QSplitter::handle{background:#ffff55;}") : QStringLiteral(
            "QWidget#dbaseVirtualFileDialog{background:#f0f2f8;color:#1e2130;border:2px solid #5474ae;}"
            "QLabel{color:#1e2130;}"
            "QListWidget,QTreeWidget,QLineEdit{background:#ffffff;color:#182440;"
            "border:1px solid #5474ae;selection-background-color:#acc1ed;}"
            "QHeaderView::section{background:#dfe7f7;color:#233b66;border:1px solid #5474ae;}"
            "QPushButton{background:#dfe7f7;color:#233b66;border:1px solid #5474ae;"
            "padding:5px 11px;min-width:60px;}"
            "QSplitter::handle{background:#5474ae;}"));
        auto *outer = new QVBoxLayout(this);
        outer->setContentsMargins(9, 7, 9, 8);
        // Turbo-Vision-Titelleiste mit Schliessen links oben. Kein
        // eigenes OS-Fenster; der gesamte Dialog bleibt in der Modalschicht.
        titleBar_ = new QWidget(this);
        titleBar_->setObjectName(QStringLiteral("dbaseVirtualFileTitleBar"));
        titleBar_->setStyleSheet(darkMode_ ? QStringLiteral(
            "QWidget#dbaseVirtualFileTitleBar{background:#2256cf;}")
            : QStringLiteral("QWidget#dbaseVirtualFileTitleBar{background:#c4d7f4;}"));
        titleBar_->setCursor(Qt::ArrowCursor);
        titleBar_->setMouseTracking(true);
        auto *titleRow = new QHBoxLayout(titleBar_);
        titleRow->setContentsMargins(2, 1, 2, 1);
        titleRow->setSpacing(3);
        closeButton_ = new QToolButton(titleBar_);
        closeButton_->setObjectName(QStringLiteral("dbaseVirtualFileClose"));
        closeButton_->setText(QStringLiteral("×"));
        closeButton_->setToolTip(QStringLiteral("Schließen / Abbrechen"));
        closeButton_->setFixedSize(22, 20);
        closeButton_->setFocusPolicy(Qt::NoFocus);
        closeButton_->setStyleSheet(darkMode_ ? QStringLiteral(
            "QToolButton#dbaseVirtualFileClose{color:#ffff55;background:#163b9c;"
            "border:1px solid #ffff55;font-weight:bold;padding:0;}"
            "QToolButton#dbaseVirtualFileClose:hover{background:#355de0;}")
            : QStringLiteral(
            "QToolButton#dbaseVirtualFileClose{color:#15284a;background:#dce6f5;"
            "border:1px solid #5474ae;font-weight:bold;padding:0;}"));
        title_ = new QLabel(mode == OpenFile ? QStringLiteral("Datei öffnen")
                                            : QStringLiteral("Datei speichern unter"), titleBar_);
        title_->setObjectName(QStringLiteral("dbaseVirtualFileTitle"));
        title_->setAlignment(Qt::AlignCenter);
        title_->setCursor(Qt::ArrowCursor);
        title_->setMouseTracking(true);
        title_->setStyleSheet(darkMode_ ? QStringLiteral(
            "QLabel#dbaseVirtualFileTitle{font-weight:bold;background:transparent;color:#ffffff;}")
            : QStringLiteral(
            "QLabel#dbaseVirtualFileTitle{font-weight:bold;background:transparent;color:#1e2130;}"));
        titleBalance_ = new QWidget(titleBar_);
        titleBalance_->setFixedWidth(22);
        titleBalance_->setCursor(Qt::ArrowCursor);
        titleRow->addWidget(closeButton_);
        titleRow->addWidget(title_, 1);
        titleRow->addWidget(titleBalance_);
        outer->addWidget(titleBar_);
        titleBar_->installEventFilter(this);
        title_->installEventFilter(this);
        titleBalance_->installEventFilter(this);
        QObject::connect(closeButton_, &QToolButton::clicked, this,
                         [this]() { finish(Rejected); });
        location_ = new QLabel(this);
        location_->setObjectName(QStringLiteral("dbaseVirtualFilePath"));
        outer->addWidget(location_);
        auto *searchRow = new QHBoxLayout();
        searchRow->addWidget(new QLabel(QStringLiteral("Suchen"), this));
        search_ = new QLineEdit(this);
        search_->setObjectName(QStringLiteral("dbaseVirtualFileSearch"));
        searchRow->addWidget(search_, 1);
        outer->addLayout(searchRow);
        splitter_ = new QSplitter(Qt::Horizontal, this);
        splitter_->setObjectName(QStringLiteral("dbaseVirtualFileSplitter"));
        splitter_->setChildrenCollapsible(false);
        folders_ = new QListWidget(splitter_);
        folders_->setObjectName(QStringLiteral("dbaseVirtualFolders"));
        folders_->setMinimumWidth(155);
        folders_->setCursor(Qt::ArrowCursor);
        files_ = new QTreeWidget(splitter_);
        files_->setObjectName(QStringLiteral("dbaseVirtualFiles"));
        files_->setHeaderLabels({QStringLiteral("Name"), QStringLiteral("Datum"), QStringLiteral("Größe")});
        files_->header()->setObjectName(QStringLiteral("dbaseVirtualFileHeader"));
        files_->setRootIsDecorated(false);
        files_->setMinimumWidth(265);
        // Stage 645: Alle vier Leisten erhalten die Turbo-Vision-Zeichnung.
        // Die gemeinsame Geometrie aus Stage 630 trennt Thumb und Pfeilfelder
        // auch in den beiden Endpositionen und beim Ziehen strikt voneinander.
        auto installFileScrollbars = [](QAbstractScrollArea *view) {
            auto *vertical = new D64TurboArrowScrollBar(Qt::Vertical, view);
            vertical->setObjectName(QStringLiteral("dbaseVirtualVerticalScroll"));
            vertical->setTurboEditorTheme();
            vertical->setFixedWidth(15);
            vertical->setCursor(Qt::ArrowCursor);
            view->setVerticalScrollBar(vertical);

            auto *horizontal = new D64TurboArrowScrollBar(Qt::Horizontal, view);
            horizontal->setObjectName(QStringLiteral("dbaseVirtualHorizontalScroll"));
            horizontal->setTurboEditorTheme();
            horizontal->setFixedHeight(15);
            horizontal->setCursor(Qt::ArrowCursor);
            view->setHorizontalScrollBar(horizontal);
        };
        installFileScrollbars(folders_);
        installFileScrollbars(files_);
        // Handcursor nur auf tatsächlichen Einträgen, niemals auf Leerraum.
        folders_->viewport()->setMouseTracking(true);
        files_->viewport()->setMouseTracking(true);
        folders_->viewport()->setCursor(Qt::ArrowCursor);
        files_->viewport()->setCursor(Qt::ArrowCursor);
        folders_->viewport()->installEventFilter(this);
        files_->viewport()->installEventFilter(this);
        splitter_->addWidget(folders_);
        splitter_->addWidget(files_);
        splitter_->setStretchFactor(0, 1);
        splitter_->setStretchFactor(1, 3);
        splitter_->setSizes({235, 530});
        // Splitter-Handle und Spalten-Grenzen sind echte Sizer-Zonen.
        // Nach dem generellen Cursor-Reset am Konstruktorende erneut setzen.
        files_->header()->setMouseTracking(true);
        files_->header()->viewport()->setMouseTracking(true);
        files_->header()->viewport()->installEventFilter(this);
        outer->addWidget(splitter_, 1);
        auto *fileRow = new QHBoxLayout();
        fileRow->addWidget(new QLabel(QStringLiteral("Dateiname"), this));
        filename_ = new QLineEdit(this);
        filename_->setObjectName(QStringLiteral("dbaseVirtualFilename"));
        fileRow->addWidget(filename_, 1);
        outer->addLayout(fileRow);
        info_ = new QLabel(this);
        info_->setObjectName(QStringLiteral("dbaseVirtualFileStatus"));
        info_->setWordWrap(true);
        info_->setMinimumHeight(16);
        outer->addWidget(info_);
        auto *buttons = new QHBoxLayout();
        auto *add = new QPushButton(QStringLiteral("Verz. Hinzufügen"), this);
        auto *remove = new QPushButton(QStringLiteral("Löschen"), this);
        add->setObjectName(QStringLiteral("dbaseVirtualAddDirectory"));
        remove->setObjectName(QStringLiteral("dbaseVirtualDelete"));
        buttons->addWidget(add);
        buttons->addWidget(remove);
        buttons->addStretch(1);
        auto *ok = new QPushButton(QStringLiteral("OK"), this);
        auto *cancel = new QPushButton(QStringLiteral("Abbrechen"), this);
        auto *help = new QPushButton(QStringLiteral("Hilfe"), this);
        ok->setObjectName(QStringLiteral("dbaseVirtualFileOK"));
        cancel->setObjectName(QStringLiteral("dbaseVirtualFileCancel"));
        help->setObjectName(QStringLiteral("dbaseVirtualFileHelp"));
        buttons->addWidget(ok); buttons->addWidget(cancel); buttons->addWidget(help);
        outer->addLayout(buttons);

        QObject::connect(ok, &QPushButton::clicked, this, [this]() { acceptSelection(); });
        QObject::connect(cancel, &QPushButton::clicked, this, [this]() { finish(Rejected); });
        QObject::connect(help, &QPushButton::clicked, this, [this]() {
            status(QStringLiteral("Links: virtuelle Ordner und '..' zum Zurückgehen. "
                "Rechts: Dateien (Name, Datum, Größe), Doppelklick zum Öffnen. "
                "Die Suche filtert Namen. Verzeichnisse können nur in 'Alle Benutzer' "
                "oder den eigenen 'Dokumente' angelegt werden."));
        });
        QObject::connect(add, &QPushButton::clicked, this, [this]() { addDirectory(); });
        QObject::connect(remove, &QPushButton::clicked, this, [this]() { deleteSelection(); });
        QObject::connect(folders_, &QListWidget::itemClicked, this, [this](QListWidgetItem *item) {
            if (!item || !vfs_) return;
            const QString selected = item->data(Qt::UserRole).toString();
            selectedEntry_ = selected;
            if (!vfs_->existingDirectory(selected).isEmpty()) showDirectory(selected);
            else if (!vfs_->readableFile(selected).isEmpty())
                filename_->setText(QFileInfo(selected).fileName());
        });
        QObject::connect(folders_, &QListWidget::itemDoubleClicked, this, [this](QListWidgetItem *item) {
            if (!item || !vfs_) return;
            const QString selected = item->data(Qt::UserRole).toString();
            if (!vfs_->existingDirectory(selected).isEmpty()) showDirectory(selected);
            else if (!vfs_->readableFile(selected).isEmpty()) {
                filename_->setText(QFileInfo(selected).fileName());
                acceptSelection();
            }
        });
        QObject::connect(files_, &QTreeWidget::itemClicked, this, [this](QTreeWidgetItem *item, int) {
            if (!item) return;
            const QString value = item->data(0, Qt::UserRole).toString();
            selectedEntry_ = item->data(0, Qt::UserRole + 1).toString() == QLatin1String("file")
                ? D64ApplicationVfs::join(currentDirectory_, value) : value;
            if (item->data(0, Qt::UserRole + 1).toString() == QLatin1String("file"))
                filename_->setText(value);
        });
        QObject::connect(files_, &QTreeWidget::itemDoubleClicked, this, [this](QTreeWidgetItem *item, int) {
            if (!item) return;
            const QString value = item->data(0, Qt::UserRole).toString();
            const QString type = item->data(0, Qt::UserRole + 1).toString();
            if (type == QLatin1String("dir")) showDirectory(value);
            else if (type == QLatin1String("file")) {
                filename_->setText(value); acceptSelection();
            }
        });
        QObject::connect(search_, &QLineEdit::textChanged, this, [this](const QString &) { filterFiles(); });
        QObject::connect(filename_, &QLineEdit::returnPressed, this, [this]() { acceptSelection(); });
        // Stage 646: Path und beide Dateilisten erhalten dieselbe Schrift.
        // Qt5-/Windows-Fallback wie bei der internen Turbo-MessageBox.
        QFontDatabase availableFonts;
        QString fileFontFamily = QStringLiteral("Courier");
        for (const QString &candidate : {QStringLiteral("Consolas"),
                                         QStringLiteral("Courier New"),
                                         QStringLiteral("Courier")}) {
            if (availableFonts.hasFamily(candidate)) {
                fileFontFamily = candidate;
                break;
            }
        }
        QFont fileFont = font();
        fileFont.setFamily(fileFontFamily);
        fileFont.setStyleHint(QFont::TypeWriter);
        fileFont.setStyleStrategy(QFont::PreferMatch);
        const QString fileFontStyle = QStringLiteral("font-family:'%1';").arg(fileFontFamily);
        for (QWidget *item : {static_cast<QWidget *>(location_),
                              static_cast<QWidget *>(folders_),
                              static_cast<QWidget *>(files_),
                              static_cast<QWidget *>(files_->header())}) {
            item->setFont(fileFont);
            // Lokales QSS erzwingt die gewählte Familie auch gegenüber
            // einem globalen Anwendungs-Stylesheet (analog MessageBox).
            item->setStyleSheet(fileFontStyle);
        }

        const QString initial = vfs_ && !vfs_->existingDirectory(
            D64ApplicationVfs::parentVirtual(previousFile)).isEmpty()
            ? D64ApplicationVfs::parentVirtual(previousFile) : QString();
        showDirectory(initial);
        if (!previousFile.isEmpty()) filename_->setText(QFileInfo(previousFile).fileName());
        // Keine nativen Qt-Kontextmenüs (auch nicht in QLineEdit oder
        // den Scroll-Viewports). Nur Einträge und Aktionsbuttons zeigen Hand.
        for (QWidget *widget : findChildren<QWidget *>()) {
            widget->setContextMenuPolicy(Qt::NoContextMenu);
            widget->setCursor(Qt::ArrowCursor);
            widget->installEventFilter(this);
        }
        for (QPushButton *button : {add, remove, ok, cancel, help})
            button->setCursor(Qt::PointingHandCursor);
        closeButton_->setCursor(Qt::PointingHandCursor);
        // Titel ist eine Verschiebezone; Schließen bleibt Handcursor.
        // Unbedingt nach dem generellen Kindwidget-Reset zuweisen.
        for (QWidget *dragSurface : {titleBar_, static_cast<QWidget *>(title_), titleBalance_})
            dragSurface->setCursor(Qt::SizeAllCursor);
        // Die Ruecksetzung fuer die normalen Dialogflaechen darf die
        // Sizer- und Scrollbar-Cursor nicht ueberschreiben.
        if (QSplitterHandle *handle = splitter_->handle(1))
            handle->setCursor(Qt::SplitHCursor);
        files_->header()->viewport()->setCursor(Qt::ArrowCursor);
        for (QAbstractScrollArea *view : {static_cast<QAbstractScrollArea *>(folders_),
                                          static_cast<QAbstractScrollArea *>(files_)}) {
            view->verticalScrollBar()->setCursor(Qt::ArrowCursor);
            view->horizontalScrollBar()->setCursor(Qt::ArrowCursor);
        }
    }

    QString selectedVirtualPath() const { return selected_; }

    // Die innere Eventloop startet erst nach der Qt-Menueaktion.
    int exec()
    {
        QWidget *desktop = D64TurboMessageBox::consoleDesktop(parentWidget());
        if (!desktop) return Rejected;
        if (QWidget *popup = QApplication::activePopupWidget()) popup->close();
        QWidget *owner = parentWidget();
        D64TurboModalLayer layer(desktop);
        layer.setGeometry(desktop->rect());
        layer_ = &layer;
        setParent(&layer, Qt::Widget);
        const int dialogWidth = qMax(557,
            qMin(qMax(280, desktop->width() - 20), 820) - 3);
        const int dialogHeight = qMin(qMax(200, desktop->height() - 16), 525);
        resize(dialogWidth, dialogHeight);
        const QSize cell = d64_turbo_message_grid::cellSize(desktop);
        const QPoint centered = d64_turbo_message_grid::clampCells(
            d64_turbo_message_grid::roundCells((desktop->width() - dialogWidth) / 2,
                                               cell.width()),
            d64_turbo_message_grid::roundCells((desktop->height() - dialogHeight) / 2,
                                               cell.height()), desktop);
        setGridPosition(centered);
        QEventLoop loop;
        result_ = Rejected;
        running_ = true;
        finished_ = [&loop]() { loop.quit(); };
        layer.setEscapeHandler([this]() { finish(Rejected); });
        layer.show(); layer.raise();
        show(); raise(); setFocus(Qt::OtherFocusReason);
        loop.exec(QEventLoop::AllEvents);
        if (dragging_) {
            if (dragWidget_) dragWidget_->releaseMouse();
            dragging_ = false;
            dragWidget_ = nullptr;
        }
        hide(); finished_ = {};
        running_ = false;
        layer_ = nullptr;
        setParent(owner, Qt::Widget);
        return result_;
    }

protected:
    bool eventFilter(QObject *watched, QEvent *event) override
    {
        if (!event) return QWidget::eventFilter(watched, event);
        // Unterdrückt Qt-Standardkontextmenüs auch in den Kind-Widgets.
        if (event->type() == QEvent::ContextMenu) {
            event->accept();
            return true;
        }
        // Der Spalten-Sizer liegt innerhalb von +/- 5 Pixeln der rechten
        // Spaltenkante. Nur dort den Split-Cursor; auf Header-Text normal.
        if (watched == files_->header()->viewport()) {
            auto *area = files_->header()->viewport();
            if (event->type() == QEvent::MouseMove) {
                const int x = static_cast<QMouseEvent *>(event)->pos().x();
                const QHeaderView *header = files_->header();
                bool atDivider = false;
                for (int section = 0; section < header->count(); ++section) {
                    if (header->isSectionHidden(section)) continue;
                    const int right = header->sectionViewportPosition(section)
                                    + header->sectionSize(section);
                    if (qAbs(x - right) <= 5) { atDivider = true; break; }
                }
                area->setCursor(atDivider ? Qt::SplitHCursor : Qt::ArrowCursor);
            } else if (event->type() == QEvent::Leave) {
                area->setCursor(Qt::ArrowCursor);
            }
        }
        if (watched == folders_->viewport() || watched == files_->viewport()) {
            QWidget *area = static_cast<QWidget *>(watched);
            if (event->type() == QEvent::MouseMove) {
                const QPoint pos = static_cast<QMouseEvent *>(event)->pos();
                const bool overEntry = watched == folders_->viewport()
                    ? folders_->itemAt(pos) != nullptr
                    : files_->itemAt(pos) != nullptr;
                area->setCursor(overEntry ? Qt::PointingHandCursor : Qt::ArrowCursor);
            } else if (event->type() == QEvent::Leave) {
                area->setCursor(Qt::ArrowCursor);
            }
        }
        if (watched == titleBar_ || watched == title_ || watched == titleBalance_) {
            switch (event->type()) {
            case QEvent::MouseButtonPress: {
                auto *mouse = static_cast<QMouseEvent *>(event);
                if (mouse->button() != Qt::LeftButton) break;
                dragging_ = true;
                dragStartGlobal_ = mouse->globalPos();
                QWidget *desktop = layer_ ? layer_->parentWidget() : nullptr;
                if (desktop) {
                    const QSize cell = d64_turbo_message_grid::cellSize(desktop);
                    dragStartCells_ = d64_turbo_message_grid::clampCells(
                        d64_turbo_message_grid::roundCells(x(), cell.width()),
                        d64_turbo_message_grid::roundCells(y(), cell.height()),
                        desktop);
                    // Auch nach einer Zoom-/Viewport-Aenderung ohne Sprung
                    // exakt bei der aktuellen sichtbaren Zellposition starten.
                    setGridPosition(dragStartCells_);
                } else {
                    dragStartCells_ = QPoint(gridColumn_, gridRow_);
                }
                dragWidget_ = static_cast<QWidget *>(watched);
                dragWidget_->grabMouse();
                raise();
                mouse->accept();
                return true;
            }
            case QEvent::MouseMove: {
                if (!dragging_) break;
                auto *mouse = static_cast<QMouseEvent *>(event);
                if (mouse->buttons() & Qt::LeftButton)
                    updateDragPosition(mouse->globalPos());
                else
                    endTitleDrag();
                mouse->accept();
                return true;
            }
            case QEvent::MouseButtonRelease: {
                auto *mouse = static_cast<QMouseEvent *>(event);
                if (!dragging_ || mouse->button() != Qt::LeftButton) break;
                updateDragPosition(mouse->globalPos());
                endTitleDrag();
                mouse->accept();
                return true;
            }
            default: break;
            }
        }
        return QWidget::eventFilter(watched, event);
    }
    void contextMenuEvent(QContextMenuEvent *event) override
    { event->accept(); }
    void keyPressEvent(QKeyEvent *e) override
    {
        if (e->key() == Qt::Key_Escape) { finish(Rejected); return; }
        QWidget::keyPressEvent(e);
    }
    void closeEvent(QCloseEvent *event) override
    {
        if (running_) { finish(Rejected); event->ignore(); return; }
        QWidget::closeEvent(event);
    }

private:
    void setGridPosition(const QPoint &cells)
    {
        QWidget *desktop = layer_ ? layer_->parentWidget()
                                   : D64TurboMessageBox::consoleDesktop(parentWidget());
        if (!desktop) return;
        const QPoint clamped = d64_turbo_message_grid::clampCells(
            cells.x(), cells.y(), desktop);
        gridColumn_ = clamped.x();
        gridRow_ = clamped.y();
        setProperty("d64GridCol", gridColumn_);
        setProperty("d64GridRow", gridRow_);
        move(d64_turbo_message_grid::gridPixels(clamped, desktop));
    }
    void updateDragPosition(const QPoint &global)
    {
        QWidget *desktop = layer_ ? layer_->parentWidget() : nullptr;
        if (!desktop) return;
        const QSize cell = d64_turbo_message_grid::cellSize(desktop);
        const QPoint delta = global - dragStartGlobal_;
        setGridPosition(QPoint(
            dragStartCells_.x() + d64_turbo_message_grid::roundCells(delta.x(), cell.width()),
            dragStartCells_.y() + d64_turbo_message_grid::roundCells(delta.y(), cell.height())));
    }
    void endTitleDrag()
    {
        dragging_ = false;
        if (dragWidget_) dragWidget_->releaseMouse();
        dragWidget_ = nullptr;
    }
    void finish(int result)
    {
        if (!running_) return;
        if (dragging_) endTitleDrag();
        result_ = result;
        if (finished_) finished_();
    }
    void status(const QString &message) { if (info_) info_->setText(message); }
    void filterFiles()
    {
        const QString value = search_->text();
        for (int i = 0; i < files_->topLevelItemCount(); ++i) {
            auto *item = files_->topLevelItem(i);
            if (!item) continue;
            item->setHidden(!item->text(0).contains(value, Qt::CaseInsensitive)
                            && item->data(0, Qt::UserRole).toString() != QLatin1String(".."));
        }
    }

    void addTreeEntry(const QString &label, const QString &virtualName,
                      const QString &type, const QFileInfo &info)
    {
        auto *item = new QTreeWidgetItem(files_);
        item->setText(0, label);
        item->setData(0, Qt::UserRole, virtualName);
        item->setData(0, Qt::UserRole + 1, type);
        item->setIcon(0, style()->standardIcon(type == QLatin1String("dir")
                            ? QStyle::SP_DirIcon : QStyle::SP_FileIcon));
        if (info.exists()) {
            item->setText(1, info.lastModified().toString(QStringLiteral("dd.MM.yyyy HH:mm")));
            if (type == QLatin1String("file")) item->setText(2, QString::number(info.size()));
        }
    }

    void showDirectory(const QString &virtualDirectory)
    {
        if (!vfs_) return;
        const QString host = vfs_->existingDirectory(virtualDirectory);
        if (host.isEmpty()) { status(QStringLiteral("Verzeichnis nicht zugänglich.")); return; }
        currentDirectory_ = virtualDirectory;
        selectedEntry_.clear();
        location_->setText(QStringLiteral("Pfad: /") + virtualDirectory);
        folders_->clear(); files_->clear(); filename_->clear();
        auto addFolder = [this](const QString &caption, const QString &path,
                                QStyle::StandardPixmap icon) {
            auto *item = new QListWidgetItem(style()->standardIcon(icon), caption, folders_);
            item->setData(Qt::UserRole, path);
        };
        if (!virtualDirectory.isEmpty()) {
            const QString parent = D64ApplicationVfs::parentVirtual(virtualDirectory);
            addFolder(QStringLiteral(".."), parent, QStyle::SP_ArrowUp);
            addTreeEntry(QStringLiteral(".."), parent, QStringLiteral("dir"), QFileInfo());
        }
        if (virtualDirectory.isEmpty()) {
            for (const QString &mount : vfs_->mountPoints()) {
                addFolder(mount, mount, QStyle::SP_DirHomeIcon);
                addTreeEntry(mount, mount, QStringLiteral("dir"), QFileInfo());
            }
        } else {
            const QFileInfoList folders = QDir(host).entryInfoList(
                QDir::Dirs | QDir::NoDotAndDotDot | QDir::Readable, QDir::Name);
            for (const QFileInfo &folder : folders) {
                const QString virtualChild = D64ApplicationVfs::join(virtualDirectory, folder.fileName());
                if (folder.isSymLink() || vfs_->existingDirectory(virtualChild).isEmpty()) continue;
                addFolder(folder.fileName(), virtualChild, QStyle::SP_DirIcon);
                addTreeEntry(folder.fileName(), virtualChild, QStringLiteral("dir"), folder);
            }
            const QFileInfoList entries = QDir(host).entryInfoList(QDir::Files | QDir::Readable,
                                                                    QDir::Name | QDir::IgnoreCase);
            for (const QFileInfo &file : entries) {
                if (file.isSymLink()) continue;
                if (vfs_->readableFile(D64ApplicationVfs::join(virtualDirectory, file.fileName())).isEmpty())
                    continue;
                const QString virtualFile = D64ApplicationVfs::join(virtualDirectory, file.fileName());
                addFolder(file.fileName(), virtualFile, QStyle::SP_FileIcon);
                addTreeEntry(file.fileName(), file.fileName(), QStringLiteral("file"), file);
            }
        }
        files_->resizeColumnToContents(0);
        // Genau 24 zusätzliche Pixel zwischen dem durch Qt gemessenen
        // Namensinhalt (inklusive Icon/Einrückung) und der Datum-Spalte.
        // Nach jedem Ordnerwechsel erneut anwenden.
        files_->setColumnWidth(0, files_->columnWidth(0) + 24);
        filterFiles();
        status(QString());
    }

    void acceptSelection()
    {
        if (!vfs_) return;
        const QString name = filename_->text().trimmed();
        if (!D64ApplicationVfs::safeName(name) || currentDirectory_.isEmpty()) {
            status(QStringLiteral("Bitte eine Datei in 'Dokumente' oder 'Alle Benutzer' auswählen."));
            return;
        }
        const QString relative = D64ApplicationVfs::join(currentDirectory_, name);
        const QString host = mode_ == OpenFile ? vfs_->readableFile(relative)
                                                : vfs_->writableFile(relative);
        if (host.isEmpty()) {
            status(QStringLiteral("Dateizugriff verweigert oder Datei nicht vorhanden."));
            return;
        }
        if (mode_ == SaveFile && QFileInfo::exists(host) &&
            !inputPrompt(QStringLiteral("Datei '%1' überschreiben?").arg(name),
                         QString(), nullptr, true))
            return;
        selected_ = relative;
        finish(Accepted);
    }

    // Eingabe- und Bestaetigungsdialoge sind eingebettete Widgets IN dieser
    // Datei-Dialogebene, keine nativen QMessageBox-/QInputDialog-Fenster.
    bool inputPrompt(const QString &title, const QString &initial, QString *value,
                     bool confirmOnly = false)
    {
        QWidget blocker(this);
        blocker.setObjectName(QStringLiteral("dbaseVirtualInputBlocker"));
        blocker.setGeometry(rect());
        blocker.setStyleSheet(QStringLiteral("QWidget#dbaseVirtualInputBlocker{background:rgba(0,0,0,75);}"));
        QWidget panel(&blocker);
        panel.setObjectName(QStringLiteral("dbaseVirtualInputPanel"));
        panel.setStyleSheet(darkMode_ ? QStringLiteral(
            "QWidget#dbaseVirtualInputPanel{background:#0000aa;color:white;border:2px solid #ffff55;}"
            "QLabel{color:white;}QLineEdit{background:#000080;color:white;border:1px solid yellow;}"
            "QPushButton{background:#0000aa;color:yellow;border:1px solid yellow;padding:6px;}")
            : QStringLiteral(
            "QWidget#dbaseVirtualInputPanel{background:#dddddd;color:black;border:2px solid #555555;}"
            "QLabel{color:black;}QLineEdit{background:white;color:black;}"
            "QPushButton{background:#cccccc;color:black;border:1px solid #666666;padding:6px;}"));
        const int w = qMin(440, qMax(270, width()-30));
        const int h = confirmOnly ? 155 : 180;
        panel.setGeometry(qMax(0,(width()-w)/2), qMax(0,(height()-h)/2), w, h);
        auto *layout = new QVBoxLayout(&panel);
        layout->addWidget(new QLabel(title, &panel));
        QLineEdit *edit = nullptr;
        if (!confirmOnly) {
            edit = new QLineEdit(initial, &panel);
            edit->setObjectName(QStringLiteral("dbaseVirtualInputName"));
            layout->addWidget(edit);
        }
        auto *row = new QHBoxLayout();
        row->addStretch();
        auto *ok = new QPushButton(QStringLiteral("OK"), &panel);
        auto *cancel = new QPushButton(QStringLiteral("Abbrechen"), &panel);
        auto *help = new QPushButton(QStringLiteral("Hilfe"), &panel);
        row->addWidget(ok); row->addWidget(cancel); row->addWidget(help);
        layout->addLayout(row);
        bool accepted = false;
        QEventLoop loop;
        auto done = [&](bool success) { accepted = success; loop.quit(); };
        QObject::connect(ok, &QPushButton::clicked, &panel, [&]() { done(true); });
        QObject::connect(cancel, &QPushButton::clicked, &panel, [&]() { done(false); });
        QObject::connect(help, &QPushButton::clicked, &panel, [&]() {
            if (edit) edit->setPlaceholderText(QStringLiteral("Neuer Verzeichnisname ohne /, \\, .."));
        });
        if (edit) QObject::connect(edit, &QLineEdit::returnPressed, &panel, [&]() { done(true); });
        blocker.setContextMenuPolicy(Qt::NoContextMenu);
        panel.setContextMenuPolicy(Qt::NoContextMenu);
        for (QWidget *widget : blocker.findChildren<QWidget *>()) {
            widget->setContextMenuPolicy(Qt::NoContextMenu);
            widget->setCursor(Qt::ArrowCursor);
        }
        for (QPushButton *button : {ok, cancel, help})
            button->setCursor(Qt::PointingHandCursor);
        // Bisherige Escape-Weitergabe wird fuer den Unterdialog temporär blockiert.
        if (layer_) layer_->setEscapeHandler([&]() { done(false); });
        blocker.show(); blocker.raise(); panel.show(); panel.raise();
        if (edit) edit->setFocus(Qt::OtherFocusReason);
        else ok->setFocus(Qt::OtherFocusReason);
        loop.exec(QEventLoop::AllEvents);
        if (layer_) layer_->setEscapeHandler([this]() { finish(Rejected); });
        if (accepted && value && edit) *value = edit->text().trimmed();
        return accepted;
    }

    void addDirectory()
    {
        if (!vfs_ || currentDirectory_.isEmpty()) {
            status(QStringLiteral("Bitte zuerst 'Dokumente' oder 'Alle Benutzer' öffnen."));
            return;
        }
        QString name;
        if (!inputPrompt(QStringLiteral("Neues Verzeichnis:"), QString(), &name)) return;
        if (!vfs_->createDirectory(currentDirectory_, name)) {
            status(QStringLiteral("Verzeichnis konnte nicht erstellt werden: ungültiger Name oder Zugriff verweigert."));
            return;
        }
        showDirectory(currentDirectory_);
    }

    void deleteSelection()
    {
        if (!vfs_ || currentDirectory_.isEmpty()) return;
        const QString selected = selectedEntry_;
        if (selected.isEmpty() || selected == currentDirectory_ ||
            selected == vfs_->shared() || selected == vfs_->documents() ||
            selected == D64ApplicationVfs::parentVirtual(currentDirectory_)) {
            status(QStringLiteral("Kein löschbarer Eintrag gewählt.")); return;
        }
        if (!inputPrompt(QStringLiteral("'%1' wirklich löschen?").arg(selected), QString(), nullptr, true))
            return;
        if (!vfs_->removeEntry(selected)) {
            status(QStringLiteral("Löschen nicht möglich (Verzeichnis muss leer sein)."));
            return;
        }
        showDirectory(currentDirectory_);
    }

    QWidget *titleBar_ = nullptr;
    QWidget *titleBalance_ = nullptr;
    QLabel *title_ = nullptr;
    QToolButton *closeButton_ = nullptr;
    bool dragging_ = false;
    QWidget *dragWidget_ = nullptr;
    QPoint dragStartGlobal_;
    QPoint dragStartCells_;
    int gridColumn_ = 0;
    int gridRow_ = 0;
    D64ApplicationVfs *vfs_ = nullptr;
    Mode mode_ = OpenFile;
    bool darkMode_ = true;
    bool running_ = false;
    int result_ = Rejected;
    std::function<void()> finished_;
    D64TurboModalLayer *layer_ = nullptr;
    QSplitter *splitter_ = nullptr;
    QListWidget *folders_ = nullptr;
    QTreeWidget *files_ = nullptr;
    QLineEdit *filename_ = nullptr;
    QLineEdit *search_ = nullptr;
    QLabel *location_ = nullptr;
    QLabel *info_ = nullptr;
    QString currentDirectory_;
    QString selectedEntry_;
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
        if (dialog.exec() != D64VirtualFileDialog::Accepted) return false;
        return loadVirtualDocument(dialog.selectedVirtualPath());
    }

    bool loadVirtualDocument(const QString &relative)
    {
        if (!vfs_) return false;
        const QString host = vfs_->readableFile(relative);
        if (host.isEmpty()) return false;
        const QFileInfo selectedInfo(host);
        if (selectedInfo.size() > 16 * 1024 * 1024) {
            showError(QStringLiteral("Datei zu groß"),
                      QStringLiteral("Der Editor öffnet Textdateien bis 16 MiB."));
            return false;
        }
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
        QString content = QString::fromUtf8(data);
        // Bestehende dBASE-.prg/.wfm-Dateien koennen noch CP1252/ANSI
        // enthalten. Nur bei ungueltigem UTF-8 auf die Systemcodepage fallen.
        if (content.contains(QChar::ReplacementCharacter))
            content = QString::fromLocal8Bit(data);
        edit_->setPlainText(content);
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
            if (dialog.exec() != D64VirtualFileDialog::Accepted) return false;
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
        D64TurboMessageBox::showMessage(this, title, description,
            {{QStringLiteral("OK"), D64TurboMessageBox::Ok}});
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
