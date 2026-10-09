// ---------------------------------------------------------------------------
// File:   workstation_runner.cpp
// Author: (c) 2026 Jens Kallup - paule32
// All rights reserved
// ---------------------------------------------------------------------------
// Generic Workstation host/launcher for PE32/PE32+ programs which do not
// initialize d64qt5 themselves.  The authoritative Workstation lifecycle stays
// in the existing d64_workstation.cpp (OWNER/JOINED/Desktop/Panel/EXIT).
// ---------------------------------------------------------------------------
#include "d64_workstation.h"
#include "d64_debug_title_surface.hpp"
#include "d64_debug_context_menu.hpp"

#ifdef _WIN32
#  define WIN32_LEAN_AND_MEAN
#  include <windows.h>
#  include <shellapi.h>
#endif

#include <QApplication>
#include <QDialog>
#include <QEventLoop>
#include <QFontDatabase>
#include <QCloseEvent>
#include <QCursor>
#include <QLinearGradient>
#include <QMouseEvent>
#include <QMoveEvent>
#include <QPainter>
#include <QPalette>
#include <QPaintEvent>
#include <QPolygon>
#include <QProxyStyle>
#include <QPushButton>
#include <QLabel>
#include <QHBoxLayout>
#include <QStyle>
#include <QStyleOption>
#include <QPlainTextEdit>
#include <QResizeEvent>
#include <QShowEvent>
#include <QScreen>
#include <QScrollBar>
#include <QTextCursor>
#include <QTimer>
#include <QVBoxLayout>

#include <algorithm>
#include <atomic>
#include <cstdint>
#include <cwchar>
#include <cwctype>
#include <functional>
#include <memory>
#include <string>
#include <thread>
#include <vector>

namespace {

constexpr wchar_t RUNNER_WINDOW_CLASS[] = L"D64WorkstationRunnerWindow";
constexpr wchar_t RUNNER_WINDOW_TITLE[] = L"D64 Workstation Runner";
constexpr wchar_t RUNNER_PIPE_NAME[] = L"\\\\.\\pipe\\dBase2Many.D64Workstation.Runner.v1";
// Stage 271: Child-Runtimes erkennen an dieser geerbten Variablen, dass
// Write/WriteLn zusaetzlich in das zentrale Workstation-DEBUG-Fenster
// gespiegelt werden sollen. Der normale Console-Ausgabepfad bleibt erhalten.
constexpr wchar_t RUNNER_DEBUG_OUTPUT_ENV[] = L"D64_WORKSTATION_DEBUG_OUTPUT";
constexpr std::uint32_t RUNNER_PIPE_MAGIC = 0x31525744u; // "DWR1"
constexpr std::uint32_t RUNNER_OUTPUT_MAGIC = 0x31574F44u; // "DOW1"
constexpr std::uint32_t RUNNER_OUTPUT_NEWLINE = 0x00000001u;
constexpr std::uint32_t RUNNER_LAUNCH_CONSOLE             = 0x00000001u;
constexpr std::uint32_t RUNNER_LAUNCH_THEME_PRESENT       = 0x00000002u;
constexpr std::uint32_t RUNNER_LAUNCH_THEME_DARK          = 0x00000004u;
constexpr std::uint32_t RUNNER_LAUNCH_DEBUG_THEME_PRESENT = 0x00000008u;
constexpr std::uint32_t RUNNER_LAUNCH_DEBUG_THEME_LIGHT   = 0x00000010u;
constexpr std::uint32_t RUNNER_LAUNCH_DEBUG_THEME_DARK    = 0x00000020u;
// Stage 274: GUI-Console-Starts laufen im Workstation Mode ohne sichtbare
// Win32-Konsole. Der Runner faengt STDOUT/STDERR direkt ab und schreibt die
// Bytes in das residente DEBUG-Fenster; die Ziel-Runtime muss DOW1 nicht kennen.
constexpr std::uint32_t RUNNER_LAUNCH_DEBUG_CONSOLE_ONLY  = 0x00000040u;
constexpr std::uint32_t RUNNER_OUTPUT_THEME_PRESENT       = 0x00000002u;
constexpr std::uint32_t RUNNER_OUTPUT_THEME_LIGHT         = 0x00000004u;
constexpr std::uint32_t RUNNER_OUTPUT_THEME_DARK          = 0x00000008u;
constexpr std::uint32_t RUNNER_OUTPUT_LATIN1              = 0x00000010u;
constexpr std::uint32_t RUNNER_OUTPUT_DEBUG_SHOW          = 0x00000020u;
constexpr std::uint32_t RUNNER_OUTPUT_DEBUG_HIDE          = 0x00000040u;
constexpr UINT WM_RUNNER_LAUNCH = WM_APP + 0x321;
constexpr UINT WM_RUNNER_EXIT   = WM_APP + 0x322;
constexpr UINT WM_RUNNER_OUTPUT = WM_APP + 0x323;
constexpr UINT_PTR RUNNER_TIMER = 0xD641;

constexpr wchar_t D64_APP_WINDOW_PREFIX[] = L"dBase2Many.D64ApplicationWindow.";
constexpr wchar_t WORKSTATION_PANEL_CLASS[] = L"D64WorkstationPanel";
constexpr wchar_t WORKSTATION_BOTTOM_PANEL_CLASS[] = L"D64WorkstationBottomPanel";
constexpr wchar_t WORKSTATION_TOOL_WINDOW_PROPERTY[] = L"D64Workstation.ToolWindow";
constexpr char D64_LAZY_CONSOLE_MARKER[] = "D64DBASE_LAZY_CONSOLE_V1";
constexpr char D64_WFM_QT_OUTPUT_MARKER[] = "D64DBASE_WFM_QT_OUTPUT_V1";

constexpr int WORKSTATION_PANEL_WIDTH = 76;
constexpr int WORKSTATION_DB_CLICK_TOP = 176;
constexpr int WORKSTATION_ITEM_HEIGHT = 86;

struct PipeHeader {
    std::uint32_t magic;
    std::uint32_t flags;
    std::uint32_t pathBytes;
    std::uint32_t cwdBytes;
};

struct LaunchRequest {
    std::wstring application;
    std::wstring workingDirectory;
    bool consoleMode = false;
    bool debugConsoleOnly = false; // Stage 274: keine sichtbare Console, STDOUT/STDERR -> DEBUG-Fenster
    int themeMode = -1;      // Workstation-Chrome: -1 unveraendert, 0 light, 1 dark
    int debugThemeMode = -1; // Debugfenster: -1 unveraendert, 0 default, 1 light, 2 dark
};

struct OutputMessage {
    std::string text;
    bool newline = false;
    bool latin1 = false;
    DWORD processId = 0;
    int debugThemeMode = -1;
    int debugVisibility = -1; // -1 = Text, 0 = SET DEBUG OFF, 1 = ON
};

// Stage 129: Echte, transparente Maus-Handles fuer die acht sichtbaren
// Resize-Stellen. Dadurch koennen Child-Widgets (z.B. QPlainTextEdit) die
// Mausereignisse am Fensterrand nicht mehr verschlucken. Die Handles sind nur
// beim aktiven Fenster sichtbar/bedienbar und tragen den passenden Cursor.
class WorkstationResizeHandle final : public QWidget
{
public:
    WorkstationResizeHandle(QWidget *host, int hitCode)
        : QWidget(host), host_(host), hitCode_(hitCode)
    {
        // Stage 130: Die Catch-Zone ist ein echtes 5x5-Qt-Widget im
        // Clientbereich. Mouse tracking sorgt fuer den passenden Cursor ohne
        // gedrueckte Taste; der Drag selbst laeuft rein ueber Qt-Geometrie.
        setMouseTracking(true);
        setAttribute(Qt::WA_NoSystemBackground, true);
        setAttribute(Qt::WA_TransparentForMouseEvents, false);
        setAutoFillBackground(false);
        setFocusPolicy(Qt::NoFocus);
        setCursor(cursorForHitCode(hitCode_));
        hide();
    }

protected:
    void mousePressEvent(QMouseEvent *event) override
    {
        if (
            event && event->button() == Qt::LeftButton && host_ &&
            !host_->isMaximized()
        ) {
            resizing_ = true;
            pressGlobal_ = event->globalPos();
            startGeometry_ = host_->geometry();
            grabMouse(QCursor(cursorForHitCode(hitCode_)));
            event->accept();
            return;
        }
        QWidget::mousePressEvent(event);
    }

    void mouseMoveEvent(QMouseEvent *event) override
    {
        if (resizing_ && event && host_) {
            const QPoint delta = event->globalPos() - pressGlobal_;
            QRect next = startGeometry_;

            const int minWidth = qMax(80, qMax(host_->minimumWidth(), host_->minimumSizeHint().width()));
            const int minHeight = qMax(60, qMax(host_->minimumHeight(), host_->minimumSizeHint().height()));

            int left = startGeometry_.left();
            int right = startGeometry_.right();
            int top = startGeometry_.top();
            int bottom = startGeometry_.bottom();

            if (movesLeft())
                left = qMin(startGeometry_.left() + delta.x(), right - minWidth + 1);
            if (movesRight())
                right = qMax(startGeometry_.right() + delta.x(), left + minWidth - 1);
            if (movesTop())
                top = qMin(startGeometry_.top() + delta.y(), bottom - minHeight + 1);
            if (movesBottom())
                bottom = qMax(startGeometry_.bottom() + delta.y(), top + minHeight - 1);

            next.setCoords(left, top, right, bottom);
            host_->setGeometry(next);
            host_->update();
            event->accept();
            return;
        }
        QWidget::mouseMoveEvent(event);
    }

    void mouseReleaseEvent(QMouseEvent *event) override
    {
        if (resizing_ && event && event->button() == Qt::LeftButton) {
            resizing_ = false;
            releaseMouse();
            event->accept();
            return;
        }
        QWidget::mouseReleaseEvent(event);
    }

private:
    bool movesLeft() const
    {
        return hitCode_ == HTLEFT || hitCode_ == HTTOPLEFT || hitCode_ == HTBOTTOMLEFT;
    }
    bool movesRight() const
    {
        return hitCode_ == HTRIGHT || hitCode_ == HTTOPRIGHT || hitCode_ == HTBOTTOMRIGHT;
    }
    bool movesTop() const
    {
        return hitCode_ == HTTOP || hitCode_ == HTTOPLEFT || hitCode_ == HTTOPRIGHT;
    }
    bool movesBottom() const
    {
        return hitCode_ == HTBOTTOM || hitCode_ == HTBOTTOMLEFT || hitCode_ == HTBOTTOMRIGHT;
    }

    static Qt::CursorShape cursorForHitCode(int hitCode)
    {
        switch (hitCode) {
        case HTLEFT:
        case HTRIGHT:
            return Qt::SizeHorCursor;
        case HTTOP:
        case HTBOTTOM:
            return Qt::SizeVerCursor;
        case HTTOPLEFT:
        case HTBOTTOMRIGHT:
            return Qt::SizeFDiagCursor;
        case HTTOPRIGHT:
        case HTBOTTOMLEFT:
            return Qt::SizeBDiagCursor;
        default:
            return Qt::ArrowCursor;
        }
    }

    QWidget *host_ = nullptr;
    int hitCode_ = HTNOWHERE;
    bool resizing_ = false;
    QPoint pressGlobal_;
    QRect startGeometry_;
};

// Stage 278: Die Scrollbars des DEBUG-QPlainTextEdit werden komplett durch
// diesen Proxy-Style gezeichnet. In Stage 275 wurden nur die Pfeil-Primitives
// ueberschrieben. Sobald der Style direkt auf QScrollBar gesetzt war, konnte
// deshalb der native Windows-Style den eigentlichen Kanal und Griff weiterhin
// grau zeichnen. Jetzt kommen Kanal, Buttons, Griff UND Pfeile aus einer Hand.
class WorkstationScrollBarStyle final : public QProxyStyle
{
public:
    WorkstationScrollBarStyle()
        : QProxyStyle()
    {
    }

    int pixelMetric(
        PixelMetric metric,
        const QStyleOption *option = nullptr,
        const QWidget *widget = nullptr
    ) const override
    {
        if (metric == PM_ScrollBarExtent)
            return 16;
        if (metric == PM_ScrollBarSliderMin)
            return 24;
        return QProxyStyle::pixelMetric(metric, option, widget);
    }

    void drawComplexControl(
        ComplexControl control,
        const QStyleOptionComplex *option,
        QPainter *painter,
        const QWidget *widget = nullptr
    ) const override
    {
        if (control != CC_ScrollBar || !option || !painter) {
            QProxyStyle::drawComplexControl(control, option, painter, widget);
            return;
        }

        const QStyleOptionSlider *slider =
            qstyleoption_cast<const QStyleOptionSlider *>(option);
        if (!slider) {
            QProxyStyle::drawComplexControl(control, option, painter, widget);
            return;
        }

        const QColor trackColor(6, 21, 43);       // #06152b
        const QColor buttonColor(6, 27, 58);      // #061b3a
        const QColor handleColor(11, 47, 99);     // #0b2f63
        const QColor handleHover(18, 68, 126);    // #12447e
        const QColor handlePressed(14, 55, 108);  // #0e376c
        const QColor borderColor(36, 77, 122);    // #244d7a
        const QColor hoverBorder(255, 216, 0);    // #ffd800

        painter->save();
        painter->setRenderHint(QPainter::Antialiasing, false);

        // Niemals den nativen Style den Scrollbar-Hintergrund zeichnen lassen.
        painter->fillRect(slider->rect, trackColor);

        const QRect groove = subControlRect(
            CC_ScrollBar, slider, SC_ScrollBarGroove, widget
        );
        const QRect knob = subControlRect(
            CC_ScrollBar, slider, SC_ScrollBarSlider, widget
        );
        const QRect subLine = subControlRect(
            CC_ScrollBar, slider, SC_ScrollBarSubLine, widget
        );
        const QRect addLine = subControlRect(
            CC_ScrollBar, slider, SC_ScrollBarAddLine, widget
        );

        if (groove.isValid())
            painter->fillRect(groove, trackColor);

        auto drawBox = [&](const QRect &rect, const QColor &fill, const QColor &border) {
            if (!rect.isValid() || rect.isEmpty())
                return;
            painter->fillRect(rect, fill);
            painter->setPen(QPen(border, 1));
            painter->setBrush(Qt::NoBrush);
            painter->drawRect(rect.adjusted(0, 0, -1, -1));
        };

        drawBox(subLine, buttonColor, borderColor);
        drawBox(addLine, buttonColor, borderColor);

        const bool sliderHover =
            (slider->state & State_MouseOver) &&
            (slider->activeSubControls & SC_ScrollBarSlider);
        const bool sliderPressed =
            (slider->state & State_Sunken) &&
            (slider->activeSubControls & SC_ScrollBarSlider);

        QColor knobColor = handleColor;
        QColor knobBorder = borderColor;
        if (sliderPressed) {
            knobColor = handlePressed;
            knobBorder = hoverBorder;
        } else if (sliderHover) {
            knobColor = handleHover;
            knobBorder = hoverBorder;
        }
        drawBox(knob, knobColor, knobBorder);

        // Die vier Pfeile werden absichtlich selbst gezeichnet. Damit bleiben
        // sie auch bei Windows High-Contrast-/Fusion-/Native-Styles gelb.
        if (slider->orientation == Qt::Vertical) {
            drawYellowArrow(PE_IndicatorArrowUp, subLine, painter);
            drawYellowArrow(PE_IndicatorArrowDown, addLine, painter);
        } else {
            drawYellowArrow(PE_IndicatorArrowLeft, subLine, painter);
            drawYellowArrow(PE_IndicatorArrowRight, addLine, painter);
        }

        painter->setPen(QPen(borderColor, 1));
        painter->setBrush(Qt::NoBrush);
        painter->drawRect(slider->rect.adjusted(0, 0, -1, -1));
        painter->restore();
    }

    void drawPrimitive(
        PrimitiveElement element,
        const QStyleOption *option,
        QPainter *painter,
        const QWidget *widget = nullptr
    ) const override
    {
        if (option && painter &&
            (element == PE_IndicatorArrowUp ||
             element == PE_IndicatorArrowDown ||
             element == PE_IndicatorArrowLeft ||
             element == PE_IndicatorArrowRight)) {
            drawYellowArrow(element, option->rect, painter);
            return;
        }

        QProxyStyle::drawPrimitive(element, option, painter, widget);
    }

private:
    static void drawYellowArrow(
        PrimitiveElement element,
        const QRect &buttonRect,
        QPainter *painter
    )
    {
        if (!painter || !buttonRect.isValid() || buttonRect.isEmpty())
            return;

        painter->save();
        painter->setRenderHint(QPainter::Antialiasing, false);
        painter->setPen(Qt::NoPen);
        painter->setBrush(QColor(255, 216, 0));

        QRect r = buttonRect.adjusted(4, 4, -4, -4);
        if (r.width() < 3 || r.height() < 3)
            r = buttonRect.adjusted(2, 2, -2, -2);

        const QPoint c = r.center();
        const int sx = qMax(2, r.width() / 3);
        const int sy = qMax(2, r.height() / 3);
        QPolygon points;

        switch (element) {
        case PE_IndicatorArrowUp:
            points << QPoint(c.x(), c.y() - sy)
                   << QPoint(c.x() - sx, c.y() + sy)
                   << QPoint(c.x() + sx, c.y() + sy);
            break;
        case PE_IndicatorArrowDown:
            points << QPoint(c.x() - sx, c.y() - sy)
                   << QPoint(c.x() + sx, c.y() - sy)
                   << QPoint(c.x(), c.y() + sy);
            break;
        case PE_IndicatorArrowLeft:
            points << QPoint(c.x() - sx, c.y())
                   << QPoint(c.x() + sx, c.y() - sy)
                   << QPoint(c.x() + sx, c.y() + sy);
            break;
        case PE_IndicatorArrowRight:
            points << QPoint(c.x() - sx, c.y() - sy)
                   << QPoint(c.x() + sx, c.y())
                   << QPoint(c.x() - sx, c.y() + sy);
            break;
        default:
            painter->restore();
            return;
        }

        painter->drawPolygon(points);
        painter->restore();
    }
};


// Stage 279: QStyle/QSS kann die von einem Proxy-Style gezeichneten Pfeile
// unter Windows noch einmal uebermalen. Deshalb liegen die DEBUG-Pfeile jetzt
// in einem echten QScrollBar-Subclass. paintEvent() laesst zuerst Qt/QSS den
// kompletten Balken zeichnen und malt die gelben Dreiecke DANACH als letzte
// sichtbare Ebene. Damit koennen weder QStyleSheetStyle noch der Windows-Style
// die Pfeile wieder verdecken.
class WorkstationDebugScrollBar final : public QScrollBar
{
public:
    explicit WorkstationDebugScrollBar(
        Qt::Orientation orientation,
        QWidget *parent = nullptr
    )
        : QScrollBar(orientation, parent)
    {
        setMouseTracking(true);
        setAttribute(Qt::WA_Hover, true);
    }

protected:
    void paintEvent(QPaintEvent *event) override
    {
        // Erst Kanal, Griff und Button-Flaechen durch den normalen
        // QScrollBar/QSS-Pfad zeichnen lassen.
        QScrollBar::paintEvent(event);

        // Danach die Pfeile als Overlay. Das ist absichtlich NICHT Teil des
        // Proxy-Styles, weil Qt unter Windows einen QStyleSheetStyle um den
        // Widget-Style legen kann und dessen Ausgabe sonst uebermalt.
        QPainter painter(this);
        painter.setRenderHint(QPainter::Antialiasing, false);
        painter.setPen(Qt::NoPen);
        painter.setBrush(QColor(255, 216, 0)); // #ffd800

        if (orientation() == Qt::Vertical) {
            const int extent = qMin(16, height() / 2);
            drawArrow(painter, QRect(0, 0, width(), extent), Qt::UpArrow);
            drawArrow(
                painter,
                QRect(0, qMax(0, height() - extent), width(), extent),
                Qt::DownArrow
            );
        } else {
            const int extent = qMin(16, width() / 2);
            drawArrow(painter, QRect(0, 0, extent, height()), Qt::LeftArrow);
            drawArrow(
                painter,
                QRect(qMax(0, width() - extent), 0, extent, height()),
                Qt::RightArrow
            );
        }
    }

private:
    static void drawArrow(QPainter &painter, const QRect &buttonRect, Qt::ArrowType arrow)
    {
        if (!buttonRect.isValid() || buttonRect.width() < 5 || buttonRect.height() < 5)
            return;

        // Ein deutlich sichtbares 7x7-Pixel-Dreieck in der Mitte der
        // 16-Pixel-Navy-Schaltflaeche. Bei kleineren Balken wird automatisch
        // skaliert, bleibt aber mindestens 5 Pixel gross.
        const QPoint c = buttonRect.center();
        const int half = qMax(2, qMin(4, qMin(buttonRect.width(), buttonRect.height()) / 3));
        QPolygon points;

        switch (arrow) {
        case Qt::UpArrow:
            points << QPoint(c.x(),        c.y() - half)
                   << QPoint(c.x() - half, c.y() + half)
                   << QPoint(c.x() + half, c.y() + half);
            break;
        case Qt::DownArrow:
            points << QPoint(c.x() - half, c.y() - half)
                   << QPoint(c.x() + half, c.y() - half)
                   << QPoint(c.x(),        c.y() + half);
            break;
        case Qt::LeftArrow:
            points << QPoint(c.x() - half, c.y())
                   << QPoint(c.x() + half, c.y() - half)
                   << QPoint(c.x() + half, c.y() + half);
            break;
        case Qt::RightArrow:
            points << QPoint(c.x() + half, c.y())
                   << QPoint(c.x() - half, c.y() - half)
                   << QPoint(c.x() - half, c.y() + half);
            break;
        default:
            return;
        }

        painter.drawPolygon(points);
    }
};

void apply_workstation_output_debug_theme(int mode);

class WorkstationOutputDialog final : public QDialog
{
public:
    explicit WorkstationOutputDialog(QWidget *parent = nullptr)
        : QDialog(parent)
    {
        setMouseTracking(true);
        setAttribute(Qt::WA_Hover, true);
        setWindowFlags(
            Qt::Window |
            Qt::FramelessWindowHint |
            Qt::WindowSystemMenuHint |
            Qt::WindowMinMaxButtonsHint |
            Qt::WindowStaysOnTopHint
        );
        titleSurface_ = new D64DebugTitleSurface(titleHeight(), true, this);
        createResizeHandles();
        syncResizeHandles();
    }

    // Stage 128: Sichtbar bleibt der Resizer exakt 3 Pixel stark. Die
    // Maus-Hit-Zone ist davon bewusst getrennt und groesser, damit die
    // schlanken Linien auch bei hoher DPI-Skalierung sicher greifbar bleiben.
    void setDarkChrome(bool dark)
    {
        darkChrome_ = dark;
        QPalette pal = palette();
        const QColor background = dark ? QColor(23,23,23) : QColor(236,236,236);
        const QColor foreground = dark ? QColor(237,237,237) : QColor(32,32,32);
        pal.setColor(QPalette::Window, background);
        pal.setColor(QPalette::WindowText, foreground);
        pal.setColor(QPalette::Base, dark ? QColor(23,23,23) : Qt::white);
        pal.setColor(QPalette::Text, foreground);
        setPalette(pal);
        setAutoFillBackground(true);
        if (titleSurface_) { titleSurface_->setDarkChrome(dark); titleSurface_->raise(); }
        syncResizeHandles(); // Cursor-Fangzonen muessen ueber der Titeloberflaeche liegen.
        update();
    }

    static constexpr int borderSize() { return 3; }
    static constexpr int resizeHitSize() { return 10; }
    static constexpr int resizeCatchSize() { return 5; }
    static constexpr int resizeGripLength() { return 22; }
    static constexpr int titleHeight() { return 32; }
    static constexpr int buttonWidth() { return 46; }
    static constexpr int clientInset() { return borderSize() + 1; }
    static constexpr int clientTop() { return titleHeight() + clientInset(); }

    QRect closeButtonRect() const
    {
        return QRect(width() - buttonWidth(), 0, buttonWidth(), titleHeight());
    }
    QRect maxButtonRect() const
    {
        return QRect(width() - 2 * buttonWidth(), 0, buttonWidth(), titleHeight());
    }
    QRect minButtonRect() const
    {
        return QRect(width() - 3 * buttonWidth(), 0, buttonWidth(), titleHeight());
    }

protected:
#ifdef _WIN32
    int resizeHitCode(const QPoint &p) const
    {
        // Stage 130: Nur acht echte 5x5-Catch-Zonen sind Resize-Bereiche.
        // Dadurch bleibt die restliche Titelleiste normal verschiebbar.
        if (isMaximized() || !isActiveWindow())
            return HTNOWHERE;

        const int s = resizeCatchSize();
        const int cx = width() / 2;
        const int cy = height() / 2;
        const QRect topLeft(0, 0, s, s);
        const QRect top(cx - s / 2, 0, s, s);
        const QRect topRight(qMax(0, width() - s), 0, s, s);
        const QRect left(0, cy - s / 2, s, s);
        const QRect right(qMax(0, width() - s), cy - s / 2, s, s);
        const QRect bottomLeft(0, qMax(0, height() - s), s, s);
        const QRect bottom(cx - s / 2, qMax(0, height() - s), s, s);
        const QRect bottomRight(qMax(0, width() - s), qMax(0, height() - s), s, s);

        if (topLeft.contains(p)) return HTTOPLEFT;
        if (top.contains(p)) return HTTOP;
        if (topRight.contains(p)) return HTTOPRIGHT;
        if (left.contains(p)) return HTLEFT;
        if (right.contains(p)) return HTRIGHT;
        if (bottomLeft.contains(p)) return HTBOTTOMLEFT;
        if (bottom.contains(p)) return HTBOTTOM;
        if (bottomRight.contains(p)) return HTBOTTOMRIGHT;
        return HTNOWHERE;
    }

    void updateResizeCursor(const QPoint &p)
    {
        switch (resizeHitCode(p)) {
        case HTLEFT:
        case HTRIGHT:
            setCursor(Qt::SizeHorCursor);
            break;
        case HTTOP:
        case HTBOTTOM:
            setCursor(Qt::SizeVerCursor);
            break;
        case HTTOPLEFT:
        case HTBOTTOMRIGHT:
            setCursor(Qt::SizeFDiagCursor);
            break;
        case HTTOPRIGHT:
        case HTBOTTOMLEFT:
            setCursor(Qt::SizeBDiagCursor);
            break;
        default:
            unsetCursor();
            break;
        }
    }

    bool startSystemResizeAt(const QPoint &p)
    {
        const int hit = resizeHitCode(p);
        if (hit == HTNOWHERE)
            return false;
        HWND hwnd = reinterpret_cast<HWND>(winId());
        if (!hwnd || !IsWindow(hwnd))
            return false;

        // WM_NCHITTEST ist auf einigen Qt5/Windows-DPI-Konfigurationen nicht
        // ausreichend verlaesslich. Der Mausklick auf eine Resize-Hot-Zone
        // startet deshalb zusaetzlich explizit den nativen System-Resize.
        ReleaseCapture();
        SendMessageW(hwnd, WM_NCLBUTTONDOWN, static_cast<WPARAM>(hit), 0);
        return true;
    }

    bool nativeEvent(const QByteArray &eventType, void *message, long *result) override
    {
        MSG *msg = static_cast<MSG *>(message);
        if (msg && (msg->message == WM_SETTINGCHANGE || msg->message == WM_THEMECHANGED)) {
            QTimer::singleShot(0, []() { apply_workstation_output_debug_theme(-1); });
        }
        if (msg && msg->message == WM_GETMINMAXINFO && msg->lParam) {
            D64WorkstationConstrainMaximizeInfo(reinterpret_cast<void *>(msg->lParam));
            if (result) *result = 0;
            return true;
        }
        if (msg && msg->message == WM_MOVING && msg->lParam) {
            D64WorkstationConstrainMovingRect(reinterpret_cast<RECT *>(msg->lParam));
            if (result) *result = TRUE;
            return true;
        }
        if (msg && msg->message == WM_NCHITTEST) {
            // QCursor::pos() ist bereits in Qt-Global-Koordinaten und vermeidet
            // die physisch/logisch-DPI-Mischung von LOWORD/HIWORD(lParam).
            const QPoint p = mapFromGlobal(QCursor::pos());
            // Stage 130: Die acht 5x5-Catch-Widgets muessen Client-Mausereignisse
            // bekommen. Deshalb hier bewusst HTCLIENT statt HTLEFT/HTTOP/... .
            for (auto *handle : resizeHandles_) {
                if (handle && handle->isVisible() && handle->geometry().contains(p)) {
                    if (result) *result = HTCLIENT;
                    return true;
                }
            }
            if (closeButtonRect().contains(p) || maxButtonRect().contains(p) || minButtonRect().contains(p)) {
                if (result) *result = HTCLIENT;
                return true;
            }
            if (p.y() >= 0 && p.y() < titleHeight()) {
                // Qt5-Titelwidget steuert Ziehen, Buttons und Doppelklick.
                if (result) *result = HTCLIENT;
                return true;
            }
        }
        return QDialog::nativeEvent(eventType, message, result);
    }
#endif

    void drawResizeChrome(QPainter &painter)
    {
        if (isMaximized())
            return;

        const int r = borderSize();
        const QColor resizeLine(105, 105, 105);
        painter.fillRect(QRect(0, 0, width(), r), resizeLine);
        painter.fillRect(QRect(0, height() - r, width(), r), resizeLine);
        painter.fillRect(QRect(0, r, r, qMax(0, height() - 2 * r)), resizeLine);
        painter.fillRect(QRect(width() - r, r, r, qMax(0, height() - 2 * r)), resizeLine);

        // Beim aktiven Fenster werden die acht Resize-Stellen als kurze,
        // ausschliesslich 3 Pixel starke Liniensegmente hervorgehoben.
        if (!isActiveWindow())
            return;

        const QColor activeLine(185, 185, 185);
        const int len = qMin(resizeGripLength(), qMax(3, qMin(width(), height()) / 3));
        const int cx = width() / 2;
        const int cy = height() / 2;

        // 1/2/3: oben links, oben Mitte, oben rechts.
        painter.fillRect(QRect(0, 0, len, r), activeLine);
        painter.fillRect(QRect(0, 0, r, len), activeLine);
        painter.fillRect(QRect(cx - len / 2, 0, len, r), activeLine);
        painter.fillRect(QRect(qMax(0, width() - len), 0, len, r), activeLine);
        painter.fillRect(QRect(width() - r, 0, r, len), activeLine);

        // 4/5: links/rechts Mitte.
        painter.fillRect(QRect(0, cy - len / 2, r, len), activeLine);
        painter.fillRect(QRect(width() - r, cy - len / 2, r, len), activeLine);

        // 6/7/8: unten links, unten Mitte, unten rechts.
        painter.fillRect(QRect(0, height() - r, len, r), activeLine);
        painter.fillRect(QRect(0, qMax(0, height() - len), r, len), activeLine);
        painter.fillRect(QRect(cx - len / 2, height() - r, len, r), activeLine);
        painter.fillRect(QRect(qMax(0, width() - len), height() - r, len, r), activeLine);
        painter.fillRect(QRect(width() - r, qMax(0, height() - len), r, len), activeLine);
    }

    void paintEvent(QPaintEvent *event) override
    {
        QDialog::paintEvent(event);
        // Titel/Buttons werden separat durch D64DebugTitleSurface gezeichnet.
        QPainter painter(this);
        drawResizeChrome(painter);
    }

    void resizeEvent(QResizeEvent *event) override
    {
        QDialog::resizeEvent(event);
        if (titleSurface_) titleSurface_->syncGeometry(isMaximized());
        syncResizeHandles();
    }

    // Stage 317: Eigene Qt5-Titel-Drags rufen QWidget::move() direkt auf.
    // Dabei gibt es kein WM_MOVING. Die bestehenden Workstation-Panel-Grenzen
    // darum auch bei Qt-Moves explizit respektieren, ohne Rekursion.
    void moveEvent(QMoveEvent *event) override
    {
        QDialog::moveEvent(event);
#ifdef _WIN32
        if (!adjustingWorkstationMove_ && isVisible() && !isMaximized()) {
            RECT r = { x(), y(), x() + width(), y() + height() };
            D64WorkstationConstrainMovingRect(&r);
            if (r.left != x() || r.top != y()) {
                adjustingWorkstationMove_ = true;
                move(r.left, r.top);
                adjustingWorkstationMove_ = false;
            }
        }
#endif
    }

    void showEvent(QShowEvent *event) override
    {
        QDialog::showEvent(event);
        if (titleSurface_) titleSurface_->syncGeometry(isMaximized());
        syncResizeHandles();
    }

    void mouseMoveEvent(QMouseEvent *event) override
    {
        int hover = 0;
        if (event) {
#ifdef _WIN32
            updateResizeCursor(event->pos());
#endif
            if (minButtonRect().contains(event->pos())) hover = 1;
            else if (maxButtonRect().contains(event->pos())) hover = 2;
            else if (closeButtonRect().contains(event->pos())) hover = 3;
        }
        if (hover != hoverButton_) {
            hoverButton_ = hover;
            if (titleSurface_) titleSurface_->setHoverButton(hover);
        }
        QDialog::mouseMoveEvent(event);
    }

    void mousePressEvent(QMouseEvent *event) override
    {
#ifdef _WIN32
        if (event && event->button() == Qt::LeftButton && startSystemResizeAt(event->pos())) {
            event->accept();
            return;
        }
#endif
        // Stage 316: Die gezeichneten Fenster-Icons muessen auch mit einem
        // einfachen Linksklick funktionieren; der Doppelklick bleibt erhalten.
        if (event && event->button() == Qt::LeftButton) {
            const QPoint p = event->pos();
            if (closeButtonRect().contains(p)) {
                hide();
                event->accept();
                return;
            }
            if (minButtonRect().contains(p)) {
                showMinimized();
                event->accept();
                return;
            }
            if (maxButtonRect().contains(p)) {
                isMaximized() ? showNormal() : showMaximized();
                event->accept();
                return;
            }
        }
        QDialog::mousePressEvent(event);
    }

    void leaveEvent(QEvent *event) override
    {
        unsetCursor();
        if (hoverButton_ != 0) {
            hoverButton_ = 0;
            if (titleSurface_) titleSurface_->setHoverButton(0);
        }
        QDialog::leaveEvent(event);
    }

    void mouseDoubleClickEvent(QMouseEvent *event) override
    {
        if (event && event->button() == Qt::LeftButton) {
            const QPoint p = event->pos();
            if (closeButtonRect().contains(p) || minButtonRect().contains(p) ||
                maxButtonRect().contains(p)) {
                // Buttonaktion wurde bereits mit dem ersten Klick ausgeloest.
                event->accept();
                return;
            }
            if (p.y() >= borderSize() && p.y() < titleHeight()) {
                isMaximized() ? showNormal() : showMaximized();
                event->accept();
                return;
            }
        }
        QDialog::mouseDoubleClickEvent(event);
    }

    void changeEvent(QEvent *event) override
    {
        QDialog::changeEvent(event);
        if (event && (event->type() == QEvent::ActivationChange || event->type() == QEvent::WindowStateChange)) {
            if (titleSurface_) titleSurface_->syncGeometry(isMaximized());
            syncResizeHandles();
            update();
        }
    }

    void closeEvent(QCloseEvent *event) override
    {
        // Stage 128: Das Debug-/Print-Fenster gehoert zur Workstation. Ein X
        // versteckt es nur temporaer; der bestehende 500-ms-Watchdog darf es
        // beim naechsten Takt wieder aktivieren.
        hide();
        event->ignore();
    }

private:
    enum ResizeHandleIndex {
        HandleTopLeft = 0,
        HandleTop,
        HandleTopRight,
        HandleLeft,
        HandleRight,
        HandleBottomLeft,
        HandleBottom,
        HandleBottomRight,
        HandleTopStrip,
        HandleBottomStrip,
        HandleLeftStrip,
        HandleRightStrip,
        ResizeHandleCount
    };

    void createResizeHandles()
    {
#ifdef _WIN32
        const int codes[ResizeHandleCount] = {
            HTTOPLEFT, HTTOP, HTTOPRIGHT, HTLEFT,
            HTRIGHT, HTBOTTOMLEFT, HTBOTTOM, HTBOTTOMRIGHT,
            HTTOP, HTBOTTOM, HTLEFT, HTRIGHT
        };
        for (int i = 0; i < ResizeHandleCount; ++i)
            resizeHandles_[i] = new WorkstationResizeHandle(this, codes[i]);
#endif
    }

    void syncResizeHandles()
    {
#ifdef _WIN32
        const bool enabled = isVisible() && !isMaximized();
        const int s = resizeCatchSize();
        const int cx = width() / 2;
        const int cy = height() / 2;

        const QRect rects[ResizeHandleCount] = {
            QRect(0, 0, s, s),
            QRect(cx - s / 2, 0, s, s),
            QRect(qMax(0, width() - s), 0, s, s),
            QRect(0, cy - s / 2, s, s),
            QRect(qMax(0, width() - s), cy - s / 2, s, s),
            QRect(0, qMax(0, height() - s), s, s),
            QRect(cx - s / 2, qMax(0, height() - s), s, s),
            QRect(qMax(0, width() - s), qMax(0, height() - s), s, s),
            QRect(s, 0, qMax(0, width() - 2*s), s),
            QRect(s, qMax(0, height() - s), qMax(0, width() - 2*s), s),
            QRect(0, s, s, qMax(0, height() - 2*s)),
            QRect(qMax(0, width() - s), s, s, qMax(0, height() - 2*s))
        };

        for (int i = 0; i < ResizeHandleCount; ++i) {
            if (!resizeHandles_[i])
                continue;
            resizeHandles_[i]->setGeometry(rects[i]);
            resizeHandles_[i]->setEnabled(enabled);
            resizeHandles_[i]->setVisible(enabled);
        }
        // Ecken und mittige 5px-Griffe liegen ueber den Seitenstreifen.
        if (enabled) {
            for (int i = 8; i < ResizeHandleCount; ++i) resizeHandles_[i]->raise();
            for (int i = 0; i < 8; ++i) resizeHandles_[i]->raise();
        }
#endif
    }

    bool darkChrome_ = true;
    bool adjustingWorkstationMove_ = false;
    int hoverButton_ = 0;
    D64DebugTitleSurface *titleSurface_ = nullptr;
    WorkstationResizeHandle *resizeHandles_[ResizeHandleCount] = {};
};

// Stage 275: Eigener Workstation-Exit-Dialog statt nativer MessageBox.
// Optisch folgt er bewusst dem DEBUG-Fenster (frameless, 3px-Rahmen,
// dunkle Verlaufstitelleiste, db-Icon und rotes X).
class WorkstationExitDialog final : public QDialog
{
public:
    explicit WorkstationExitDialog(bool darkMode, QWidget *parent = nullptr)
        : QDialog(parent), darkMode_(darkMode)
    {
        setObjectName(QStringLiteral("d64WorkstationExitDialog"));
        setWindowTitle(QStringLiteral("Workstation beenden"));
        setModal(true);
        setFixedSize(500, 190);
        setMouseTracking(true);
        setWindowFlags(
            Qt::Dialog |
            Qt::FramelessWindowHint |
            Qt::WindowSystemMenuHint |
            Qt::WindowStaysOnTopHint
        );

        auto *layout = new QVBoxLayout(this);
        layout->setContentsMargins(18, 48, 18, 16);
        layout->setSpacing(16);

        auto *label = new QLabel(
            QStringLiteral("Möchten Sie die Workstation wirklich beenden?"),
            this
        );
        label->setObjectName(QStringLiteral("d64WorkstationExitText"));
        label->setAlignment(Qt::AlignLeft | Qt::AlignVCenter);
        label->setWordWrap(true);
        layout->addWidget(label, 1);

        auto *buttons = new QHBoxLayout();
        buttons->setSpacing(10);
        buttons->addStretch(1);

        auto *yesButton = new QPushButton(QStringLiteral("Ja"), this);
        yesButton->setObjectName(QStringLiteral("d64WorkstationExitYes"));
        yesButton->setMinimumWidth(96);
        auto *noButton = new QPushButton(QStringLiteral("Nein"), this);
        noButton->setObjectName(QStringLiteral("d64WorkstationExitNo"));
        noButton->setMinimumWidth(96);
        noButton->setDefault(true);
        noButton->setAutoDefault(true);

        buttons->addWidget(yesButton);
        buttons->addWidget(noButton);
        layout->addLayout(buttons);

        connect(yesButton, &QPushButton::clicked, this, &QDialog::accept);
        connect(noButton, &QPushButton::clicked, this, &QDialog::reject);
        noButton->setFocus(Qt::OtherFocusReason);

        applyTheme();
    }

    static constexpr int borderSize() { return 3; }
    static constexpr int titleHeight() { return 32; }
    static constexpr int buttonWidth() { return 46; }

    QRect closeButtonRect() const
    {
        return QRect(width() - buttonWidth(), 0, buttonWidth(), titleHeight());
    }

protected:
#ifdef _WIN32
    bool nativeEvent(const QByteArray &eventType, void *message, long *result) override
    {
        MSG *msg = static_cast<MSG *>(message);
        if (msg && msg->message == WM_NCHITTEST) {
            const QPoint p = mapFromGlobal(QCursor::pos());
            if (closeButtonRect().contains(p)) {
                if (result) *result = HTCLIENT;
                return true;
            }
            if (p.y() >= 0 && p.y() < titleHeight()) {
                if (result) *result = HTCAPTION;
                return true;
            }
        }
        return QDialog::nativeEvent(eventType, message, result);
    }
#endif

    void paintEvent(QPaintEvent *event) override
    {
        QDialog::paintEvent(event);
        QPainter painter(this);
        painter.setRenderHint(QPainter::Antialiasing, false);

        QLinearGradient gradient(0, 0, width(), 0);
        gradient.setColorAt(0.0, QColor(68, 68, 68));
        gradient.setColorAt(1.0, QColor(14, 14, 14));
        painter.fillRect(QRect(0, 0, width(), titleHeight()), gradient);

        const QRect closeRect = closeButtonRect();
        if (hoverClose_)
            painter.fillRect(closeRect, QColor(205, 35, 35));

        QRect iconRect(8, 6, 20, 20);
        painter.setPen(QPen(QColor(230, 230, 230), 1));
        painter.setBrush(QColor(0, 115, 80));
        painter.drawRoundedRect(iconRect, 3, 3);
        QFont iconFont(QStringLiteral("Segoe UI"), 7, QFont::Bold);
        painter.setFont(iconFont);
        painter.setPen(Qt::white);
        painter.drawText(iconRect, Qt::AlignCenter, QStringLiteral("db"));

        painter.setFont(QFont(QStringLiteral("Segoe UI"), 9));
        painter.setPen(QColor(235, 235, 235));
        const QRect titleRect(34, 0, qMax(0, width() - 34 - buttonWidth()), titleHeight());
        painter.drawText(titleRect, Qt::AlignVCenter | Qt::AlignLeft, windowTitle());

        QFont glyph(QStringLiteral("Segoe MDL2 Assets"), 10);
        painter.setFont(glyph);
        painter.setPen(QColor(238, 238, 238));
        painter.drawText(closeRect, Qt::AlignCenter, QString(QChar(0xE8BB)));

        const QColor border = isActiveWindow() ? QColor(185, 185, 185) : QColor(105, 105, 105);
        const int r = borderSize();
        painter.fillRect(QRect(0, 0, width(), r), border);
        painter.fillRect(QRect(0, height() - r, width(), r), border);
        painter.fillRect(QRect(0, r, r, qMax(0, height() - 2 * r)), border);
        painter.fillRect(QRect(width() - r, r, r, qMax(0, height() - 2 * r)), border);
    }

    void mouseMoveEvent(QMouseEvent *event) override
    {
        const bool hover = event && closeButtonRect().contains(event->pos());
        if (hover != hoverClose_) {
            hoverClose_ = hover;
            update(closeButtonRect());
        }
        QDialog::mouseMoveEvent(event);
    }

    void leaveEvent(QEvent *event) override
    {
        if (hoverClose_) {
            hoverClose_ = false;
            update(closeButtonRect());
        }
        QDialog::leaveEvent(event);
    }

    void mouseReleaseEvent(QMouseEvent *event) override
    {
        if (event && event->button() == Qt::LeftButton && closeButtonRect().contains(event->pos())) {
            reject();
            event->accept();
            return;
        }
        QDialog::mouseReleaseEvent(event);
    }

private:
    void applyTheme()
    {
        if (darkMode_) {
            setStyleSheet(QStringLiteral(
                "QDialog#d64WorkstationExitDialog { background:#171717; }"
                "QLabel#d64WorkstationExitText { color:#d2ca87; font:10pt 'Segoe UI'; }"
                "QPushButton { background:#061b3a; color:#ffd800; border:1px solid #315581;"
                " border-radius:3px; padding:6px 18px; min-height:24px; }"
                "QPushButton:hover { background:#0b2f63; border-color:#ffd800; }"
                "QPushButton:pressed { background:#0e376c; }"
                "QPushButton:default { border:2px solid #ffd800; }"
            ));
        } else {
            setStyleSheet(QStringLiteral(
                "QDialog#d64WorkstationExitDialog { background:#ececec; }"
                "QLabel#d64WorkstationExitText { color:#202020; font:10pt 'Segoe UI'; }"
                "QPushButton { background:#f7f7f7; color:#102c52; border:1px solid #607d9e;"
                " border-radius:3px; padding:6px 18px; min-height:24px; }"
                "QPushButton:hover { background:#dbe8f5; border-color:#173b66; }"
                "QPushButton:pressed { background:#c8dced; }"
                "QPushButton:default { border:2px solid #173b66; }"
            ));
        }
    }

    bool darkMode_ = true;
    bool hoverClose_ = false;
};

struct ChildProcess {
    std::wstring canonicalPath;
    HANDLE process = nullptr;
    DWORD pid = 0;
    // Stage 114: Das Console-HWND gehoert auf modernen Windows-Versionen
    // dem Console Host und nicht zwingend der PID des Kindprozesses. Der
    // Runner merkt es sich deshalb nach AttachConsole(pid) separat.
    HWND consoleWindow = nullptr;

    // Stage 115 TEST: Eine sichtbare dBase-Console wird temporaer modal
    // behandelt. Das echte Console-HWND kennt keine Qt-Modality; deshalb
    // werden die GUI-Top-Level-Fenster des Kindes deaktiviert und die
    // Console TOPMOST gehalten. Schliessen der Console beendet bei der
    // normalen Win32-Console den Testprozess; bei Verstecken/Verlust des
    // Console-HWND werden die GUI-Fenster wieder aktiviert.
    bool consoleModalTest = false;
    std::vector<HWND> modalDisabledWindows;
};

HWND g_host_window = nullptr;
WorkstationOutputDialog *g_output_dialog = nullptr;
QPlainTextEdit *g_output_edit = nullptr;
HHOOK g_mouse_hook = nullptr;
HHOOK g_keyboard_hook = nullptr;
HWND g_close_candidate = nullptr;
std::vector<HWND> g_hidden_windows;
std::vector<ChildProcess> g_children;
std::thread g_pipe_thread;
std::atomic<bool> g_pipe_stop{false};
// Stage 273: true nur solange eine frische Pipe-Instanz wirklich auf den
// naechsten Client wartet. Damit wird der Kind-Thread erst freigegeben, wenn
// Write/WriteLn garantiert einen empfangsbereiten Runner vorfindet.
std::atomic<bool> g_pipe_ready{false};
bool g_leave_started = false;
// Stage 275: Der Panel-Klick darf niemals zwei Bestätigungsdialoge erzeugen.
bool g_exit_prompt_active = false;
bool g_exit_confirmed = false;
ULONGLONG g_exit_prompt_suppress_until = 0;
// Stage 144: 0=default (Workstation-Theme folgen), 1=light, 2=dark.
int g_output_debug_theme_mode = 0;
// Stage 318: Sichtbarkeit ist ein expliziter Runtimezustand. Nur ON oder
// ein neuer Programmstart duerfen ein mit OFF verborgenes Fenster zeigen.
bool g_output_visibility_enabled = true;
// Stage 319: UI-Theme nur bei tatsaechlicher Aenderung erneut anwenden.
// Ein vollstaendiges setStyleSheet() je WriteLn war extrem teuer.
int g_last_applied_output_theme_mode = -1;
int g_last_applied_output_dark_mode = -1;

// Stage 319: DOW1-Nachrichten werden in einem kurzen Zeitfenster gesammelt,
// damit Qt-Textlayout, Scrollbars und Fenstermalerei nicht pro Byte/Fragment
// ausgefuehrt werden muessen. Aenderungen an SET DEBUG ON/OFF leeren die
// Queue vorher, damit deren Reihenfolge erhalten bleibt.
QString g_pending_output_text;
bool g_pending_output_flush_scheduled = false;
// Stage 320: Nach Programmstart ist das Debug-Fenster einmalig aktiv
// vorzuziehen, bevor die gebuendelte Textausgabe in den QTimer geht.
// Kein teures Raise fuer jedes der folgenden Textfragmente.
bool g_output_reveal_on_next_write = true;

// Der DB-Button repraesentiert das zuletzt an den Runner uebergebene
// Hauptprogramm. Dadurch kann das Programm nach einem normalen Schliessen
// (Hide) wieder angezeigt oder nach einem echten Prozessende neu gestartet
// werden.
LaunchRequest g_db_launch_request;
bool g_has_db_launch_request = false;

QString workstation_debug_scrollbar_style_sheet()
{
    return QStringLiteral(
        "QScrollBar:vertical { background:#06152b; width:16px; margin:16px 0 16px 0;"
        " border:1px solid #244d7a; }"
        "QScrollBar::handle:vertical { background:#0b2f63; min-height:24px;"
        " border:1px solid #416d9c; border-radius:2px; }"
        "QScrollBar::handle:vertical:hover { background:#12447e; border-color:#ffd800; }"
        "QScrollBar::sub-line:vertical { background:#061b3a; height:16px;"
        " subcontrol-position:top; subcontrol-origin:margin; border:1px solid #244d7a; }"
        "QScrollBar::add-line:vertical { background:#061b3a; height:16px;"
        " subcontrol-position:bottom; subcontrol-origin:margin; border:1px solid #244d7a; }"
        "QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background:#06152b; }"
        "QScrollBar:horizontal { background:#06152b; height:16px; margin:0 16px 0 16px;"
        " border:1px solid #244d7a; }"
        "QScrollBar::handle:horizontal { background:#0b2f63; min-width:24px;"
        " border:1px solid #416d9c; border-radius:2px; }"
        "QScrollBar::handle:horizontal:hover { background:#12447e; border-color:#ffd800; }"
        "QScrollBar::sub-line:horizontal { background:#061b3a; width:16px;"
        " subcontrol-position:left; subcontrol-origin:margin; border:1px solid #244d7a; }"
        "QScrollBar::add-line:horizontal { background:#061b3a; width:16px;"
        " subcontrol-position:right; subcontrol-origin:margin; border:1px solid #244d7a; }"
        "QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal { background:#06152b; }"
    );
}

// Stage 315: Default folgt dem Windows-App-Theme, NICHT der separaten
// Workstation-Panel-Farbe. Explizite Debug-Radiobuttons bleiben vorrangig.
bool workstation_windows_apps_dark_mode()
{
#ifdef _WIN32
    HKEY key = nullptr;
    if (RegOpenKeyExW(HKEY_CURRENT_USER,
        L"Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize",
        0, KEY_QUERY_VALUE, &key) == ERROR_SUCCESS) {
        const wchar_t *names[] = { L"AppsUseLightTheme", L"SystemUsesLightTheme" };
        for (const wchar_t *name : names) {
            DWORD value = 1, type = 0, size = sizeof(value);
            const LONG code = RegQueryValueExW(key, name, nullptr, &type,
                                              reinterpret_cast<LPBYTE>(&value), &size);
            if (code == ERROR_SUCCESS && type == REG_DWORD && size == sizeof(value)) {
                RegCloseKey(key);
                return value == 0;
            }
        }
        RegCloseKey(key);
    }
#endif
    return false;
}

bool workstation_debug_uses_dark_theme()
{
    if (g_output_debug_theme_mode == 1)
        return false;
    if (g_output_debug_theme_mode == 2)
        return true;
    return workstation_windows_apps_dark_mode();
}

void apply_workstation_output_theme(bool darkMode)
{
    if (!g_output_dialog || !g_output_edit)
        return;

    g_output_dialog->setDarkChrome(darkMode);
    static_cast<D64DebugOutputTextEdit *>(g_output_edit)->setDebugContextDark(darkMode);
    QString style;
    if (darkMode) {
        // Stage 278: Dark-Mode an den Beenden-Dialog angleichen:
        // gleiche Grundflaeche, gleiche gelb/beige Textfarbe und Navy-Akzente.
        style = QStringLiteral(
            "QDialog#d64WorkstationOutputDialog { background:#171717; color:#ededed; }"
            "QDialog#d64WorkstationOutputDialog QWidget#qt_scrollarea_viewport { background:#171717; }"
            "QPlainTextEdit#d64WorkstationOutput {"
            " background:#171717; color:#d2ca87; border:1px solid #315581;"
            " padding:2px;"
            " selection-background-color:#0b2f63; selection-color:#ffd800; }"
        );
    } else {
        style = QStringLiteral(
            "QDialog#d64WorkstationOutputDialog { background:#ececec; }"
            "QPlainTextEdit#d64WorkstationOutput {"
            " background:#ffffff; color:#202020; border:1px solid #8a8a8a;"
            " selection-background-color:#3478c7; selection-color:#ffffff; }"
        );
    }

    // Stage 275: Beide DEBUG-Scrollbars bleiben bewusst navyblau, unabhaengig
    // vom Text-Theme. Die Pfeile selbst zeichnet WorkstationScrollBarStyle
    // gelb; die QSS-Regeln liefern Kanal, Griff und Pfeilbutton-Hintergrund.
    style += workstation_debug_scrollbar_style_sheet();
    g_output_dialog->setStyleSheet(style);
    g_output_dialog->update();
    g_output_edit->viewport()->update();
}

void apply_workstation_output_debug_theme(int mode)
{
    if (mode >= 0 && mode <= 2)
        g_output_debug_theme_mode = mode;

    // Stage 319: Mit jeder dBase-/WFM-Ausgabe wird das gewaehlte Theme
    // erneut im DOW1-Paket uebermittelt. Das soll nicht pro Ausgabe
    // setStyleSheet(), update() und ein komplettes Qt-Repolish ausloesen.
    // Im default-Modus wird Windows weiterhin bei jedem Aufruf abgefragt;
    // ein echter Windows-Theme-Wechsel wird dadurch sofort uebernommen.
    const bool dark = workstation_debug_uses_dark_theme();
    if (!g_output_dialog || !g_output_edit)
        return;
    if (g_last_applied_output_theme_mode == g_output_debug_theme_mode &&
        g_last_applied_output_dark_mode == static_cast<int>(dark))
        return;

    g_last_applied_output_theme_mode = g_output_debug_theme_mode;
    g_last_applied_output_dark_mode = static_cast<int>(dark);
    apply_workstation_output_theme(dark);
}

void workstation_theme_changed(bool darkMode)
{
    Q_UNUSED(darkMode)
    apply_workstation_output_debug_theme(g_output_debug_theme_mode);
}

void create_workstation_output_dialog()
{
    if (g_output_dialog && g_output_edit)
        return;

    // Ein neu angelegter Dialog muss sein Theme immer erstmalig erhalten.
    g_last_applied_output_theme_mode = -1;
    g_last_applied_output_dark_mode = -1;

    // Stage 116 compatibility marker: g_output_dialog = new QDialog(nullptr);
    g_output_dialog = new WorkstationOutputDialog(nullptr);
    g_output_dialog->setObjectName(QStringLiteral("d64WorkstationOutputDialog"));
    // Stage 271: gemeinsamer DEBUG-Ausgabekanal fuer dBase/WFM und
    // generische Pascal/C-Programme im Workstation Mode.
    g_output_dialog->setWindowTitle(QStringLiteral("Debug"));
    g_output_dialog->setModal(false);
    g_output_dialog->setAttribute(Qt::WA_DeleteOnClose, false);
    g_output_dialog->resize(680, 300);

    auto *layout = new QVBoxLayout(g_output_dialog);
    layout->setContentsMargins(
        WorkstationOutputDialog::clientInset(),
        WorkstationOutputDialog::clientTop(),
        WorkstationOutputDialog::clientInset(),
        WorkstationOutputDialog::clientInset()
    );
    layout->setSpacing(0);

    g_output_edit = new D64DebugOutputTextEdit(g_output_dialog);
    g_output_edit->setObjectName(QStringLiteral("d64WorkstationOutput"));
    g_output_edit->setReadOnly(true);
    g_output_edit->setPlaceholderText(
        QStringLiteral(
            "DEBUG-Ausgabe bereit - Write/WriteLn, Print und dBase-DEBUG erscheinen hier."
        )
    );
    g_output_edit->setLineWrapMode(QPlainTextEdit::NoWrap);

    // Stage 279: Die echten Scrollbar-Widgets des QPlainTextEdit ersetzen.
    // Der Subclass malt seine gelben Pfeile nach dem kompletten Qt/QSS-Paint
    // und ist deshalb unter dem Windows-Style sichtbar.
    auto *verticalBar = new WorkstationDebugScrollBar(Qt::Vertical, g_output_edit);
    auto *horizontalBar = new WorkstationDebugScrollBar(Qt::Horizontal, g_output_edit);
    g_output_edit->setVerticalScrollBar(verticalBar);
    g_output_edit->setHorizontalScrollBar(horizontalBar);
    g_output_edit->setHorizontalScrollBarPolicy(Qt::ScrollBarAsNeeded);
    g_output_edit->setVerticalScrollBarPolicy(Qt::ScrollBarAsNeeded);

    // Kanal/Griff/Button-Flaechen bleiben im Stage-278-Navy-Style.
    // WorkstationDebugScrollBar garantiert zusaetzlich die gelben Pfeile.
    auto *scrollStyle = new WorkstationScrollBarStyle();
    scrollStyle->setParent(g_output_edit);
    verticalBar->setStyle(scrollStyle);
    horizontalBar->setStyle(scrollStyle);

    // Stage 278: QPlainTextEdit besitzt eigene QScrollBar-Child-Widgets.
    // Der Proxy-Style zeichnet diese beiden Widgets nun VOLLSTAENDIG selbst.
    // Deshalb kann der native Windows-Style nicht mehr als grauer Balken
    // durchscheinen; QSS bleibt nur noch eine zusaetzliche Theme-Absicherung.
    verticalBar->setMinimumWidth(16);
    verticalBar->setMaximumWidth(16);
    horizontalBar->setMinimumHeight(16);
    horizontalBar->setMaximumHeight(16);

    g_output_edit->document()->setMaximumBlockCount(500);
    g_output_edit->setFont(QFontDatabase::systemFont(QFontDatabase::FixedFont));
    layout->addWidget(g_output_edit, 1);
    apply_workstation_output_debug_theme(g_output_debug_theme_mode);

    QRect workArea;
    if (QScreen *screen = QApplication::primaryScreen())
        workArea = screen->availableGeometry();
    if (!workArea.isValid())
        workArea = QRect(80, 40, 1024, 700);

    workArea.adjust(
        D64WorkstationLeftPanelWidth() + 8,
        8,
        -8,
        -(D64WorkstationBottomPanelHeight() + 8)
    );

    const QSize size = g_output_dialog->size();
    const int x = qMax(workArea.left(), workArea.right() - size.width() + 1);
    const int y = qMax(workArea.top(), workArea.bottom() - size.height() + 1);
    g_output_dialog->move(x, y);

    // Stage 119: Der Ausgabedialog ist Bestandteil des Workstation-Runners
    // selbst und muss bereits beim Runner-Start sichtbar sein. winId() wird
    // absichtlich vor show() angefordert, damit das native HWND auf dem durch
    // D64WorkstationPrepare() gebundenen D64Workstation-Desktop entsteht.
    const HWND outputHwnd = reinterpret_cast<HWND>(g_output_dialog->winId());
    if (outputHwnd) {
        SetPropW(
            outputHwnd,
            WORKSTATION_TOOL_WINDOW_PROPERTY,
            reinterpret_cast<HANDLE>(1)
        );
    }

    g_output_dialog->show();
    g_output_dialog->raise();

    // Ein unmittelbar danach gestartetes Formular wird vom Runner bewusst in
    // den Vordergrund geholt. Deshalb den nicht-modalen Ausgabedialog als
    // TOPMOST-Workstation-Toolfenster halten; er bleibt bedienbar, blockiert
    // die Anwendung aber nicht.
    if (outputHwnd) {
        ShowWindow(outputHwnd, SW_SHOWNORMAL);
        SetWindowPos(
            outputHwnd,
            HWND_TOPMOST,
            0, 0, 0, 0,
            SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW | SWP_NOACTIVATE
        );
    }
}

void ensure_workstation_output_dialog_on_screen()
{
    if (!g_output_dialog)
        return;

#ifdef _WIN32
    const HWND outputHwnd = reinterpret_cast<HWND>(g_output_dialog->winId());
    if (!outputHwnd || !IsWindow(outputHwnd))
        return;

    RECT rect{};
    if (!GetWindowRect(outputHwnd, &rect))
        return;

    // Stage 122: Nach dem Start eines WFM-Formulars darf der zentrale
    // Konsolenersatz nicht auf einem nicht mehr sichtbaren Monitor-/Desktop-
    // Bereich verbleiben. Nur wenn das Fenster wirklich mit keinem Monitor
    // ueberlappt, wird die vom Benutzer gewuenschte Fallback-Origin 10/10
    // verwendet. Eine gueltige benutzerdefinierte Position bleibt erhalten.
    const HMONITOR monitor = MonitorFromRect(&rect, MONITOR_DEFAULTTONULL);
    if (!monitor) {
        constexpr int fallbackX = 10;
        constexpr int fallbackY = 10;
        g_output_dialog->move(fallbackX, fallbackY);
        SetWindowPos(
            outputHwnd,
            HWND_TOPMOST,
            fallbackX, fallbackY,
            0, 0,
            SWP_NOSIZE | SWP_SHOWWINDOW | SWP_NOACTIVATE
        );
    }
#else
    bool visible = false;
    const QRect dialogRect = g_output_dialog->frameGeometry();
    for (QScreen *screen : QApplication::screens()) {
        if (screen && screen->availableGeometry().intersects(dialogRect)) {
            visible = true;
            break;
        }
    }
    if (!visible)
        g_output_dialog->move(10, 10);
#endif
}

void ensure_workstation_output_dialog_visible()
{
    // Stage 318: Dieser Guard ist auch fuer den 500-ms-Watchdog und
    // alle alten Start-/Output-Pfade verbindlich.
    if (!g_output_visibility_enabled)
        return;
    create_workstation_output_dialog();
    if (!g_output_dialog)
        return;

    // Stage 272: Das DEBUG-Fenster ist ein fester Bestandteil des Runners.
    // Ein minimierter Zustand darf deshalb nicht dazu fuehren, dass der
    // Sichtbarkeits-Watchdog dauerhaft wirkungslos bleibt. Das war besonders
    // bei residenten Runner-Sessions problematisch: Die IDE konnte eine neue
    // Pascal-EXE erfolgreich uebergeben, das DEBUG-Fenster blieb aber
    // minimiert bzw. scheinbar verschwunden.
    if (g_output_dialog->isMinimized())
        g_output_dialog->showNormal();

    if (!g_output_dialog->isVisible())
        g_output_dialog->show();

    ensure_workstation_output_dialog_on_screen();
    g_output_dialog->raise();

#ifdef _WIN32
    const HWND outputHwnd = reinterpret_cast<HWND>(g_output_dialog->winId());
    if (outputHwnd && IsWindow(outputHwnd)) {
        if (!IsWindowVisible(outputHwnd) || IsIconic(outputHwnd))
            ShowWindow(outputHwnd, SW_RESTORE);
        SetWindowPos(
            outputHwnd,
            HWND_TOPMOST,
            0, 0, 0, 0,
            SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW | SWP_NOACTIVATE
        );
        // Eine echte Console wird vom Runner ebenfalls TOPMOST gehalten.
        // BringWindowToTop() nach SetWindowPos() stellt sicher, dass das
        // DEBUG-Fenster innerhalb dieses TOPMOST-Bandes sichtbar bleibt.
        BringWindowToTop(outputHwnd);
    }
#endif
}

// Stage 274: Console-Programme aus dem GUI-Workstation-Pfad werden nicht
// mehr darauf angewiesen, dass ihre Runtime den proprietaeren DOW1-Kanal
// kennt. Der Runner faengt den echten STDOUT/STDERR-Byte-Strom des Kindes
// ueber eine anonyme Pipe ab. Damit erscheint exakt die Ausgabe, die bei
// einem normalen Start in der Windows-Konsole landen wuerde, im DEBUG-Fenster.
void start_child_standard_output_capture(
    HANDLE readPipe,
    DWORD processId,
    int debugThemeMode)
{
    if (!readPipe || readPipe == INVALID_HANDLE_VALUE)
        return;

    std::thread([readPipe, processId, debugThemeMode]() {
        char buffer[4096];
        for (;;) {
            DWORD bytesRead = 0;
            const BOOL ok = ReadFile(
                readPipe,
                buffer,
                static_cast<DWORD>(sizeof(buffer)),
                &bytesRead,
                nullptr
            );
            if (!ok || bytesRead == 0)
                break;

            std::unique_ptr<OutputMessage> output(new OutputMessage());
            output->text.assign(buffer, buffer + bytesRead);
            // Die aktuelle Pascal-Runtime schreibt ihre Console-Bytes als
            // ANSI/Latin-1. Das entspricht auch der bisherigen DOW1-Route.
            output->latin1 = true;
            output->processId = processId;
            output->debugThemeMode = debugThemeMode;

            HWND host = g_host_window;
            if (host && IsWindow(host)) {
                if (PostMessageW(
                        host,
                        WM_RUNNER_OUTPUT,
                        0,
                        reinterpret_cast<LPARAM>(output.get()))) {
                    output.release();
                }
            }
        }
        CloseHandle(readPipe);
    }).detach();
}

// Stage 319: GUI nur alle ca. 16 ms statt fuer jedes einzelne Pipe-Paket
// aktualisieren. Der HWND-Nachrichtenhandler darf nie auf Paint/Scroll warten.
void flush_workstation_output_text()
{
    g_pending_output_flush_scheduled = false;
    if (!g_output_edit || g_pending_output_text.isEmpty()) {
        g_pending_output_text.clear();
        return;
    }

    QString text;
    text.swap(g_pending_output_text);
    QScrollBar *scroll = g_output_edit->verticalScrollBar();
    const bool followTail = !scroll || scroll->value() >= scroll->maximum() - 2;
    const int oldValue = scroll ? scroll->value() : 0;

    QTextCursor cursor = g_output_edit->textCursor();
    cursor.movePosition(QTextCursor::End);
    cursor.insertText(text);

    if (followTail) {
        g_output_edit->setTextCursor(cursor);
        g_output_edit->ensureCursorVisible();
    } else if (scroll) {
        scroll->setValue(qMin(oldValue, scroll->maximum()));
    }

    // Ein verborgener Dialog darf durch neue Textausgabe nicht erscheinen.
    // Beim sichtbaren Dialog ist keinerlei Raise/TopMost pro Paket noetig;
    // die bestehenden 500-ms-Watchdogs sichern seine Lage bei Bedarf.
    if (g_output_visibility_enabled && g_output_dialog &&
        !g_output_dialog->isVisible()) {
        ensure_workstation_output_dialog_visible();
    }
}

void append_workstation_output(const OutputMessage &message)
{
    create_workstation_output_dialog();
    if (!g_output_edit || !g_output_dialog)
        return;

    if (message.debugThemeMode >= 0)
        apply_workstation_output_debug_theme(message.debugThemeMode);

    if (message.debugVisibility >= 0) {
        // Reihenfolge garantieren: alle vorangegangenen Texte zuerst rendern.
        flush_workstation_output_text();
        g_output_visibility_enabled = message.debugVisibility != 0;
        if (g_output_visibility_enabled) {
            g_output_reveal_on_next_write = true;
            ensure_workstation_output_dialog_visible();
        } else {
            g_output_dialog->hide();
        }
        if (message.text.empty() && !message.newline)
            return;
    }

    if (!message.text.empty()) {
        const int textSize = static_cast<int>(message.text.size());
        g_pending_output_text += message.latin1
            ? QString::fromLatin1(message.text.data(), textSize)
            : QString::fromUtf8(message.text.data(), textSize);
    }
    if (message.newline)
        g_pending_output_text += QLatin1Char('\n');

    if (g_pending_output_text.isEmpty())
        return;

    // Stage 320: Bereits das ERSTE DOW1-Textpaket muss das QDialog zeigen,
    // nicht erst der 16-ms-Timeout. Das wirkt auch auf direkt per CLI an
    // einen bereits residenten Runner uebergebene Programme.
    if (g_output_visibility_enabled && g_output_reveal_on_next_write) {
        g_output_reveal_on_next_write = false;
        ensure_workstation_output_dialog_visible();
    }

    // Grosses Burst-Paket unmittelbar ausgeben, sonst maximal eine
    // GUI-Aktualisierung pro Bildintervall einplanen.
    if (g_pending_output_text.size() >= 64 * 1024) {
        flush_workstation_output_text();
    } else if (!g_pending_output_flush_scheduled) {
        g_pending_output_flush_scheduled = true;
        QTimer::singleShot(16, QApplication::instance(), []() {
            flush_workstation_output_text();
        });
    }
}

UINT workstation_global_shutdown_message()
{
    static const UINT message = RegisterWindowMessageW(
        L"dBase2Many.D64Workstation.GlobalShutdown"
    );
    return message;
}

UINT workstation_restore_application_message()
{
    static const UINT message = RegisterWindowMessageW(
        L"dBase2Many.D64Workstation.RestoreApplication"
    );
    return message;
}

std::wstring normalize_path(const std::wstring &path)
{
    if (path.empty())
        return std::wstring();

    wchar_t fullPath[32768] = {0};
    const DWORD length = GetFullPathNameW(
        path.c_str(),
        static_cast<DWORD>(sizeof(fullPath) / sizeof(fullPath[0])),
        fullPath,
        nullptr
    );

    std::wstring result =
        (length > 0 && length < (sizeof(fullPath) / sizeof(fullPath[0])))
            ? std::wstring(fullPath, length)
            : path;

    for (wchar_t &ch : result) {
        if (ch == L'/')
            ch = L'\\';
        ch = static_cast<wchar_t>(std::towlower(ch));
    }
    return result;
}


std::vector<std::wstring> process_runner_arguments()
{
    // Stage 148: Nicht selbst versuchen, die Windows-Kommandozeile zu
    // zerlegen. Python subprocess.list2cmdline/CreateProcess und Windows
    // besitzen definierte Quote-/Backslash-Regeln, die der bisherige
    // Minimalparser nicht vollstaendig nachgebildet hat. CommandLineToArgvW
    // verwendet die native Windows-Auswertung und liefert exakt die
    // Argumentgrenzen des gestarteten Prozesses. argv[0] ist der Runner
    // selbst und wird hier bewusst nicht zurueckgegeben.
    std::vector<std::wstring> args;
    int argc = 0;
    LPWSTR *argv = CommandLineToArgvW(GetCommandLineW(), &argc);
    if (!argv)
        return args;

    for (int i = 1; i < argc; ++i)
        args.emplace_back(argv[i] ? argv[i] : L"");

    LocalFree(argv);
    return args;
}

std::wstring absolute_path(const std::wstring &path)
{
    if (path.empty())
        return std::wstring();

    wchar_t fullPath[32768] = {0};
    const DWORD length = GetFullPathNameW(
        path.c_str(),
        static_cast<DWORD>(sizeof(fullPath) / sizeof(fullPath[0])),
        fullPath,
        nullptr
    );
    if (length > 0 && length < (sizeof(fullPath) / sizeof(fullPath[0])))
        return std::wstring(fullPath, length);
    return path;
}

std::wstring parent_directory(const std::wstring &path)
{
    const std::wstring full = absolute_path(path);
    const std::wstring::size_type slash = full.find_last_of(L"\\/");
    if (slash == std::wstring::npos)
        return std::wstring();
    if (slash == 2 && full.size() >= 3 && full[1] == L':')
        return full.substr(0, 3);
    return full.substr(0, slash);
}

bool regular_file_exists(const std::wstring &path)
{
    const DWORD attributes = GetFileAttributesW(path.c_str());
    return attributes != INVALID_FILE_ATTRIBUTES &&
        (attributes & FILE_ATTRIBUTE_DIRECTORY) == 0;
}

bool pe_uses_console_subsystem(const std::wstring &path)
{
    HANDLE file = CreateFileW(
        path.c_str(),
        GENERIC_READ,
        FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE,
        nullptr,
        OPEN_EXISTING,
        FILE_ATTRIBUTE_NORMAL,
        nullptr
    );
    if (file == INVALID_HANDLE_VALUE)
        return false;

    bool console = false;
    IMAGE_DOS_HEADER dos{};
    DWORD got = 0;
    if (!ReadFile(file, &dos, sizeof(dos), &got, nullptr) ||
        got != sizeof(dos) || dos.e_magic != IMAGE_DOS_SIGNATURE) {
        CloseHandle(file);
        return false;
    }

    LARGE_INTEGER position{};
    position.QuadPart = dos.e_lfanew;
    if (!SetFilePointerEx(file, position, nullptr, FILE_BEGIN)) {
        CloseHandle(file);
        return false;
    }

    DWORD signature = 0;
    IMAGE_FILE_HEADER fileHeader{};
    WORD optionalMagic = 0;
    if (!ReadFile(file, &signature, sizeof(signature), &got, nullptr) ||
        got != sizeof(signature) || signature != IMAGE_NT_SIGNATURE ||
        !ReadFile(file, &fileHeader, sizeof(fileHeader), &got, nullptr) ||
        got != sizeof(fileHeader) ||
        !ReadFile(file, &optionalMagic, sizeof(optionalMagic), &got, nullptr) ||
        got != sizeof(optionalMagic)) {
        CloseHandle(file);
        return false;
    }

    position.QuadPart = dos.e_lfanew + sizeof(DWORD) + sizeof(IMAGE_FILE_HEADER);
    if (!SetFilePointerEx(file, position, nullptr, FILE_BEGIN)) {
        CloseHandle(file);
        return false;
    }

    if (optionalMagic == IMAGE_NT_OPTIONAL_HDR32_MAGIC) {
        IMAGE_OPTIONAL_HEADER32 optional{};
        if (ReadFile(file, &optional, sizeof(optional), &got, nullptr) &&
            got == sizeof(optional)) {
            console = optional.Subsystem == IMAGE_SUBSYSTEM_WINDOWS_CUI;
        }
    } else if (optionalMagic == IMAGE_NT_OPTIONAL_HDR64_MAGIC) {
        IMAGE_OPTIONAL_HEADER64 optional{};
        if (ReadFile(file, &optional, sizeof(optional), &got, nullptr) &&
            got == sizeof(optional)) {
            console = optional.Subsystem == IMAGE_SUBSYSTEM_WINDOWS_CUI;
        }
    }

    CloseHandle(file);
    return console;
}

bool file_contains_marker(
    const std::wstring &path,
    const char *marker,
    std::size_t markerLength)
{
    if (!marker || markerLength == 0)
        return false;

    HANDLE file = CreateFileW(
        path.c_str(),
        GENERIC_READ,
        FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE,
        nullptr,
        OPEN_EXISTING,
        FILE_ATTRIBUTE_NORMAL,
        nullptr
    );
    if (file == INVALID_HANDLE_VALUE)
        return false;

    LARGE_INTEGER size{};
    if (!GetFileSizeEx(file, &size) ||
        size.QuadPart <= 0 ||
        size.QuadPart > (128ll * 1024ll * 1024ll)) {
        CloseHandle(file);
        return false;
    }

    std::vector<char> data(static_cast<std::size_t>(size.QuadPart));
    DWORD total = 0;
    while (total < data.size()) {
        DWORD got = 0;
        const DWORD chunk = static_cast<DWORD>(
            std::min<std::size_t>(data.size() - total, 1024u * 1024u)
        );
        if (!ReadFile(file, data.data() + total, chunk, &got, nullptr) || !got)
            break;
        total += got;
    }
    CloseHandle(file);

    if (total < markerLength)
        return false;

    const char *begin = data.data();
    const char *end = begin + total;
    return std::search(begin, end, marker, marker + markerLength) != end;
}

bool file_contains_lazy_console_marker(const std::wstring &path)
{
    return file_contains_marker(
        path,
        D64_LAZY_CONSOLE_MARKER,
        sizeof(D64_LAZY_CONSOLE_MARKER) - 1
    );
}

bool file_contains_wfm_qt_output_marker(const std::wstring &path)
{
    return file_contains_marker(
        path,
        D64_WFM_QT_OUTPUT_MARKER,
        sizeof(D64_WFM_QT_OUTPUT_MARKER) - 1
    );
}

std::wstring runner_module_directory()
{
    wchar_t path[32768] = {0};
    const DWORD length = GetModuleFileNameW(
        nullptr, path, static_cast<DWORD>(sizeof(path) / sizeof(path[0]))
    );
    if (!length || length >= (sizeof(path) / sizeof(path[0])))
        return std::wstring();
    std::wstring value(path, length);
    const std::wstring::size_type slash = value.find_last_of(L"\\/");
    return slash == std::wstring::npos ? std::wstring() : value.substr(0, slash);
}

void log_runner_argument_error(
    const std::vector<std::wstring> &args,
    const std::wstring &error
)
{
    // Stage 148: Ein fehlerhafter automatischer Start darf den Benutzer nicht
    // mit der allgemeinen Usage-MessageBox unterbrechen. Die komplette
    // Diagnose bleibt stattdessen neben dem Runner erhalten.
    std::wstring directory = runner_module_directory();
    std::wstring path = directory.empty()
        ? L"d64_workstation_runner_error.log"
        : directory + L"\\d64_workstation_runner_error.log";

    HANDLE file = CreateFileW(
        path.c_str(), FILE_APPEND_DATA, FILE_SHARE_READ | FILE_SHARE_WRITE,
        nullptr, OPEN_ALWAYS, FILE_ATTRIBUTE_NORMAL, nullptr
    );
    if (file == INVALID_HANDLE_VALUE)
        return;

    std::wstring text = L"\r\n--- D64 Workstation Runner Argument Error ---\r\n";
    text += L"Reason: " + error + L"\r\n";
    text += L"CommandLine: ";
    const wchar_t *commandLine = GetCommandLineW();
    text += commandLine ? commandLine : L"";
    text += L"\r\nArguments:";
    for (std::size_t i = 0; i < args.size(); ++i) {
        text += L"\r\n  [" + std::to_wstring(i) + L"] = <" + args[i] + L">";
    }
    text += L"\r\n";

    const int utf8Length = WideCharToMultiByte(
        CP_UTF8, 0, text.c_str(), static_cast<int>(text.size()),
        nullptr, 0, nullptr, nullptr
    );
    if (utf8Length > 0) {
        std::vector<char> utf8(static_cast<std::size_t>(utf8Length));
        WideCharToMultiByte(
            CP_UTF8, 0, text.c_str(), static_cast<int>(text.size()),
            utf8.data(), utf8Length, nullptr, nullptr
        );
        DWORD written = 0;
        WriteFile(file, utf8.data(), static_cast<DWORD>(utf8.size()), &written, nullptr);
    }
    CloseHandle(file);
}

void show_runner_usage()
{
    MessageBoxW(
        nullptr,
        L"Direkter Start:\n\n"
        L"  d64_workstation_runner.exe <Anwendung.exe>\n"
        L"  d64_workstation_runner.exe --console <Anwendung.exe>\n"
        L"  d64_workstation_runner.exe --gui <Anwendung.exe>\n"
        L"  d64_workstation_runner.exe --dark|--light <Anwendung.exe>\n"
        L"  d64_workstation_runner.exe --debug-theme default|light|dark <Anwendung.exe>\n"
        L"  d64_workstation_runner.exe --cwd <Verzeichnis> <Anwendung.exe>\n\n"
        L"Ohne --console/--gui wird das PE-Subsystem automatisch erkannt.\n"
        L"Ohne Anwendung bleibt der Runner als kompatibler Pipe-Host aktiv.",
        L"D64 Workstation Runner",
        MB_OK | MB_ICONINFORMATION | MB_SETFOREGROUND
    );
}

bool parse_runner_arguments(
    const std::vector<std::wstring> &args,
    LaunchRequest &request,
    bool &hasRequest,
    bool &showHelp,
    std::wstring &error
)
{
    hasRequest = false;
    showHelp = false;
    error.clear();
    request = LaunchRequest();

    if (args.empty())
        return true;

    bool modeSpecified = false;
    std::wstring application;
    std::wstring workingDirectory;

    for (std::size_t i = 0; i < args.size(); ++i) {
        const std::wstring &arg = args[i];
        if (_wcsicmp(arg.c_str(), L"--help") == 0 ||
            _wcsicmp(arg.c_str(), L"-h") == 0 ||
            _wcsicmp(arg.c_str(), L"/?") == 0) {
            showHelp = true;
            return true;
        }
        if (_wcsicmp(arg.c_str(), L"--console") == 0) {
            request.consoleMode = true;
            modeSpecified = true;
            continue;
        }
        if (_wcsicmp(arg.c_str(), L"--gui") == 0) {
            request.consoleMode = false;
            modeSpecified = true;
            continue;
        }
        if (_wcsicmp(arg.c_str(), L"--dark") == 0) {
            request.themeMode = 1;
            continue;
        }
        if (_wcsicmp(arg.c_str(), L"--light") == 0) {
            request.themeMode = 0;
            continue;
        }
        if (_wcsicmp(arg.c_str(), L"--debug-theme") == 0) {
            if (i + 1 >= args.size()) {
                error = L"Nach --debug-theme fehlt der Wert default, light oder dark.";
                return false;
            }
            const std::wstring value = args[++i];
            if (_wcsicmp(value.c_str(), L"default") == 0)
                request.debugThemeMode = 0;
            else if (_wcsicmp(value.c_str(), L"light") == 0)
                request.debugThemeMode = 1;
            else if (_wcsicmp(value.c_str(), L"dark") == 0)
                request.debugThemeMode = 2;
            else {
                error = L"Ungueltiger Wert fuer --debug-theme: " + value;
                return false;
            }
            continue;
        }
        if (_wcsicmp(arg.c_str(), L"--cwd") == 0) {
            if (i + 1 >= args.size()) {
                error = L"Nach --cwd fehlt das Arbeitsverzeichnis.";
                return false;
            }
            workingDirectory = args[++i];
            continue;
        }
        if (arg.size() >= 2 && arg[0] == L'-') {
            error = L"Unbekannte Runner-Option: " + arg;
            return false;
        }
        if (!application.empty()) {
            error = L"Mehr als eine Anwendung wurde uebergeben: " + arg;
            return false;
        }
        application = arg;
    }

    if (application.empty()) {
        error = L"Es wurde eine Runner-Option, aber keine Anwendung.exe uebergeben.";
        return false;
    }

    application = absolute_path(application);
    if (!regular_file_exists(application)) {
        error = L"Die uebergebene Anwendung existiert nicht: " + application;
        return false;
    }

    if (workingDirectory.empty())
        workingDirectory = parent_directory(application);
    else
        workingDirectory = absolute_path(workingDirectory);

    request.application = application;
    request.workingDirectory = workingDirectory;
    if (!modeSpecified)
        request.consoleMode = pe_uses_console_subsystem(application);
    hasRequest = true;
    return true;
}

bool class_name_equals(HWND hwnd, const wchar_t *expected)
{
    if (!hwnd || !expected)
        return false;
    wchar_t className[256] = {0};
    if (!GetClassNameW(hwnd, className, 255))
        return false;
    return _wcsicmp(className, expected) == 0;
}

struct PropertyScanContext {
    bool found = false;
};

int CALLBACK scan_window_property(
    HWND,
    LPWSTR string,
    HANDLE,
    ULONG_PTR parameter
)
{
    PropertyScanContext *context =
        reinterpret_cast<PropertyScanContext *>(parameter);
    if (!context || context->found || !string)
        return FALSE;

    wchar_t atomName[256] = {0};
    const wchar_t *name = string;
    if (IS_INTRESOURCE(string)) {
        const ATOM atom = static_cast<ATOM>(reinterpret_cast<ULONG_PTR>(string));
        if (!GlobalGetAtomNameW(atom, atomName, 255))
            return TRUE;
        name = atomName;
    }

    constexpr std::size_t prefixLength =
        (sizeof(D64_APP_WINDOW_PREFIX) / sizeof(D64_APP_WINDOW_PREFIX[0])) - 1;
    if (_wcsnicmp(name, D64_APP_WINDOW_PREFIX, prefixLength) == 0) {
        context->found = true;
        return FALSE;
    }
    return TRUE;
}

bool has_d64_application_marker(HWND hwnd)
{
    if (!hwnd || !IsWindow(hwnd))
        return false;
    PropertyScanContext context;
    EnumPropsExW(hwnd, &scan_window_property, reinterpret_cast<LPARAM>(&context));
    return context.found;
}

bool is_workstation_panel(HWND hwnd)
{
    if (!hwnd)
        return false;
    return class_name_equals(hwnd, WORKSTATION_PANEL_CLASS) ||
           class_name_equals(hwnd, WORKSTATION_BOTTOM_PANEL_CLASS);
}

bool is_db_panel_click(const POINT &screenPoint)
{
    HWND hwnd = WindowFromPoint(screenPoint);
    if (!hwnd)
        return false;
    hwnd = GetAncestor(hwnd, GA_ROOT);
    if (!class_name_equals(hwnd, WORKSTATION_PANEL_CLASS))
        return false;

    POINT point = screenPoint;
    if (!ScreenToClient(hwnd, &point))
        return false;
    return point.x >= 0 && point.x < WORKSTATION_PANEL_WIDTH &&
           point.y >= WORKSTATION_DB_CLICK_TOP &&
           point.y < WORKSTATION_DB_CLICK_TOP + WORKSTATION_ITEM_HEIGHT;
}

bool is_candidate_application_window(HWND hwnd)
{
    if (!hwnd || !IsWindow(hwnd) || hwnd == g_host_window)
        return false;
    if (is_workstation_panel(hwnd))
        return false;
    if (GetPropW(hwnd, WORKSTATION_TOOL_WINDOW_PROPERTY) != nullptr)
        return false;
    if (!IsWindowVisible(hwnd))
        return false;

    const LONG_PTR style = GetWindowLongPtrW(hwnd, GWL_STYLE);
    const LONG_PTR exStyle = GetWindowLongPtrW(hwnd, GWL_EXSTYLE);
    if ((style & WS_CHILD) != 0 || (exStyle & WS_EX_TOOLWINDOW) != 0)
        return false;

    // Dialoge/Popups duerfen ihr normales Close-Verhalten behalten. Fuer die
    // Workstation-Semantik wird nur das Hauptfenster einer Anwendung versteckt.
    if (GetWindow(hwnd, GW_OWNER) != nullptr)
        return false;

    // d64qt5-Fenster besitzen bereits Stage-128-closeEvent()/Dialog-Restore.
    // Diese bestehende Logik darf der generische Runner nicht uebergehen.
    if (has_d64_application_marker(hwnd))
        return false;

    return true;
}

bool point_hits_close_button(HWND hwnd, const POINT &point)
{
    if (!is_candidate_application_window(hwnd))
        return false;

    DWORD_PTR hit = HTNOWHERE;
    const LPARAM packed = MAKELPARAM(
        static_cast<SHORT>(point.x),
        static_cast<SHORT>(point.y)
    );
    if (!SendMessageTimeoutW(
            hwnd,
            WM_NCHITTEST,
            0,
            packed,
            SMTO_ABORTIFHUNG | SMTO_BLOCK,
            100,
            &hit)) {
        return false;
    }
    return static_cast<LRESULT>(hit) == HTCLOSE;
}

void remember_hidden_window(HWND hwnd)
{
    if (!hwnd || !IsWindow(hwnd))
        return;
    if (std::find(g_hidden_windows.begin(), g_hidden_windows.end(), hwnd)
        == g_hidden_windows.end()) {
        g_hidden_windows.push_back(hwnd);
    }
}

void hide_application_window(HWND hwnd)
{
    if (!is_candidate_application_window(hwnd))
        return;

    DWORD pid = 0;
    GetWindowThreadProcessId(hwnd, &pid);

    remember_hidden_window(hwnd);
    ShowWindowAsync(hwnd, SW_HIDE);

    // Stage 114: Wenn das Hauptfenster eines vom Runner gestarteten
    // dBase-Programms ausgeblendet wird, muss dessen spaeter per
    // AllocConsole erzeugte Console mit ausgeblendet werden. Das Console-
    // Fenster laeuft typischerweise unter conhost.exe und kann deshalb nicht
    // ueber die PID des Formularfensters gefunden werden.
    if (pid) {
        for (ChildProcess &child : g_children) {
            if (child.pid != pid)
                continue;
            if (child.consoleWindow && IsWindow(child.consoleWindow)) {
                remember_hidden_window(child.consoleWindow);
                ShowWindowAsync(child.consoleWindow, SW_HIDE);
            }
            break;
        }
    }
}

struct RestoreMarkedContext {
    HWND host = nullptr;
    std::vector<HWND> restored;
};

BOOL CALLBACK restore_marked_window(HWND hwnd, LPARAM parameter)
{
    RestoreMarkedContext *context =
        reinterpret_cast<RestoreMarkedContext *>(parameter);
    if (!context || !hwnd || !IsWindow(hwnd) || hwnd == context->host)
        return TRUE;
    if (IsWindowVisible(hwnd))
        return TRUE;

    const LONG_PTR style = GetWindowLongPtrW(hwnd, GWL_STYLE);
    const LONG_PTR exStyle = GetWindowLongPtrW(hwnd, GWL_EXSTYLE);
    if ((style & WS_CHILD) != 0 || (exStyle & WS_EX_TOOLWINDOW) != 0)
        return TRUE;
    if (!has_d64_application_marker(hwnd))
        return TRUE;

    // Stage 124: markierte d64qt5/WFM-Fenster niemals direkt per Win32
    // einblenden. Der Zielprozess restauriert sich Qt-aware und erzwingt
    // danach ein vollstaendiges Style-/Paint-Refresh.
    PostMessageW(
        hwnd,
        workstation_restore_application_message(),
        0,
        0
    );
    context->restored.push_back(hwnd);
    return TRUE;
}

void restore_hidden_windows()
{
    HWND last = nullptr;
    for (auto it = g_hidden_windows.begin(); it != g_hidden_windows.end();) {
        HWND hwnd = *it;
        if (!hwnd || !IsWindow(hwnd)) {
            it = g_hidden_windows.erase(it);
            continue;
        }
        ShowWindowAsync(hwnd, SW_RESTORE);
        ShowWindowAsync(hwnd, SW_SHOW);
        last = hwnd;
        ++it;
    }

    // Wenn der Runner OWNER ist und spaeter eine d64qt5-Anwendung JOINED,
    // liegt deren DB-Callback in einem anderen Prozess. Stage 124 delegiert
    // das Wiederherstellen markierter Fenster deshalb per registrierter
    // Nachricht an den Qt-Eventloop des Zielprozesses.
    const wchar_t *desktopName = D64WorkstationDesktopName();
    if (desktopName && *desktopName) {
        HDESK desktop = OpenDesktopW(
            desktopName,
            0,
            FALSE,
            DESKTOP_ENUMERATE | DESKTOP_READOBJECTS | DESKTOP_WRITEOBJECTS
        );
        if (desktop) {
            RestoreMarkedContext context;
            context.host = g_host_window;
            EnumDesktopWindows(
                desktop,
                &restore_marked_window,
                reinterpret_cast<LPARAM>(&context)
            );
            if (!context.restored.empty())
                last = context.restored.back();
            CloseDesktop(desktop);
        }
    }

    if (last && IsWindow(last)) {
        DWORD pid = 0;
        GetWindowThreadProcessId(last, &pid);
        if (pid)
            AllowSetForegroundWindow(pid);

        // Stage 124: Ein markiertes d64qt5/WFM-Fenster wurde oben bereits
        // per RestoreApplication-Nachricht an seinen eigenen Qt-Eventloop
        // delegiert. SWP_SHOWWINDOW hier wuerde den Qt-Restore erneut umgehen.
        if (!has_d64_application_marker(last)) {
            SetWindowPos(
                last, HWND_TOP, 0, 0, 0, 0,
                SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW
            );
            BringWindowToTop(last);
            SetForegroundWindow(last);
        }
    }
}

LRESULT CALLBACK runner_mouse_proc(int nCode, WPARAM wParam, LPARAM lParam)
{
    if (nCode < 0)
        return CallNextHookEx(g_mouse_hook, nCode, wParam, lParam);

    const MSLLHOOKSTRUCT *mouse =
        reinterpret_cast<const MSLLHOOKSTRUCT *>(lParam);
    if (!mouse)
        return CallNextHookEx(g_mouse_hook, nCode, wParam, lParam);

    if (wParam == WM_LBUTTONUP && is_db_panel_click(mouse->pt)) {
        restore_hidden_windows();
        return CallNextHookEx(g_mouse_hook, nCode, wParam, lParam);
    }

    if (wParam == WM_LBUTTONDOWN) {
        HWND hwnd = WindowFromPoint(mouse->pt);
        if (hwnd)
            hwnd = GetAncestor(hwnd, GA_ROOT);
        if (point_hits_close_button(hwnd, mouse->pt)) {
            g_close_candidate = hwnd;
            return 1;
        }
        g_close_candidate = nullptr;
    } else if (wParam == WM_LBUTTONUP && g_close_candidate) {
        HWND candidate = g_close_candidate;
        g_close_candidate = nullptr;
        hide_application_window(candidate);
        return 1;
    }

    return CallNextHookEx(g_mouse_hook, nCode, wParam, lParam);
}

bool install_mouse_guard()
{
    if (g_mouse_hook)
        return true;
    g_mouse_hook = SetWindowsHookExW(
        WH_MOUSE_LL,
        &runner_mouse_proc,
        GetModuleHandleW(nullptr),
        0
    );
    return g_mouse_hook != nullptr;
}

void remove_mouse_guard()
{
    if (!g_mouse_hook)
        return;
    UnhookWindowsHookEx(g_mouse_hook);
    g_mouse_hook = nullptr;
}

LRESULT CALLBACK runner_keyboard_proc(int nCode, WPARAM wParam, LPARAM lParam)
{
    if (nCode < 0)
        return CallNextHookEx(g_keyboard_hook, nCode, wParam, lParam);

    if (wParam != WM_KEYDOWN && wParam != WM_SYSKEYDOWN)
        return CallNextHookEx(g_keyboard_hook, nCode, wParam, lParam);

    const KBDLLHOOKSTRUCT *kbd =
        reinterpret_cast<const KBDLLHOOKSTRUCT *>(lParam);
    if (!kbd)
        return CallNextHookEx(g_keyboard_hook, nCode, wParam, lParam);

    const bool alt =
        ((kbd->flags & LLKHF_ALTDOWN) != 0) ||
        ((GetAsyncKeyState(VK_MENU) & 0x8000) != 0);

    if (alt && kbd->vkCode == VK_F4) {
        HWND focused = GetForegroundWindow();
        if (focused)
            focused = GetAncestor(focused, GA_ROOTOWNER);
        if (!focused)
            focused = GetForegroundWindow();

        if (is_candidate_application_window(focused)) {
            hide_application_window(focused);
            return 1;
        }
    }

    return CallNextHookEx(g_keyboard_hook, nCode, wParam, lParam);
}

bool install_keyboard_guard()
{
    if (g_keyboard_hook)
        return true;
    g_keyboard_hook = SetWindowsHookExW(
        WH_KEYBOARD_LL,
        &runner_keyboard_proc,
        GetModuleHandleW(nullptr),
        0
    );
    return g_keyboard_hook != nullptr;
}

void remove_keyboard_guard()
{
    if (!g_keyboard_hook)
        return;
    UnhookWindowsHookEx(g_keyboard_hook);
    g_keyboard_hook = nullptr;
}


bool switch_to_workstation_desktop();

struct ConsoleModalWindowContext {
    DWORD pid = 0;
    std::vector<HWND> *disabled = nullptr;
};

BOOL CALLBACK disable_child_window_for_console_modal(HWND hwnd, LPARAM value)
{
    ConsoleModalWindowContext *ctx =
        reinterpret_cast<ConsoleModalWindowContext *>(value);
    if (!ctx || !ctx->disabled || !hwnd || !IsWindow(hwnd))
        return TRUE;

    DWORD pid = 0;
    GetWindowThreadProcessId(hwnd, &pid);
    if (pid != ctx->pid)
        return TRUE;

    const LONG_PTR style = GetWindowLongPtrW(hwnd, GWL_STYLE);
    if ((style & WS_CHILD) != 0)
        return TRUE;

    if (IsWindowEnabled(hwnd)) {
        EnableWindow(hwnd, FALSE);
        ctx->disabled->push_back(hwnd);
    }
    return TRUE;
}

void end_console_modal_test(ChildProcess &child)
{
    if (!child.consoleModalTest && child.modalDisabledWindows.empty())
        return;

    for (HWND hwnd : child.modalDisabledWindows) {
        if (hwnd && IsWindow(hwnd))
            EnableWindow(hwnd, TRUE);
    }
    child.modalDisabledWindows.clear();

    if (child.consoleWindow && IsWindow(child.consoleWindow)) {
        SetWindowPos(
            child.consoleWindow,
            HWND_NOTOPMOST,
            0,
            0,
            0,
            0,
            SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE
        );
    }
    child.consoleModalTest = false;
}

void begin_console_modal_test(ChildProcess &child)
{
    if (child.consoleModalTest)
        return;
    if (!child.consoleWindow || !IsWindow(child.consoleWindow))
        return;
    if (!IsWindowVisible(child.consoleWindow))
        return;

    // Stage 115 TEST: Die Console bleibt als echtes Win32-Console-HWND
    // bestehen, wird aber modal emuliert. Die Formulare des gestarteten
    // Prozesses auf D64Workstation werden deaktiviert und die Console wird
    // TOPMOST/Vordergrund. So laesst sich eindeutig erkennen, auf welchem
    // Desktop der Console-Host das HWND erzeugt hat.
    switch_to_workstation_desktop();

    ConsoleModalWindowContext context;
    context.pid = child.pid;
    context.disabled = &child.modalDisabledWindows;
    EnumWindows(
        &disable_child_window_for_console_modal,
        reinterpret_cast<LPARAM>(&context)
    );

    ShowWindowAsync(child.consoleWindow, SW_RESTORE);
    ShowWindowAsync(child.consoleWindow, SW_SHOW);
    SetWindowPos(
        child.consoleWindow,
        HWND_TOPMOST,
        0,
        0,
        0,
        0,
        SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW
    );

    DWORD consolePid = 0;
    GetWindowThreadProcessId(child.consoleWindow, &consolePid);
    if (consolePid)
        AllowSetForegroundWindow(consolePid);
    BringWindowToTop(child.consoleWindow);
    SetForegroundWindow(child.consoleWindow);
    child.consoleModalTest = true;

    // Stage 272: Console und DEBUG-Dialog sind beide TOPMOST. Bisher wurde
    // die Console nach dem 500-ms-Watchdog zuletzt nach oben geholt und konnte
    // den DEBUG-Dialog vollstaendig verdecken. Das DEBUG-Fenster wird deshalb
    // unmittelbar danach erneut in den sichtbaren TOPMOST-Bereich gehoben,
    // ohne der Console den Eingabefokus wegzunehmen.
    ensure_workstation_output_dialog_visible();
}

void cleanup_finished_children()
{
    bool childExited = false;
    for (auto it = g_children.begin(); it != g_children.end();) {
        if (!it->process) {
            end_console_modal_test(*it);
            it = g_children.erase(it);
            childExited = true;
            continue;
        }
        if (WaitForSingleObject(it->process, 0) == WAIT_OBJECT_0) {
            // Stage 273: ExitProcess() beendet ausschliesslich das uebergebene
            // Programm. Der Runner/Workstation-OWNER bleibt resident. Damit
            // bleibt das DEBUG-Fenster samt letzter Write/WriteLn-Ausgabe bis
            // zum grossen Workstation-X erhalten.
            end_console_modal_test(*it);
            CloseHandle(it->process);
            it = g_children.erase(it);
            childExited = true;
            continue;
        }
        ++it;
    }

    if (childExited && !g_leave_started) {
        switch_to_workstation_desktop();
        ensure_workstation_output_dialog_visible();
    }
}

ChildProcess *find_running_child(const std::wstring &canonicalPath)
{
    cleanup_finished_children();
    for (ChildProcess &child : g_children) {
        if (_wcsicmp(child.canonicalPath.c_str(), canonicalPath.c_str()) == 0)
            return &child;
    }
    return nullptr;
}

struct ActivateChildWindowContext
{
    DWORD pid;
    HWND target;
    HWND fallbackTarget;
};

BOOL CALLBACK activate_child_window_enum_proc(HWND hwnd, LPARAM value)
{
    ActivateChildWindowContext *ctx =
        reinterpret_cast<ActivateChildWindowContext *>(value);
    if (!ctx)
        return FALSE;

    DWORD windowPid = 0;
    GetWindowThreadProcessId(hwnd, &windowPid);
    if (windowPid != ctx->pid)
        return TRUE;

    const LONG_PTR style = GetWindowLongPtrW(hwnd, GWL_STYLE);
    const LONG_PTR exStyle = GetWindowLongPtrW(hwnd, GWL_EXSTYLE);
    if ((style & WS_CHILD) != 0 || (exStyle & WS_EX_TOOLWINDOW) != 0)
        return TRUE;
    if (GetPropW(hwnd, WORKSTATION_TOOL_WINDOW_PROPERTY) != nullptr)
        return TRUE;

    // Stage 124: Ein von d64qt5 markiertes Hauptfenster ist fuer den
    // DB-Relaunch immer die erste Wahl. Die WFM-Runtime soll ihr Fenster
    // selbst im eigenen Qt-Eventloop wiederherstellen, statt dass der Runner
    // es per ShowWindowAsync am Qt-Zustand vorbei sichtbar macht.
    if (has_d64_application_marker(hwnd)) {
        ctx->target = hwnd;
        return FALSE;
    }

    if (!ctx->fallbackTarget)
        ctx->fallbackTarget = hwnd;
    return TRUE;
}

bool switch_to_workstation_desktop()
{
    const wchar_t *desktopName = D64WorkstationDesktopName();
    if (!desktopName || !*desktopName)
        desktopName = L"D64Workstation";

    HDESK desktop = OpenDesktopW(
        desktopName,
        0,
        FALSE,
        DESKTOP_SWITCHDESKTOP |
        DESKTOP_ENUMERATE |
        DESKTOP_READOBJECTS |
        DESKTOP_WRITEOBJECTS
    );
    if (!desktop)
        return false;

    // Stage 322: Desktop-Umschalten ist teuer (Synchronisation mit
    // Desktop-Kompositor/Input). Nur umschalten, wenn der sichtbare
    // Eingabedesktop tatsaechlich ein anderer ist.
    bool alreadyActive = false;
    HDESK input = OpenInputDesktop(0, FALSE, DESKTOP_READOBJECTS);
    if (input) {
        wchar_t name[128] = {};
        DWORD length = 0;
        if (GetUserObjectInformationW(input, UOI_NAME, name,
                sizeof(name), &length) &&
            _wcsicmp(name, desktopName) == 0) {
            alreadyActive = true;
        }
        CloseDesktop(input);
    }
    const BOOL ok = alreadyActive ? TRUE : SwitchDesktop(desktop);
    CloseDesktop(desktop);
    return ok != FALSE;
}

bool discover_child_console_window(ChildProcess &child, bool makeVisible = true)
{
    if (!child.process || !child.pid)
        return false;
    if (WaitForSingleObject(child.process, 0) == WAIT_OBJECT_0)
        return false;

    if (child.consoleWindow && IsWindow(child.consoleWindow)) {
        if (makeVisible) {
            ShowWindowAsync(child.consoleWindow, SW_RESTORE);
            ShowWindowAsync(child.consoleWindow, SW_SHOW);
        }
        return true;
    }

    child.consoleWindow = nullptr;

    /*
     * Stage 114:
     * GetConsoleWindow() im GUI-Runner liefert nicht die Console eines
     * fremden Prozesses. Ausserdem gehoert das sichtbare Console-HWND unter
     * modernen Windows-Versionen normalerweise conhost.exe und wird daher
     * von EnumWindows(pid == child.pid) niemals gefunden.
     *
     * AttachConsole(child.pid) ist hier nur ein kurzer Discovery-Schritt:
     * der Runner haengt sich an dieselbe Console, liest deren HWND mit
     * GetConsoleWindow() und trennt sich sofort wieder. FreeConsole() wirkt
     * dabei nur auf den Runner; das dBase-Kind bleibt an seiner Console.
     */
    if (GetConsoleWindow() != nullptr)
        return false; // Runner besitzt unerwartet selbst eine Console.

    if (!AttachConsole(child.pid))
        return false; // Das Kind hat (noch) keine Console.

    HWND consoleWindow = GetConsoleWindow();
    FreeConsole();

    if (!consoleWindow || !IsWindow(consoleWindow))
        return false;

    child.consoleWindow = consoleWindow;
    switch_to_workstation_desktop();

    if (!makeVisible) {
        // Fuer dBase-GUI-Programme wird die Console bereits vom Runner auf
        // dem richtigen Desktop erzeugt, bleibt aber bis zum ersten ?/??
        // unsichtbar. Der generierte __dbase_console_ensure-Pfad zeigt genau
        // dieses HWND spaeter mit ShowWindow(SW_SHOW) an.
        ShowWindowAsync(consoleWindow, SW_HIDE);
        return true;
    }

    ShowWindowAsync(consoleWindow, SW_RESTORE);
    ShowWindowAsync(consoleWindow, SW_SHOW);

    RECT rect = {};
    if (GetWindowRect(consoleWindow, &rect)) {
        D64WorkstationConstrainMovingRect(&rect);
        SetWindowPos(
            consoleWindow,
            HWND_TOPMOST,
            rect.left,
            rect.top,
            0,
            0,
            SWP_NOSIZE | SWP_NOACTIVATE | SWP_SHOWWINDOW
        );
    } else {
        SetWindowPos(
            consoleWindow,
            HWND_TOPMOST,
            0,
            0,
            0,
            0,
            SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE | SWP_SHOWWINDOW
        );
    }

    DWORD consolePid = 0;
    GetWindowThreadProcessId(consoleWindow, &consolePid);
    if (consolePid)
        AllowSetForegroundWindow(consolePid);
    BringWindowToTop(consoleWindow);
    return true;
}

void discover_child_console_windows()
{
    cleanup_finished_children();
    for (ChildProcess &child : g_children) {
        if (!child.consoleWindow || !IsWindow(child.consoleWindow)) {
            end_console_modal_test(child);
            discover_child_console_window(child);
        }

        if (child.consoleWindow && IsWindow(child.consoleWindow)) {
            if (IsWindowVisible(child.consoleWindow))
                begin_console_modal_test(child);
            else
                end_console_modal_test(child);
        }
    }
}

bool activate_child_windows(DWORD pid)
{
    ActivateChildWindowContext context = {};
    context.pid = pid;
    context.target = nullptr;
    context.fallbackTarget = nullptr;

    /*
     * Der Runner-GUI-Thread wurde durch D64WorkstationPrepare() bereits an
     * D64Workstation gebunden. EnumWindows() sieht deshalb genau die Fenster
     * dieses Desktops.
     */
    EnumWindows(
        &activate_child_window_enum_proc,
        reinterpret_cast<LPARAM>(&context)
    );

    if (!context.target)
        context.target = context.fallbackTarget;
    if (!context.target)
        return false;

    /*
     * Stage 254:
     * Eine generische, vom Runner gestartete PE-GUI besitzt keine eigene
     * d64qt5-Workstation-Runtime. Deshalb kann sie D64WorkstationActivate()
     * nicht selbst aufrufen. Der Runner macht das Sichtbarmachen hier
     * stellvertretend.
     */
    switch_to_workstation_desktop();

    if (has_d64_application_marker(context.target)) {
        // Stage 124: Qt-aware Restore. Das versteckte WFM-Hauptfenster bleibt
        // Eigentum seines Prozesses; dort werden show()/Style/Paint im
        // laufenden Qt-Eventloop ausgefuehrt.
        PostMessageW(
            context.target,
            workstation_restore_application_message(),
            0,
            0
        );
        AllowSetForegroundWindow(pid);
        return true;
    }

    ShowWindowAsync(context.target, SW_RESTORE);
    ShowWindowAsync(context.target, SW_SHOW);

    SetWindowPos(
        context.target,
        HWND_TOP,
        0,
        0,
        0,
        0,
        SWP_NOMOVE |
        SWP_NOSIZE |
        SWP_SHOWWINDOW
    );

    AllowSetForegroundWindow(pid);
    BringWindowToTop(context.target);
    SetForegroundWindow(context.target);
    return true;
}

bool wait_for_runner_output_pipe_ready(DWORD timeoutMs)
{
    const DWORD started = GetTickCount();
    while (!g_pipe_stop.load()) {
        if (g_pipe_ready.load())
            return true;
        if (static_cast<DWORD>(GetTickCount() - started) >= timeoutMs)
            return false;
        Sleep(5);
    }
    return false;
}

bool prepare_debug_window_before_child_start()
{
    // Stage 322: Workstation und DEBUG-Dialog sind zu diesem Zeitpunkt
    // bereits sichtbar. Keine mehrfachen synchronen RedrawWindow() /
    // UpdateWindow() / processEvents() in der Startbarriere. Die Pipe
    // muss empfangsbereit sein, bevor das Kind loslaufen darf.
    if (!switch_to_workstation_desktop())
        return false;
    ensure_workstation_output_dialog_visible();
    return wait_for_runner_output_pipe_ready(1500);
}

bool launch_program(const LaunchRequest &request)
{
    if (request.application.empty())
        return false;

    // Der zuletzt uebergebene Startauftrag wird zum Ziel des DB-Icons.
    // Auch Pipe-/CLI-Starts aktualisieren damit konsistent dieselbe Anwendung.
    g_db_launch_request = request;
    g_has_db_launch_request = true;

    const std::wstring canonical = normalize_path(request.application);
    if (canonical.empty())
        return false;

    if (ChildProcess *existing = find_running_child(canonical)) {
        switch_to_workstation_desktop();
        activate_child_windows(existing->pid);
        if (!existing->consoleWindow || !IsWindow(existing->consoleWindow))
            discover_child_console_window(*existing);
        restore_hidden_windows();
        ensure_workstation_output_dialog_visible();
        return true;
    }

    // Stage 318: Fuer ein NEUES Programm startet die Debug-Sichtbarkeit
    // neutral wie bisher. Ein laufender Prozess behaelt bei DB-Reaktivierung
    // hingegen sein vorheriges SET DEBUG OFF.
    g_output_visibility_enabled = true;
    g_output_reveal_on_next_write = true;

    // Stage 273: Nicht nur "show before launch_program", sondern eine echte
    // Startbarriere vor CreateProcess/ResumeThread. So kann selbst ein sehr
    // kurzes Pascal-Programm sofort WriteLn() ausfuehren und findet den
    // DEBUG-Empfaenger bereits vollstaendig betriebsbereit vor.
    if (!prepare_debug_window_before_child_start())
        return false;

    std::wstring desktopSpec = L"WinSta0\\";
    const wchar_t *desktopName = D64WorkstationDesktopName();
    desktopSpec += (desktopName && *desktopName) ? desktopName : L"D64Workstation";

    std::wstring commandLine = L"\"";
    commandLine += request.application;
    commandLine += L"\"";
    std::vector<wchar_t> command(commandLine.begin(), commandLine.end());
    command.push_back(L'\0');

    // Stage 114: Native dBase-GUI-Programme tragen einen Marker im PE.
    // Nur fuer diese Programme reserviert der Runner eine Console bereits
    // beim CreateProcess auf dem expliziten Workstation-Desktop. Sie wird
    // vor dem ersten Instruktionslauf versteckt und erst beim ersten ?/??
    // vom generierten AllocConsole-/ShowWindow-Pfad sichtbar gemacht.
    // Stage 116: WFM-GUIs mit Qt-Ausgabedialog tragen weiterhin den
    // historischen Core-Marker im unbenutzten Basis-Shell. Der neue Marker
    // hat Vorrang und verhindert CREATE_NEW_CONSOLE/Modal-Test vollstaendig.
    // Stage 123: WFM nicht nur ueber den historischen Marker erkennen.
    // Der interne PE-Writer kann unreferenzierte .data-Marker verwerfen;
    // echte WFM-Programme lassen sich dagegen stabil an ihren Runtime-Imports
    // DBaseQtInitializeGui + DBaseQtFormOpen erkennen. Genau dieser Fall
    // tritt bei Form1.exe auf.
    const bool wfmRuntimeImports =
        file_contains_marker(
            request.application,
            "DBaseQtInitializeGui",
            sizeof("DBaseQtInitializeGui") - 1
        ) &&
        file_contains_marker(
            request.application,
            "DBaseQtFormOpen",
            sizeof("DBaseQtFormOpen") - 1
        );
    const bool wfmQtOutput =
        !request.consoleMode &&
        (file_contains_wfm_qt_output_marker(request.application) ||
         wfmRuntimeImports);
    const bool lazyDBaseConsole =
        !request.consoleMode &&
        !wfmQtOutput &&
        file_contains_lazy_console_marker(request.application);

    STARTUPINFOW startup;
    ZeroMemory(&startup, sizeof(startup));
    startup.cb = sizeof(startup);
    startup.lpDesktop = const_cast<LPWSTR>(desktopSpec.c_str());
    // Stage 113: STARTUPINFO gilt laut Win32 auch fuer eine Console, die das
    // Kind spaeter per AllocConsole() erzeugt. Der Runner selbst ist
    // unsichtbar; deshalb SW_SHOWNORMAL explizit vorgeben, damit eine lazy
    // dBase-Console auf D64Workstation nicht mit einem versteckten Show-State
    // startet.
    startup.dwFlags |= STARTF_USESHOWWINDOW;
    startup.wShowWindow = SW_SHOWNORMAL;

    PROCESS_INFORMATION processInfo;
    ZeroMemory(&processInfo, sizeof(processInfo));

    // Stage 274: Fuer den GUI->Runner-Console-Pfad wird echtes STDOUT/STDERR
    // umgeleitet. Das ist absichtlich auf Runner-Ebene geloest: auch bereits
    // gebaute/komprimierte Pascal-EXEs, deren Runtime keinen DOW1-Spiegel
    // enthaelt, schreiben damit in dasselbe DEBUG-Fenster.
    const bool captureStandardOutput =
        request.consoleMode && request.debugConsoleOnly;
    HANDLE childStdoutRead = nullptr;
    HANDLE childStdoutWrite = nullptr;
    HANDLE childStdin = nullptr;

    if (captureStandardOutput) {
        SECURITY_ATTRIBUTES inheritAttributes{};
        inheritAttributes.nLength = sizeof(inheritAttributes);
        inheritAttributes.bInheritHandle = TRUE;

        if (!CreatePipe(
                &childStdoutRead,
                &childStdoutWrite,
                &inheritAttributes,
                0)) {
            return false;
        }

        // Nur die Schreibseite darf ins Kind vererbt werden. Haelt das Kind
        // versehentlich auch die Leseseite, koennte EOF nie erkannt werden.
        if (!SetHandleInformation(
                childStdoutRead, HANDLE_FLAG_INHERIT, 0)) {
            CloseHandle(childStdoutRead);
            CloseHandle(childStdoutWrite);
            return false;
        }

        // STARTF_USESTDHANDLES verlangt einen gueltigen Satz von drei Handles.
        // Fuer Stage 274 ist das DEBUG-Fenster ein reiner Ausgabekanal; ReadLn
        // bleibt eine spaetere, getrennte STDIN-Erweiterung.
        childStdin = CreateFileW(
            L"NUL",
            GENERIC_READ,
            FILE_SHARE_READ | FILE_SHARE_WRITE,
            &inheritAttributes,
            OPEN_EXISTING,
            FILE_ATTRIBUTE_NORMAL,
            nullptr
        );
        if (childStdin == INVALID_HANDLE_VALUE) {
            childStdin = nullptr;
            CloseHandle(childStdoutRead);
            CloseHandle(childStdoutWrite);
            return false;
        }

        startup.dwFlags |= STARTF_USESTDHANDLES;
        startup.hStdInput = childStdin;
        startup.hStdOutput = childStdoutWrite;
        startup.hStdError = childStdoutWrite;
    }

    // Stage 273: Jede Ziel-EXE wird zunaechst suspendiert erzeugt. Der Runner
    // gibt den Hauptthread erst nach sichtbarem DEBUG-Fenster und bereiter
    // DOW1-Pipe frei. Dadurch gehen auch Ausgaben direkt am Programmeinstieg
    // nicht verloren.
    DWORD creationFlags =
        CREATE_UNICODE_ENVIRONMENT |
        CREATE_NEW_PROCESS_GROUP |
        CREATE_SUSPENDED;

    if (request.consoleMode && request.debugConsoleOnly) {
        // GUI->Runner Console-Programme werden mit unsichtbarer Console
        // gestartet. STDOUT/STDERR zeigen ueber die geerbte anonyme Pipe
        // direkt auf das residente DEBUG-Fenster des Runners.
        creationFlags |= CREATE_NO_WINDOW;
    } else if (request.consoleMode) {
        // Legacy/CLI-Verhalten bleibt verfuegbar.
        creationFlags |= CREATE_NEW_CONSOLE;
    } else if (lazyDBaseConsole) {
        // Die Console muss auf dem in startup.lpDesktop angegebenen
        // D64Workstation-Desktop entstehen. Der suspendierte Hauptthread
        // verhindert ein Aufblitzen, bevor der Runner das HWND versteckt.
        creationFlags |= CREATE_NEW_CONSOLE;
    }

    // Stage 271-Kompatibilitaet: GUI-/Legacy-Pfade duerfen weiterhin den
    // Runtime-DOW1-Spiegel verwenden. Beim Stage-274-STDOUT-Capture wird der
    // Spiegel dagegen bewusst NICHT aktiviert, sonst wuerde eine neue Runtime
    // dieselbe WriteLn-Ausgabe doppelt ins DEBUG-Fenster senden.
    const bool enableRuntimeDebugMirror = !captureStandardOutput;
    std::wstring previousDebugOutputEnv;
    bool hadPreviousDebugOutputEnv = false;
    if (enableRuntimeDebugMirror) {
        const DWORD required = GetEnvironmentVariableW(
            RUNNER_DEBUG_OUTPUT_ENV, nullptr, 0
        );
        if (required > 0) {
            std::vector<wchar_t> previous(required);
            const DWORD copied = GetEnvironmentVariableW(
                RUNNER_DEBUG_OUTPUT_ENV, previous.data(), required
            );
            if (copied > 0 && copied < required) {
                previousDebugOutputEnv.assign(previous.data(), copied);
                hadPreviousDebugOutputEnv = true;
            }
        }
        SetEnvironmentVariableW(RUNNER_DEBUG_OUTPUT_ENV, L"1");
    }

    const BOOL ok = CreateProcessW(
        request.application.c_str(),
        command.data(),
        nullptr,
        nullptr,
        captureStandardOutput ? TRUE : FALSE,
        creationFlags,
        nullptr,
        request.workingDirectory.empty()
            ? nullptr
            : request.workingDirectory.c_str(),
        &startup,
        &processInfo
    );

    if (enableRuntimeDebugMirror) {
        if (hadPreviousDebugOutputEnv) {
            SetEnvironmentVariableW(
                RUNNER_DEBUG_OUTPUT_ENV, previousDebugOutputEnv.c_str()
            );
        } else {
            SetEnvironmentVariableW(RUNNER_DEBUG_OUTPUT_ENV, nullptr);
        }
    }

    // Der Parent darf die geerbten Kind-Seiten unmittelbar nach CreateProcess
    // schliessen. Nur dadurch sieht der Reader nach ExitProcess() sicher EOF.
    if (childStdoutWrite) {
        CloseHandle(childStdoutWrite);
        childStdoutWrite = nullptr;
    }
    if (childStdin) {
        CloseHandle(childStdin);
        childStdin = nullptr;
    }

    if (!ok) {
        if (childStdoutRead)
            CloseHandle(childStdoutRead);
        return false;
    }

    ChildProcess child;
    child.canonicalPath = canonical;
    child.process = processInfo.hProcess;
    child.pid = processInfo.dwProcessId;
    g_children.push_back(child);

    if (captureStandardOutput && childStdoutRead) {
        // Reader vor ResumeThread starten. Selbst wenn der OS-Scheduler den
        // Thread erst spaeter ausfuehrt, puffert die Pipe die ersten Bytes;
        // damit kann ein extrem kurzes Programm unmittelbar WriteLn +
        // ExitProcess ausfuehren, ohne Ausgabe zu verlieren.
        start_child_standard_output_capture(
            childStdoutRead,
            processInfo.dwProcessId,
            request.debugThemeMode
        );
        childStdoutRead = nullptr;
    }

    if (lazyDBaseConsole) {
        ChildProcess &created = g_children.back();
        // CREATE_NEW_CONSOLE wird durch CreateProcess angelegt, bevor der
        // suspendierte Hauptthread dBase-Code ausfuehrt. Ein kurzer Retry
        // deckt langsame Console-Host-Initialisierung ab; sichtbar wird sie
        // erst spaeter durch den expliziten dBase-Console-Pfad.
        const DWORD consoleDeadline = GetTickCount() + 1000;
        while (!discover_child_console_window(created, false)) {
            if (static_cast<LONG>(GetTickCount() - consoleDeadline) >= 0)
                break;
            Sleep(10);
        }
    }

    // Noch einmal unmittelbar vor ResumeThread zeichnen. Zwischen CreateProcess
    // und hier kann Windows neue TOPMOST-Fenster/Console-Hosts angelegt haben.
    // Der Zielcode hat bis zu diesem Punkt noch keine einzige Instruktion
    // ausgefuehrt.
    switch_to_workstation_desktop();
    ensure_workstation_output_dialog_visible();
    // Stage 322: Der Qt-Eventloop ist bereits aktiv. Ein verschachteltes
    // processEvents() mitten in der Kindprozess-Erzeugung kann Fenster-
    // Ereignisse reentrant ausfuehren und verzoegert die Freigabe.
    const DWORD resumeResult = ResumeThread(processInfo.hThread);
    CloseHandle(processInfo.hThread);
    if (resumeResult == static_cast<DWORD>(-1)) {
        TerminateProcess(processInfo.hProcess, 1);
        return false;
    }

    // Stage 322: Ein gepacktes WFM-EXE gibt seine Import-Marker nicht
    // zwingend preis. Generische Fenstererkennung deshalb asynchron via Qt:
    // weder WaitForInputIdle(1500) noch bis zu 3 Sekunden Sleep/EnumWindows
    // duerfen die Ereignisschleife des Workstation-Runners blockieren.
    if (!request.consoleMode) {
        if (!wfmQtOutput) {
            const DWORD pid = processInfo.dwProcessId;
            const DWORD started = GetTickCount();
            QTimer *activationTimer = new QTimer(QApplication::instance());
            activationTimer->setInterval(50);
            QObject::connect(activationTimer, &QTimer::timeout,
                QApplication::instance(), [activationTimer, pid, started]() {
                // Qt-WFM kann seine eigene Workstation-Aktivierung bereits
                // durchgefuehrt haben. Bei generischen Programmen wird das
                // erste Hauptfenster weiterhin erkannt und aktiviert.
                bool running = false;
                for (const ChildProcess &entry : g_children) {
                    if (entry.pid == pid && entry.process &&
                        WaitForSingleObject(entry.process, 0) == WAIT_TIMEOUT) {
                        running = true;
                        break;
                    }
                }
                const bool timedOut =
                    static_cast<DWORD>(GetTickCount() - started) >= 3000;
                if (!running || timedOut || activate_child_windows(pid)) {
                    activationTimer->stop();
                    activationTimer->deleteLater();
                }
            });
            activationTimer->start();
        } else {
            ensure_workstation_output_dialog_visible();
        }
    } else {
        switch_to_workstation_desktop();
    }

    // Stage 122: Das gerade aktivierte Kind darf den Konsolenersatz weder
    // verdecken noch durch eine geaenderte Monitor-Geometrie ausserhalb des
    // sichtbaren Bereichs zuruecklassen. Sofort pruefen; der 500-ms-Watchdog
    // wiederholt dieselbe Sicherung anschliessend dauerhaft.
    ensure_workstation_output_dialog_visible();
    return true;
}

struct CloseChildWindowContext
{
    DWORD pid;
};

BOOL CALLBACK close_child_window_enum_proc(HWND hwnd, LPARAM value)
{
    CloseChildWindowContext *ctx =
        reinterpret_cast<CloseChildWindowContext *>(value);
    if (!ctx)
        return FALSE;

    DWORD windowPid = 0;
    GetWindowThreadProcessId(hwnd, &windowPid);
    if (windowPid != ctx->pid)
        return TRUE;

    const LONG_PTR style = GetWindowLongPtrW(hwnd, GWL_STYLE);
    if ((style & WS_CHILD) != 0)
        return TRUE;

    PostMessageW(hwnd, WM_CLOSE, 0, 0);
    return TRUE;
}

void request_child_window_close(DWORD pid)
{
    CloseChildWindowContext context = {};
    context.pid = pid;

    const wchar_t *desktopName = D64WorkstationDesktopName();
    if (!desktopName || !*desktopName)
        return;

    HDESK desktop = OpenDesktopW(
        desktopName,
        0,
        FALSE,
        DESKTOP_ENUMERATE | DESKTOP_READOBJECTS | DESKTOP_WRITEOBJECTS
    );
    if (!desktop)
        return;

    EnumDesktopWindows(
        desktop,
        &close_child_window_enum_proc,
        reinterpret_cast<LPARAM>(&context)
    );
    CloseDesktop(desktop);
}

void terminate_children()
{
    cleanup_finished_children();

    // Red Workstation EXIT authorizes a real application shutdown. Give GUI
    // programs a chance to process WM_CLOSE and release files/sessions first.
    for (ChildProcess &child : g_children) {
        if (!child.process ||
            WaitForSingleObject(child.process, 0) == WAIT_OBJECT_0)
            continue;
        request_child_window_close(child.pid);
    }

    const DWORD deadline = GetTickCount() + 2000;
    for (;;) {
        bool anyRunning = false;
        for (ChildProcess &child : g_children) {
            if (child.process &&
                WaitForSingleObject(child.process, 0) != WAIT_OBJECT_0) {
                anyRunning = true;
                break;
            }
        }
        if (!anyRunning || static_cast<LONG>(GetTickCount() - deadline) >= 0)
            break;
        Sleep(25);
    }

    // Console applications without a closeable top-level window, or hung
    // programs, must not keep the Workstation session alive after EXIT.
    for (ChildProcess &child : g_children) {
        if (!child.process)
            continue;
        if (WaitForSingleObject(child.process, 0) != WAIT_OBJECT_0) {
            TerminateProcess(child.process, 0);
            WaitForSingleObject(child.process, 1000);
        }
        CloseHandle(child.process);
        child.process = nullptr;
    }
    g_children.clear();
}


bool write_exact(HANDLE pipe, const void *buffer, DWORD bytes)
{
    const BYTE *source = static_cast<const BYTE *>(buffer);
    DWORD total = 0;
    while (total < bytes) {
        DWORD written = 0;
        if (!WriteFile(
                pipe,
                source + total,
                bytes - total,
                &written,
                nullptr) || written == 0) {
            return false;
        }
        total += written;
    }
    return true;
}

bool send_request_to_existing_runner(
    const LaunchRequest &request,
    DWORD timeoutMs
)
{
    if (request.application.empty())
        return false;

    const DWORD started = GetTickCount();
    HANDLE pipe = INVALID_HANDLE_VALUE;

    for (;;) {
        if (WaitNamedPipeW(RUNNER_PIPE_NAME, 200)) {
            pipe = CreateFileW(
                RUNNER_PIPE_NAME,
                GENERIC_WRITE,
                0,
                nullptr,
                OPEN_EXISTING,
                0,
                nullptr
            );
            if (pipe != INVALID_HANDLE_VALUE)
                break;
        }

        if (static_cast<DWORD>(GetTickCount() - started) >= timeoutMs)
            return false;
        Sleep(50);
    }

    const std::uint64_t pathBytes64 =
        static_cast<std::uint64_t>(request.application.size()) * sizeof(wchar_t);
    const std::uint64_t cwdBytes64 =
        static_cast<std::uint64_t>(request.workingDirectory.size()) * sizeof(wchar_t);
    if (pathBytes64 == 0 || pathBytes64 > 60u * 1024u ||
        cwdBytes64 > 60u * 1024u) {
        CloseHandle(pipe);
        return false;
    }

    PipeHeader header{};
    header.magic = RUNNER_PIPE_MAGIC;
    header.flags = request.consoleMode ? RUNNER_LAUNCH_CONSOLE : 0u;
    if (request.debugConsoleOnly)
        header.flags |= RUNNER_LAUNCH_DEBUG_CONSOLE_ONLY;
    if (request.themeMode >= 0) {
        header.flags |= RUNNER_LAUNCH_THEME_PRESENT;
        if (request.themeMode != 0)
            header.flags |= RUNNER_LAUNCH_THEME_DARK;
    }
    if (request.debugThemeMode >= 0) {
        header.flags |= RUNNER_LAUNCH_DEBUG_THEME_PRESENT;
        if (request.debugThemeMode == 1)
            header.flags |= RUNNER_LAUNCH_DEBUG_THEME_LIGHT;
        else if (request.debugThemeMode == 2)
            header.flags |= RUNNER_LAUNCH_DEBUG_THEME_DARK;
    }
    header.pathBytes = static_cast<std::uint32_t>(pathBytes64);
    header.cwdBytes = static_cast<std::uint32_t>(cwdBytes64);

    bool ok = write_exact(pipe, &header, sizeof(header));
    if (ok) {
        ok = write_exact(
            pipe,
            request.application.data(),
            header.pathBytes
        );
    }
    if (ok && header.cwdBytes) {
        ok = write_exact(
            pipe,
            request.workingDirectory.data(),
            header.cwdBytes
        );
    }

    FlushFileBuffers(pipe);
    CloseHandle(pipe);
    return ok;
}

bool request_existing_runner_output_window(DWORD timeoutMs)
{
    const DWORD started = GetTickCount();
    HANDLE pipe = INVALID_HANDLE_VALUE;

    for (;;) {
        if (WaitNamedPipeW(RUNNER_PIPE_NAME, 200)) {
            pipe = CreateFileW(
                RUNNER_PIPE_NAME,
                GENERIC_WRITE,
                0,
                nullptr,
                OPEN_EXISTING,
                0,
                nullptr
            );
            if (pipe != INVALID_HANDLE_VALUE)
                break;
        }
        if (static_cast<DWORD>(GetTickCount() - started) >= timeoutMs)
            return false;
        Sleep(50);
    }

    // Das Stage-116+-Protokoll kennt bereits leere Output-Nachrichten.
    // Dadurch kann auch eine schon residente Runner-Instanz ihren
    // QPlainTextEdit-Konsolenersatz sichtbar machen, ohne Text einzufuegen.
    PipeHeader header{};
    header.magic = RUNNER_OUTPUT_MAGIC;
    header.flags = 0;
    header.pathBytes = 0;
    header.cwdBytes = GetCurrentProcessId();

    const bool ok = write_exact(pipe, &header, sizeof(header));
    FlushFileBuffers(pipe);
    CloseHandle(pipe);
    return ok;
}

bool read_exact(HANDLE pipe, void *buffer, DWORD bytes)
{
    BYTE *target = static_cast<BYTE *>(buffer);
    DWORD total = 0;
    while (total < bytes) {
        DWORD got = 0;
        if (!ReadFile(pipe, target + total, bytes - total, &got, nullptr) || got == 0)
            return false;
        total += got;
    }
    return true;
}

void pipe_server_loop()
{
    while (!g_pipe_stop.load()) {
        HANDLE pipe = CreateNamedPipeW(
            RUNNER_PIPE_NAME,
            PIPE_ACCESS_INBOUND,
            PIPE_TYPE_BYTE | PIPE_READMODE_BYTE | PIPE_WAIT,
            1,
            64 * 1024,
            64 * 1024,
            0,
            nullptr
        );
        if (pipe == INVALID_HANDLE_VALUE) {
            g_pipe_ready.store(false);
            return;
        }

        // Stage 273: Ab hier existiert eine frische Pipe-Instanz und wartet
        // auf genau den naechsten Launch-/Output-Client.
        g_pipe_ready.store(true);
        const BOOL connected = ConnectNamedPipe(pipe, nullptr)
            ? TRUE
            : (GetLastError() == ERROR_PIPE_CONNECTED);
        // Sobald ein Client verbunden ist, ist diese Instanz nicht mehr fuer
        // den ersten WriteLn-Aufruf der neuen Anwendung verfuegbar. Erst die
        // naechste Schleifenrunde setzt ready wieder auf true.
        g_pipe_ready.store(false);

        if (!connected) {
            CloseHandle(pipe);
            if (g_pipe_stop.load())
                break;
            continue;
        }

        if (g_pipe_stop.load()) {
            DisconnectNamedPipe(pipe);
            CloseHandle(pipe);
            break;
        }

        PipeHeader header{};
        if (read_exact(pipe, &header, sizeof(header))) {
            if (header.magic == RUNNER_OUTPUT_MAGIC) {
                // Stage 116: dBase-WFM-Ausgabe. Fuer dieses Protokoll ist
                // pathBytes die UTF-8-Textlaenge und cwdBytes die Sender-PID.
                if (header.pathBytes <= 1024u * 1024u) {
                    std::vector<char> textBytes(header.pathBytes);
                    const bool textOk = header.pathBytes == 0 ||
                        read_exact(pipe, textBytes.data(), header.pathBytes);
                    if (textOk && g_host_window) {
                        std::unique_ptr<OutputMessage> output(new OutputMessage());
                        if (!textBytes.empty())
                            output->text.assign(textBytes.data(), textBytes.size());
                        output->newline =
                            (header.flags & RUNNER_OUTPUT_NEWLINE) != 0;
                        output->latin1 =
                            (header.flags & RUNNER_OUTPUT_LATIN1) != 0;
                        output->processId = static_cast<DWORD>(header.cwdBytes);
                        // Nur exakt eines der beiden Bits darf die
                        // Sichtbarkeit veraendern; alte DOW1-Pakete bleiben
                        // weiterhin reine Textausgaben.
                        const bool showRequested =
                            (header.flags & RUNNER_OUTPUT_DEBUG_SHOW) != 0;
                        const bool hideRequested =
                            (header.flags & RUNNER_OUTPUT_DEBUG_HIDE) != 0;
                        if (showRequested != hideRequested)
                            output->debugVisibility = showRequested ? 1 : 0;
                        if ((header.flags & RUNNER_OUTPUT_THEME_PRESENT) != 0) {
                            if ((header.flags & RUNNER_OUTPUT_THEME_DARK) != 0)
                                output->debugThemeMode = 2;
                            else if ((header.flags & RUNNER_OUTPUT_THEME_LIGHT) != 0)
                                output->debugThemeMode = 1;
                            else
                                output->debugThemeMode = 0;
                        }
                        PostMessageW(
                            g_host_window,
                            WM_RUNNER_OUTPUT,
                            0,
                            reinterpret_cast<LPARAM>(output.release())
                        );
                    }
                }
            } else if (
                header.magic == RUNNER_PIPE_MAGIC &&
                header.pathBytes > 0 &&
                header.pathBytes <= 60 * 1024 &&
                header.cwdBytes <= 60 * 1024 &&
                (header.pathBytes % sizeof(wchar_t)) == 0 &&
                (header.cwdBytes % sizeof(wchar_t)) == 0
            ) {
                std::vector<BYTE> pathBytes(header.pathBytes);
                std::vector<BYTE> cwdBytes(header.cwdBytes);
                const bool pathOk = read_exact(pipe, pathBytes.data(), header.pathBytes);
                const bool cwdOk = header.cwdBytes == 0 ||
                    read_exact(pipe, cwdBytes.data(), header.cwdBytes);

                if (pathOk && cwdOk && g_host_window) {
                    std::unique_ptr<LaunchRequest> request(new LaunchRequest());
                    request->application.assign(
                        reinterpret_cast<const wchar_t *>(pathBytes.data()),
                        header.pathBytes / sizeof(wchar_t)
                    );
                    if (header.cwdBytes) {
                        request->workingDirectory.assign(
                            reinterpret_cast<const wchar_t *>(cwdBytes.data()),
                            header.cwdBytes / sizeof(wchar_t)
                        );
                    }
                    request->consoleMode = (header.flags & RUNNER_LAUNCH_CONSOLE) != 0;
                    request->debugConsoleOnly =
                        (header.flags & RUNNER_LAUNCH_DEBUG_CONSOLE_ONLY) != 0;
                    if ((header.flags & RUNNER_LAUNCH_THEME_PRESENT) != 0)
                        request->themeMode = (header.flags & RUNNER_LAUNCH_THEME_DARK) != 0 ? 1 : 0;
                    if ((header.flags & RUNNER_LAUNCH_DEBUG_THEME_PRESENT) != 0) {
                        if ((header.flags & RUNNER_LAUNCH_DEBUG_THEME_DARK) != 0)
                            request->debugThemeMode = 2;
                        else if ((header.flags & RUNNER_LAUNCH_DEBUG_THEME_LIGHT) != 0)
                            request->debugThemeMode = 1;
                        else
                            request->debugThemeMode = 0;
                    }
                    PostMessageW(
                        g_host_window,
                        WM_RUNNER_LAUNCH,
                        0,
                        reinterpret_cast<LPARAM>(request.release())
                    );
                }
            }
        }

        // Stage 319: Inbound-only DOW1/Launch-Pipe besitzt keine
        // ausgehenden Daten, die FlushFileBuffers() abwarten muesste.
        DisconnectNamedPipe(pipe);
        CloseHandle(pipe);
    }
    g_pipe_ready.store(false);
}

void wake_pipe_server()
{
    HANDLE pipe = CreateFileW(
        RUNNER_PIPE_NAME,
        GENERIC_WRITE,
        0,
        nullptr,
        OPEN_EXISTING,
        0,
        nullptr
    );
    if (pipe != INVALID_HANDLE_VALUE)
        CloseHandle(pipe);
}

void stop_pipe_server()
{
    g_pipe_ready.store(false);
    g_pipe_stop.store(true);
    wake_pipe_server();
    if (g_pipe_thread.joinable())
        g_pipe_thread.join();
}

void begin_leave_once()
{
    if (g_leave_started)
        return;
    g_leave_started = true;
    stop_pipe_server();
    remove_keyboard_guard();
    remove_mouse_guard();
    if (g_output_dialog)
        g_output_dialog->hide();
    terminate_children();
    D64WorkstationBeginLeave();
}

void workstation_exit_requested()
{
    // Stage 275: Ein einzelner physischer Panel-Klick konnte unter der
    // verschachtelten modalen Eventloop-Situation zweimal beim Callback
    // ankommen. Solange ein Dialog offen ist, nach einem bestaetigten Exit
    // sowie fuer eine kurze Entprellzeit wird jeder weitere Aufruf ignoriert.
    if (g_leave_started || g_exit_confirmed || g_exit_prompt_active)
        return;

    const ULONGLONG now = GetTickCount64();
    if (now < g_exit_prompt_suppress_until)
        return;

    g_exit_prompt_active = true;

    WorkstationExitDialog dialog(
        workstation_debug_uses_dark_theme(),
        g_output_dialog
    );

    // Der Dialog gehoert zum Workstation-Desktop und wird ueber dem
    // DEBUG-Fenster zentriert. "Nein" ist absichtlich der Default.
    if (g_output_dialog) {
        const QRect parentGeometry = g_output_dialog->frameGeometry();
        const QSize dialogSize = dialog.size();
        dialog.move(
            parentGeometry.center().x() - dialogSize.width() / 2,
            parentGeometry.center().y() - dialogSize.height() / 2
        );
    }

    const int answer = dialog.exec();
    g_exit_prompt_active = false;
    g_exit_prompt_suppress_until = GetTickCount64() + 600;

    if (answer == QDialog::Accepted && g_host_window) {
        g_exit_confirmed = true;
        PostMessageW(g_host_window, WM_RUNNER_EXIT, 0, 0);
    }
}

void workstation_db_requested()
{
    // Zuerst alle vom Runner versteckten Fenster wieder sichtbar machen.
    restore_hidden_windows();

    if (!g_has_db_launch_request)
        return;

    const std::wstring canonical =
        normalize_path(g_db_launch_request.application);
    if (canonical.empty())
        return;

    // Laeuft die Anwendung noch, wird keine zweite Instanz erzeugt.
    // Stattdessen das vorhandene Hauptfenster wiederherstellen/aktivieren.
    if (ChildProcess *existing = find_running_child(canonical)) {
        activate_child_windows(existing->pid);
        if (!existing->consoleWindow || !IsWindow(existing->consoleWindow))
            discover_child_console_window(*existing);
        restore_hidden_windows();
        return;
    }

    // Der Prozess wurde wirklich beendet: derselbe gespeicherte Startauftrag
    // (EXE, Arbeitsverzeichnis, Console/GUI) wird erneut ausgefuehrt.
    if (!launch_program(g_db_launch_request)) {
        MessageBoxW(
            nullptr,
            L"Die DB-Anwendung konnte nicht erneut gestartet werden.",
            L"Workstation Mode",
            MB_OK | MB_ICONERROR | MB_SETFOREGROUND
        );
    }
}

LRESULT CALLBACK runner_window_proc(
    HWND hwnd,
    UINT message,
    WPARAM wParam,
    LPARAM lParam
)
{
    if (message == workstation_global_shutdown_message()) {
        PostMessageW(hwnd, WM_RUNNER_EXIT, 0, 0);
        return 0;
    }

    switch (message) {
    case WM_RUNNER_LAUNCH: {
        std::unique_ptr<LaunchRequest> request(
            reinterpret_cast<LaunchRequest *>(lParam)
        );
        if (request && request->themeMode >= 0)
            D64WorkstationSetDarkMode(request->themeMode != 0);
        if (request && request->debugThemeMode >= 0)
            apply_workstation_output_debug_theme(request->debugThemeMode);

        // Stage 272: Das DEBUG-Fenster zuerst sichtbar machen und einmal
        // zeichnen lassen. launch_program() kann bei einer generischen GUI
        // anschliessend bis WaitForInputIdle()/Fenstersuche warten. Ohne
        // diesen Schritt war bei einer residenten Runner-Session waehrend
        // genau dieser Zeit kein DEBUG-Fenster zu sehen.
        if (request) {
            switch_to_workstation_desktop();
            ensure_workstation_output_dialog_visible();
            QCoreApplication::processEvents(QEventLoop::AllEvents, 100);
        }

        if (request && !launch_program(*request)) {
            MessageBoxW(
                nullptr,
                L"Die Anwendung konnte nicht auf der Workstation gestartet werden.",
                L"Workstation Mode",
                MB_OK | MB_ICONERROR | MB_SETFOREGROUND
            );
        }
        return 0;
    }

    case WM_RUNNER_EXIT:
        begin_leave_once();
        QCoreApplication::quit();
        return 0;

    case WM_RUNNER_OUTPUT: {
        std::unique_ptr<OutputMessage> output(
            reinterpret_cast<OutputMessage *>(lParam)
        );
        if (output)
            append_workstation_output(*output);
        return 0;
    }

    case WM_TIMER:
        if (wParam == RUNNER_TIMER) {
            cleanup_finished_children();
            // Stage 114: Eine lazy AllocConsole-Konsole kann erst lange nach
            // dem ersten Formularfenster entstehen. Deshalb alle 500 ms neue
            // Consolen der laufenden Kindprozesse entdecken und genau beim
            // ersten Auftauchen sichtbar machen.
            discover_child_console_windows();

            // Stage 272: Erst NACH der Console-Behandlung den DEBUG-Dialog
            // nach oben holen. Beide Fenster koennen TOPMOST sein; in der
            // alten Reihenfolge gewann die Console bei jedem Timer-Takt und
            // das DEBUG-Fenster wirkte dadurch wie nicht angezeigt.
            if (!g_leave_started)
                ensure_workstation_output_dialog_visible();
        }
        return 0;

    case WM_CLOSE:
        // Das Runner-Fenster selbst darf die Session nicht beenden. Es bleibt
        // unsichtbare Infrastruktur bis zum roten Workstation-EXIT.
        ShowWindow(hwnd, SW_HIDE);
        return 0;

    case WM_DESTROY:
        return 0;
    }
    return DefWindowProcW(hwnd, message, wParam, lParam);
}

bool register_runner_class(HINSTANCE instance)
{
    WNDCLASSEXW wc;
    ZeroMemory(&wc, sizeof(wc));
    wc.cbSize = sizeof(wc);
    wc.lpfnWndProc = &runner_window_proc;
    wc.hInstance = instance;
    wc.hCursor = LoadCursorW(nullptr, IDC_ARROW);
    wc.hbrBackground = reinterpret_cast<HBRUSH>(COLOR_WINDOW + 1);
    wc.lpszClassName = RUNNER_WINDOW_CLASS;
    if (RegisterClassExW(&wc))
        return true;
    return GetLastError() == ERROR_CLASS_ALREADY_EXISTS;
}

HWND create_runner_window(HINSTANCE instance)
{
    return CreateWindowExW(
        WS_EX_TOOLWINDOW,
        RUNNER_WINDOW_CLASS,
        RUNNER_WINDOW_TITLE,
        WS_OVERLAPPEDWINDOW,
        120,
        120,
        360,
        180,
        nullptr,
        nullptr,
        instance,
        nullptr
    );
}

} // namespace

int main(int, char **)
{
    HINSTANCE instance = GetModuleHandleW(nullptr);

    // Stage 148: Die Argumente werden nativ durch CommandLineToArgvW
    // getrennt. Damit stimmen Python subprocess.Popen([...]) und Runner auch
    // bei Leerzeichen, Quotes und Backslashes exakt ueberein.
    const std::vector<std::wstring> runnerArgs = process_runner_arguments();

    LaunchRequest startupRequest;
    bool hasStartupRequest = false;
    bool showHelp = false;
    std::wstring parseError;
    if (!parse_runner_arguments(
            runnerArgs,
            startupRequest,
            hasStartupRequest,
            showHelp,
            parseError)) {
        log_runner_argument_error(runnerArgs, parseError);
        return 20;
    }
    if (showHelp) {
        show_runner_usage();
        return 0;
    }

    if (!D64WorkstationPrepare()) {
        const DWORD error = GetLastError();
        // A resident Runner already owns its per-application mutex.  For the
        // new direct CLI syntax the short-lived second process forwards the
        // application to that Runner and exits immediately.
        if (error == ERROR_ALREADY_EXISTS && hasStartupRequest) {
            const bool forwarded =
                send_request_to_existing_runner(startupRequest, 5000);
            if (forwarded)
                request_existing_runner_output_window(1500);
            return forwarded ? 0 : 11;
        }
        return error == ERROR_ALREADY_EXISTS ? 10 : 2;
    }

    // Stage 116: QApplication wird erst NACH D64WorkstationPrepare() erzeugt.
    // Dadurch gehoeren QDialog/QPlainTextEdit garantiert zum gebundenen
    // D64Workstation-Desktop und koennen nicht auf dem Root-Desktop landen.
    int qtArgc = 1;
    char qtArg0[] = "d64_workstation_runner";
    char *qtArgv[] = { qtArg0, nullptr };
    QApplication qtApp(qtArgc, qtArgv);
    qtApp.setQuitOnLastWindowClosed(false);

    D64WorkstationSetThemeCallback(&workstation_theme_changed);
    if (startupRequest.themeMode >= 0)
        D64WorkstationSetDarkMode(startupRequest.themeMode != 0);
    if (startupRequest.debugThemeMode >= 0)
        g_output_debug_theme_mode = startupRequest.debugThemeMode;
    else
        D64WorkstationSetDarkMode(true);

    if (!register_runner_class(instance)) {
        D64WorkstationBeginLeave();
        D64WorkstationFinalizeLeave();
        return 3;
    }

    g_host_window = create_runner_window(instance);
    if (!g_host_window) {
        D64WorkstationBeginLeave();
        D64WorkstationFinalizeLeave();
        return 4;
    }

    D64WorkstationSetExitCallback(&workstation_exit_requested);
    D64WorkstationSetDbCallback(&workstation_db_requested);

    // Activate() requires a visible HWND. OWNER creates/switches the desktop
    // and panels here; JOINED attaches this Runner to the existing Workstation.
    ShowWindow(g_host_window, SW_SHOWNORMAL);
    UpdateWindow(g_host_window);
    if (!D64WorkstationActivate(g_host_window)) {
        DestroyWindow(g_host_window);
        g_host_window = nullptr;
        D64WorkstationBeginLeave();
        D64WorkstationFinalizeLeave();
        return 5;
    }

    // Stage 116: Der zentrale, nicht modale Qt5-Ausgabedialog wird genau
    // jetzt geoeffnet: der Workstation-Desktop ist bereits sichtbar und der
    // QApplication-GUI-Thread ist seit Prepare() an diesen Desktop gebunden.
    create_workstation_output_dialog();
    ensure_workstation_output_dialog_visible();
    qtApp.processEvents(QEventLoop::AllEvents, 100);

    // Stage 120: Der erste Show-Aufruf vor exec() reicht auf einigen
    // Workstation-Desktop-Konfigurationen nicht aus. Nach Eintritt in den
    // echten Qt-Eventloop wird der Dialog deshalb erneut sichtbar gemacht.
    QTimer::singleShot(0, []() {
        ensure_workstation_output_dialog_visible();
    });

    // Sichtbarkeits-Watchdog: Der Konsolenersatz gehoert fest zur Workstation.
    // Falls ein gestartetes Formular oder ein Close/Hide-Ereignis ihn verdeckt
    // bzw. versteckt, wird er wieder eingeblendet.
    QTimer outputDialogWatchdog;
    outputDialogWatchdog.setInterval(500);
    QObject::connect(&outputDialogWatchdog, &QTimer::timeout, []() {
        if (!g_leave_started)
            ensure_workstation_output_dialog_visible();
    });
    outputDialogWatchdog.start();

    // The existing core guard keeps Win/Alt-Tab/etc. inside the Workstation.
    // Install our generic-app guard afterwards so Alt+F4 on a normal PE child
    // means "hide", matching the old d64qt5 Stage-128 semantics.
    if (!D64WorkstationInstallKeyboardGuard(g_host_window) ||
        !install_mouse_guard() ||
        !install_keyboard_guard()) {
        begin_leave_once();
        DestroyWindow(g_host_window);
        g_host_window = nullptr;
        D64WorkstationFinalizeLeave();
        return 6;
    }

    // The host window is infrastructure only. The Workstation panels remain
    // visible. Requests may now arrive either from the CLI or the legacy pipe.
    ShowWindow(g_host_window, SW_HIDE);
    SetTimer(g_host_window, RUNNER_TIMER, 500, nullptr);

    g_pipe_stop.store(false);
    g_pipe_thread = std::thread(&pipe_server_loop);

    int resultCode = 0;
    if (hasStartupRequest && !launch_program(startupRequest)) {
        MessageBoxW(
            nullptr,
            L"Die angegebene Anwendung konnte nicht auf der Workstation gestartet werden.",
            L"Workstation Mode",
            MB_OK | MB_ICONERROR | MB_SETFOREGROUND
        );
        resultCode = 7;
        PostMessageW(g_host_window, WM_RUNNER_EXIT, 0, 0);
    }

    // Stage 116: QApplication verarbeitet sowohl die Qt5-Dialoge als auch
    // die native Runner-HWND/WM_TIMER/WM_APP-Nachrichten.
    const int qtLoopResult = qtApp.exec();
    (void)qtLoopResult;

    begin_leave_once();
    flush_workstation_output_text();
    if (g_output_dialog) {
        g_output_dialog->hide();
        delete g_output_dialog;
    }
    g_output_dialog = nullptr;
    g_output_edit = nullptr;

    if (g_host_window && IsWindow(g_host_window)) {
        KillTimer(g_host_window, RUNNER_TIMER);
        DestroyWindow(g_host_window);
    }
    g_host_window = nullptr;
    D64WorkstationFinalizeLeave();
    return resultCode;
}
