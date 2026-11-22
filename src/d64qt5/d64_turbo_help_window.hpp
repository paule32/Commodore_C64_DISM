#pragma once
// Stage 655: Native Turbo Vision help viewer INSIDE the Konsole viewport.
// No parser/compiler/menu: the Python application compiles THLP -> PO -> MO.
// No Q_OBJECT; Windows PE32/PE64 ABI is exposed by DBaseQtHelpShowMo().

#include "d64_turbo_scrollbar.hpp"
#include "d64_turbo_grid_motion.hpp"
#include <QByteArray>
#include <QEvent>
#include <QFile>
#include <QFrame>
#include <QGraphicsDropShadowEffect>
#include <QColor>
#include <QHash>
#include <QHBoxLayout>
#include <QKeyEvent>
#include <QLabel>
#include <QMouseEvent>
#include <QPointer>
#include <QRegularExpression>
#include <QScrollBar>
#include <QResizeEvent>
#include <QTextBrowser>
#include <QTextDocument>
#include <QTextFrame>
#include <QTextFormat>
#include <QToolButton>
#include <QUrl>
#include <QVBoxLayout>
#include <QWidget>
#include <QtGlobal>

class D64TurboHelpWindow final : public QWidget
{
public:
    explicit D64TurboHelpWindow(QWidget *consoleViewport)
        : QWidget(consoleViewport)
    {
        setObjectName(QStringLiteral("dbaseTurboHelpWindow"));
        setAttribute(Qt::WA_StyledBackground, true);
        setContextMenuPolicy(Qt::NoContextMenu);
        setFocusPolicy(Qt::StrongFocus);
        // Stage 664: hard-edged DOS-style shadow, +5 px right and +5 px down.
        auto *shadow = new QGraphicsDropShadowEffect(this);
        shadow->setBlurRadius(0.0);
        shadow->setOffset(5.0, 5.0);
        shadow->setColor(QColor(0, 0, 0, 160));
        setGraphicsEffect(shadow);
        setStyleSheet(QStringLiteral(
            "QWidget#dbaseTurboHelpWindow{background:#00bfc7;border:2px solid #ffe600;}"
            "QFrame#dbaseTurboHelpTitle{background:#73edf1;border-bottom:2px solid #07566b;}"
            "QLabel#dbaseTurboHelpCaption{color:#002935;font: bold 11pt Consolas;}"
            "QToolButton#dbaseTurboHelpClose{background:#abfaff;color:#003947;"
            "border:1px solid #07566b;font:bold 13pt Consolas;}"
            "QToolButton#dbaseTurboHelpClose:hover{background:#ffffff;}"
            "QTextBrowser#dbaseTurboHelpText{background:#00bfc7;color:#062b34;"
            "border:0;selection-background-color:#197bb4;}"
        ));
        auto *layout = new QVBoxLayout(this);
        layout->setContentsMargins(2, 2, 2, 2);
        layout->setSpacing(0);

        title_ = new QFrame(this);
        title_->setObjectName(QStringLiteral("dbaseTurboHelpTitle"));
        title_->setFixedHeight(30);
        title_->setMouseTracking(true);
        title_->setCursor(Qt::SizeAllCursor);
        title_->setContextMenuPolicy(Qt::NoContextMenu);
        title_->installEventFilter(this);
        auto *header = new QHBoxLayout(title_);
        header->setContentsMargins(5, 2, 7, 2);
        header->setSpacing(7);
        auto *close = new QToolButton(title_);
        close->setObjectName(QStringLiteral("dbaseTurboHelpClose"));
        close->setText(QStringLiteral("\u00d7"));
        close->setToolTip(QStringLiteral("Hilfe schlie\u00dfen"));
        close->setCursor(Qt::ArrowCursor);
        close->setFixedSize(24, 23);
        close->setContextMenuPolicy(Qt::NoContextMenu);
        QObject::connect(close, &QToolButton::clicked, this, [this]() { hide(); });
        header->addWidget(close);
        auto *caption = new QLabel(QStringLiteral("Hilfe"), title_);
        caption->setObjectName(QStringLiteral("dbaseTurboHelpCaption"));
        caption->setAttribute(Qt::WA_TransparentForMouseEvents);
        header->addWidget(caption);
        caption_ = caption;
        header->addStretch(1);
        layout->addWidget(title_);

        browser_ = new QTextBrowser(this);
        browser_->setObjectName(QStringLiteral("dbaseTurboHelpText"));
        browser_->setFrameShape(QFrame::NoFrame);
        browser_->setOpenLinks(false);
        browser_->setOpenExternalLinks(false);
        // Stage 656: This is a scrollable *child* window, not the console.
        // Both arrow bars stay visible; their thumbs remain strictly between
        // the arrow buttons (d64TurboScrollGeometry uses half-open bounds).
        auto *helpHScroll = new D64TurboArrowScrollBar(Qt::Horizontal, browser_);
        helpHScroll->setTurboHelpTheme();
        helpHScroll->setFixedHeight(17);
        browser_->setHorizontalScrollBar(helpHScroll);
        auto *helpVScroll = new D64TurboArrowScrollBar(Qt::Vertical, browser_);
        helpVScroll->setTurboHelpTheme();
        helpVScroll->setFixedWidth(17);
        browser_->setVerticalScrollBar(helpVScroll);
        browser_->setHorizontalScrollBarPolicy(Qt::ScrollBarAlwaysOn);
        browser_->setVerticalScrollBarPolicy(Qt::ScrollBarAlwaysOn);
        browser_->setContextMenuPolicy(Qt::NoContextMenu);
        // Mouse events inside QTextBrowser normally go to its viewport,
        // not to the enclosing help window. Activate on either surface.
        browser_->installEventFilter(this);
        browser_->viewport()->installEventFilter(this);
        helpHScroll->installEventFilter(this);
        helpVScroll->installEventFilter(this);
        browser_->setFont(QFont(QStringLiteral("Consolas"), 11));
        // Stage 664: HTML adds a horizontal DOS-grid inset; document margins
        // must not add unwanted top/right space or shift the text by 4 px.
        browser_->document()->setDocumentMargin(0.0);
        QObject::connect(browser_, &QTextBrowser::anchorClicked, this,
                         [this](const QUrl &link) {
            if (link.scheme() != QLatin1String("tvhelp") ||
                link.host() != QLatin1String("topic")) return;
            const QString topic = link.path(QUrl::FullyDecoded).mid(1);
            showTopic(topic, link.fragment(QUrl::FullyDecoded));
        });
        layout->addWidget(browser_, 1);
        // Manually resized child widget: never resize the surrounding Konsole window.
        grip_ = new QToolButton(this);
        grip_->setObjectName(QStringLiteral("dbaseTurboHelpResizeGrip"));
        grip_->setText(QStringLiteral("\u25e2"));
        grip_->setCursor(Qt::SizeFDiagCursor);
        grip_->setFixedSize(19, 19);
        grip_->setToolTip(QStringLiteral("Fensterbreite und -höhe ändern"));
        grip_->setStyleSheet(QStringLiteral(
            "QToolButton#dbaseTurboHelpResizeGrip{border:0;background:#00bfc7;"
            "color:#07566b;font:bold 13pt Consolas;padding:0;}"
            "QToolButton#dbaseTurboHelpResizeGrip:hover{background:#73edf1;}"));
        grip_->setMouseTracking(true);
        grip_->installEventFilter(this);
        grip_->raise();
        setMinimumSize(320, 200);
        if (consoleViewport) {
            consoleViewport->installEventFilter(this);
            const QRect area = consoleViewport->rect();
            moveOnGrid(QPoint(gridCellWidth_, gridCellHeight_));
            resizeOnGrid(QSize(qMax(320, qMin(area.width() - 16, 760)),
                                   qMax(200, qMin(area.height() - 16, 480))));
        }
        hide();
    }

    // Stage 657: Mausbewegung nur in ganzen DOS-Zeichenzellen.
    // Die Hauptkonsole liefert die tatsaechlichen Font-Metriken (DPI/Zoom).
    void setGridCellSize(const QSize &cellSize)
    {
        const int oldWidth = qMax(1, gridCellWidth_);
        const int oldHeight = qMax(1, gridCellHeight_);
        const int column = d64TurboRoundCells(x(), oldWidth);
        const int row = d64TurboRoundCells(y(), oldHeight);
        const int columns = d64TurboRoundCells(width(), oldWidth);
        const int rows = d64TurboRoundCells(height(), oldHeight);
        gridCellWidth_ = qMax(1, cellSize.width());
        gridCellHeight_ = qMax(1, cellSize.height());
        if (browser_ && !currentTopic_.isEmpty() && topics_.contains(currentTopic_)) {
            const int oldScroll = browser_->verticalScrollBar()->value();
            setHelpHtml(topics_.value(currentTopic_));
            browser_->verticalScrollBar()->setValue(oldScroll);
        }
        if (maximized_) {
            const int restoreColumn = d64TurboRoundCells(restore_.x(), oldWidth);
            const int restoreRow = d64TurboRoundCells(restore_.y(), oldHeight);
            const int restoreColumns = d64TurboRoundCells(restore_.width(), oldWidth);
            const int restoreRows = d64TurboRoundCells(restore_.height(), oldHeight);
            restore_.moveTopLeft(QPoint(restoreColumn * gridCellWidth_,
                                        restoreRow * gridCellHeight_));
            const int maxW = qMax(minimumWidth(), parentWidget()->width() - restore_.x());
            const int maxH = qMax(minimumHeight(), parentWidget()->height() - restore_.y());
            restore_.setSize(QSize(
                d64TurboClampGridExtent(restoreColumns * gridCellWidth_,
                                        gridCellWidth_, minimumWidth(), maxW),
                d64TurboClampGridExtent(restoreRows * gridCellHeight_,
                                        gridCellHeight_, minimumHeight(), maxH)));
        } else {
            moveOnGrid(QPoint(column * gridCellWidth_, row * gridCellHeight_));
            resizeOnGrid(QSize(columns * gridCellWidth_, rows * gridCellHeight_));
        }
    }

    bool openMo(const QString &filename, QString *error = nullptr)
    {
        QFile file(filename);
        if (!file.open(QIODevice::ReadOnly)) {
            if (error) *error = QStringLiteral("HLP-Datei kann nicht ge\u00f6ffnet werden: ") + filename;
            return false;
        }
        if (file.size() < 28 || file.size() > 32 * 1024 * 1024) {
            if (error) *error = QStringLiteral("Ung\u00fcltige GNU-HLP-Dateigr\u00f6\u00dfe");
            return false;
        }
        const QByteArray data = file.readAll();
        auto u32 = [&data](quint64 offset, bool bigEndian) -> quint32 {
            const auto *p = reinterpret_cast<const uchar *>(data.constData() + offset);
            if (bigEndian)
                return (quint32(p[0]) << 24) | (quint32(p[1]) << 16) |
                       (quint32(p[2]) << 8) | quint32(p[3]);
            return quint32(p[0]) | (quint32(p[1]) << 8) |
                   (quint32(p[2]) << 16) | (quint32(p[3]) << 24);
        };
        // The GNU MO file magic is 0x950412de, stored as DE 12 04 95 in LE.
        const QByteArray magic = data.left(4);
        const bool bigEndian = magic == QByteArray::fromHex("950412de");
        if (!bigEndian && magic != QByteArray::fromHex("de120495")) {
            if (error) *error = QStringLiteral("Ung\u00fcltiger GNU-HLP-Header");
            return false;
        }
        const quint32 count = u32(8, bigEndian);
        const quint32 idsOffset = u32(12, bigEndian);
        const quint32 strsOffset = u32(16, bigEndian);
        const quint64 size = quint64(data.size());
        if (count == 0 || count > 20000 ||
            quint64(idsOffset) + quint64(count) * 8 > size ||
            quint64(strsOffset) + quint64(count) * 8 > size) {
            if (error) *error = QStringLiteral("Ung\u00fcltige GNU-HLP-Zeichentabellen");
            return false;
        }
        QHash<QString, QString> loaded;
        QHash<quint32, QString> numberToTopic;
        const QString numericPrefix = QStringLiteral("turbo-help-id\x04");
        for (quint32 n = 0; n < count; ++n) {
            const quint32 idlen = u32(quint64(idsOffset) + quint64(n) * 8, bigEndian);
            const quint32 idoff = u32(quint64(idsOffset) + quint64(n) * 8 + 4, bigEndian);
            const quint32 valen = u32(quint64(strsOffset) + quint64(n) * 8, bigEndian);
            const quint32 vaoff = u32(quint64(strsOffset) + quint64(n) * 8 + 4, bigEndian);
            if (idlen > 1024 * 1024 || valen > 8 * 1024 * 1024 ||
                quint64(idoff) + idlen > size || quint64(vaoff) + valen > size) {
                if (error) *error = QStringLiteral("Defekte GNU-HLP-Eintragsl\u00e4nge");
                return false;
            }
            const QString id = QString::fromUtf8(data.constData() + idoff, int(idlen));
            const QString value = QString::fromUtf8(data.constData() + vaoff, int(valen));
            if (id.startsWith(numericPrefix)) {
                // GNU gettext msgctxt + msgid are joined by byte 0x04 in MO.
                // Help ID 1234 maps to the *symbolic* topic name "test".
                bool ok = false;
                const quint32 numericId = id.mid(numericPrefix.size()).toUInt(&ok, 10);
                if (!ok || numberToTopic.contains(numericId)) {
                    if (error) *error = QStringLiteral("Doppelte/ungültige Hilfenummer in HLP");
                    return false;
                }
                numberToTopic.insert(numericId, value);
            } else if (!id.isEmpty()) {
                loaded.insert(id, value);
            }
        }
        if (!loaded.contains(QStringLiteral("index"))) {
            if (error) *error = QStringLiteral("Das Standardthema index fehlt in der HLP-Datei");
            return false;
        }
        // Reject invalid numeric aliases before replacing a running catalog.
        for (auto it = numberToTopic.cbegin(); it != numberToTopic.cend(); ++it) {
            if (!loaded.contains(it.value())) {
                if (error) *error = QStringLiteral("Hilfenummer verweist auf fehlendes Thema");
                return false;
            }
        }
        topics_.swap(loaded);
        helpNumbers_.swap(numberToTopic);
        return showTopic(QStringLiteral("index"));
    }

    bool showTopicByNumber(quint32 number, const QString &anchor = QString())
    {
        const auto found = helpNumbers_.constFind(number);
        if (found == helpNumbers_.cend()) return false;
        return showTopic(found.value(), anchor);
    }

    bool showTopic(const QString &topic, const QString &anchor = QString())
    {
        // A quoted %link "1234" (or %link 1234) works as a numeric link too;
        // explicit text topic names always have precedence over numeric aliases.
        QString resolvedTopic = topic;
        if (!topics_.contains(resolvedTopic)) {
            bool ok = false;
            const quint32 number = topic.toUInt(&ok, 10);
            if (ok && helpNumbers_.contains(number))
                resolvedTopic = helpNumbers_.value(number);
        }
        if (!topics_.contains(resolvedTopic)) {
            // Never navigate to file:// or network URLs.
            setHelpHtml(QStringLiteral("<b>Hilfethema nicht gefunden: </b>") + topic);
            return false;
        }
        browser_->clear(); // Replace the previous topic, never append.
        setHelpHtml(topics_.value(resolvedTopic));
        currentTopic_ = resolvedTopic;
        if (caption_) caption_->setText(QStringLiteral("Hilfe:  ") + resolvedTopic);
        if (!anchor.isEmpty()) browser_->scrollToAnchor(anchor);
        else browser_->verticalScrollBar()->setValue(0);
        show();
        raise();
        setFocus(Qt::OtherFocusReason);
        return true;
    }

    void toggleMaximized()
    {
        if (!parentWidget()) return;
        if (!maximized_) {
            restore_ = geometry();
            maximized_ = true;
            resizing_ = false;
            if (grip_) grip_->hide();
            setGeometry(parentWidget()->rect());
        } else {
            maximized_ = false;
            if (grip_) grip_->show();
            setGeometry(restore_);
            moveOnGrid(pos());
            resizeOnGrid(size());
        }
    }

protected:
    void mousePressEvent(QMouseEvent *event) override
    {
        // Clicking the window background also activates the help window.
        if (event->button() == Qt::LeftButton)
            raise();
        QWidget::mousePressEvent(event);
    }

    bool eventFilter(QObject *obj, QEvent *event) override
    {
        // Clicking the title, the browser (including its viewport), the
        // scrollbars or the resize grip brings this child to the front.
        // Do not consume the event: links/scrolling/dragging must still work.
        if (event->type() == QEvent::MouseButtonPress) {
            auto *mouse = static_cast<QMouseEvent *>(event);
            if (mouse->button() == Qt::LeftButton &&
                (obj == title_ || obj == grip_ || obj == browser_ ||
                 obj == browser_->viewport() ||
                 obj == browser_->horizontalScrollBar() ||
                 obj == browser_->verticalScrollBar())) {
                raise();
            }
        }
        if (obj == parentWidget() && event->type() == QEvent::Resize) {
            if (maximized_) setGeometry(parentWidget()->rect());
            else {
                moveOnGrid(pos());
                resizeOnGrid(size());
            }
        }
        if (obj == grip_) {
            if (event->type() == QEvent::MouseButtonPress) {
                auto *mouse = static_cast<QMouseEvent *>(event);
                if (mouse->button() == Qt::LeftButton && !maximized_) {
                    resizing_ = true;
                    resizeStartGlobal_ = mouse->globalPos();
                    resizeStart_ = size();
                    return true;
                }
            }
            if (event->type() == QEvent::MouseMove && resizing_) {
                auto *mouse = static_cast<QMouseEvent *>(event);
                if (mouse->buttons() & Qt::LeftButton) {
                    const QPoint change = mouse->globalPos() - resizeStartGlobal_;
                    const int maxW = qMax(minimumWidth(), parentWidget()->width() - x());
                    const int maxH = qMax(minimumHeight(), parentWidget()->height() - y());
                    resize(d64TurboGridDragExtent(resizeStart_.width(), change.x(),
                                                  gridCellWidth_, minimumWidth(), maxW),
                           d64TurboGridDragExtent(resizeStart_.height(), change.y(),
                                                  gridCellHeight_, minimumHeight(), maxH));
                    return true;
                }
            }
            if (event->type() == QEvent::MouseButtonRelease) {
                resizing_ = false;
                return true;
            }
        }
        if (obj == title_) {
            if (event->type() == QEvent::MouseButtonDblClick) {
                auto *mouse = static_cast<QMouseEvent *>(event);
                if (mouse->button() == Qt::LeftButton) {
                    moving_ = false;
                    toggleMaximized();
                    return true;
                }
            }
            if (event->type() == QEvent::MouseButtonPress) {
                auto *mouse = static_cast<QMouseEvent *>(event);
                if (mouse->button() == Qt::LeftButton && !maximized_) {
                    moving_ = true;
                    dragGlobal_ = mouse->globalPos();
                    dragPosition_ = pos();
                    return true;
                }
            }
            if (event->type() == QEvent::MouseMove && moving_) {
                auto *mouse = static_cast<QMouseEvent *>(event);
                if (mouse->buttons() & Qt::LeftButton) {
                    const QPoint delta = mouse->globalPos() - dragGlobal_;
                    const QPoint position = dragPosition_ + QPoint(
                        d64TurboRoundCells(delta.x(), gridCellWidth_) * gridCellWidth_,
                        d64TurboRoundCells(delta.y(), gridCellHeight_) * gridCellHeight_);
                    moveOnGrid(position);
                    return true;
                }
            }
            if (event->type() == QEvent::MouseButtonRelease) {
                moving_ = false;
            }
        }
        return QWidget::eventFilter(obj, event);
    }

    void resizeEvent(QResizeEvent *event) override
    {
        QWidget::resizeEvent(event);
        if (grip_)
            grip_->move(qMax(0, width() - grip_->width() - 3),
                        qMax(0, height() - grip_->height() - 3));
    }

    void keyPressEvent(QKeyEvent *event) override
    {
        if (event->key() == Qt::Key_Escape) {
            hide();
            event->accept();
            return;
        }
        QWidget::keyPressEvent(event);
    }

private:
    // Die erlaubten Fensterpositionen liegen stets auf dem Konsolenraster;
    // auch die rechte/untere Sichtbarkeitsgrenze wird auf Zellen abgerundet.
    void moveOnGrid(const QPoint &desired)
    {
        if (!parentWidget() || maximized_) return;
        move(d64TurboClampGridCoordinate(
                 desired.x(), gridCellWidth_, parentWidget()->width() - 72),
             d64TurboClampGridCoordinate(
                 desired.y(), gridCellHeight_, parentWidget()->height() - title_->height()));
    }

    // Stage 659: Breite und Hoehe bleiben im DOS-Zeichenraster. Dieses
    // Verfahren wird beim Initialisieren, bei Font-/DPI-Wechsel und beim
    // Veraendern des Konsolen-Viewports verwendet. Maximieren fuellt dagegen
    // weiterhin bewusst den gesamten Viewport.
    void resizeOnGrid(const QSize &desired)
    {
        if (!parentWidget() || maximized_) return;
        const int maxW = qMax(minimumWidth(), parentWidget()->width() - x());
        const int maxH = qMax(minimumHeight(), parentWidget()->height() - y());
        resize(d64TurboClampGridExtent(desired.width(), gridCellWidth_,
                                       minimumWidth(), maxW),
               d64TurboClampGridExtent(desired.height(), gridCellHeight_,
                                       minimumHeight(), maxH));
    }

    // Stage 666: QTextBrowser/QTextDocument does not reliably apply CSS
    // "padding-left" to <body> on all Qt5 builds. Set the margin on the
    // document's ROOT FRAME instead. This leaves exactly one entire DOS
    // character cell empty between the inside of the yellow window frame
    // and the first character of any topic (also error messages and links).
    // Always apply AFTER setHtml(), which reconstructs the document frames.
    void setHelpHtml(const QString &source)
    {
        browser_->setHtml(renderMarkup(source));
        QTextFrame *root = browser_->document()->rootFrame();
        if (!root) return;
        QTextFrameFormat format = root->frameFormat();
        format.setLeftMargin(qreal(qMax(1, gridCellWidth_)));
        format.setRightMargin(0.0);
        format.setTopMargin(0.0);
        format.setBottomMargin(0.0);
        root->setFrameFormat(format);
    }

    // Only <b>, <ref>, <link> and <anchor> are interpreted. All other markup
    // is HTML-escaped; the help compiler never feeds arbitrary HTML to Qt.
    static QString renderMarkup(const QString &text)
    {
        static const QRegularExpression token(
            QStringLiteral(R"(</?b>|<anchor\s+id=["'][^"']+["']\s*>\s*</anchor>|<ref>[^<]*</ref>|<link>[^<]*</link>)"),
            QRegularExpression::CaseInsensitiveOption);
        static const QRegularExpression refValue(
            QStringLiteral(R"(^\s*(["'])(.*?)\1\s+#([\w.-]+)\s*$)"));
        static const QRegularExpression linkValue(
            QStringLiteral(R"(^\s*(["'])(.*?)\1\s*$)"));
        static const QRegularExpression anchorValue(
            QStringLiteral(R"(^<anchor\s+id=["']([^"']+)["']\s*>\s*</anchor>$)"),
            QRegularExpression::CaseInsensitiveOption);
        QString body;
        int begin = 0;
        auto it = token.globalMatch(text);
        auto safeText = [](const QString &part) {
            QString escaped = part.toHtmlEscaped();
            escaped.replace(QLatin1Char('\n'), QStringLiteral("<br/>"));
            return escaped;
        };
        while (it.hasNext()) {
            const auto match = it.next();
            body += safeText(text.mid(begin, match.capturedStart() - begin));
            const QString matched = match.captured();
            const QString lowered = matched.toLower();
            if (lowered == QLatin1String("<b>") || lowered == QLatin1String("</b>")) {
                body += lowered;
            } else if (lowered.startsWith(QLatin1String("<anchor"))) {
                const auto anchor = anchorValue.match(matched);
                if (anchor.hasMatch())
                    body += QStringLiteral("<a name=\"") + anchor.captured(1).toHtmlEscaped() +
                            QStringLiteral("\"></a>");
            } else {
                const bool isRef = lowered.startsWith(QLatin1String("<ref>"));
                const QString payload = isRef ? matched.mid(5, matched.size() - 11)
                                              : matched.mid(6, matched.size() - 13);
                const auto value = (isRef ? refValue : linkValue).match(payload);
                if (value.hasMatch()) {
                    const QString name = value.captured(2);
                    const QString fragment = isRef ? value.captured(3) : QString();
                    QUrl url;
                    url.setScheme(QStringLiteral("tvhelp"));
                    url.setHost(QStringLiteral("topic"));
                    url.setPath(QLatin1Char('/') + name);
                    if (!fragment.isEmpty()) url.setFragment(fragment);
                    body += QStringLiteral("<a href=\"") + url.toString(QUrl::FullyEncoded).toHtmlEscaped() +
                            QStringLiteral("\"><u>") + name.toHtmlEscaped() + QStringLiteral("</u></a>");
                } else {
                    body += safeText(matched);
                }
            }
            begin = match.capturedEnd();
        }
        body += safeText(text.mid(begin));
        return QStringLiteral(
            "<html><head><style>body{background:#00bfc7;color:#062b34;"
            "margin:0;padding:0;font-family:Consolas,'Courier New',monospace;font-size:11pt;}"
            "a,a:visited{color:#003bc7;text-decoration:underline;}"
            "</style></head><body>") + body + QStringLiteral("</body></html>");
    }

    QHash<QString, QString> topics_;
    QHash<quint32, QString> helpNumbers_;
    QString currentTopic_;
    QFrame *title_ = nullptr;
    QLabel *caption_ = nullptr;
    QToolButton *grip_ = nullptr;
    QPoint resizeStartGlobal_;
    QSize resizeStart_;
    bool resizing_ = false;
    QTextBrowser *browser_ = nullptr;
    QRect restore_;
    QPoint dragGlobal_;
    QPoint dragPosition_;
    bool moving_ = false;
    bool maximized_ = false;
    int gridCellWidth_ = 8;
    int gridCellHeight_ = 16;
};
