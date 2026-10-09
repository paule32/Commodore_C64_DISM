// Stage 317: Qt5-gezeichnete Titelleiste fuer Debug-QDialog (kein Q_OBJECT).
// Eigenes QWidget empfaengt die Mausereignisse fuer Fensterbuttons und Drag;
// die Windows-HTCAPTION-Abhaengigkeit entfällt. Vollstaendig Qt5-gezeichnet.
#pragma once

#include <QColor>
#include <QFont>
#include <QLinearGradient>
#include <QMouseEvent>
#include <QCursor>
#include <QPaintEvent>
#include <QPainter>
#include <QPen>
#include <QRect>
#include <QWidget>

class D64DebugTitleSurface final : public QWidget
{
public:
    explicit D64DebugTitleSurface(int titleHeight, bool withDbLogo,
                                  QWidget *parent = nullptr)
        : QWidget(parent), height_(titleHeight), withDbLogo_(withDbLogo)
    {
        setObjectName(QStringLiteral("d64DebugCustomTitleSurface"));
        setAttribute(Qt::WA_TransparentForMouseEvents, false);
        setMouseTracking(true);
        setAttribute(Qt::WA_Hover, true);
        setAttribute(Qt::WA_StyledBackground, false);
        setAutoFillBackground(false);
        setFocusPolicy(Qt::NoFocus);
        setGeometry(0, 3, parent ? parent->width() : 0, qMax(0, height_ - 3));
        show();
    }

    void setDarkChrome(bool dark)
    {
        if (dark_ == dark) return;
        dark_ = dark;
        update();
    }

    void setHoverButton(int button)
    {
        if (hoverButton_ == button) return;
        hoverButton_ = button;
        update();
    }

    void syncGeometry(bool maximized)
    {
        const int h = qMax(0, height_ - 3);
        if (parentWidget()) setGeometry(0, 3, parentWidget()->width(), h);
        if (maximized_ != maximized) {
            maximized_ = maximized;
            update();
        }
        raise();
    }

protected:
    // Das Titel-Widget bekommt die Qt5-Events selbst. Wird HTCAPTION benutzt,
    // erreicht der Mausdruck auf Windows die Qt5-Kindkomponente nicht mehr.
    void mousePressEvent(QMouseEvent *event) override
    {
        if (!event || event->button() != Qt::LeftButton) {
            QWidget::mousePressEvent(event);
            return;
        }
        QWidget *host = window();
        if (!host) return;
        const int button = buttonAt(event->pos());
        if (button == 1) host->showMinimized();
        else if (button == 2) {
            host->isMaximized() ? host->showNormal() : host->showMaximized();
            syncGeometry(host->isMaximized());
        }
        else if (button == 3) host->hide();
        else if (!host->isMaximized()) {
            dragging_ = true;
            originGlobal_ = event->globalPos();
            originPos_ = host->pos();
            grabMouse(QCursor(Qt::ArrowCursor));
        }
        event->accept();
    }

    void mouseMoveEvent(QMouseEvent *event) override
    {
        if (!event) return;
        QWidget *host = window();
        if (dragging_ && host && (event->buttons() & Qt::LeftButton)) {
            host->move(originPos_ + event->globalPos() - originGlobal_);
            event->accept();
            return;
        }
        if (!dragging_) {
            const int hovered = buttonAt(event->pos());
            setHoverButton(hovered);
            setCursor(Qt::ArrowCursor);
        }
        QWidget::mouseMoveEvent(event);
    }

    void mouseReleaseEvent(QMouseEvent *event) override
    {
        if (event && event->button() == Qt::LeftButton && dragging_) {
            dragging_ = false;
            releaseMouse();
            event->accept();
            return;
        }
        QWidget::mouseReleaseEvent(event);
    }

    void mouseDoubleClickEvent(QMouseEvent *event) override
    {
        if (event && event->button() == Qt::LeftButton) {
            if (dragging_) { dragging_ = false; releaseMouse(); }
            QWidget *host = window();
            if (host && buttonAt(event->pos()) == 0) {
                host->isMaximized() ? host->showNormal() : host->showMaximized();
                syncGeometry(host->isMaximized());
            }
            event->accept();
            return;
        }
        QWidget::mouseDoubleClickEvent(event);
    }

    void leaveEvent(QEvent *event) override
    {
        if (!dragging_) setHoverButton(0);
        QWidget::leaveEvent(event);
    }

    void paintEvent(QPaintEvent *) override
    {
        QPainter painter(this);
        painter.setRenderHint(QPainter::Antialiasing, false);
        // Die 3px-Aussenkanten zeichnet weiterhin das Elternfenster.
        QLinearGradient gradient(3, 0, qMax(3, width() - 3), 0);
        if (dark_) {
            gradient.setColorAt(0.0, QColor(0, 0, 0));
            gradient.setColorAt(1.0, QColor(105, 105, 105));
        } else {
            gradient.setColorAt(0.0, QColor(218, 218, 218));
            gradient.setColorAt(1.0, QColor(244, 244, 244));
        }
        painter.fillRect(QRect(3, 0, qMax(0, width() - 6), height()), gradient);

        constexpr int buttonWidth = 46;
        const QRect minRect(width() - 3 * buttonWidth, 0, buttonWidth, height());
        const QRect maxRect(width() - 2 * buttonWidth, 0, buttonWidth, height());
        const QRect closeRect(width() - buttonWidth, 0, buttonWidth, height());
        if (hoverButton_ == 1) painter.fillRect(minRect, QColor(0, 90, 185));
        if (hoverButton_ == 2) painter.fillRect(maxRect, QColor(0, 145, 70));
        if (hoverButton_ == 3) painter.fillRect(closeRect, QColor(205, 35, 35));

        const QColor ink = dark_ ? QColor(255, 255, 255) : QColor(25, 25, 25);
        int titleX = 12;
        if (withDbLogo_) {
            const QRect logo(8, qMax(0, (height() - 20) / 2), 20, 20);
            painter.setPen(QPen(QColor(230, 230, 230), 1));
            painter.setBrush(QColor(0, 115, 80));
            painter.drawRoundedRect(logo, 3, 3);
            painter.setFont(QFont(QStringLiteral("Segoe UI"), 7, QFont::Bold));
            painter.setPen(Qt::white);
            painter.drawText(logo, Qt::AlignCenter, QStringLiteral("db"));
            titleX = 34;
        }
        painter.setBrush(Qt::NoBrush);
        painter.setFont(QFont(QStringLiteral("Segoe UI"), 9));
        painter.setPen(ink);
        painter.drawText(QRect(titleX, 0, qMax(0, width() - titleX - 3 * buttonWidth), height()),
                         Qt::AlignVCenter | Qt::AlignLeft, QStringLiteral("Debug"));

        // Vektorglyphen: unabhaengig von Segoe-MDL2-/Windows-Schriftpaketen.
        // Koordinaten werden auf Pixel gerundet, keine unklaren Unicode-Glyphen.
        const auto glyph = [&](const QRect &button, int kind) {
            const QPoint center = button.center();
            painter.setPen(QPen(ink, 1.5));
            if (kind == 1) {
                painter.drawLine(center.x() - 5, center.y() + 4,
                                 center.x() + 5, center.y() + 4);
            } else if (kind == 2 && maximized_) {
                painter.drawRect(QRect(center.x() - 5, center.y() - 2, 9, 8));
                painter.drawLine(center.x() - 3, center.y() - 4,
                                 center.x() + 6, center.y() - 4);
                painter.drawLine(center.x() + 6, center.y() - 4,
                                 center.x() + 6, center.y() + 3);
            } else if (kind == 2) {
                painter.drawRect(QRect(center.x() - 5, center.y() - 4, 10, 9));
            } else {
                painter.drawLine(center.x() - 5, center.y() - 5,
                                 center.x() + 5, center.y() + 5);
                painter.drawLine(center.x() + 5, center.y() - 5,
                                 center.x() - 5, center.y() + 5);
            }
        };
        glyph(minRect, 1);
        glyph(maxRect, 2);
        glyph(closeRect, 3);
    }

private:
    int buttonAt(const QPoint &p) const
    {
        constexpr int buttonWidth = 46;
        if (p.x() < width() - 3 * buttonWidth || p.y() < 0 || p.y() >= height())
            return 0;
        if (p.x() < width() - 2 * buttonWidth) return 1;
        if (p.x() < width() - buttonWidth) return 2;
        return 3;
    }

    QPoint originGlobal_;
    QPoint originPos_;
    bool dragging_ = false;
    int height_ = 32;
    bool withDbLogo_ = false;
    bool dark_ = false;
    bool maximized_ = false;
    int hoverButton_ = 0;
};
