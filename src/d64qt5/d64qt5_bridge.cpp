#define D64QT5_BRIDGE_EXPORTS 1
#include "d64qt5_bridge.h"

#include <QApplication>
#include <QAction>
#include <QByteArray>
#include <QColor>
#include <QCoreApplication>
#include <QDialog>
#include <QEventLoop>
#include <QEvent>
#include <QFont>
#include <QFontDatabase>
#include <QFontInfo>
#include <QFontMetrics>
#include <QFrame>
#include <QHBoxLayout>
#include <QGridLayout>
#include <QIcon>
#include <QLineEdit>
#include <QLabel>
#include <QKeySequence>
#include <QList>
#include <QMainWindow>
#include <QMenu>
#include <QMenuBar>
#include <QPainter>
#include <QPaintEvent>
#include <QMouseEvent>
#include <QPalette>
#include <QPixmap>
#include <QPlainTextEdit>
#include <QPushButton>
#include <QRegularExpression>
#include <QRegion>
#include <QCloseEvent>
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
#include <QTimer>
#include <QVBoxLayout>
#include <QWidget>
#include <QString>
#include <QStringList>
#include <QVariant>

#include <cmath>
#include <string>
#include <vector>

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

class LoginDialog;
LoginDialog *g_login_dialog = nullptr;
QMenu *g_security_file_menu = nullptr;
QAction *g_login_action = nullptr;
QAction *g_quit_action = nullptr;
struct SessionNode;
SessionNode *g_active_login_session = nullptr;
bool g_login_session = false;

bool g_debug_visible = false;
bool g_program_finished = false;
bool g_default_menu_created = false;
// Stage 29: zentraler, idempotenter Shutdown-Status. Er wird bereits beim
// Schliessen des Hauptfensters gesetzt, also auch dann, wenn gerade ein
// eigener Login-QEventLoop laeuft.
bool g_shutdown_requested = false;
bool g_shutdown_in_progress = false;
int g_font_point_size = 10;
int g_font_pixel_adjust = 0;
QString g_console_font_family;
QColor g_console_background(0, 0, 0);
QColor g_console_border_color(255, 255, 255);
QColor g_output_foreground(169, 169, 169);
QColor g_output_background(0, 0, 0);

// Stage 26: CLEAR SCREEN-Zustand fuer Raster-Neuberechnungen merken.
// Nur ein unveraendertes Zeichenmuster wird nach einem Lupen-Zoom neu
// aufgebaut; normale Textausgabe hebt den aktiven Musterzustand auf.
enum class ConsoleClearMode {
    None,
    Plain,
    CharacterPattern,
    Color
};
ConsoleClearMode g_console_clear_mode = ConsoleClearMode::None;
int g_console_clear_char_code = -1;
QColor g_console_clear_char_foreground(169, 169, 169);
QColor g_console_clear_char_background(0, 0, 0);

constexpr int DBASE_FONT_MIN_PT = 9;
constexpr int DBASE_FONT_MAX_PT = 75;
constexpr int DBASE_TEXT_COLUMNS = 80;
constexpr int DBASE_TEXT_ROWS = 25;
constexpr int DBASE_LOGIN_DIALOG_COLUMNS = 48;
constexpr int DBASE_LOGIN_DIALOG_ROWS = 12;
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

struct SessionNode {
    void *parent = nullptr;
    bool authenticated = false;
    QString username;
    QString group;
};

QList<MenuNode *> g_menu_nodes;

// Forward declarations fuer Stage-26-Raster-/CLEAR-SCREEN-Helfer.
void apply_console_appearance();
void select_console();
QList<SessionNode *> g_session_nodes;

void update_menu_access_state();
void ensure_security_menu_items();
void show_login_dialog(SessionNode *session);
void set_login_session_state(bool value);
void cancel_login_dialog();
void request_runtime_shutdown();

class DBaseMainWindow final : public QMainWindow
{
protected:
    void closeEvent(QCloseEvent *event) override
    {
        // Das Hauptfenster ist der Owner der kompletten dBase-UI. Ein Close
        // beendet deshalb auch verschachtelte Dialog-Eventloops und alle
        // weiteren Top-Level-/Subfenster.
        request_runtime_shutdown();
        QMainWindow::closeEvent(event);
    }
};

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

void connect_quit_action(QAction *action)
{
    if (!action)
        return;
    if (action->property("dbaseQuitHooked").toBool())
        return;
    action->setProperty("dbaseQuitHooked", true);
    QObject::connect(action, &QAction::triggered, []() {
        if (g_window)
            g_window->close();
        else
            request_runtime_shutdown();
    });
}

void connect_login_action(QAction *action)
{
    if (!action)
        return;
    if (action->property("dbaseLoginHooked").toBool())
        return;
    action->setProperty("dbaseLoginHooked", true);
    QObject::connect(action, &QAction::triggered, []() {
        if (g_active_login_session)
            show_login_dialog(g_active_login_session);
    });
}

QString normalized_menu_text(const QString &text)
{
    QString value = text;
    value.remove(QLatin1Char('&'));
    return value.trimmed();
}

QMenu *find_file_menu()
{
    if (!g_menu_bar)
        return nullptr;
    for (QAction *topAction : g_menu_bar->actions()) {
        QMenu *menu = topAction ? topAction->menu() : nullptr;
        if (!menu)
            continue;
        if (normalized_menu_text(menu->title()).compare(
                QStringLiteral("Datei"), Qt::CaseInsensitive) == 0)
            return menu;
    }
    return nullptr;
}

QAction *find_menu_action(QMenu *menu, const QString &text)
{
    if (!menu)
        return nullptr;
    for (QAction *action : menu->actions()) {
        if (!action || action->isSeparator())
            continue;
        if (normalized_menu_text(action->text()).compare(text, Qt::CaseInsensitive) == 0)
            return action;
    }
    return nullptr;
}

void ensure_security_menu_items()
{
    if (!g_menu_bar)
        return;

    QMenu *fileMenu = find_file_menu();
    if (!fileMenu) {
        AsciiPopupMenu *popup = new AsciiPopupMenu(QStringLiteral("Datei"), g_menu_bar);
        popup->setPointSize(g_font_point_size);
        popup->setFont(g_menu_bar->font());
        g_menu_bar->addMenu(popup);
        fileMenu = popup;
    }
    g_security_file_menu = fileMenu;

    QAction *loginAction = find_menu_action(fileMenu, QStringLiteral("Login"));
    QAction *quitAction = find_menu_action(fileMenu, QStringLiteral("Beenden"));

    if (!loginAction) {
        if (quitAction) {
            loginAction = new QAction(QStringLiteral("Login"), fileMenu);
            fileMenu->insertAction(quitAction, loginAction);
        } else {
            loginAction = fileMenu->addAction(QStringLiteral("Login"));
        }
    }
    if (!quitAction)
        quitAction = fileMenu->addAction(QStringLiteral("Beenden"));

    g_login_action = loginAction;
    g_quit_action = quitAction;
    connect_login_action(g_login_action);
    connect_quit_action(g_quit_action);
    update_menu_access_state();
}

void remember_and_set_action_enabled(QAction *action, bool enabled)
{
    if (!action)
        return;
    if (!action->property("dbaseSecuritySavedEnabled").isValid())
        action->setProperty("dbaseSecuritySavedEnabled", action->isEnabled());
    action->setEnabled(enabled);
}

void restore_action_enabled(QAction *action)
{
    if (!action)
        return;
    const QVariant saved = action->property("dbaseSecuritySavedEnabled");
    if (saved.isValid()) {
        action->setEnabled(saved.toBool());
        action->setProperty("dbaseSecuritySavedEnabled", QVariant());
    }
}

void update_menu_access_state()
{
    if (!g_menu_bar)
        return;

    // Ohne SESSION gibt es noch keinen Login-Zwang. Erst new SESSION()
    // aktiviert die Zugriffssperre.
    if (!g_active_login_session) {
        for (QAction *topAction : g_menu_bar->actions()) {
            restore_action_enabled(topAction);
            if (QMenu *menu = topAction ? topAction->menu() : nullptr) {
                for (QAction *action : menu->actions())
                    restore_action_enabled(action);
            }
        }
        return;
    }

    if (g_login_session) {
        for (QAction *topAction : g_menu_bar->actions()) {
            restore_action_enabled(topAction);
            if (QMenu *menu = topAction ? topAction->menu() : nullptr) {
                for (QAction *action : menu->actions())
                    restore_action_enabled(action);
            }
        }
        return;
    }

    // Ohne Login darf nur das Datei-Menue als Container geoeffnet werden.
    // Innerhalb davon bleiben ausschliesslich Login und Beenden aktiv.
    for (QAction *topAction : g_menu_bar->actions()) {
        QMenu *menu = topAction ? topAction->menu() : nullptr;
        const bool fileContainer = menu && menu == g_security_file_menu;
        remember_and_set_action_enabled(topAction, fileContainer);
        if (!menu)
            continue;
        for (QAction *action : menu->actions()) {
            if (!action || action->isSeparator())
                continue;
            const bool allowed = action == g_login_action || action == g_quit_action;
            remember_and_set_action_enabled(action, allowed);
        }
    }
}

void set_login_session_state(bool value)
{
    g_login_session = value;
    update_menu_access_state();
}

void create_standard_menu()
{
    if (!g_menu_bar || g_default_menu_created)
        return;

    QAction *systemEntry = g_menu_bar->addAction(QStringLiteral("="));
    systemEntry->setEnabled(true);

    AsciiPopupMenu *fileMenu = new AsciiPopupMenu(QStringLiteral("Datei"), g_menu_bar);
    fileMenu->setPointSize(g_font_point_size);
    fileMenu->setFont(g_menu_bar->font());

    fileMenu->addAction(QStringLiteral("Neu"));
    fileMenu->addAction(QStringLiteral("Speichern"));
    fileMenu->addAction(QStringLiteral("Speichern unter..."));
    fileMenu->addAction(QStringLiteral("Alle Schließen"));
    fileMenu->addSeparator();
    g_login_action = fileMenu->addAction(QStringLiteral("Login"));
    g_quit_action = fileMenu->addAction(QStringLiteral("Beenden"));
    g_security_file_menu = fileMenu;

    connect_login_action(g_login_action);
    connect_quit_action(g_quit_action);

    g_menu_bar->addMenu(fileMenu);
    g_default_menu_created = true;
    update_menu_access_state();
}

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

QChar cp437_character(int code)
{
    if (code < 0 || code > 255)
        return QChar();
    if (code < 128)
        return QChar(static_cast<ushort>(code));

    static const ushort table[128] = {
        0x00C7, 0x00FC, 0x00E9, 0x00E2, 0x00E4, 0x00E0, 0x00E5, 0x00E7,
        0x00EA, 0x00EB, 0x00E8, 0x00EF, 0x00EE, 0x00EC, 0x00C4, 0x00C5,
        0x00C9, 0x00E6, 0x00C6, 0x00F4, 0x00F6, 0x00F2, 0x00FB, 0x00F9,
        0x00FF, 0x00D6, 0x00DC, 0x00A2, 0x00A3, 0x00A5, 0x20A7, 0x0192,
        0x00E1, 0x00ED, 0x00F3, 0x00FA, 0x00F1, 0x00D1, 0x00AA, 0x00BA,
        0x00BF, 0x2310, 0x00AC, 0x00BD, 0x00BC, 0x00A1, 0x00AB, 0x00BB,
        0x2591, 0x2592, 0x2593, 0x2502, 0x2524, 0x2561, 0x2562, 0x2556,
        0x2555, 0x2563, 0x2551, 0x2557, 0x255D, 0x255C, 0x255B, 0x2510,
        0x2514, 0x2534, 0x252C, 0x251C, 0x2500, 0x253C, 0x255E, 0x255F,
        0x255A, 0x2554, 0x2569, 0x2566, 0x2560, 0x2550, 0x256C, 0x2567,
        0x2568, 0x2564, 0x2565, 0x2559, 0x2558, 0x2552, 0x2553, 0x256B,
        0x256A, 0x2518, 0x250C, 0x2588, 0x2584, 0x258C, 0x2590, 0x2580,
        0x03B1, 0x00DF, 0x0393, 0x03C0, 0x03A3, 0x03C3, 0x00B5, 0x03C4,
        0x03A6, 0x0398, 0x03A9, 0x03B4, 0x221E, 0x03C6, 0x03B5, 0x2229,
        0x2261, 0x00B1, 0x2265, 0x2264, 0x2320, 0x2321, 0x00F7, 0x2248,
        0x00B0, 0x2219, 0x00B7, 0x221A, 0x207F, 0x00B2, 0x25A0, 0x00A0,
    };
    return QChar(table[code - 128]);
}

void reset_console_after_clear()
{
    if (!g_console)
        return;
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

bool render_console_character_pattern(
    int byteCode,
    const QColor &foreground,
    const QColor &background)
{
    if (!g_console || byteCode < 0 || byteCode > 255)
        return false;

    const QChar glyph = cp437_character(byteCode);
    if (glyph.isNull() && byteCode != 0)
        return false;

    QString pattern;
    pattern.reserve(DBASE_TEXT_COLUMNS * DBASE_TEXT_ROWS + (DBASE_TEXT_ROWS - 1));
    const QString row(DBASE_TEXT_COLUMNS, glyph);
    for (int y = 0; y < DBASE_TEXT_ROWS; ++y) {
        if (y)
            pattern.append(QLatin1Char('\n'));
        pattern.append(row);
    }

    select_console();
    g_console->clear();
    g_console_background = background;
    apply_console_appearance();

    QTextCursor cursor(g_console->document());
    cursor.movePosition(QTextCursor::Start);
    QTextCharFormat format;
    format.setForeground(foreground);
    format.setBackground(background);
    cursor.insertText(pattern, format);
    g_console->setTextCursor(cursor);
    reset_console_after_clear();
    return true;
}

void restore_console_clear_pattern_after_grid_change()
{
    if (g_console_clear_mode != ConsoleClearMode::CharacterPattern)
        return;

    render_console_character_pattern(
        g_console_clear_char_code,
        g_console_clear_char_foreground,
        g_console_clear_char_background
    );
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

QSize current_console_cell_size()
{
    const QFont font = g_console ? g_console->font() : QFont(choose_console_font_family(), g_font_point_size);
    const QFontMetrics fm(font);
    return QSize(
        qMax(1, fm.horizontalAdvance(QLatin1Char('M'))),
        qMax(1, fm.lineSpacing())
    );
}

class LoginDialog final : public QDialog
{
public:
    explicit LoginDialog(SessionNode *session, QWidget *parent = nullptr)
        : QDialog(parent), m_session(session)
    {
        setObjectName(QStringLiteral("dbaseLoginDialog"));
        setWindowFlags(Qt::Dialog | Qt::FramelessWindowHint);
        setModal(false);
        setWindowTitle(QStringLiteral("Login"));
        setAttribute(Qt::WA_DeleteOnClose, false);

        m_userLabel = new QLabel(QStringLiteral("Benutzer"), this);
        m_passwordLabel = new QLabel(QStringLiteral("Passwort"), this);
        m_groupLabel = new QLabel(QStringLiteral("Gruppe"), this);
        m_userEdit = new QLineEdit(this);
        m_passwordEdit = new QLineEdit(this);
        m_groupEdit = new QLineEdit(this);
        m_loginButton = new QPushButton(QStringLiteral("Login"), this);
        m_cancelButton = new QPushButton(QStringLiteral("Abbrechen"), this);

        m_userEdit->setObjectName(QStringLiteral("dbaseLoginUser"));
        m_passwordEdit->setObjectName(QStringLiteral("dbaseLoginPassword"));
        m_groupEdit->setObjectName(QStringLiteral("dbaseLoginGroup"));
        m_loginButton->setObjectName(QStringLiteral("dbaseLoginButton"));
        m_cancelButton->setObjectName(QStringLiteral("dbaseLoginCancel"));
        m_passwordEdit->setEchoMode(QLineEdit::Password);

        m_layout = new QGridLayout(this);
        m_layout->setSpacing(0);
        m_layout->addWidget(m_userLabel, 0, 0);
        m_layout->addWidget(m_userEdit, 0, 1, 1, 3);
        m_layout->addWidget(m_passwordLabel, 1, 0);
        m_layout->addWidget(m_passwordEdit, 1, 1, 1, 3);
        m_layout->addWidget(m_groupLabel, 2, 0);
        m_layout->addWidget(m_groupEdit, 2, 1, 1, 3);
        m_layout->addWidget(m_loginButton, 4, 2);
        m_layout->addWidget(m_cancelButton, 4, 3);
        m_layout->setColumnStretch(1, 1);

        setStyleSheet(QStringLiteral(
            "QDialog#dbaseLoginDialog { background-color: #909090; color: #000000; border: 0px; }"
            "QLabel { background-color: #909090; color: #000000; border: 0px; }"
            "QLineEdit { background-color: #008000; color: #ffffff; border: 1px solid #ffffff; padding: 0px; margin: 0px; }"
            "QLineEdit:focus { border: 1px solid #ffff00; }"
            "QPushButton { background-color: #909090; color: #000000; border: 1px solid #ffffff; padding: 2px 8px; }"
            "QPushButton:hover { background-color: #b0b0b0; }"
            "QPushButton:pressed { background-color: #707070; color: #ffffff; }"
        ));

        QObject::connect(m_loginButton, &QPushButton::clicked, [this]() { submitLogin(); });
        QObject::connect(m_cancelButton, &QPushButton::clicked, [this]() { reject(); });
        QObject::connect(m_passwordEdit, &QLineEdit::returnPressed, [this]() { submitLogin(); });
        QObject::connect(m_groupEdit, &QLineEdit::returnPressed, [this]() { submitLogin(); });

        // Das Login-Fenster ist ein top-level Dialog mit Parent. Bei einer
        // Bewegung/Neuberechnung des Hauptfensters wird seine gespeicherte
        // Zeichenrasterposition relativ zum Konsolen-Viewport wiederhergestellt.
        if (g_window)
            g_window->installEventFilter(this);
        if (g_console && g_console->viewport())
            g_console->viewport()->installEventFilter(this);

        updateForGrid(false);
    }

    void setSession(SessionNode *session)
    {
        m_session = session;
    }

    void updateForGrid(bool preservePosition)
    {
        const QSize cell = current_console_cell_size();
        m_cellWidth = qMax(1, cell.width());
        m_cellHeight = qMax(1, cell.height());

        QFont uiFont(choose_menu_font_family(), g_font_point_size);
        uiFont.setFixedPitch(true);
        uiFont.setStyleHint(QFont::TypeWriter);
        setFont(uiFont);
        const QList<QWidget *> widgets = findChildren<QWidget *>();
        for (QWidget *widget : widgets)
            widget->setFont(uiFont);

        m_borderFont = QFont(choose_popup_border_font_family(), g_font_point_size);
        m_borderFont.setFixedPitch(true);
        m_borderFont.setStyleHint(QFont::TypeWriter);

        const int side = m_cellWidth;
        const int top = m_cellHeight + 2;
        const int bottom = m_cellHeight;
        m_layout->setContentsMargins(side, top, side, bottom);
        m_layout->setHorizontalSpacing(m_cellWidth);
        m_layout->setVerticalSpacing(qMax(1, m_cellHeight / 3));

        setFixedSize(
            DBASE_LOGIN_DIALOG_COLUMNS * m_cellWidth,
            DBASE_LOGIN_DIALOG_ROWS * m_cellHeight
        );

        if (!preservePosition || !m_haveGridPosition)
            setInitialGridPosition();
        else
            repositionToStoredGrid();
        update();
    }

    void reject() override
    {
        set_login_session_state(false);
        m_passwordEdit->clear();
        QDialog::reject();
    }

protected:
    void closeEvent(QCloseEvent *event) override
    {
        set_login_session_state(false);
        QDialog::closeEvent(event);
    }

    void mousePressEvent(QMouseEvent *event) override
    {
        if (event->button() == Qt::LeftButton && event->pos().y() < m_cellHeight) {
            m_moving = true;
            m_pressGlobal = event->globalPos();
            ensureStoredGridPosition();
            m_startGridColumn = m_gridColumn;
            m_startGridRow = m_gridRow;
            update();
            event->accept();
            return;
        }
        QDialog::mousePressEvent(event);
    }

    void mouseMoveEvent(QMouseEvent *event) override
    {
        if (m_moving && (event->buttons() & Qt::LeftButton)) {
            const QPoint delta = event->globalPos() - m_pressGlobal;
            const int dxCells = qRound(static_cast<double>(delta.x()) / qMax(1, m_cellWidth));
            const int dyCells = qRound(static_cast<double>(delta.y()) / qMax(1, m_cellHeight));
            setStoredGridPosition(m_startGridColumn + dxCells, m_startGridRow + dyCells);
            repositionToStoredGrid();
            event->accept();
            return;
        }
        QDialog::mouseMoveEvent(event);
    }

    void mouseReleaseEvent(QMouseEvent *event) override
    {
        if (m_moving && event->button() == Qt::LeftButton) {
            m_moving = false;
            ensureStoredGridPosition();
            repositionToStoredGrid();
            update();
            event->accept();
            return;
        }
        QDialog::mouseReleaseEvent(event);
    }

    bool eventFilter(QObject *watched, QEvent *event) override
    {
        const bool geometryEvent =
            event->type() == QEvent::Move
            || event->type() == QEvent::Resize
            || event->type() == QEvent::Show
            || event->type() == QEvent::LayoutRequest;

        if (geometryEvent
            && (watched == g_window
                || (g_console && watched == g_console->viewport())))
        {
            // Erst nach Abschluss des Qt-Geometrieereignisses neu positionieren.
            // Dadurch bleibt derselbe Rasterplatz auch beim Verschieben des
            // Hauptfensters relativ zur Text-Edit-Komponente erhalten.
            QTimer::singleShot(0, this, [this]() {
                if (isVisible())
                    repositionToStoredGrid();
            });
        }

        return QDialog::eventFilter(watched, event);
    }

    void paintEvent(QPaintEvent *event) override
    {
        QDialog::paintEvent(event);
        QPainter painter(this);
        painter.setRenderHint(QPainter::TextAntialiasing, false);
        painter.setFont(m_borderFont);
        painter.setPen(m_moving ? QColor(255, 216, 0) : QColor(255, 255, 255));

        const QFontMetrics fm(m_borderFont);
        const int cw = qMax(1, m_cellWidth);
        const int ch = qMax(1, m_cellHeight);
        const int ascent = fm.ascent();
        const int rightX = qMax(0, width() - cw);
        const QString TL(QChar(0x2554));
        const QString TR(QChar(0x2557));
        const QString BL(QChar(0x255A));
        const QString BR(QChar(0x255D));
        const QString H(QChar(0x2550));
        const QString V(QChar(0x2551));

        painter.drawText(0, ascent, TL);
        for (int x = cw; x < width() - cw; x += cw)
            painter.drawText(x, ascent, H);
        painter.drawText(rightX, ascent, TR);

        const int bottomBaseline = height() - qMax(0, fm.descent());
        painter.drawText(0, bottomBaseline, BL);
        for (int x = cw; x < width() - cw; x += cw)
            painter.drawText(x, bottomBaseline, H);
        painter.drawText(rightX, bottomBaseline, BR);

        for (int y = ch; y < height() - ch; y += ch) {
            const int baseline = y + ascent;
            painter.drawText(0, baseline, V);
            painter.drawText(rightX, baseline, V);
        }

        // Custom-Titlebar: Titel unterbricht die obere Rahmenlinie.
        QFont titleFont(choose_menu_font_family(), g_font_point_size);
        titleFont.setFixedPitch(true);
        titleFont.setStyleHint(QFont::TypeWriter);
        painter.setFont(titleFont);
        const QString title = QStringLiteral(" Login ");
        const QFontMetrics tfm(titleFont);
        const int titleWidth = tfm.horizontalAdvance(title);
        const QRect titleRect(cw * 2, 0, titleWidth + 4, ch);
        painter.fillRect(titleRect, QColor(144, 144, 144));
        painter.setPen(m_moving ? QColor(255, 216, 0) : QColor(255, 255, 255));
        painter.drawText(titleRect.adjusted(2, 0, -2, 0), Qt::AlignVCenter | Qt::AlignLeft, title);
    }

private:
    int maxGridColumn() const
    {
        if (!g_console || !g_console->viewport())
            return 0;

        // Stage 28: der Dialog darf rechts fast vollstaendig aus dem
        // 80-Spalten-Clientbereich geschoben werden. Zwei Zeichenzellen
        // bleiben sichtbar, damit der linke Dialogrand als Greifrest
        // erhalten bleibt. Bei 80 Spalten ist die groesste Startspalte 78.
        const int viewportColumns = qMax(
            1,
            g_console->viewport()->width() / qMax(1, m_cellWidth)
        );
        const int usableColumns = qMin(DBASE_TEXT_COLUMNS, viewportColumns);
        return qMax(0, usableColumns - 2);
    }

    int maxGridRow() const
    {
        if (!g_console || !g_console->viewport())
            return 0;

        // Stage 28: die obere Dialogkante/Titlebar darf bis auf die letzte
        // Textzeile direkt vor der Statusleiste geschoben werden. Bei 25
        // Zeilen ist die groesste Startzeile deshalb 24. Der darunter
        // liegende Teil des Dialogs wird an der Viewport-Grenze abgeschnitten.
        const int viewportRows = qMax(
            1,
            g_console->viewport()->height() / qMax(1, m_cellHeight)
        );
        const int usableRows = qMin(DBASE_TEXT_ROWS, viewportRows);
        return qMax(0, usableRows - 1);
    }

    void setStoredGridPosition(int column, int row)
    {
        m_gridColumn = qBound(0, column, maxGridColumn());
        m_gridRow = qBound(0, row, maxGridRow());
        m_haveGridPosition = true;
    }

    void ensureStoredGridPosition()
    {
        if (m_haveGridPosition || !g_console || !g_console->viewport())
            return;
        const QPoint origin = g_console->viewport()->mapToGlobal(QPoint(0, 0));
        setStoredGridPosition(
            qRound(static_cast<double>(pos().x() - origin.x()) / qMax(1, m_cellWidth)),
            qRound(static_cast<double>(pos().y() - origin.y()) / qMax(1, m_cellHeight))
        );
    }

    void updateViewportClipMask()
    {
        if (!g_console || !g_console->viewport()) {
            clearMask();
            return;
        }

        // Der Login-Dialog bleibt ein top-level Qt-Dialog, wird aber optisch
        // exakt an der Text-Edit-Komponente abgeschnitten. Dadurch kann die
        // Titlebar auf Zeile 24 liegen, waehrend darunter nur noch der Teil
        // innerhalb des Konsolen-Viewports sichtbar bleibt. Rechts gilt das
        // Gleiche: bei Startspalte 78 bleiben genau zwei Zeichenzellen sichtbar.
        const QPoint viewportOrigin =
            g_console->viewport()->mapToGlobal(QPoint(0, 0));
        const QRect viewportGlobal(viewportOrigin, g_console->viewport()->size());
        const QRect dialogGlobal(pos(), size());
        const QRect visibleGlobal = dialogGlobal.intersected(viewportGlobal);

        if (visibleGlobal.isEmpty()) {
            setMask(QRegion());
            return;
        }

        const QRect visibleLocal(
            visibleGlobal.topLeft() - dialogGlobal.topLeft(),
            visibleGlobal.size()
        );
        if (visibleLocal == rect())
            clearMask();
        else
            setMask(QRegion(visibleLocal));
    }

    void repositionToStoredGrid()
    {
        if (!g_console || !g_console->viewport())
            return;
        ensureStoredGridPosition();
        setStoredGridPosition(m_gridColumn, m_gridRow);
        const QPoint origin = g_console->viewport()->mapToGlobal(QPoint(0, 0));
        move(
            origin.x() + m_gridColumn * m_cellWidth,
            origin.y() + m_gridRow * m_cellHeight
        );
        updateViewportClipMask();
    }

    void setInitialGridPosition()
    {
        if (!g_console || !g_console->viewport()) {
            m_haveGridPosition = false;
            clearMask();
            if (g_window)
                move(g_window->geometry().center() - QPoint(width() / 2, height() / 2));
            return;
        }

        // Die erweiterten Move-Grenzen duerfen die Anfangsposition nicht
        // nach rechts/unten verschieben. Initial bleibt der Dialog voll
        // sichtbar und mittig im 80x25-Clientbereich.
        const int initialColumn = qMax(
            0,
            (DBASE_TEXT_COLUMNS - DBASE_LOGIN_DIALOG_COLUMNS) / 2
        );
        const int initialRow = qMax(
            0,
            (DBASE_TEXT_ROWS - DBASE_LOGIN_DIALOG_ROWS) / 2
        );
        setStoredGridPosition(initialColumn, initialRow);
        repositionToStoredGrid();
    }

    void submitLogin()
    {
        if (!m_session)
            return;
        const QByteArray user = m_userEdit->text().toLocal8Bit();
        QByteArray password = m_passwordEdit->text().toLocal8Bit();
        const QByteArray group = m_groupEdit->text().toLocal8Bit();

        const int result = DBaseQtSessionLogin(
            m_session,
            user.constData(), user.size(),
            password.constData(), password.size(),
            group.constData(), group.size()
        );
        if (!password.isEmpty())
            password.fill('\0');

        if (result) {
            QDialog::accept();
            return;
        }
        m_passwordEdit->clear();
        m_passwordEdit->setFocus();
        m_passwordEdit->selectAll();
    }

    SessionNode *m_session = nullptr;
    QGridLayout *m_layout = nullptr;
    QLabel *m_userLabel = nullptr;
    QLabel *m_passwordLabel = nullptr;
    QLabel *m_groupLabel = nullptr;
    QLineEdit *m_userEdit = nullptr;
    QLineEdit *m_passwordEdit = nullptr;
    QLineEdit *m_groupEdit = nullptr;
    QPushButton *m_loginButton = nullptr;
    QPushButton *m_cancelButton = nullptr;
    QFont m_borderFont;
    bool m_moving = false;
    QPoint m_pressGlobal;
    bool m_haveGridPosition = false;
    int m_gridColumn = 0;
    int m_gridRow = 0;
    int m_startGridColumn = 0;
    int m_startGridRow = 0;
    int m_cellWidth = 8;
    int m_cellHeight = 16;
};

void cancel_login_dialog()
{
    if (g_login_dialog)
        g_login_dialog->reject();
}

void close_runtime_data_files()
{
    // Stage 29 legt den zentralen Dateiclose-Hook bereits fest. Die aktuelle
    // Qt-Runtime haelt noch keine persistenten DBF/MDX/NDX/DBT-Dateihandles;
    // der kommende Datenbank-Reader registriert/loest seine Handles hier.
    // menuFile selbst wird zur Compile-Zeit eingelesen und ist deshalb kein
    // offener Runtime-Dateideskriptor.
}

void request_runtime_shutdown()
{
    // Mehrfache Close-/Quit-Signale duerfen keinen zweiten Cleanup starten.
    g_shutdown_requested = true;
    if (g_shutdown_in_progress)
        return;

    g_shutdown_in_progress = true;

    // Zuerst einen eventuell blockierenden Login-Dialog beenden. Dadurch
    // verlaesst show_login_dialog() auch dann seine lokale QEventLoop, wenn
    // der Fokus gerade in Benutzer/Passwort/Gruppe steht.
    cancel_login_dialog();

    // Danach alle weiteren Top-Level-Dialoge/Popup-/Subfenster schliessen.
    // Das Hauptfenster selbst wird vom ausloesenden closeEvent geschlossen
    // und wird hier absichtlich ausgespart, um keine Close-Rekursion zu
    // erzeugen.
    const QWidgetList topLevels = QApplication::topLevelWidgets();
    for (QWidget *widget : topLevels) {
        if (!widget || widget == g_window)
            continue;
        widget->close();
    }

    // Falls bereits die normale QApplication::exec()-Schleife laeuft, wird
    // sie sofort beendet. Vor DBaseQtExec ist dieser Aufruf unkritisch; der
    // generierte Code prueft g_shutdown_requested und ueberspringt exec().
    if (g_app)
        g_app->quit();

    g_shutdown_in_progress = false;
}

void show_login_dialog(SessionNode *session)
{
    if (!session || !g_window || g_shutdown_requested)
        return;

    g_active_login_session = session;
    ensure_security_menu_items();
    set_login_session_state(false);

    if (g_login_dialog) {
        g_login_dialog->setSession(session);
        g_login_dialog->raise();
        g_login_dialog->activateWindow();
        return;
    }

    LoginDialog *dialog = new LoginDialog(session, g_window);
    g_login_dialog = dialog;
    dialog->show();
    dialog->raise();
    dialog->activateWindow();

    // Die Programmausfuehrung wartet, aber das Hauptfenster bleibt aktiv.
    // Dadurch koennen die Lupen den Dialog weiterhin mit dem 80x25-Raster
    // mitskalieren.
    QEventLoop waitLoop;
    QObject::connect(dialog, &QDialog::finished, &waitLoop, &QEventLoop::quit);
    if (g_app)
        QObject::connect(g_app, &QCoreApplication::aboutToQuit, &waitLoop, &QEventLoop::quit);
    waitLoop.exec();

    g_login_dialog = nullptr;
    delete dialog;
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
    restore_console_clear_pattern_after_grid_change();
    if (g_login_dialog)
        g_login_dialog->updateForGrid(true);
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

    // Sobald nach einem CLEAR SCREEN <Zeichen> normaler Konsolentext
    // geschrieben wird, ist das Dokument nicht mehr das reine Fuellmuster.
    // Ein spaeterer Lupen-Zoom darf dann nicht den neuen Text ueberschreiben.
    if (editor == g_console && g_console_clear_mode == ConsoleClearMode::CharacterPattern)
        g_console_clear_mode = ConsoleClearMode::None;

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

QString session_text_from_bytes(const char *text, int length)
{
    if (!text || length <= 0)
        return QString();
    return QString::fromLocal8Bit(text, length);
}

#ifdef _WIN32
bool resolve_windows_group_sid(
    const std::wstring &groupName,
    std::vector<unsigned char> *sidBuffer
)
{
    if (!sidBuffer || groupName.empty())
        return false;

    DWORD sidSize = 0;
    DWORD domainSize = 0;
    SID_NAME_USE sidUse = SidTypeUnknown;

    SetLastError(ERROR_SUCCESS);
    LookupAccountNameW(
        nullptr,
        groupName.c_str(),
        nullptr,
        &sidSize,
        nullptr,
        &domainSize,
        &sidUse
    );

    if (GetLastError() != ERROR_INSUFFICIENT_BUFFER || sidSize == 0)
        return false;

    sidBuffer->assign(sidSize, 0);
    std::vector<wchar_t> domainBuffer(domainSize ? domainSize : 1, L'\0');

    if (!LookupAccountNameW(
            nullptr,
            groupName.c_str(),
            reinterpret_cast<PSID>(sidBuffer->data()),
            &sidSize,
            domainBuffer.data(),
            &domainSize,
            &sidUse))
    {
        sidBuffer->clear();
        return false;
    }

    if (sidUse != SidTypeGroup &&
        sidUse != SidTypeAlias &&
        sidUse != SidTypeWellKnownGroup)
    {
        sidBuffer->clear();
        return false;
    }

    return IsValidSid(reinterpret_cast<PSID>(sidBuffer->data())) != FALSE;
}

bool split_windows_login_name(
    const std::wstring &input,
    std::wstring *username,
    std::wstring *domain,
    bool *domainIsNull
)
{
    if (!username || !domain || !domainIsNull || input.empty())
        return false;

    const std::wstring::size_type slash = input.find(L'\\');
    if (slash != std::wstring::npos) {
        if (slash == 0 || slash + 1 >= input.size())
            return false;
        *domain = input.substr(0, slash);
        *username = input.substr(slash + 1);
        *domainIsNull = false;
        return true;
    }

    *username = input;
    if (input.find(L'@') != std::wstring::npos) {
        domain->clear();
        *domainIsNull = true;
    } else {
        // Ein einfacher Name wird bewusst gegen die lokale Windows-
        // Kontodatenbank validiert. Fuer Domains DOMAIN\user oder UPN nutzen.
        *domain = L".";
        *domainIsNull = false;
    }
    return true;
}
#endif

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

    // Eine erneute Initialisierung im selben Host-Prozess beginnt mit einem
    // sauberen Shutdown-Zustand.
    g_shutdown_requested = false;
    g_shutdown_in_progress = false;

    g_window = new DBaseMainWindow();
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
    g_console->setHorizontalScrollBarPolicy(Qt::ScrollBarAlwaysOff);
    g_console->setVerticalScrollBarPolicy(Qt::ScrollBarAlwaysOff);
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
    if (!g_window || g_shutdown_requested)
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

    // CLEAR SCREEN ohne Ausdruck: bisheriges Verhalten. Die aktuelle
    // SET-COLOR-Hintergrundfarbe wird zur Flaechenfarbe der Konsole.
    g_console_clear_mode = ConsoleClearMode::Plain;
    g_console_clear_char_code = -1;
    select_console();
    g_console->clear();
    g_console_background = g_output_background;
    apply_console_appearance();
    reset_console_after_clear();
}

extern "C" D64QT5_API int DBaseQtClearScreenChar(double code)
{
    if (!g_console || !std::isfinite(code) || std::floor(code) != code || code < 0.0 || code > 255.0)
        return 0;

    const int byteCode = static_cast<int>(code);
    g_console_clear_mode = ConsoleClearMode::CharacterPattern;
    g_console_clear_char_code = byteCode;
    g_console_clear_char_foreground = g_output_foreground;
    g_console_clear_char_background = g_output_background;

    if (!render_console_character_pattern(
            byteCode,
            g_console_clear_char_foreground,
            g_console_clear_char_background))
    {
        g_console_clear_mode = ConsoleClearMode::None;
        g_console_clear_char_code = -1;
        return 0;
    }
    return 1;
}

extern "C" D64QT5_API int DBaseQtClearScreenColor(const char *name, int length)
{
    if (!g_console || !name || length <= 0)
        return 0;

    const QString requested = QString::fromLocal8Bit(name, length).trimmed();
    QColor color;
    if (!rgb_literal_color(requested, &color))
        return 0;

    g_console_clear_mode = ConsoleClearMode::Color;
    g_console_clear_char_code = -1;
    select_console();
    g_console->clear();
    g_console_background = color;
    apply_console_appearance();
    reset_console_after_clear();
    return 1;
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

extern "C" D64QT5_API void *DBaseQtSessionCreate(void *parent)
{
    if (g_shutdown_requested)
        return nullptr;

    SessionNode *session = new SessionNode();
    session->parent = parent;
    g_session_nodes.append(session);
    g_active_login_session = session;
    ensure_security_menu_items();
    set_login_session_state(false);
    show_login_dialog(session);
    return session;
}

extern "C" D64QT5_API int DBaseQtGetLoginSession(void)
{
    return g_login_session ? 1 : 0;
}

extern "C" D64QT5_API int DBaseQtSessionLogin(
    void *handle,
    const char *username,
    int usernameLength,
    const char *password,
    int passwordLength,
    const char *group,
    int groupLength
)
{
    SessionNode *session = static_cast<SessionNode *>(handle);
    if (!session || !username || usernameLength <= 0 ||
        !password || passwordLength < 0 || !group || groupLength <= 0)
    {
        return 0;
    }

    session->authenticated = false;
    session->username.clear();
    session->group.clear();
    set_login_session_state(false);

#ifndef _WIN32
    Q_UNUSED(username)
    Q_UNUSED(usernameLength)
    Q_UNUSED(password)
    Q_UNUSED(passwordLength)
    Q_UNUSED(group)
    Q_UNUSED(groupLength)
    return 0;
#else
    QString usernameText = session_text_from_bytes(username, usernameLength).trimmed();
    QString passwordText = session_text_from_bytes(password, passwordLength);
    QString groupText = session_text_from_bytes(group, groupLength).trimmed();

    if (usernameText.isEmpty() || groupText.isEmpty()) {
        passwordText.fill(QChar(0));
        return 0;
    }

    std::wstring loginInput = usernameText.toStdWString();
    std::wstring accountName;
    std::wstring domainName;
    bool domainIsNull = false;
    if (!split_windows_login_name(loginInput, &accountName, &domainName, &domainIsNull)) {
        passwordText.fill(QChar(0));
        return 0;
    }

    std::wstring passwordWide = passwordText.toStdWString();
    passwordText.fill(QChar(0));

    HANDLE token = nullptr;
    const BOOL loggedOn = LogonUserW(
        accountName.c_str(),
        domainIsNull ? nullptr : domainName.c_str(),
        passwordWide.c_str(),
        LOGON32_LOGON_NETWORK,
        LOGON32_PROVIDER_DEFAULT,
        &token
    );

    if (!passwordWide.empty())
        SecureZeroMemory(&passwordWide[0], passwordWide.size() * sizeof(wchar_t));

    if (!loggedOn || !token) {
        if (token)
            CloseHandle(token);
        return 0;
    }

    std::vector<unsigned char> groupSid;
    const std::wstring groupName = groupText.toStdWString();
    bool accepted = false;

    if (resolve_windows_group_sid(groupName, &groupSid)) {
        BOOL isMember = FALSE;
        if (CheckTokenMembership(
                token,
                reinterpret_cast<PSID>(groupSid.data()),
                &isMember))
        {
            accepted = isMember != FALSE;
        }
    }

    CloseHandle(token);

    if (!accepted)
        return 0;

    session->authenticated = true;
    session->username = usernameText;
    session->group = groupText;
    set_login_session_state(true);
    return 1;
#endif
}

extern "C" D64QT5_API void DBaseQtEnsureDefaultMenu(void)
{
    create_standard_menu();
    if (g_app)
        g_app->processEvents();
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
    if (g_active_login_session) {
        ensure_security_menu_items();
        update_menu_access_state();
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
    if (node && node->menu && normalized_menu_text(node->menu->title()).compare(QStringLiteral("Datei"), Qt::CaseInsensitive) == 0) {
        g_security_file_menu = node->menu;
        if (g_active_login_session)
            ensure_security_menu_items();
    }
    if (g_active_login_session)
        update_menu_access_state();
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
    if (g_shutdown_requested)
        return 0;
    return g_app->exec();
}

extern "C" D64QT5_API int DBaseQtShutdownRequested(void)
{
    return g_shutdown_requested ? 1 : 0;
}

extern "C" D64QT5_API void DBaseQtShutdown(void)
{
    // Auch ein expliziter Runtime-Shutdown benutzt denselben zentralen
    // Abbaupfad wie das Schliessen des Hauptfensters.
    request_runtime_shutdown();

    // Daten-Dateien werden vor dem Zerlegen der Objekt-/GUI-Strukturen
    // geschlossen. In Stage 29 ist die Liste noch leer; der DBF/MDX/NDX/DBT-
    // Reader kann denselben Hook ohne einen zweiten Shutdown-Pfad nutzen.
    close_runtime_data_files();

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
    g_login_dialog = nullptr;
    g_security_file_menu = nullptr;
    g_login_action = nullptr;
    g_quit_action = nullptr;
    g_active_login_session = nullptr;
    g_login_session = false;
    g_debug_visible = false;
    g_program_finished = false;
    g_default_menu_created = false;
    g_font_point_size = 10;
    g_font_pixel_adjust = 0;
    g_console_font_family.clear();
    g_console_background = QColor(0, 0, 0);
    g_console_border_color = QColor(255, 255, 255);
    g_output_foreground = QColor(169, 169, 169);
    g_output_background = QColor(0, 0, 0);
    g_console_clear_mode = ConsoleClearMode::None;
    g_console_clear_char_code = -1;
    g_console_clear_char_foreground = QColor(169, 169, 169);
    g_console_clear_char_background = QColor(0, 0, 0);
    for (MenuNode *node : g_menu_nodes)
        delete node;
    g_menu_nodes.clear();
    for (SessionNode *session : g_session_nodes)
        delete session;
    g_session_nodes.clear();

    if (g_owns_app) {
        delete g_app;
        g_app = nullptr;
        g_owns_app = false;
    }

    // Nach vollstaendigem Abbau darf ein Host die Bridge spaeter erneut
    // initialisieren. Bis hierhin bleibt g_shutdown_requested bewusst wahr,
    // damit kein nachlaufender Runtime-Aufruf neue UI erzeugt.
    g_shutdown_in_progress = false;
}
