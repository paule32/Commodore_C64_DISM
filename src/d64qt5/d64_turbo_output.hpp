#pragma once

// Stage 623: Zeichenraster-basiertes, verschiebbares Turbo-Vision-Ausgabefenster
// mit Maximieren/Wiederherstellen fuer die normale dBASE-.prg-Konsole.
// Kein Q_OBJECT / kein zusaetzlicher MOC-Schritt.
// Der Eltern-Viewport bleibt fuer das 80x25-Grundfenster verantwortlich.
#include <QWidget>
#include "d64_turbo_scrollbar.hpp"
#include <QPlainTextEdit>
#include <QFrame>
#include <QLabel>
#include <QToolButton>
#include <QScrollBar>
#include <QTextCursor>
#include <QTextBlock>
#include <QFontMetrics>
#include <QMouseEvent>
#include <QPainter>
#include <QEvent>
#include <QPalette>
#include <QTimer>
#include <QtGlobal>
#include <QStringList>
#include <functional>

class D64TurboOutputWidget final : public QWidget
{
public:
    explicit D64TurboOutputWidget(QWidget *viewport)
        : QWidget(viewport)
    {
        setObjectName(QStringLiteral("dbaseTurboVisionOutput"));
        setAttribute(Qt::WA_StyledBackground, true);
        setMouseTracking(true);
        setFocusPolicy(Qt::StrongFocus);

        editor_ = new QPlainTextEdit(this);
        editor_->setObjectName(QStringLiteral("dbaseTurboVisionText"));
        editor_->setReadOnly(true);
        editor_->setUndoRedoEnabled(false);
        editor_->setFrameShape(QFrame::NoFrame);
        editor_->setLineWrapMode(QPlainTextEdit::NoWrap);
        editor_->document()->setDocumentMargin(2.0);
        editor_->setHorizontalScrollBarPolicy(Qt::ScrollBarAsNeeded);
        editor_->setVerticalScrollBarPolicy(Qt::ScrollBarAlwaysOn);
        auto *vArrowBar = new D64TurboArrowScrollBar(Qt::Vertical, editor_);
        vArrowBar->setArrowColor(QColor(QStringLiteral("#e8ffcb")));
        vArrowBar->setArrowBackground(QColor(QStringLiteral("#076b30")));
        editor_->setVerticalScrollBar(vArrowBar);
        auto *hArrowBar = new D64TurboArrowScrollBar(Qt::Horizontal, editor_);
        hArrowBar->setArrowColor(QColor(QStringLiteral("#e8ffcb")));
        hArrowBar->setArrowBackground(QColor(QStringLiteral("#076b30")));
        editor_->setHorizontalScrollBar(hArrowBar);
        editor_->document()->setMaximumBlockCount(10000);
        editor_->setStyleSheet(QStringLiteral(
            "QPlainTextEdit#dbaseTurboVisionText{background:#076b30;color:#e8ffcb;"
            "border:0;padding:1px;selection-background-color:#b7ef9b;"
            "selection-color:#064023;}"
            "QScrollBar:vertical{background:#06451f;width:15px;"
            "margin:15px 0px 15px 0px;border:1px solid #88e98e;}"
            "QScrollBar::groove:vertical{background:#06451f;}"
            "QScrollBar::handle:vertical{background:#55bf62;min-height:15px;border:1px solid #bcffbd;}"
            "QScrollBar::sub-line:vertical{background:#076b30;height:15px;"
            "subcontrol-position:top;subcontrol-origin:margin;border:1px solid #88e98e;}"
            "QScrollBar::add-line:vertical{background:#076b30;height:15px;"
            "subcontrol-position:bottom;subcontrol-origin:margin;border:1px solid #88e98e;}"
            "QScrollBar::add-page:vertical,QScrollBar::sub-page:vertical{background:#06451f;}"
            "QScrollBar:horizontal{background:#06451f;height:15px;"
            "margin:0px 15px 0px 15px;border:1px solid #88e98e;}"
            "QScrollBar::groove:horizontal{background:#06451f;}"
            "QScrollBar::handle:horizontal{background:#55bf62;min-width:15px;border:1px solid #bcffbd;}"
            "QScrollBar::sub-line:horizontal{background:#076b30;width:15px;"
            "subcontrol-position:left;subcontrol-origin:margin;border:1px solid #88e98e;}"
            "QScrollBar::add-line:horizontal{background:#076b30;width:15px;"
            "subcontrol-position:right;subcontrol-origin:margin;border:1px solid #88e98e;}"
            "QScrollBar::add-page:horizontal,QScrollBar::sub-page:horizontal{background:#06451f;}"
        ));
        QPalette pal = editor_->palette();
        pal.setColor(QPalette::Base, QColor("#076b30"));
        pal.setColor(QPalette::Text, QColor("#e8ffcb"));
        editor_->setPalette(pal);

        indicator_ = new QLabel(this);
        indicator_->setObjectName(QStringLiteral("dbaseTurboVisionIndicator"));
        indicator_->setAlignment(Qt::AlignLeft | Qt::AlignVCenter);
        indicator_->setStyleSheet(QStringLiteral("color:#d8ffd5;background:#07552b;border:0;"));
        grip_ = new QLabel(QStringLiteral("\u25e2"), this);
        grip_->setObjectName(QStringLiteral("dbaseTurboVisionGridGrip"));
        grip_->setAlignment(Qt::AlignCenter);
        grip_->setCursor(Qt::SizeFDiagCursor);
        grip_->setStyleSheet(QStringLiteral("color:#d9ffd4;background:#288e48;border:1px solid #a4f6a9;"));
        grip_->setMouseTracking(true);
        maximizeButton_ = new QToolButton(this);
        maximizeButton_->setObjectName(QStringLiteral("dbaseTurboVisionMaximizeButton"));
        maximizeButton_->setFocusPolicy(Qt::NoFocus);
        maximizeButton_->setCursor(Qt::PointingHandCursor);
        maximizeButton_->setStyleSheet(QStringLiteral(
            "QToolButton#dbaseTurboVisionMaximizeButton{background:#07552b;"
            "color:#e8ffcb;border:1px solid #b0ffc7;padding:0px;font-weight:bold;}"
            "QToolButton#dbaseTurboVisionMaximizeButton:hover{background:#39a75b;}"
            "QToolButton#dbaseTurboVisionMaximizeButton:pressed{background:#024320;}"
        ));
        maximizeButton_->setText(QStringLiteral("\u25a1"));
        maximizeButton_->setToolTip(QStringLiteral("Ausgabefenster maximieren"));
        maximizeButton_->installEventFilter(this);
        QObject::connect(maximizeButton_, &QToolButton::clicked,
                         this, [this]() { toggleMaximized(); });
        QObject::connect(editor_, &QPlainTextEdit::cursorPositionChanged,
                         this, [this]() { updateIndicator(); });
        grip_->installEventFilter(this);
        editor_->installEventFilter(this);
        editor_->viewport()->installEventFilter(this);
        if (viewport)
            viewport->installEventFilter(this);
        hide();
    }

    void setGridFont(const QFont &font)
    {
        editor_->setFont(font);
        indicator_->setFont(font);
        grip_->setFont(font);
        const QFontMetrics fm(font);
        const int oldWidth = qMax(1, cellWidth_);
        const int oldHeight = qMax(1, cellHeight_);
        const int oldCol = (originX_ + oldWidth/2) / oldWidth;
        const int oldRow = (originY_ + oldHeight/2) / oldHeight;
        const int restoreCol = (restoreOriginX_ + oldWidth/2) / oldWidth;
        const int restoreRow = (restoreOriginY_ + oldHeight/2) / oldHeight;
        cellWidth_ = qMax(1, fm.horizontalAdvance(QLatin1Char('M')));
        cellHeight_ = qMax(1, fm.lineSpacing());
        originX_ = oldCol * cellWidth_;
        originY_ = oldRow * cellHeight_;
        restoreOriginX_ = restoreCol * cellWidth_;
        restoreOriginY_ = restoreRow * cellHeight_;
        if (maximized_)
            fitMaximizedToViewport();
        else
            resizeInCharacters(requestedColumns_, requestedRows_);
    }

    // Stage 631: gemeinsames DOS-Zeichenraster für Fensteranordnung.
    void setGridGeometry(int column, int row, int columns, int rows)
    {
        if (maximized_) toggleMaximized();
        resizeInCharacters(qMax(24, columns), qMax(8, rows));
        moveWithinViewport(column * cellWidth_, row * cellHeight_);
    }
    void setActivationCallback(std::function<void(D64TurboOutputWidget *)> callback)
    { onActivated_ = std::move(callback); }

    void appendOutput(const QString &text)
    {
        if (text.isEmpty()) return;
        if (backgroundFillActive_) {
            // WRITE / ? after SET BACKGROUND overwrites the character cells
            // starting from the top-left; do not append below the filler.
            overlayText_ += text;
            refreshBackgroundFill();
            return;
        }
        QScrollBar *scroll = editor_->verticalScrollBar();
        const bool follow = !scroll || scroll->value() >= scroll->maximum() - 1;
        const int saved = scroll ? scroll->value() : 0;
        QTextCursor cursor = editor_->textCursor();
        cursor.movePosition(QTextCursor::End);
        cursor.insertText(text);
        editor_->setTextCursor(cursor);
        if (follow) {
            editor_->ensureCursorVisible();
        } else if (scroll) {
            scroll->setValue(qMin(saved, scroll->maximum()));
        }
        updateIndicator();
    }

    // VGA-DOS-Palette und CP437-Zeichen. Der Befehl fuellt die gesamte
    // Zeichenflaeche des Turbo-Vision-Viewports und veraendert nicht den
    // Fensterrand, die Titelleiste oder den Zoomfaktor.
    bool fillBackground(int background, int foreground, int character)
    {
        if (character < 0 || character > 255 ||
            background < -1 || background > 15 ||
            foreground < -1 || foreground > 15)
            return false;
        if (background >= 0) fillBackgroundColor_ = vgaColor(background);
        if (foreground >= 0) fillForegroundColor_ = vgaColor(foreground);
        fillCharacter_ = character;
        overlayText_.clear();
        backgroundFillActive_ = true;
        refreshBackgroundFill();
        return true;
    }

    static QColor vgaColor(int index)
    {
        static const QRgb palette[16] = {
            0x000000, 0x0000AA, 0x00AA00, 0x00AAAA,
            0xAA0000, 0xAA00AA, 0xAA5500, 0xAAAAAA,
            0x555555, 0x5555FF, 0x55FF55, 0x55FFFF,
            0xFF5555, 0xFF55FF, 0xFFFF55, 0xFFFFFF
        };
        return QColor::fromRgb(palette[qBound(0, index, 15)]);
    }

    static QChar dosCharacter(int code)
    {
        static const ushort codePoints[256] = {
            0x0020, 0x263A, 0x263B, 0x2665, 0x2666, 0x2663, 0x2660, 0x2022, 0x25D8, 0x25CB, 0x25D9, 0x2642,
            0x2640, 0x266A, 0x266B, 0x263C, 0x25BA, 0x25C4, 0x2195, 0x203C, 0x00B6, 0x00A7, 0x25AC, 0x21A8,
            0x2191, 0x2193, 0x2192, 0x2190, 0x221F, 0x2194, 0x25B2, 0x25BC, 0x0020, 0x0021, 0x0022, 0x0023,
            0x0024, 0x0025, 0x0026, 0x0027, 0x0028, 0x0029, 0x002A, 0x002B, 0x002C, 0x002D, 0x002E, 0x002F,
            0x0030, 0x0031, 0x0032, 0x0033, 0x0034, 0x0035, 0x0036, 0x0037, 0x0038, 0x0039, 0x003A, 0x003B,
            0x003C, 0x003D, 0x003E, 0x003F, 0x0040, 0x0041, 0x0042, 0x0043, 0x0044, 0x0045, 0x0046, 0x0047,
            0x0048, 0x0049, 0x004A, 0x004B, 0x004C, 0x004D, 0x004E, 0x004F, 0x0050, 0x0051, 0x0052, 0x0053,
            0x0054, 0x0055, 0x0056, 0x0057, 0x0058, 0x0059, 0x005A, 0x005B, 0x005C, 0x005D, 0x005E, 0x005F,
            0x0060, 0x0061, 0x0062, 0x0063, 0x0064, 0x0065, 0x0066, 0x0067, 0x0068, 0x0069, 0x006A, 0x006B,
            0x006C, 0x006D, 0x006E, 0x006F, 0x0070, 0x0071, 0x0072, 0x0073, 0x0074, 0x0075, 0x0076, 0x0077,
            0x0078, 0x0079, 0x007A, 0x007B, 0x007C, 0x007D, 0x007E, 0x2302, 0x00C7, 0x00FC, 0x00E9, 0x00E2,
            0x00E4, 0x00E0, 0x00E5, 0x00E7, 0x00EA, 0x00EB, 0x00E8, 0x00EF, 0x00EE, 0x00EC, 0x00C4, 0x00C5,
            0x00C9, 0x00E6, 0x00C6, 0x00F4, 0x00F6, 0x00F2, 0x00FB, 0x00F9, 0x00FF, 0x00D6, 0x00DC, 0x00A2,
            0x00A3, 0x00A5, 0x20A7, 0x0192, 0x00E1, 0x00ED, 0x00F3, 0x00FA, 0x00F1, 0x00D1, 0x00AA, 0x00BA,
            0x00BF, 0x2310, 0x00AC, 0x00BD, 0x00BC, 0x00A1, 0x00AB, 0x00BB, 0x2591, 0x2592, 0x2593, 0x2502,
            0x2524, 0x2561, 0x2562, 0x2556, 0x2555, 0x2563, 0x2551, 0x2557, 0x255D, 0x255C, 0x255B, 0x2510,
            0x2514, 0x2534, 0x252C, 0x251C, 0x2500, 0x253C, 0x255E, 0x255F, 0x255A, 0x2554, 0x2569, 0x2566,
            0x2560, 0x2550, 0x256C, 0x2567, 0x2568, 0x2564, 0x2565, 0x2559, 0x2558, 0x2552, 0x2553, 0x256B,
            0x256A, 0x2518, 0x250C, 0x2588, 0x2584, 0x258C, 0x2590, 0x2580, 0x03B1, 0x00DF, 0x0393, 0x03C0,
            0x03A3, 0x03C3, 0x00B5, 0x03C4, 0x03A6, 0x0398, 0x03A9, 0x03B4, 0x221E, 0x03C6, 0x03B5, 0x2229,
            0x2261, 0x00B1, 0x2265, 0x2264, 0x2320, 0x2321, 0x00F7, 0x2248, 0x00B0, 0x2219, 0x00B7, 0x221A,
            0x207F, 0x00B2, 0x25A0, 0x00A0
        };
        return QChar(codePoints[qBound(0, code, 255)]);
    }

    int columns() const { return columns_; }
    int rows() const { return rows_; }
    int characterWidth() const { return cellWidth_; }
    int characterHeight() const { return cellHeight_; }
    QString outputText() const { return editor_->toPlainText(); }
    bool isMaximizedInViewport() const { return maximized_; }

    // Speichert bei Maximierung die vorherige Geometrie in Zeichenzellen.
    // Wiederherstellen bleibt auch nach einem Zoom-/Viewportwechsel moeglich.
    void toggleMaximized()
    {
        if (!parentWidget()) return;
        moving_ = false;
        dragging_ = false;
        if (!maximized_) {
            restoreOriginX_ = originX_;
            restoreOriginY_ = originY_;
            restoreColumns_ = columns_;
            restoreRows_ = rows_;
            maximized_ = true;
            maximizeButton_->setText(QStringLiteral("\u2750"));
            maximizeButton_->setToolTip(QStringLiteral("Ausgabefenster wiederherstellen"));
            grip_->hide();
            fitMaximizedToViewport();
        } else {
            maximized_ = false;
            maximizeButton_->setText(QStringLiteral("\u25a1"));
            maximizeButton_->setToolTip(QStringLiteral("Ausgabefenster maximieren"));
            originX_ = restoreOriginX_;
            originY_ = restoreOriginY_;
            resizeInCharacters(restoreColumns_, restoreRows_);
            grip_->show();
        }
        update();
    }

    void resizeInCharacters(int columns, int rows)
    {
        requestedColumns_ = qMax(22, columns);
        requestedRows_ = qMax(6, rows);
        if (maximized_) {
            fitMaximizedToViewport();
            return;
        }
        // Das virtuelle Fenster darf rechts/unten aus dem 80x25-Viewport
        // hinausragen. Den Textbereich nicht mehr auf die Restgroesse stutzen.
        columns_ = requestedColumns_;
        rows_ = requestedRows_;
        moveWithinViewport(originX_, originY_);
        setGeometry(originX_, originY_,
                    columns_ * cellWidth_ + chromeWidth() + shadow_,
                    rows_ * cellHeight_ + chromeHeight() + shadow_);
        layoutChildren();
        refreshBackgroundFill();
        updateIndicator();
    }

protected:
    bool eventFilter(QObject *watched, QEvent *event) override
    {
        if (watched == parentWidget() && event->type() == QEvent::Resize) {
            // Zoom-/Zeichenraster erhalten; maximiert immer Viewport ausfuellen.
            QTimer::singleShot(0, this, [this]() {
                if (maximized_)
                    fitMaximizedToViewport();
                else
                    resizeInCharacters(requestedColumns_, requestedRows_);
            });
        } else if (event->type() == QEvent::MouseButtonPress &&
                   (watched == grip_ || watched == maximizeButton_ ||
                    watched == editor_ || watched == editor_->viewport())) {
            auto *mouse = static_cast<QMouseEvent *>(event);
            if (mouse->button() == Qt::LeftButton) {
                raise();
                if (onActivated_) onActivated_(this);
            }
        }
        if (watched == grip_) {
            if (maximized_) return QWidget::eventFilter(watched, event);
            if (event->type() == QEvent::MouseButtonPress) {
                auto *e = static_cast<QMouseEvent *>(event);
                if (e->button() == Qt::LeftButton) {
                    dragging_ = true;
                    dragPos_ = e->globalPos();
                    dragColumns_ = columns_;
                    dragRows_ = rows_;
                    return true;
                }
            } else if (event->type() == QEvent::MouseMove && dragging_) {
                auto *e = static_cast<QMouseEvent *>(event);
                const QPoint delta = e->globalPos() - dragPos_;
                const int dx = delta.x() >= 0
                    ? (delta.x() + cellWidth_/2) / cellWidth_
                    : -((-delta.x() + cellWidth_/2) / cellWidth_);
                const int dy = delta.y() >= 0
                    ? (delta.y() + cellHeight_/2) / cellHeight_
                    : -((-delta.y() + cellHeight_/2) / cellHeight_);
                resizeInCharacters(dragColumns_ + dx, dragRows_ + dy);
                return true;
            } else if (event->type() == QEvent::MouseButtonRelease && dragging_) {
                dragging_ = false;
                return true;
            }
        }
        return QWidget::eventFilter(watched, event);
    }

    // Die Titelleiste gehoert zum QWidget selbst. Die Zeichenoberflaeche
    // und die Scrollbars bleiben dadurch frei fuer ihre eigenen Mausaktionen.
    void mousePressEvent(QMouseEvent *event) override
    {
        if (event->button() == Qt::LeftButton && isTitleBarPoint(event->pos())) {
            raise();
            if (onActivated_) onActivated_(this);
            setFocus(Qt::MouseFocusReason);
            if (!maximized_) {
                moving_ = true;
                moveStartGlobal_ = event->globalPos();
                moveStartOriginX_ = originX_;
                moveStartOriginY_ = originY_;
                setCursor(Qt::SizeAllCursor);
            }
            event->accept();
            return;
        }
        QWidget::mousePressEvent(event);
    }

    void mouseMoveEvent(QMouseEvent *event) override
    {
        if (moving_ && (event->buttons() & Qt::LeftButton) && !maximized_) {
            const QPoint delta = event->globalPos() - moveStartGlobal_;
            moveWithinViewport(moveStartOriginX_ + roundToCell(delta.x(), cellWidth_),
                               moveStartOriginY_ + roundToCell(delta.y(), cellHeight_));
            event->accept();
            return;
        }
        if (!maximized_ && isTitleBarPoint(event->pos()))
            setCursor(Qt::SizeAllCursor);
        else
            unsetCursor();
        QWidget::mouseMoveEvent(event);
    }

    void mouseReleaseEvent(QMouseEvent *event) override
    {
        if (event->button() == Qt::LeftButton && moving_) {
            moving_ = false;
            unsetCursor();
            event->accept();
            return;
        }
        QWidget::mouseReleaseEvent(event);
    }

    void mouseDoubleClickEvent(QMouseEvent *event) override
    {
        if (event->button() == Qt::LeftButton && isTitleBarPoint(event->pos())) {
            toggleMaximized();
            event->accept();
            return;
        }
        QWidget::mouseDoubleClickEvent(event);
    }

    void resizeEvent(QResizeEvent *event) override
    {
        QWidget::resizeEvent(event);
        layoutChildren();
    }

    void paintEvent(QPaintEvent *) override
    {
        QPainter p(this);
        const int right = width() - shadow_ - 1;
        const int bottom = height() - shadow_ - 1;
        p.fillRect(QRect(shadow_, shadow_, width()-shadow_, height()-shadow_), QColor("#002f18"));
        p.fillRect(QRect(0, 0, right+1, bottom+1), QColor("#07552b"));
        p.setPen(QPen(QColor("#a6ffac"), 2));
        p.drawRect(1, 1, right-2, bottom-2);
        p.setPen(QPen(QColor("#49b45b"), 1));
        p.drawRect(4, 4, right-8, bottom-8);
        p.fillRect(QRect(6, 6, right-11, titleHeight()-7), QColor("#208d49"));
        p.setPen(QColor("#f0ffe1"));
        p.setFont(editor_->font());
        // Die rechte Ecke gehoert dem echten Maximieren/Restore-Button.
        p.drawText(QRect(8, 5, qMax(1, right-maxButtonWidth()-19), titleHeight()-7),
                   Qt::AlignCenter, QStringLiteral(" Ausgabe "));
    }

private:
    static int roundToCell(int delta, int cell)
    {
        cell = qMax(1, cell);
        return delta >= 0 ? ((delta + cell/2) / cell) * cell
                          : -(((-delta + cell/2) / cell) * cell);
    }

    bool isTitleBarPoint(const QPoint &point) const
    {
        return point.x() >= 5 && point.y() >= 5 &&
               point.x() < width() - shadow_ - 5 &&
               point.y() < titleHeight();
    }

    void moveWithinViewport(int x, int y)
    {
        if (!parentWidget()) {
            originX_ = qMax(0, roundToCell(x, cellWidth_));
            originY_ = qMax(0, roundToCell(y, cellHeight_));
        } else {
            const int viewportCols = qMax(1, parentWidget()->width()/cellWidth_);
            const int viewportRows = qMax(1, parentWidget()->height()/cellHeight_);
            const int visibleTitleCols = qMin(10, viewportCols);
            const int maxCol = qMin(79, qMax(0, viewportCols-visibleTitleCols));
            const int maxRow = qMin(24, viewportRows-1);
            originX_ = qBound(0, roundToCell(x, cellWidth_)/cellWidth_, maxCol)*cellWidth_;
            originY_ = qBound(0, roundToCell(y, cellHeight_)/cellHeight_, maxRow)*cellHeight_;
        }
        move(originX_, originY_);
    }

    void fitMaximizedToViewport()
    {
        if (!parentWidget() || !maximized_) return;
        originX_ = 0;
        originY_ = 0;
        const QSize available = parentWidget()->size();
        const int w = qMax(1, available.width());
        const int h = qMax(1, available.height());
        columns_ = qMax(1, (w - chromeWidth() - shadow_) / qMax(1, cellWidth_));
        rows_ = qMax(1, (h - chromeHeight() - shadow_) / qMax(1, cellHeight_));
        setGeometry(0, 0, w, h);
        layoutChildren();
        refreshBackgroundFill();
        updateIndicator();
    }

    int titleHeight() const { return cellHeight_ + 14; }
    int footerHeight() const { return cellHeight_ + 9; }
    int maxButtonWidth() const { return qMax(22, cellWidth_ * 3); }
    int chromeWidth() const { return 15 + 12; } // Rand + staendiger Scrollbalken
    int chromeHeight() const { return titleHeight() + footerHeight() + 8; }

    void layoutChildren()
    {
        if (!editor_) return;
        const int right = width() - shadow_;
        const int bottom = height() - shadow_;
        const int footer = footerHeight();
        editor_->setGeometry(7, titleHeight(), qMax(1, right-14),
                             qMax(1, bottom-titleHeight()-footer-6));
        indicator_->setGeometry(8, bottom-footer+2, qMax(1, right-35), footer-5);
        grip_->setGeometry(qMax(0,right-25), qMax(0,bottom-footer+1), 20, qMax(1,footer-5));
        if (maximizeButton_) {
            const int buttonHeight = qMax(14, cellHeight_);
            maximizeButton_->setGeometry(qMax(5, right-maxButtonWidth()-7),
                                         qMax(5, (titleHeight()-buttonHeight)/2),
                                         maxButtonWidth(), buttonHeight);
            maximizeButton_->raise();
        }
    }
    void updateIndicator()
    {
        if (!indicator_) return;
        const QTextCursor cursor = editor_->textCursor();
        indicator_->setText(QStringLiteral(" %1:%2  |  %3x%4  |  Zeichenraster")
            .arg(cursor.blockNumber()+1, 2, 10, QLatin1Char('0'))
            .arg(cursor.positionInBlock()+1, 2, 10, QLatin1Char('0'))
            .arg(columns_).arg(rows_));
    }

    void refreshBackgroundFill()
    {
        if (!backgroundFillActive_ || !editor_) return;
        const int ncols = qBound(1, columns_, 500);
        const int nrows = qBound(1, rows_, 500);
        const QString line(ncols, dosCharacter(fillCharacter_));
        QStringList lines;
        lines.reserve(nrows);
        for (int i = 0; i < nrows; ++i) lines << line;
        int currentRow = 0;
        int currentColumn = 0;
        for (const QChar letter : overlayText_) {
            if (letter == QLatin1Char('\r')) continue;
            if (letter == QLatin1Char('\n')) {
                ++currentRow;
                currentColumn = 0;
                continue;
            }
            if (currentColumn >= ncols) {
                currentColumn = 0;
                ++currentRow;
            }
            while (currentRow >= lines.size() && currentRow < 10000)
                lines << line;
            if (currentRow >= 10000) break;
            lines[currentRow][currentColumn] = letter;
            ++currentColumn;
        }
        // CSS must be updated as well: the editor stylesheet normally
        // contains the original fixed green colors.
        const QString bg = fillBackgroundColor_.name();
        const QString fg = fillForegroundColor_.name();
        editor_->setStyleSheet(QStringLiteral(
            "QPlainTextEdit#dbaseTurboVisionText{background:%1;color:%2;"
            "border:0;padding:1px;selection-background-color:#b7ef9b;"
            "selection-color:#064023;}"
            "QScrollBar:vertical{background:#06451f;width:15px;"
            "margin:15px 0px 15px 0px;border:1px solid #88e98e;}"
            "QScrollBar::groove:vertical{background:#06451f;}"
            "QScrollBar::handle:vertical{background:#55bf62;min-height:15px;border:1px solid #bcffbd;}"
            "QScrollBar::sub-line:vertical{background:#076b30;height:15px;"
            "subcontrol-position:top;subcontrol-origin:margin;border:1px solid #88e98e;}"
            "QScrollBar::add-line:vertical{background:#076b30;height:15px;"
            "subcontrol-position:bottom;subcontrol-origin:margin;border:1px solid #88e98e;}"
            "QScrollBar::add-page:vertical,QScrollBar::sub-page:vertical{background:#06451f;}"
            "QScrollBar:horizontal{background:#06451f;height:15px;"
            "margin:0px 15px 0px 15px;border:1px solid #88e98e;}"
            "QScrollBar::groove:horizontal{background:#06451f;}"
            "QScrollBar::handle:horizontal{background:#55bf62;min-width:15px;border:1px solid #bcffbd;}"
            "QScrollBar::sub-line:horizontal{background:#076b30;width:15px;"
            "subcontrol-position:left;subcontrol-origin:margin;border:1px solid #88e98e;}"
            "QScrollBar::add-line:horizontal{background:#076b30;width:15px;"
            "subcontrol-position:right;subcontrol-origin:margin;border:1px solid #88e98e;}"
            "QScrollBar::add-page:horizontal,QScrollBar::sub-page:horizontal{background:#06451f;}"
        ).arg(bg, fg));
        QPalette pal = editor_->palette();
        pal.setColor(QPalette::Base, fillBackgroundColor_);
        pal.setColor(QPalette::Text, fillForegroundColor_);
        editor_->setPalette(pal);
        editor_->setPlainText(lines.join(QLatin1Char('\n')));
        QTextCursor cursor(editor_->document());
        // Keep the last printed row visible when the filled console scrolls.
        const int cursorRow = qBound(0, currentRow, lines.size() - 1);
        const int cursorCol = qBound(0, currentColumn, ncols);
        cursor.setPosition(qMin(editor_->document()->characterCount() - 1,
                                cursorRow * (ncols + 1) + cursorCol));
        editor_->setTextCursor(cursor);
        editor_->ensureCursorVisible();
        updateIndicator();
    }

    QColor fillBackgroundColor_ = QColor("#076b30");
    QColor fillForegroundColor_ = QColor("#e8ffcb");
    bool backgroundFillActive_ = false;
    int fillCharacter_ = 32;
    QString overlayText_;

    std::function<void(D64TurboOutputWidget *)> onActivated_;
    QPlainTextEdit *editor_ = nullptr;
    QLabel *indicator_ = nullptr;
    QLabel *grip_ = nullptr;
    QToolButton *maximizeButton_ = nullptr;
    int columns_ = 58;
    int rows_ = 15;
    int requestedColumns_ = 58;
    int requestedRows_ = 15;
    int cellWidth_ = 8;
    int cellHeight_ = 16;
    int originX_ = 14;
    int originY_ = 16;
    static constexpr int shadow_ = 7;
    bool dragging_ = false;
    QPoint dragPos_;
    int dragColumns_ = 58;
    int dragRows_ = 15;
    bool moving_ = false;
    bool maximized_ = false;
    QPoint moveStartGlobal_;
    int moveStartOriginX_ = 14;
    int moveStartOriginY_ = 16;
    int restoreOriginX_ = 14;
    int restoreOriginY_ = 16;
    int restoreColumns_ = 58;
    int restoreRows_ = 15;
};
