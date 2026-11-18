#pragma once

// Stage 630: Turbo-Vision-Scrollbar mit eigener gemeinsamer Geometrie fuer
// Pfeile, punktierte Rille, Thumb und Maushitbox. Keine QStyleSheet-Subcontrols
// mehr fuer die Zeichnung/Bedienung: Der Thumb kann die Pfeile nicht ueberdecken.
// Das native QScrollBar-Modell (Range, Value, Wheel, Keyboard, Signals) bleibt.
#include "d64_turbo_scroll_geometry.hpp"
#include <QScrollBar>
#include <QPaintEvent>
#include <QPainter>
#include <QPolygon>
#include <QColor>
#include <QMouseEvent>
#include <QtGlobal>

class D64TurboArrowScrollBar final : public QScrollBar
{
public:
    explicit D64TurboArrowScrollBar(Qt::Orientation orientation, QWidget *parent = nullptr)
        : QScrollBar(orientation, parent) {}

    void setArrowColor(const QColor &color) { arrowColor_ = color; update(); }
    void setArrowBackground(const QColor &color) { arrowBackground_ = color; update(); }

    // Das blaue Editorfenster verwendet in beiden Richtungen exakt dieselbe
    // graue Thumb-/punktierte Rillen-Zeichnung. Pfeilfelder bleiben vollblau.
    void setTurboEditorTheme()
    {
        arrowColor_ = QColor(QStringLiteral("#ffff55"));
        arrowBackground_ = QColor(QStringLiteral("#0000aa"));
        grooveBackground_ = QColor(QStringLiteral("#000080"));
        grooveDot_ = QColor(QStringLiteral("#9999ad"));
        thumbBackground_ = QColor(QStringLiteral("#686868"));
        thumbLight_ = QColor(QStringLiteral("#bababa"));
        thumbDark_ = QColor(QStringLiteral("#353535"));
        borderColor_ = QColor(QStringLiteral("#ffff55"));
        dottedGroove_ = true;
        update();
    }

protected:
    void paintEvent(QPaintEvent *event) override
    {
        Q_UNUSED(event);
        const D64TurboScrollGeometry g = geometryForCurrentValue();
        if (g.axisExtent <= 0) return;

        QPainter painter(this);
        painter.setRenderHint(QPainter::Antialiasing, false);
        painter.fillRect(rect(), arrowBackground_);

        const QRect groove = grooveRect(g);
        if (!groove.isEmpty()) {
            painter.fillRect(groove, grooveBackground_);
            if (dottedGroove_) {
                painter.save();
                painter.setClipRect(groove);
                painter.setPen(grooveDot_);
                // DOS-artige Punktstruktur; nur im Bereich ZWISCHEN den Pfeilen.
                for (int y = groove.top() + 1; y <= groove.bottom(); y += 3)
                    for (int x = groove.left() + 1 + ((y / 3) % 2); x <= groove.right(); x += 3)
                        painter.drawPoint(x, y);
                painter.restore();
            }

            const QRect thumb = thumbRect(g);
            if (!thumb.isEmpty()) {
                painter.save();
                painter.setClipRect(groove); // harte Grenze gegen beide Pfeile
                painter.fillRect(thumb, isEnabled() ? thumbBackground_ : thumbBackground_.darker(130));
                painter.setPen(thumbLight_);
                painter.drawLine(thumb.topLeft(), thumb.topRight());
                painter.drawLine(thumb.topLeft(), thumb.bottomLeft());
                painter.setPen(thumbDark_);
                painter.drawLine(thumb.bottomLeft(), thumb.bottomRight());
                painter.drawLine(thumb.topRight(), thumb.bottomRight());
                painter.restore();
            }
        }

        paintArrow(painter, arrowStartRect(g), true);
        paintArrow(painter, arrowEndRect(g), false);
        painter.setPen(borderColor_);
        if (width() > 1 && height() > 1)
            painter.drawRect(rect().adjusted(0, 0, -1, -1));
    }

    void mousePressEvent(QMouseEvent *event) override
    {
        if (event->button() != Qt::LeftButton) {
            QScrollBar::mousePressEvent(event);
            return;
        }
        event->accept();
        if (!isEnabled()) return;
        const D64TurboScrollGeometry g = geometryForCurrentValue();
        const int coordinate = axisCoordinate(event->pos());
        const QRect thumb = thumbRect(g);
        if (arrowStartRect(g).contains(event->pos())) {
            triggerAction(QAbstractSlider::SliderSingleStepSub);
            setRepeatAction(QAbstractSlider::SliderSingleStepSub, 350, 70);
        } else if (arrowEndRect(g).contains(event->pos())) {
            triggerAction(QAbstractSlider::SliderSingleStepAdd);
            setRepeatAction(QAbstractSlider::SliderSingleStepAdd, 350, 70);
        } else if (thumb.contains(event->pos()) && maximum() > minimum()) {
            draggingThumb_ = true;
            dragOffset_ = coordinate - g.thumbStart;
            setSliderDown(true);
        } else if (coordinate < g.thumbStart) {
            triggerAction(QAbstractSlider::SliderPageStepSub);
            setRepeatAction(QAbstractSlider::SliderPageStepSub, 350, 70);
        } else if (coordinate >= g.thumbEnd()) {
            triggerAction(QAbstractSlider::SliderPageStepAdd);
            setRepeatAction(QAbstractSlider::SliderPageStepAdd, 350, 70);
        }
    }

    void mouseMoveEvent(QMouseEvent *event) override
    {
        if (!draggingThumb_) {
            QScrollBar::mouseMoveEvent(event);
            return;
        }
        const D64TurboScrollGeometry g = geometryForCurrentValue();
        setSliderPosition(g.valueForThumbStart(axisCoordinate(event->pos()) - dragOffset_));
        event->accept();
    }

    void mouseReleaseEvent(QMouseEvent *event) override
    {
        if (event->button() != Qt::LeftButton) {
            QScrollBar::mouseReleaseEvent(event);
            return;
        }
        setRepeatAction(QAbstractSlider::SliderNoAction);
        if (draggingThumb_) {
            draggingThumb_ = false;
            setSliderDown(false);
        }
        event->accept();
    }

private:
    int axisCoordinate(const QPoint &pos) const
    { return orientation() == Qt::Vertical ? pos.y() : pos.x(); }

    D64TurboScrollGeometry geometryForCurrentValue() const
    {
        const bool vertical = orientation() == Qt::Vertical;
        return d64TurboScrollGeometry(vertical ? height() : width(),
                                      vertical ? width() : height(),
                                      minimum(), maximum(), pageStep(), sliderPosition());
    }

    QRect grooveRect(const D64TurboScrollGeometry &g) const
    {
        return orientation() == Qt::Vertical
            ? QRect(0, g.grooveStart, width(), g.grooveExtent)
            : QRect(g.grooveStart, 0, g.grooveExtent, height());
    }

    QRect thumbRect(const D64TurboScrollGeometry &g) const
    {
        return orientation() == Qt::Vertical
            ? QRect(1, g.thumbStart, qMax(0, width() - 2), g.thumbExtent)
            : QRect(g.thumbStart, 1, g.thumbExtent, qMax(0, height() - 2));
    }

    QRect arrowStartRect(const D64TurboScrollGeometry &g) const
    {
        return orientation() == Qt::Vertical
            ? QRect(0, 0, width(), g.buttonExtent)
            : QRect(0, 0, g.buttonExtent, height());
    }

    QRect arrowEndRect(const D64TurboScrollGeometry &g) const
    {
        return orientation() == Qt::Vertical
            ? QRect(0, g.arrowEndStart(), width(), g.buttonExtent)
            : QRect(g.arrowEndStart(), 0, g.buttonExtent, height());
    }

    void paintArrow(QPainter &painter, const QRect &button, bool decrement)
    {
        if (button.width() < 5 || button.height() < 5) return;
        painter.save();
        painter.setClipRect(button);
        painter.fillRect(button, arrowBackground_); // ganzflaechig blau im Editor
        painter.setPen(Qt::NoPen);
        painter.setBrush(isEnabled() ? arrowColor_ : arrowColor_.darker(170));
        const QPoint center = button.center();
        const int radius = qMax(1, qMin(5, qMin(button.width(), button.height()) / 3));
        QPolygon polygon;
        if (orientation() == Qt::Vertical) {
            if (decrement)
                polygon << QPoint(center.x(), center.y()-radius)
                        << QPoint(center.x()-radius, center.y()+radius)
                        << QPoint(center.x()+radius, center.y()+radius);
            else
                polygon << QPoint(center.x()-radius, center.y()-radius)
                        << QPoint(center.x()+radius, center.y()-radius)
                        << QPoint(center.x(), center.y()+radius);
        } else {
            if (decrement)
                polygon << QPoint(center.x()-radius, center.y())
                        << QPoint(center.x()+radius, center.y()-radius)
                        << QPoint(center.x()+radius, center.y()+radius);
            else
                polygon << QPoint(center.x()-radius, center.y()-radius)
                        << QPoint(center.x()+radius, center.y())
                        << QPoint(center.x()-radius, center.y()+radius);
        }
        painter.drawPolygon(polygon);
        painter.restore();
    }

    QColor arrowColor_ = QColor(QStringLiteral("#ffff55"));
    QColor arrowBackground_ = QColor(QStringLiteral("#076b30"));
    QColor grooveBackground_ = QColor(QStringLiteral("#06451f"));
    QColor grooveDot_ = QColor(QStringLiteral("#85b78c"));
    QColor thumbBackground_ = QColor(QStringLiteral("#55bf62"));
    QColor thumbLight_ = QColor(QStringLiteral("#bcffbd"));
    QColor thumbDark_ = QColor(QStringLiteral("#245c31"));
    QColor borderColor_ = QColor(QStringLiteral("#88e98e"));
    bool dottedGroove_ = false;
    bool draggingThumb_ = false;
    int dragOffset_ = 0;
};
