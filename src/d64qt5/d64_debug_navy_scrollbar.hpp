// Stage 316: Eigengezeichnete gelbe Pfeile auf navyblauen Qt5-Debugscrollbars.
#pragma once
#include <QPainter>
#include <QPaintEvent>
#include <QPolygon>
#include <QScrollBar>

class D64DebugNavyScrollBar final : public QScrollBar
{
public:
    explicit D64DebugNavyScrollBar(Qt::Orientation orientation, QWidget *parent = nullptr)
        : QScrollBar(orientation, parent)
    {
        setMouseTracking(true);
        setAttribute(Qt::WA_Hover, true);
    }

protected:
    void paintEvent(QPaintEvent *event) override
    {
        QScrollBar::paintEvent(event);
        QPainter painter(this);
        painter.setPen(Qt::NoPen);
        painter.setBrush(QColor(255, 216, 0)); // #ffd800
        if (orientation() == Qt::Vertical) {
            const int n = qMin(16, height()/2);
            arrow(painter, QRect(0,0,width(),n), Qt::UpArrow);
            arrow(painter, QRect(0,height()-n,width(),n), Qt::DownArrow);
        } else {
            const int n = qMin(16, width()/2);
            arrow(painter, QRect(0,0,n,height()), Qt::LeftArrow);
            arrow(painter, QRect(width()-n,0,n,height()), Qt::RightArrow);
        }
    }
private:
    static void arrow(QPainter &p, const QRect &rect, Qt::ArrowType dir)
    {
        if (rect.width() < 5 || rect.height() < 5) return;
        const QPoint c = rect.center();
        const int d = qMax(2, qMin(4, qMin(rect.width(),rect.height())/3));
        QPolygon poly;
        switch (dir) {
        case Qt::UpArrow:
            poly << QPoint(c.x(),c.y()-d) << QPoint(c.x()-d,c.y()+d) << QPoint(c.x()+d,c.y()+d);
            break;
        case Qt::DownArrow:
            poly << QPoint(c.x()-d,c.y()-d) << QPoint(c.x()+d,c.y()-d) << QPoint(c.x(),c.y()+d);
            break;
        case Qt::LeftArrow:
            poly << QPoint(c.x()-d,c.y()) << QPoint(c.x()+d,c.y()-d) << QPoint(c.x()+d,c.y()+d);
            break;
        case Qt::RightArrow:
            poly << QPoint(c.x()+d,c.y()) << QPoint(c.x()-d,c.y()-d) << QPoint(c.x()-d,c.y()+d);
            break;
        default: return;
        }
        p.drawPolygon(poly);
    }
};
