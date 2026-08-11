#define D64QT5_BRIDGE_EXPORTS 1
#include "d64qt5_bridge.h"

#include <QApplication>
#include <QAction>
#include <QByteArray>
#include <QColor>
#include <QCoreApplication>
#include <QFont>
#include <QFontDatabase>
#include <QFontInfo>
#include <QFontMetrics>
#include <QFrame>
#include <QHBoxLayout>
#include <QIcon>
#include <QLineEdit>
#include <QKeySequence>
#include <QList>
#include <QMainWindow>
#include <QMenu>
#include <QMenuBar>
#include <QPainter>
#include <QPaintEvent>
#include <QPalette>
#include <QPixmap>
#include <QPlainTextEdit>
#include <QRegularExpression>
#include <QScrollBar>
#include <QSize>
#include <QSizePolicy>
#include <QStackedWidget>
#include <QStatusBar>
#include <QTabBar>
#include <QTextCharFormat>
#include <QTextDocument>
#include <QTextCursor>
#include <QToolButton>
#include <QVBoxLayout>
#include <QWidget>
#include <QString>
#include <QStringList>

#ifdef _WIN32
#  define WIN32_LEAN_AND_MEAN
#  include <windows.h>
#endif

namespace {
QApplication *g_app = nullptr;
bool g_owns_app = false;
QMainWindow *g_window = nullptr;

QWidget *g_root = nullptr;
QWidget *g_header = nullptr;
QTabBar *g_tab_bar = nullptr;
QStackedWidget *g_stack = nullptr;

QWidget *g_console_page = nullptr;
QWidget *g_debug_page = nullptr;
QFrame *g_console_frame = nullptr;
QFrame *g_debug_frame = nullptr;
QMenuBar *g_menu_bar = nullptr;
QStatusBar *g_status_bar = nullptr;
QPlainTextEdit *g_console = nullptr;
QPlainTextEdit *g_debug = nullptr;
QLineEdit *g_debug_input = nullptr;

QToolButton *g_zoom_in = nullptr;
QToolButton *g_zoom_out = nullptr;

bool g_debug_visible = false;
bool g_program_finished = false;
int g_font_point_size = 10;
int g_font_pixel_adjust = 0;
QString g_console_font_family;
QColor g_console_background(0, 0, 0);
QColor g_console_border_color(255, 255, 255);
QColor g_output_foreground(169, 169, 169);
QColor g_output_background(0, 0, 0);

constexpr int DBASE_FONT_MIN_PT = 9;
constexpr int DBASE_FONT_MAX_PT = 75;
constexpr int DBASE_TEXT_COLUMNS = 80;
constexpr int DBASE_TEXT_ROWS = 25;
constexpr int DBASE_GRID_TOLERANCE_PX = 1;
constexpr int TAB_CONSOLE = 0;
constexpr int TAB_DEBUG = 1;

using MenuCallback = void (*)(void);

struct MenuNode {
    MenuNode *parent = nullptr;
    QMenu *menu = nullptr;
    QAction *action = nullptr;
    QString text;
    MenuCallback callback = nullptr;
};

QList<MenuNode *> g_menu_nodes;

QString choose_menu_font_family()
{
    QFontDatabase database;
    const QStringList families = database.families();
    const QStringList preferred = {
        QStringLiteral("Consolas"),
        QStringLiteral("Courier New")
    };
    for (const QString &candidate : preferred) {
        for (const QString &actual : families) {
            if (actual.compare(candidate, Qt::CaseInsensitive) == 0)
                return actual;
        }
    }
    return QFontDatabase::systemFont(QFontDatabase::FixedFont).family();
}

QString choose_popup_border_font_family()
{
    QFontDatabase database;
    const QStringList families = database.families();
    const QStringList preferred = {
        QStringLiteral("Terminal"),
        QStringLiteral("Courier New")
    };
    for (const QString &candidate : preferred) {
        for (const QString &actual : families) {
            if (actual.compare(candidate, Qt::CaseInsensitive) == 0)
                return actual;
        }
    }
    return QFontDatabase::systemFont(QFontDatabase::FixedFont).family();
}

// ---------------------------------------------------------------------------
// Stage 18: Nur die aufgeklappten QMenu-Popups erhalten einen klassischen
// CP437/Terminal-Zeichenrahmen. Die QMenuBar selbst bleibt ein normales Qt-
// Hauptmenue. Verwendete OEM-Zeichen und Unicode-Entsprechungen:
//   B9=╣ BA=║ BB=╗ BC=╝ C8=╚ C9=╔ CA=╩ CB=╦ CC=╠ CD=═ CE=╬
// ---------------------------------------------------------------------------
class AsciiPopupMenu final : public QMenu
{
public:
    explicit AsciiPopupMenu(const QString &title, QWidget *parent = nullptr)
        : QMenu(title, parent)
    {
        setObjectName(QStringLiteral("dbaseAsciiPopupMenu"));
        setPointSize(g_font_point_size);
        setStyleSheet(QStringLiteral(
            "QMenu#dbaseAsciiPopupMenu {"
            " background-color: #909090;"
            " color: #000000;"
            " border: 0px;"
            " margin: 0px;"
            " padding: 0px;"
            "}"
            "QMenu#dbaseAsciiPopupMenu::item {"
            " background-color: transparent;"
            " color: #000000;"
            " padding: 3px 34px 3px 8px;"
            "}"
            "QMenu#dbaseAsciiPopupMenu::item:selected {"
            " background-color: #000080;"
            " color: #ffffff;"
            "}"
            "QMenu#dbaseAsciiPopupMenu::item:disabled {"
            " color: #505050;"
            "}"
            "QMenu#dbaseAsciiPopupMenu::separator {"
            " height: 1px;"
            " background-color: #505050;"
            " margin: 3px 6px;"
            "}"
        ));
    }

    void setPointSize(int pointSize)
    {
        if (pointSize < DBASE_FONT_MIN_PT)
            pointSize = DBASE_FONT_MIN_PT;
        if (pointSize > DBASE_FONT_MAX_PT)
            pointSize = DBASE_FONT_MAX_PT;

        m_borderFont = QFont(choose_popup_border_font_family(), pointSize);
        m_borderFont.setFixedPitch(true);
        m_borderFont.setStyleHint(QFont::TypeWriter);

        QFont menuFont(choose_menu_font_family(), pointSize);
        menuFont.setFixedPitch(true);
        menuFont.setStyleHint(QFont::TypeWriter);
        setFont(menuFont);

        QFontMetrics fm(m_borderFont);
        m_cellWidth = qMax(1, fm.horizontalAdvance(QString(QChar(0x2550))));
        m_cellHeight = qMax(1, fm.height());

        // Der echte QAction-Bereich bleibt innerhalb des Zeichenrahmens.
        setContentsMargins(
            m_cellWidth,
            m_cellHeight,
            m_cellWidth,
            m_cellHeight
        );
        updateGeometry();
        update();
    }

protected:
    void paintEvent(QPaintEvent *event) override
    {
        // Qt zeichnet zuerst Hintergrund, Eintraege, Hover und Shortcuts.
        QMenu::paintEvent(event);

        // Danach wird ausschließlich der Popup-Aussenrand als Zeichenrahmen
        // daruebergelegt. Alle QAction-Hitboxes bleiben unveraendert aktiv.
        QPainter painter(this);
        painter.setRenderHint(QPainter::TextAntialiasing, false);
        painter.setFont(m_borderFont);
        painter.setPen(Qt::black);

        QFontMetrics fm(m_borderFont);
        const int widthPx = width();
        const int heightPx = height();
        if (widthPx <= m_cellWidth * 2 || heightPx <= m_cellHeight * 2)
            return;

        const QString TL(QChar(0x2554)); // ╔  CP437 C9
        const QString TR(QChar(0x2557)); // ╗  CP437 BB
        const QString BL(QChar(0x255A)); // ╚  CP437 C8
        const QString BR(QChar(0x255D)); // ╝  CP437 BC
        const QString H (QChar(0x2550)); // ═  CP437 CD
        const QString V (QChar(0x2551)); // ║  CP437 BA

        const int ascent = fm.ascent();
        const int descent = fm.descent();
        const int rightX = qMax(0, widthPx - m_cellWidth);

        // Obere Kante.
        painter.drawText(0, ascent, TL);
        for (int x = m_cellWidth; x < widthPx - m_cellWidth; x += m_cellWidth)
            painter.drawText(x, ascent, H);
        painter.drawText(rightX, ascent, TR);

        // Untere Kante.
        const int bottomBaseline = heightPx - qMax(0, descent);
        painter.drawText(0, bottomBaseline, BL);
        for (int x = m_cellWidth; x < widthPx - m_cellWidth; x += m_cellWidth)
            painter.drawText(x, bottomBaseline, H);
        painter.drawText(rightX, bottomBaseline, BR);

        // Linke und rechte Kante.
        for (int y = m_cellHeight; y < heightPx - m_cellHeight; y += m_cellHeight) {
            const int baseline = y + ascent;
            painter.drawText(0, baseline, V);
            painter.drawText(rightX, baseline, V);
        }
    }

private:
    QFont m_borderFont;
    int m_cellWidth = 8;
    int m_cellHeight = 16;
};

QString choose_console_font_family()
{
    QFontDatabase database;
    const QStringList families = database.families();
    const QStringList preferred = {
        QStringLiteral("Consolas"),
        QStringLiteral("Courier New"),
        QStringLiteral("Courier")
    };

    for (const QString &candidate : preferred) {
        for (const QString &actual : families) {
            if (actual.compare(candidate, Qt::CaseInsensitive) == 0)
                return actual;
        }
    }

    return QFontDatabase::systemFont(QFontDatabase::FixedFont).family();
}

QIcon create_zoom_icon(bool plus)
{
    QPixmap pixmap(24, 24);
    pixmap.fill(Qt::transparent);

    QPainter painter(&pixmap);
    painter.setRenderHint(QPainter::Antialiasing, true);

    QPen pen(QColor(169, 169, 169));
    pen.setWidth(2);
    pen.setCapStyle(Qt::RoundCap);
    pen.setJoinStyle(Qt::RoundJoin);
    painter.setPen(pen);
    painter.setBrush(Qt::NoBrush);

    painter.drawEllipse(QRectF(3.5, 3.5, 12.0, 12.0));
    painter.drawLine(QPointF(13.0, 13.0), QPointF(20.0, 20.0));

    painter.drawLine(QPointF(7.0, 9.5), QPointF(12.0, 9.5));
    if (plus)
        painter.drawLine(QPointF(9.5, 7.0), QPointF(9.5, 12.0));

    return QIcon(pixmap);
}

bool windows_system_color(const QString &name, QColor *out)
{
    if (!out)
        return false;

#ifdef _WIN32
    struct ColorEntry {
        const char *name;
        int index;
    };

    static const ColorEntry entries[] = {
        {"ActiveBorder",        COLOR_ACTIVEBORDER},
        {"ActiveCaption",       COLOR_ACTIVECAPTION},
        {"AppWorkspace",        COLOR_APPWORKSPACE},
        {"Background",          COLOR_BACKGROUND},
        {"BtnFace",             COLOR_BTNFACE},
        {"BtnHighlight",        COLOR_BTNHIGHLIGHT},
        {"BtnShadow",           COLOR_BTNSHADOW},
        {"BtnText",             COLOR_BTNTEXT},
        {"CaptionText",         COLOR_CAPTIONTEXT},
        {"GrayText",            COLOR_GRAYTEXT},
        {"Highlight",           COLOR_HIGHLIGHT},
        {"HighlightText",       COLOR_HIGHLIGHTTEXT},
        {"InactiveBorder",      COLOR_INACTIVEBORDER},
        {"InactiveCaption",     COLOR_INACTIVECAPTION},
        {"InactiveCaptionText", COLOR_INACTIVECAPTIONTEXT},
        {"InfoText",            COLOR_INFOTEXT},
        {"InfoBk",              COLOR_INFOBK},
        {"Menu",                COLOR_MENU},
        {"MenuText",            COLOR_MENUTEXT},
        {"Scrollbar",           COLOR_SCROLLBAR},
        {"Window",              COLOR_WINDOW},
        {"WindowFrame",         COLOR_WINDOWFRAME},
        {"WindowText",          COLOR_WINDOWTEXT},
    };

    for (const ColorEntry &entry : entries) {
        if (name.compare(QString::fromLatin1(entry.name), Qt::CaseInsensitive) != 0)
            continue;
        const COLORREF value = GetSysColor(entry.index);
        *out = QColor(
            static_cast<int>(GetRValue(value)),
            static_cast<int>(GetGValue(value)),
            static_cast<int>(GetBValue(value))
        );
        return true;
    }
#else
    // Nicht-Windows-Fallback nur fuer Entwicklungs-/Analyse-Builds der Bridge.
    // Die produktive dBase-Runtime fuer PE32/PE32+ verwendet GetSysColor().
    const QPalette palette = QApplication::palette();
    if (name.compare(QStringLiteral("Window"), Qt::CaseInsensitive) == 0) {
        *out = palette.color(QPalette::Window);
        return true;
    }
    if (name.compare(QStringLiteral("Background"), Qt::CaseInsensitive) == 0 ||
        name.compare(QStringLiteral("AppWorkspace"), Qt::CaseInsensitive) == 0) {
        *out = palette.color(QPalette::Base);
        return true;
    }
#endif
    return false;
}

bool rgb_literal_color(const QString &name, QColor *out)
{
    if (!out)
        return false;
    const QString value = name.trimmed();
    if (!QRegularExpression(QStringLiteral("^#[0-9A-Fa-f]{6}$")).match(value).hasMatch())
        return false;
    const QColor color(value);
    if (!color.isValid())
        return false;
    *out = color;
    return true;
}

bool dbase_palette_color(QString code, bool background, QColor *out)
{
    if (!out)
        return false;
    code = code.trimmed().toUpper();
    bool bright = false;
    if (background) {
        if (code.endsWith(QLatin1Char('*'))) {
            bright = true;
            code.chop(1);
        } else if (code.endsWith(QLatin1Char('+'))) {
            return false;
        }
    } else {
        if (code.endsWith(QLatin1Char('+'))) {
            bright = true;
            code.chop(1);
        } else if (code.endsWith(QLatin1Char('*'))) {
            return false;
        }
    }

    if (code == QStringLiteral("BG")) code = QStringLiteral("GB");
    if (code == QStringLiteral("BR")) code = QStringLiteral("RB");
    if (code == QStringLiteral("GR")) code = QStringLiteral("RG");

    struct Entry { const char *code; int r, g, b; int br, bg, bb; };
    static const Entry entries[] = {
        {"N",  0,   0,   0,   128, 128, 128},
        {"B",  0,   0,   128, 0,   0,   255},
        {"G",  0,   128, 0,   0,   255, 0},
        {"GB", 0,   128, 128, 0,   255, 255},
        {"R",  128, 0,   0,   255, 0,   0},
        {"RB", 128, 0,   128, 255, 0,   255},
        {"RG", 128, 128, 0,   255, 255, 0},
        {"W",  192, 192, 192, 255, 255, 255},
    };
    for (const Entry &entry : entries) {
        if (code != QString::fromLatin1(entry.code))
            continue;
        *out = bright
            ? QColor(entry.br, entry.bg, entry.bb)
            : QColor(entry.r, entry.g, entry.b);
        return true;
    }
    return false;
}

bool parse_dbase_output_color(const QString &spec, QColor *background, QColor *foreground)
{
    if (!background || !foreground)
        return false;
    const QStringList parts = spec.trimmed().split(QLatin1Char('/'));
    if (parts.size() != 2)
        return false;

    // Gewuenschte Reihenfolge: Hintergrund/Vordergrund.
    // Beispiel W/N = hellgrauer Hintergrund, schwarze Schrift.
    QColor bg;
    QColor fg;
    if (!dbase_palette_color(parts.at(0), true, &bg))
        return false;
    if (!dbase_palette_color(parts.at(1), false, &fg))
        return false;
    *background = bg;
    *foreground = fg;
    return true;
}

void apply_console_appearance()
{
    const QString background = g_console_background.name(QColor::HexRgb);
    const QString border = g_console_border_color.name(QColor::HexRgb);

    // Stage 17: Der farbige Rahmen gehoert zur gesamten Seite und liegt damit
    // auch oberhalb der Menueleiste bzw. unterhalb der Statusleiste. Der
    // eigentliche QPlainTextEdit besitzt keinen eigenen Rahmen mehr.
    const QString frameStyle = QStringLiteral(
        "QFrame#dbaseConsoleFrame, QFrame#dbaseDebugFrame {"
        " background-color: #000000;"
        " border: 3px solid %1;"
        " margin: 0px;"
        " padding: 0px;"
        " }"
    ).arg(border);
    if (g_console_frame)
        g_console_frame->setStyleSheet(frameStyle);
    if (g_debug_frame)
        g_debug_frame->setStyleSheet(frameStyle);

    // Die aeussere Seitenumrandung bleibt 3 Pixel. Direkt oberhalb der
    // Statusleiste liegt zusaetzlich nur eine 2-Pixel-Trennkante in der
    // aktuell mit SET BORDERCOLOR TO gewaehlten Farbe.
    if (g_status_bar) {
        g_status_bar->setStyleSheet(
            QStringLiteral(
                "QStatusBar#dbaseStatusBar {"
                " background-color: #909090;"
                " color: #000000;"
                " border-style: solid;"
                " border-color: %1;"
                " border-width: 2px 0px 0px 0px;"
                " margin: 0px;"
                " padding: 0px;"
                " }"
                "QStatusBar#dbaseStatusBar::item {"
                " border: 0px;"
                " margin: 0px;"
                " padding: 0px;"
                " }"
            ).arg(border)
        );
    }

    if (g_console) {
        g_console->setStyleSheet(
            QStringLiteral(
                "QPlainTextEdit#dbaseConsole {"
                " background-color: %1;"
                " border: 0px;"
                " margin: 0px;"
                " padding: 0px;"
                " }"
            ).arg(background)
        );
        g_console->setContentsMargins(0, 0, 0, 0);
        if (g_console->document())
            g_console->document()->setDocumentMargin(0.0);
    }
}

void apply_console_background()
{
    // Kompatibilitaetshelfer fuer die bisherigen Aufrufstellen. Ab Stage 16
    // werden Hintergrund und Rahmen gemeinsam gesetzt, damit CLEAR SCREEN
    // niemals die Border-Farbe verliert.
    apply_console_appearance();
}

// ---------------------------------------------------------------------------
// Stage 19: 80x25-Zeichenraster. Die Lupen veraendern weiterhin die logische
// Groesse in Punkt um exakt 1 pt. Eine separate Pixelkorrektur (-1/0/+1)
// darf nur eingesetzt werden, wenn Qt/Windows durch DPI-/Metric-Rundungen
// das gemessene Raster nicht exakt trifft.
// ---------------------------------------------------------------------------
QFont make_console_grid_font(int pixelAdjust)
{
    if (g_console_font_family.isEmpty())
        g_console_font_family = choose_console_font_family();

    QFont font(g_console_font_family, g_font_point_size);
    font.setStyleHint(QFont::Monospace);
    font.setFixedPitch(true);

    if (pixelAdjust != 0) {
        int resolvedPixelSize = QFontInfo(font).pixelSize();
        if (resolvedPixelSize <= 0) {
            const qreal dpiY = g_console
                ? g_console->logicalDpiY()
                : (g_window ? g_window->logicalDpiY() : 96.0);
            resolvedPixelSize = qMax(1, qRound(g_font_point_size * dpiY / 72.0));
        }
        font.setPixelSize(qMax(1, resolvedPixelSize + pixelAdjust));
    }
    return font;
}

QSize console_grid_pixel_size(const QFont &font)
{
    const QFontMetrics fm(font);

    // Fuer einen Fixed-Pitch-Font ist M repraesentativ fuer eine Textzelle.
    // qMax(1, ...) verhindert bei exotischen Fonts eine Nullbreite.
    const int cellWidth = qMax(1, fm.horizontalAdvance(QLatin1Char('M')));
    const int lineHeight = qMax(1, fm.lineSpacing());

    return QSize(
        DBASE_TEXT_COLUMNS * cellWidth,
        DBASE_TEXT_ROWS * lineHeight
    );
}

int console_grid_error(const QFont &font, const QSize &viewportSize)
{
    const QSize target = console_grid_pixel_size(font);
    return qAbs(viewportSize.width() - target.width())
         + qAbs(viewportSize.height() - target.height());
}

void apply_output_font()
{
    if (g_font_point_size < DBASE_FONT_MIN_PT)
        g_font_point_size = DBASE_FONT_MIN_PT;
    if (g_font_point_size > DBASE_FONT_MAX_PT)
        g_font_point_size = DBASE_FONT_MAX_PT;

    const QFont font = make_console_grid_font(g_font_pixel_adjust);

    if (g_console)
        g_console->setFont(font);
    if (g_debug)
        g_debug->setFont(font);
    if (g_debug_input)
        g_debug_input->setFont(font);

    // Menue/Status/Popup-Rahmen folgen der vom Benutzer gewaehlten
    // Punktgroesse. Die optionale Pixelkorrektur betrifft nur das
    // eigentliche 80x25-Text-Raster.
    QFont chromeFont(choose_menu_font_family(), g_font_point_size);
    chromeFont.setStyleHint(QFont::Monospace);
    chromeFont.setFixedPitch(true);

    if (g_menu_bar) {
        g_menu_bar->setFont(chromeFont);
        const QList<QMenu *> menus = g_menu_bar->findChildren<QMenu *>();
        for (QMenu *menu : menus) {
            menu->setFont(chromeFont);
            if (AsciiPopupMenu *asciiMenu = dynamic_cast<AsciiPopupMenu *>(menu))
                asciiMenu->setPointSize(g_font_point_size);
        }
    }
    if (g_status_bar) {
        g_status_bar->setFont(chromeFont);
        const int lineHeight = g_status_bar->fontMetrics().height();
        g_status_bar->setFixedHeight(lineHeight + 4);
    }
}

void unlock_window_for_grid_resize()
{
    if (!g_window)
        return;

    // Der Benutzer darf das Hauptfenster nicht mit der Maus skalieren.
    // Fuer die interne 80x25-Neuberechnung (z. B. nach Lupen-Zoom)
    // werden Minimum/Maximum jedoch kurzzeitig wieder freigegeben.
    g_window->setMinimumSize(420, 260);
    g_window->setMaximumSize(QWIDGETSIZE_MAX, QWIDGETSIZE_MAX);
}

void lock_window_to_current_grid_size()
{
    if (!g_window)
        return;

    // Minimum == Maximum entfernt die resizebaren Fensterränder.
    // Die naechste interne Rasteranpassung loest die Sperre gezielt wieder.
    g_window->setFixedSize(g_window->size());
}

void resize_window_to_console_grid()
{
    if (!g_window || !g_console || !g_console->viewport())
        return;

    // Erst Layout/Style anwenden, dann die Differenz zwischen realem
    // Viewport und dem 80x25-Sollraster auf die Fenstergeometrie addieren.
    if (g_app)
        g_app->processEvents();

    for (int pass = 0; pass < 4; ++pass) {
        const QSize target = console_grid_pixel_size(g_console->font());
        const QSize actual = g_console->viewport()->size();
        const int dx = target.width() - actual.width();
        const int dy = target.height() - actual.height();

        if (qAbs(dx) <= DBASE_GRID_TOLERANCE_PX
            && qAbs(dy) <= DBASE_GRID_TOLERANCE_PX)
            break;

        g_window->resize(
            qMax(g_window->minimumWidth(),  g_window->width()  + dx),
            qMax(g_window->minimumHeight(), g_window->height() + dy)
        );

        if (g_app)
            g_app->processEvents();
    }
}

void fine_tune_console_font_for_grid()
{
    if (!g_console || !g_console->viewport())
        return;

    const QSize viewportSize = g_console->viewport()->size();
    const QFont currentFont = make_console_grid_font(0);
    const QSize currentTarget = console_grid_pixel_size(currentFont);

    const bool mismatch =
        qAbs(viewportSize.width()  - currentTarget.width())  > DBASE_GRID_TOLERANCE_PX
        ||
        qAbs(viewportSize.height() - currentTarget.height()) > DBASE_GRID_TOLERANCE_PX;

    if (!mismatch) {
        g_font_pixel_adjust = 0;
        return;
    }

    // Nur +/-1 Pixel sind als Feinkorrektur zulaessig. Gewaehlt wird die
    // Variante, deren 80x25-Raster am naechsten an der realen Viewport-
    // Groesse liegt. Wird es nicht besser, bleibt die Korrektur 0.
    int bestAdjust = 0;
    int bestError = console_grid_error(currentFont, viewportSize);

    const int adjustments[2] = { -1, +1 };
    for (int index = 0; index < 2; ++index) {
        const int adjust = adjustments[index];
        const QFont candidate = make_console_grid_font(adjust);
        const int error = console_grid_error(candidate, viewportSize);
        if (error < bestError) {
            bestError = error;
            bestAdjust = adjust;
        }
    }

    g_font_pixel_adjust = bestAdjust;
    if (bestAdjust != 0)
        apply_output_font();
}

void enforce_console_80x25_grid()
{
    if (!g_console || !g_window)
        return;

    // Das Fenster ist fuer den Benutzer fest. Fuer die interne Neuberechnung
    // des 80x25-Rasters wird es kurz geloest und danach sofort wieder auf
    // die neu berechnete Groesse festgesetzt.
    unlock_window_for_grid_resize();

    // Jeder neue Punktwert startet ohne Pixelkorrektur. Zuerst wird das
    // Fenster auf das exakte Raster der Punktgroesse gebracht. Nur falls
    // das Plattformlayout danach noch abweicht, darf +/-1 Pixel korrigieren.
    g_font_pixel_adjust = 0;
    apply_output_font();
    resize_window_to_console_grid();
    fine_tune_console_font_for_grid();
    resize_window_to_console_grid();

    lock_window_to_current_grid_size();
}

void change_font_size(int delta)
{
    int next = g_font_point_size + delta;
    if (next < DBASE_FONT_MIN_PT)
        next = DBASE_FONT_MIN_PT;
    if (next > DBASE_FONT_MAX_PT)
        next = DBASE_FONT_MAX_PT;
    if (next == g_font_point_size)
        return;

    // Lupe = exakt +/-1 pt. Danach wird das 80x25-Raster neu vermessen.
    g_font_point_size = next;
    enforce_console_80x25_grid();
}

void apply_dark_style()
{
    if (!g_window)
        return;

    g_window->setStyleSheet(QStringLiteral(
        "QMainWindow, QWidget#dbaseRoot, QWidget#dbaseHeader, "
        "QWidget#dbaseConsolePage, QWidget#dbaseDebugPage {"
        "  background-color: #000000;"
        "  color: #a9a9a9;"
        "}"
        "QTabBar {"
        "  background-color: #000000;"
        "  color: #a9a9a9;"
        "}"
        "QTabBar::tab {"
        "  background-color: #111111;"
        "  color: #a9a9a9;"
        "  border: 1px solid #505050;"
        "  border-bottom: 0px;"
        "  padding: 5px 14px;"
        "  min-width: 72px;"
        "}"
        "QTabBar::tab:selected {"
        "  background-color: #000000;"
        "  color: #c0c0c0;"
        "}"
        "QTabBar::tab:hover {"
        "  background-color: #1a1a1a;"
        "}"
        "QMenuBar {"
        "  background-color: #909090;"
        "  color: #000000;"
        "  border: 0px;"
        "  padding: 1px 3px;"
        "}"
        "QMenuBar::item {"
        "  background-color: transparent;"
        "  color: #000000;"
        "  padding: 3px 8px;"
        "}"
        "QMenuBar::item:selected, QMenuBar::item:pressed {"
        "  background-color: #b0b0b0;"
        "  color: #000000;"
        "}"
        "QMenu {"
        "  background-color: #909090;"
        "  color: #000000;"
        "  border: 0px;"
        "}"
        "QMenu::item {"
        "  color: #000000;"
        "  padding: 4px 24px 4px 10px;"
        "}"
        "QMenu::item:selected {"
        "  background-color: #b0b0b0;"
        "  color: #000000;"
        "}"
        "QMenu::separator {"
        "  height: 1px;"
        "  background: #505050;"
        "  margin: 3px 6px;"
        "}"
        "QPlainTextEdit {"
        "  background-color: #000000;"
        "  color: #a9a9a9;"
        "  border: 0px;"
        "  margin: 0px;"
        "  padding: 0px;"
        "  selection-background-color: #404040;"
        "  selection-color: #ffffff;"
        "}"
        "QStatusBar#dbaseStatusBar {"
        "  background-color: #909090;"
        "  color: #000000;"
        "  border: 0px;"
        "  margin: 0px;"
        "  padding: 0px;"
        "}"
        "QStatusBar#dbaseStatusBar::item {"
        "  border: 0px;"
        "  margin: 0px;"
        "  padding: 0px;"
        "}"
        "QLineEdit {"
        "  background-color: #000000;"
        "  color: #a9a9a9;"
        "  border: 1px solid #505050;"
        "  border-top: 0px;"
        "  selection-background-color: #404040;"
        "  selection-color: #ffffff;"
        "  padding: 5px 7px;"
        "}"
        "QToolButton {"
        "  background-color: #000000;"
        "  border: 1px solid transparent;"
        "  padding: 1px;"
        "}"
        "QToolButton:hover {"
        "  background-color: #181818;"
        "  border: 1px solid #505050;"
        "}"
        "QToolButton:pressed {"
        "  background-color: #303030;"
        "}"
        "QScrollBar:vertical {"
        "  background: #000000;"
        "  width: 15px;"
        "  margin: 0px;"
        "}"
        "QScrollBar::handle:vertical {"
        "  background: #555555;"
        "  min-height: 25px;"
        "}"
        "QScrollBar:horizontal {"
        "  background: #000000;"
        "  height: 15px;"
        "  margin: 0px;"
        "}"
        "QScrollBar::handle:horizontal {"
        "  background: #555555;"
        "  min-width: 25px;"
        "}"
    ));
}

void append_text(QPlainTextEdit *editor, const char *text, int length)
{
    if (!editor || !text || length <= 0)
        return;

    const QString value = QString::fromLocal8Bit(text, length);

    QTextCursor cursor = editor->textCursor();
    cursor.movePosition(QTextCursor::End);
    QTextCharFormat format;
    format.setForeground(g_output_foreground);
    format.setBackground(g_output_background);
    cursor.insertText(value, format);
    editor->setTextCursor(cursor);

    // WICHTIG: ensureCursorVisible() kann bei NoWrap den Editor horizontal
    // bis ans Ende einer langen Zeile verschieben. Das war die Ursache dafuer,
    // dass der Text im Fenster scheinbar nur in einem rechten/oberen Ausschnitt
    // sichtbar war. Ausgabe bleibt deshalb immer linksbuendig; vertikal wird
    // weiterhin automatisch bis zum Ende gescrollt.
    if (QScrollBar *h = editor->horizontalScrollBar())
        h->setValue(h->minimum());
    if (QScrollBar *v = editor->verticalScrollBar())
        v->setValue(v->maximum());
}

void ensure_trailing_blank_line(QPlainTextEdit *editor)
{
    if (!editor || !editor->document())
        return;

    // Eine abgeschlossene Eingabe soll am Dokumentende immer wenigstens
    // einen leeren Block lassen. Menue und Statusleiste liegen ausserhalb
    // des Dokuments und bleiben dadurch unveraendert erreichbar.
    QTextCursor cursor(editor->document());
    cursor.movePosition(QTextCursor::End);
    if (!editor->toPlainText().endsWith(QLatin1Char('\n')))
        cursor.insertText(QStringLiteral("\n"));
    editor->setTextCursor(cursor);
    if (QScrollBar *h = editor->horizontalScrollBar())
        h->setValue(h->minimum());
    if (QScrollBar *v = editor->verticalScrollBar())
        v->setValue(v->maximum());
}

int debug_tab_index()
{
    if (!g_tab_bar)
        return -1;
    for (int i = 0; i < g_tab_bar->count(); ++i) {
        if (g_tab_bar->tabData(i).toInt() == TAB_DEBUG)
            return i;
    }
    return -1;
}

void select_console()
{
    if (!g_tab_bar || !g_stack)
        return;
    g_tab_bar->setCurrentIndex(0);
    g_stack->setCurrentWidget(g_console_page);
}

void install_debug_tab(bool select_it)
{
    if (!g_tab_bar || !g_stack || !g_debug_page)
        return;

    int index = debug_tab_index();
    if (index < 0) {
        index = g_tab_bar->addTab(QStringLiteral("DEBUG"));
        g_tab_bar->setTabData(index, TAB_DEBUG);
    }

    g_debug_visible = true;
    if (select_it) {
        g_tab_bar->setCurrentIndex(index);
        g_stack->setCurrentWidget(g_debug_page);
        if (g_debug_input)
            g_debug_input->setFocus(Qt::OtherFocusReason);
    }
}

void remove_debug_tab()
{
    if (!g_tab_bar || !g_stack)
        return;

    const int index = debug_tab_index();
    if (index >= 0)
        g_tab_bar->removeTab(index);

    g_debug_visible = false;
    select_console();
}

void connect_tab_bar()
{
    if (!g_tab_bar || !g_stack)
        return;

    QObject::connect(g_tab_bar, &QTabBar::currentChanged, [](int index) {
        if (!g_tab_bar || !g_stack || index < 0)
            return;

        const int page = g_tab_bar->tabData(index).toInt();
        if (page == TAB_DEBUG && g_debug_visible)
            g_stack->setCurrentWidget(g_debug_page);
        else
            g_stack->setCurrentWidget(g_console_page);
    });
}

QToolButton *make_zoom_button(bool plus, QWidget *parent)
{
    QToolButton *button = new QToolButton(parent);
    button->setAutoRaise(true);
    button->setIcon(create_zoom_icon(plus));
    button->setIconSize(QSize(20, 20));
    button->setFixedSize(28, 28);
    button->setToolTip(
        plus
            ? QStringLiteral("Text vergroessern (maximal 75 pt)")
            : QStringLiteral("Text verkleinern (minimal 9 pt)")
    );
    return button;
}

QAction *menu_node_action(MenuNode *node)
{
    if (!node)
        return nullptr;
    if (node->action)
        return node->action;
    if (node->menu)
        return node->menu->menuAction();
    return nullptr;
}

QMenu *ensure_menu_container(MenuNode *node)
{
    if (!node)
        return nullptr;
    if (node->menu)
        return node->menu;

    QWidget *menuParent = nullptr;
    if (node->parent && node->parent->menu)
        menuParent = node->parent->menu;
    else
        menuParent = g_menu_bar;
    AsciiPopupMenu *menu = new AsciiPopupMenu(node->text, menuParent);
    menu->setPointSize(g_font_point_size);
    menu->setFont(g_menu_bar ? g_menu_bar->font() : QFont());
    if (node->parent && node->parent->menu) {
        if (node->action) {
            node->parent->menu->removeAction(node->action);
            node->action->deleteLater();
            node->action = nullptr;
        }
        node->parent->menu->addMenu(menu);
    } else if (g_menu_bar) {
        g_menu_bar->addMenu(menu);
    }
    node->menu = menu;
    return menu;
}

MenuNode *menu_node_from_handle(void *handle)
{
    return static_cast<MenuNode *>(handle);
}

QString menu_text_from_bytes(const char *text, int length)
{
    if (!text || length <= 0)
        return QString();
    return QString::fromLocal8Bit(text, length);
}

} // namespace

extern "C" D64QT5_API int DBaseQtInitialize(const char *title)
{
    if (g_window)
        return 1;

    QApplication *existing = qobject_cast<QApplication *>(QCoreApplication::instance());
    if (existing) {
        g_app = existing;
    } else {
        static int argc = 1;
        static char arg0[] = "dBase";
        static char *argv[] = { arg0, nullptr };
        g_app = new QApplication(argc, argv);
        g_owns_app = true;
    }

    if (!g_app)
        return 0;

    g_window = new QMainWindow();
    // Die Standardgroesse wird nach Aufbau des Layouts aus 80x25 Zeichen
    // und den aktuellen Font-Metriken berechnet.
    g_window->setMinimumSize(420, 260);
    g_window->setWindowTitle(
        title && *title
            ? QString::fromLocal8Bit(title)
            : QStringLiteral("dBase Qt5 Console / DEBUG")
    );

    g_root = new QWidget(g_window);
    g_root->setObjectName(QStringLiteral("dbaseRoot"));
    auto *root_layout = new QVBoxLayout(g_root);
    root_layout->setContentsMargins(0, 0, 0, 0);
    root_layout->setSpacing(0);

    // Eigene Kopfzeile: Lupen links, echte QTabBar rechts davon.
    // Kein QTabWidget-Corner-Widget: dadurch bleibt die Geometrie unter allen Qt5-
    // Styles stabil und die Tab-Titel sind garantiert sichtbar.
    g_header = new QWidget(g_root);
    g_header->setObjectName(QStringLiteral("dbaseHeader"));
    g_header->setSizePolicy(QSizePolicy::Expanding, QSizePolicy::Fixed);
    auto *header_layout = new QHBoxLayout(g_header);
    header_layout->setContentsMargins(5, 3, 5, 0);
    header_layout->setSpacing(3);

    g_zoom_in = make_zoom_button(true, g_header);
    g_zoom_out = make_zoom_button(false, g_header);
    header_layout->addWidget(g_zoom_in, 0, Qt::AlignBottom);
    header_layout->addWidget(g_zoom_out, 0, Qt::AlignBottom);
    header_layout->addSpacing(4);

    g_tab_bar = new QTabBar(g_header);
    g_tab_bar->setObjectName(QStringLiteral("dbaseTabBar"));
    g_tab_bar->setDrawBase(false);
    g_tab_bar->setExpanding(false);
    g_tab_bar->setMovable(false);
    g_tab_bar->setUsesScrollButtons(true);
    g_tab_bar->setSizePolicy(QSizePolicy::Expanding, QSizePolicy::Fixed);
    const int console_tab = g_tab_bar->addTab(QStringLiteral("Konsole"));
    g_tab_bar->setTabData(console_tab, TAB_CONSOLE);
    header_layout->addWidget(g_tab_bar, 1, Qt::AlignBottom);

    root_layout->addWidget(g_header, 0);

    g_stack = new QStackedWidget(g_root);
    g_stack->setObjectName(QStringLiteral("dbaseOutputStack"));
    g_stack->setSizePolicy(QSizePolicy::Expanding, QSizePolicy::Expanding);
    root_layout->addWidget(g_stack, 1);

    // KONSOLE ---------------------------------------------------------
    g_console_page = new QWidget(g_stack);
    g_console_page->setObjectName(QStringLiteral("dbaseConsolePage"));
    g_console_page->setSizePolicy(QSizePolicy::Expanding, QSizePolicy::Expanding);
    auto *console_page_layout = new QVBoxLayout(g_console_page);
    console_page_layout->setContentsMargins(0, 0, 0, 0);
    console_page_layout->setSpacing(0);

    // Der 3-Pixel-Rahmen umschliesst ab Stage 17 die komplette Seite:
    // Menue, Textflaeche und Statusleiste. Damit liegt seine obere Kante
    // oberhalb der Menueleiste statt zwischen Menue und Texteditor.
    g_console_frame = new QFrame(g_console_page);
    g_console_frame->setObjectName(QStringLiteral("dbaseConsoleFrame"));
    g_console_frame->setFrameShape(QFrame::NoFrame);
    g_console_frame->setSizePolicy(QSizePolicy::Expanding, QSizePolicy::Expanding);
    auto *console_layout = new QVBoxLayout(g_console_frame);
    console_layout->setContentsMargins(0, 0, 0, 0);
    console_layout->setSpacing(0);
    console_page_layout->addWidget(g_console_frame, 1);

    // Hauptmenue: feste erste Zeile innerhalb des Rahmens.
    g_menu_bar = new QMenuBar(g_console_frame);
    g_menu_bar->setObjectName(QStringLiteral("dbaseMainMenu"));
    g_menu_bar->setNativeMenuBar(false);
    g_menu_bar->setSizePolicy(QSizePolicy::Expanding, QSizePolicy::Fixed);
    g_menu_bar->setContentsMargins(0, 0, 0, 0);
    console_layout->addWidget(g_menu_bar, 0);

    // Scrollbarer Mittelbereich. Kein Padding, kein Margin, kein eigener
    // Rahmen; der QTextDocument-Innenrand ist exakt 0 Pixel. Die
    // QAbstractScrollArea-Viewport-Margins bleiben beim Qt-Default 0;
    // Der protected Viewport-Margin-Setter wird hier bewusst nicht
    // von außen aufgerufen.
    g_console = new QPlainTextEdit(g_console_frame);
    g_console->setObjectName(QStringLiteral("dbaseConsole"));
    g_console->setReadOnly(true);
    g_console->setFrameShape(QFrame::NoFrame);
    g_console->setContentsMargins(0, 0, 0, 0);
    g_console->document()->setDocumentMargin(0.0);
    g_console->setLineWrapMode(QPlainTextEdit::NoWrap);
    g_console->setHorizontalScrollBarPolicy(Qt::ScrollBarAsNeeded);
    g_console->setVerticalScrollBarPolicy(Qt::ScrollBarAsNeeded);
    g_console->setSizePolicy(QSizePolicy::Expanding, QSizePolicy::Expanding);
    console_layout->addWidget(g_console, 1);

    // Feste letzte Zeile innerhalb des Rahmens. QStatusBar ist bewusst ein
    // echtes Widget und kein Text im Dokument; dadurch bleiben spaetere
    // Statusfelder/Widgets erreichbar, waehrend nur die Mitte scrollt.
    g_status_bar = new QStatusBar(g_console_frame);
    g_status_bar->setObjectName(QStringLiteral("dbaseStatusBar"));
    g_status_bar->setSizeGripEnabled(false);
    g_status_bar->setContentsMargins(0, 0, 0, 0);
    g_status_bar->setSizePolicy(QSizePolicy::Expanding, QSizePolicy::Fixed);
    g_status_bar->setFocusPolicy(Qt::StrongFocus);
    console_layout->addWidget(g_status_bar, 0);
    g_stack->addWidget(g_console_page);

    // DEBUG -----------------------------------------------------------
    g_debug_page = new QWidget(g_stack);
    g_debug_page->setObjectName(QStringLiteral("dbaseDebugPage"));
    g_debug_page->setSizePolicy(QSizePolicy::Expanding, QSizePolicy::Expanding);
    auto *debug_page_layout = new QVBoxLayout(g_debug_page);
    debug_page_layout->setContentsMargins(0, 0, 0, 0);
    debug_page_layout->setSpacing(0);

    g_debug_frame = new QFrame(g_debug_page);
    g_debug_frame->setObjectName(QStringLiteral("dbaseDebugFrame"));
    g_debug_frame->setFrameShape(QFrame::NoFrame);
    g_debug_frame->setSizePolicy(QSizePolicy::Expanding, QSizePolicy::Expanding);
    auto *debug_layout = new QVBoxLayout(g_debug_frame);
    debug_layout->setContentsMargins(0, 0, 0, 0);
    debug_layout->setSpacing(0);
    debug_page_layout->addWidget(g_debug_frame, 1);

    g_debug = new QPlainTextEdit(g_debug_frame);
    g_debug->setObjectName(QStringLiteral("dbaseDebug"));
    g_debug->setReadOnly(true);
    g_debug->setFrameShape(QFrame::NoFrame);
    g_debug->setContentsMargins(0, 0, 0, 0);
    g_debug->document()->setDocumentMargin(0.0);
    g_debug->setLineWrapMode(QPlainTextEdit::NoWrap);
    g_debug->setHorizontalScrollBarPolicy(Qt::ScrollBarAsNeeded);
    g_debug->setVerticalScrollBarPolicy(Qt::ScrollBarAsNeeded);
    g_debug->setSizePolicy(QSizePolicy::Expanding, QSizePolicy::Expanding);
    debug_layout->addWidget(g_debug, 1);

    g_debug_input = new QLineEdit(g_debug_frame);
    g_debug_input->setObjectName(QStringLiteral("dbaseDebugInput"));
    g_debug_input->setSizePolicy(QSizePolicy::Expanding, QSizePolicy::Fixed);
    g_debug_input->setMinimumHeight(28);
    g_debug_input->setPlaceholderText(QStringLiteral("Eingabe / Debug-Befehl ..."));
    debug_layout->addWidget(g_debug_input, 0);
    g_stack->addWidget(g_debug_page);

    connect_tab_bar();

    QObject::connect(g_zoom_in, &QToolButton::clicked, []() {
        change_font_size(+1);
    });
    QObject::connect(g_zoom_out, &QToolButton::clicked, []() {
        change_font_size(-1);
    });

    QObject::connect(g_debug_input, &QLineEdit::returnPressed, []() {
        if (!g_debug_input || !g_debug)
            return;

        const QString input = g_debug_input->text();
        if (!input.isEmpty()) {
            const QByteArray bytes = (QStringLiteral("> ") + input + QLatin1Char('\n')).toLocal8Bit();
            append_text(g_debug, bytes.constData(), bytes.size());
            ensure_trailing_blank_line(g_debug);
        }
        g_debug_input->clear();
    });

    apply_dark_style();
    apply_output_font();
    apply_console_background();

    // Definierter Startzustand: Konsole sichtbar, DEBUG nicht vorhanden.
    remove_debug_tab();
    select_console();

    g_window->setCentralWidget(g_root);

    // Bereits vor dem ersten Show eine passende Standardgeometrie vorbereiten.
    // DBaseQtShowWindow wiederholt die Messung nach dem ersten nativen Layout.
    enforce_console_80x25_grid();
    return 1;
}

extern "C" D64QT5_API void DBaseQtShowWindow(void)
{
    if (!g_window)
        return;
    g_window->show();
    enforce_console_80x25_grid();
    g_window->raise();
    g_window->activateWindow();
}

extern "C" D64QT5_API void DBaseQtProcessEvents(void)
{
    if (g_app)
        g_app->processEvents();
}

extern "C" D64QT5_API void DBaseQtSetDebugVisible(int visible)
{
    if (visible)
        install_debug_tab(true);
    else
        remove_debug_tab();

    if (g_app)
        g_app->processEvents();
}

extern "C" D64QT5_API void DBaseQtAppendConsole(const char *text, int length)
{
    select_console();
    append_text(g_console, text, length);
}

extern "C" D64QT5_API void DBaseQtAppendDebug(const char *text, int length)
{
    install_debug_tab(true);
    append_text(g_debug, text, length);
}

extern "C" D64QT5_API int DBaseQtSetColorNormal(const char *name, int length)
{
    if (!g_console || !name || length <= 0)
        return 0;

    const QString requested = QString::fromLocal8Bit(name, length).trimmed();
    QColor color;
    if (!windows_system_color(requested, &color) && !rgb_literal_color(requested, &color))
        return 0;

    g_console_background = color;
    apply_console_background();
    if (g_console)
        g_console->viewport()->update();
    if (g_app)
        g_app->processEvents();
    return 1;
}

extern "C" D64QT5_API int DBaseQtSetOutputColor(const char *spec, int length)
{
    if (!spec || length <= 0)
        return 0;
    const QString requested = QString::fromLocal8Bit(spec, length).trimmed();
    QColor background;
    QColor foreground;
    if (!parse_dbase_output_color(requested, &background, &foreground))
        return 0;
    g_output_background = background;
    g_output_foreground = foreground;
    if (g_app)
        g_app->processEvents();
    return 1;
}

extern "C" D64QT5_API void DBaseQtClearScreen(void)
{
    if (!g_console)
        return;

    // CLEAR SCREEN loescht nur den Inhalt. Der QPlainTextEdit selbst, seine
    // Geometrie und insbesondere sein Rahmen bleiben bestehen. Die komplette
    // Textflaeche uebernimmt die zuletzt mit SET COLOR TO gewaehlte
    // Hintergrundfarbe.
    select_console();
    g_console->clear();
    g_console_background = g_output_background;
    apply_console_appearance();

    QTextCursor cursor(g_console->document());
    cursor.movePosition(QTextCursor::Start);
    g_console->setTextCursor(cursor);
    if (QScrollBar *h = g_console->horizontalScrollBar())
        h->setValue(h->minimum());
    if (QScrollBar *v = g_console->verticalScrollBar())
        v->setValue(v->minimum());
    g_console->viewport()->update();
    if (g_app)
        g_app->processEvents();
}

extern "C" D64QT5_API int DBaseQtSetBorderColor(const char *name, int length)
{
    if (!g_console || !name || length <= 0)
        return 0;

    const QString requested = QString::fromLocal8Bit(name, length).trimmed();
    QColor color;
    if (!windows_system_color(requested, &color) && !rgb_literal_color(requested, &color))
        return 0;

    g_console_border_color = color;
    apply_console_appearance();
    g_console->viewport()->update();
    if (g_app)
        g_app->processEvents();
    return 1;
}

extern "C" D64QT5_API void *DBaseQtMenuCreate(void *owner)
{
    if (!g_menu_bar)
        return nullptr;

    MenuNode *parent = menu_node_from_handle(owner);
    MenuNode *node = new MenuNode();
    node->parent = parent;
    g_menu_nodes.append(node);

    if (!parent) {
        AsciiPopupMenu *popup = new AsciiPopupMenu(QString(), g_menu_bar);
        popup->setPointSize(g_font_point_size);
        popup->setFont(g_menu_bar->font());
        node->menu = popup;
        g_menu_bar->addMenu(node->menu);
    } else {
        QMenu *parentMenu = ensure_menu_container(parent);
        if (!parentMenu)
            return node;
        node->action = new QAction(parentMenu);
        parentMenu->addAction(node->action);
        QObject::connect(node->action, &QAction::triggered, [node](bool) {
            if (node && node->callback)
                node->callback();
        });
    }
    return node;
}

extern "C" D64QT5_API void DBaseQtMenuSetText(void *handle, const char *text, int length)
{
    MenuNode *node = menu_node_from_handle(handle);
    if (!node)
        return;
    node->text = menu_text_from_bytes(text, length);
    if (node->menu)
        node->menu->setTitle(node->text);
    if (node->action)
        node->action->setText(node->text);
}

extern "C" D64QT5_API void DBaseQtMenuSetSeparator(void *handle, int separator)
{
    MenuNode *node = menu_node_from_handle(handle);
    QAction *action = menu_node_action(node);
    if (action)
        action->setSeparator(separator != 0);
}

extern "C" D64QT5_API void DBaseQtMenuSetShortcut(void *handle, const char *text, int length)
{
    MenuNode *node = menu_node_from_handle(handle);
    QAction *action = menu_node_action(node);
    if (!action)
        return;
    const QString shortcut = menu_text_from_bytes(text, length);
    action->setShortcut(QKeySequence(shortcut));
}

extern "C" D64QT5_API void DBaseQtMenuSetOnClick(void *handle, void (*callback)(void))
{
    MenuNode *node = menu_node_from_handle(handle);
    if (node)
        node->callback = callback;
}

extern "C" D64QT5_API void DBaseQtMarkProgramFinished(void)
{
    g_program_finished = true;
    if (g_debug_input) {
        g_debug_input->setPlaceholderText(
            QStringLiteral("Programm beendet - Eingabe moeglich; Fenster schliessen zum Beenden")
        );
    }
    if (g_app)
        g_app->processEvents();
}

extern "C" D64QT5_API int DBaseQtExec(void)
{
    if (!g_app)
        return 1;
    return g_app->exec();
}

extern "C" D64QT5_API void DBaseQtShutdown(void)
{
    delete g_window;
    g_window = nullptr;
    g_root = nullptr;
    g_header = nullptr;
    g_tab_bar = nullptr;
    g_stack = nullptr;
    g_console_page = nullptr;
    g_debug_page = nullptr;
    g_console_frame = nullptr;
    g_debug_frame = nullptr;
    g_menu_bar = nullptr;
    g_status_bar = nullptr;
    g_console = nullptr;
    g_debug = nullptr;
    g_debug_input = nullptr;
    g_zoom_in = nullptr;
    g_zoom_out = nullptr;
    g_debug_visible = false;
    g_program_finished = false;
    g_font_point_size = 10;
    g_font_pixel_adjust = 0;
    g_console_font_family.clear();
    g_console_background = QColor(0, 0, 0);
    g_console_border_color = QColor(255, 255, 255);
    g_output_foreground = QColor(169, 169, 169);
    g_output_background = QColor(0, 0, 0);
    for (MenuNode *node : g_menu_nodes)
        delete node;
    g_menu_nodes.clear();

    if (g_owns_app) {
        delete g_app;
        g_app = nullptr;
        g_owns_app = false;
    }
}
