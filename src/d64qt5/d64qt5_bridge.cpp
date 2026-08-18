#define D64QT5_BRIDGE_EXPORTS 1
#include "d64qt5_bridge.h"
#ifdef _WIN32
#  include <winsock2.h>
#  include <ws2tcpip.h>
#endif
#include "d64_workstation.h"

#include <QApplication>
#include <QAction>
#include <QByteArray>
#include <QColor>
#include <QCoreApplication>
#include <QDialog>
#include <QDir>
#include <QEventLoop>
#include <QEvent>
#include <QFileInfo>
#include <QFont>
#include <QFontDatabase>
#include <QFontInfo>
#include <QFontMetrics>
#include <QFrame>
#include <QHBoxLayout>
#include <QGridLayout>
#include <QIcon>
#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonObject>
#include <QJsonValue>
#include <QLineEdit>
#include <QLabel>
#include <QComboBox>
#include <QCheckBox>
#include <QHash>
#include <QKeyEvent>
#include <QKeySequence>
#include <QList>
#include <QMainWindow>
#include <QMenu>
#include <QMenuBar>
#include <QPainter>
#include <QPaintDevice>
#include <QPaintEvent>
#include <QMouseEvent>
#include <QPalette>
#include <QPixmap>
#include <QPlainTextEdit>
#include <QPointer>
#include <QProcess>
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
#include <QTextEdit>
#include <QWidget>
#include <QString>
#include <QStringList>
#include <QVariant>
#include <QVector>
#include <QUuid>

#include <cmath>
#include <string>
#include <vector>
#include <algorithm>
#include <cstdint>
#include <functional>

#ifdef _WIN32
#  define WIN32_LEAN_AND_MEAN
#  include <windows.h>
#  include <sql.h>
#  include <sqlext.h>
#endif

namespace {
QApplication *g_app = nullptr;
QList<QWidget *> g_wfm_forms;
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
QLabel *g_remote_listener_label = nullptr;

QToolButton *g_zoom_in = nullptr;
QToolButton *g_zoom_out = nullptr;

class LoginDialog;
class WarningDialog;
class BtxDialog;
class ServerDialog;
class RemoteCursorMarker;

// Stage 44A: ServerDialog wird weiter unten definiert, verwendet aber bereits
// im Konstruktor denselben Zoom-Button-Helper wie das Client-Hauptfenster.
// Die Deklaration muss daher vor der ServerDialog-Definition sichtbar sein.
QToolButton *make_zoom_button(bool plus, QWidget *parent);

LoginDialog *g_login_dialog = nullptr;
WarningDialog *g_warning_dialog = nullptr;
BtxDialog *g_btx_dialog = nullptr;
ServerDialog *g_server_dialog = nullptr;
RemoteCursorMarker *g_remote_cursor_marker = nullptr;
QMenu *g_security_file_menu = nullptr;
QAction *g_login_action = nullptr;
QAction *g_quit_action = nullptr;
struct SessionNode;
struct DatabaseNode;
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
// Stage 38: ein normales Close versteckt nur das Hauptfenster. Nur EXIT + JA
// darf den Prozess-/Desktop-Shutdown autorisieren.
bool g_exit_authorized = false;
bool g_exit_confirmation_open = false;
// Stage 41: Wenn der OWNER sein Hauptfenster nur versteckt, duerfen seine
// zugehoerigen top-level Dialoge nicht frei auf der Workstation stehenbleiben.
// Das zuletzt aktive Unterfenster wird fuer die Wiederherstellung ueber das
// DB-Icon schwach referenziert; bei zwischenzeitlichem Delete wird der Zeiger
// durch QPointer automatisch nullptr.
QPointer<QWidget> g_owner_hidden_active_window;
bool g_owner_restore_activated_window = false;
int g_font_point_size = 10;
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
constexpr int DBASE_WARNING_DIALOG_COLUMNS = 52;
constexpr int DBASE_WARNING_DIALOG_ROWS = 8;
constexpr int DBASE_BTX_COLUMNS = 80;
constexpr int DBASE_BTX_ROWS = 25;
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
    QString sessionId;
};

struct DatabaseNode {
    void *parent = nullptr;
    SessionNode *session = nullptr;
    QString path;
    QString databaseName;
    QString userName;
    QString passwordValue;
    QString alias;
    QString resolvedPath;
    bool active = false;
    bool odbc = false;
#ifdef _WIN32
    SQLHENV odbcEnv = SQL_NULL_HENV;
    SQLHDBC odbcDbc = SQL_NULL_HDBC;
#endif
};

QList<MenuNode *> g_menu_nodes;
QList<DatabaseNode *> g_database_nodes;

// Forward declarations fuer Stage-26-Raster-/CLEAR-SCREEN-Helfer.
void apply_console_appearance();
void select_console();
void enforce_console_80x25_grid();
QList<SessionNode *> g_session_nodes;

void update_menu_access_state();
void ensure_security_menu_items();
void show_login_dialog(SessionNode *session);
void set_login_session_state(bool value);
void cancel_login_dialog();
void close_runtime_application_windows();
void hide_owner_application_windows();
void restore_owner_application_windows();
void close_runtime_data_files();
void invalidate_runtime_sessions();
void request_runtime_shutdown();

void show_runtime_warning(const QString &message);
void show_btx_dialog();
void workstation_exit_requested();
void workstation_btx_requested();
void workstation_db_requested();
void workstation_server_requested();
void workstation_server_client_requested(int clientIndex);
void remote_client_start();
void remote_client_stop();
bool confirm_runtime_exit();
void launch_btx_executable();
int database_open_internal(DatabaseNode *database, bool showWarning);
void database_close_internal(DatabaseNode *database);
int database_commit_internal(DatabaseNode *database, bool showWarning);

class DBaseMainWindow final : public QMainWindow
{
protected:
#ifdef _WIN32
    bool nativeEvent(const QByteArray &eventType, void *message, long *result) override
    {
        MSG *msg = static_cast<MSG *>(message);
        if (msg && msg->message == WM_MOVING && msg->lParam) {
            RECT *rect = reinterpret_cast<RECT *>(msg->lParam);
            D64WorkstationConstrainMovingRect(rect);
            if (result)
                *result = TRUE;
            return true;
        }
        return QMainWindow::nativeEvent(eventType, message, result);
    }
#endif

    void changeEvent(QEvent *event) override
    {
        QMainWindow::changeEvent(event);
#ifdef _WIN32
        if (event && event->type() == QEvent::WindowStateChange && isMinimized()) {
            QPointer<DBaseMainWindow> self(this);
            QTimer::singleShot(0, [self]() {
                if (!self || !self->winId())
                    return;
                D64WorkstationPositionMinimizedWindow(
                    reinterpret_cast<HWND>(self->winId())
                );
            });
        }
#endif
    }

    void closeEvent(QCloseEvent *event) override
    {
        if (g_exit_authorized || g_shutdown_requested) {
            request_runtime_shutdown();
            QMainWindow::closeEvent(event);
            return;
        }

#ifdef _WIN32
        // Stage 40: Nur der OWNER ist das dauerhaft auf der Workstation
        // vorhandene DB-Hauptprogramm. Eine JOINED-Anwendung (z. B. BTX.exe)
        // muss beim Schliessen ihren kompletten Prozess-/Runtime-Kontext
        // abbauen. Ein blosses hide() wuerde Dialoge, Dateien, Sessions und
        // reservierten Speicher weiterleben lassen.
        if (D64WorkstationJoinedExisting()) {
            request_runtime_shutdown();
            QMainWindow::closeEvent(event);
            return;
        }
#endif

        // OWNER-Verhalten: Fenster-X, Alt+F4 und Datei->Beenden verstecken
        // die Anwendung, nicht die Workstation. Vor dem Hauptfenster werden
        // alle momentan sichtbaren top-level Dialoge derselben Anwendung
        // verborgen. So kann insbesondere eine fokussierte Login-Box nicht
        // frei auf dem Workstation-Desktop stehenbleiben.
        hide_owner_application_windows();
        hide();
        event->ignore();
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

// Legacy regression marker only; dialog/popup runtime no longer selects it:
// QStringLiteral("Terminal")
// Stage 37 compile fix: paint helpers are used by AsciiPopupMenu below,
// while their full definition remains with the common grid helpers later.
int grid_text_baseline(const QFontMetrics &fm, int cellHeight, int row);

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

        const int ch = qMax(1, m_cellHeight);
        const int topBaseline = grid_text_baseline(fm, ch, 0);
        const int descent = fm.descent();
        const int rightX = qMax(0, widthPx - m_cellWidth);

        // Obere Kante.
        painter.drawText(0, topBaseline, TL);
        for (int x = m_cellWidth; x < widthPx - m_cellWidth; x += m_cellWidth)
            painter.drawText(x, topBaseline, H);
        painter.drawText(rightX, topBaseline, TR);

        // Untere Kante.
        const int bottomBaseline = heightPx - qMax(0, descent);
        painter.drawText(0, bottomBaseline, BL);
        for (int x = m_cellWidth; x < widthPx - m_cellWidth; x += m_cellWidth)
            painter.drawText(x, bottomBaseline, H);
        painter.drawText(rightX, bottomBaseline, BR);

        // Linke und rechte Kante.
        for (int y = m_cellHeight; y < heightPx - m_cellHeight; y += m_cellHeight) {
            const int baseline = grid_text_baseline(fm, ch, y / ch);
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
    if (!value) {
        // Eine DATABASE darf nie aktiv bleiben, wenn ihre zugeordnete SESSION
        // nicht mehr authentifiziert ist. So bleibt die Zugriffskontrolle
        // auch bei erneutem/abgebrochenem Login konsistent.
        for (DatabaseNode *database : g_database_nodes) {
            if (database && database->active
                && (!database->session || !database->session->authenticated))
            {
                database_close_internal(database);
            }
        }
    }
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

// Legacy Stage-6 tertiary fallback marker; runtime preference is Consolas -> Courier New:
// QStringLiteral("Courier")

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
// Stage 37: ein einziges DPI-/Font-Raster fuer Konsole UND Dialograhmen.
// Die fruehere +/-1-Pixel-Feinkorrektur ist entfernt. Qt loest die gewaehlte
// Punktgroesse ueber den realen DPI-Wert des Konsolen-Viewports auf; genau
// diese QFont-Instanz und deren Metriken werden von allen Rasterdialogen
// wiederverwendet. Dadurch koennen Rahmen nicht mehr gegen die 80x25-Zellen
// auseinanderlaufen.
// ---------------------------------------------------------------------------
QFont make_console_grid_font()
{
    if (g_console_font_family.isEmpty())
        g_console_font_family = choose_console_font_family();

    QFont font(g_console_font_family, g_font_point_size);
    font.setStyleHint(QFont::Monospace);
    font.setFixedPitch(true);
    return font;
}

QFont current_console_grid_font()
{
    if (g_console)
        return g_console->font();
    return make_console_grid_font();
}

QFontMetrics console_font_metrics(const QFont &font)
{
    // Der Viewport ist der konkrete QPaintDevice und liefert damit den
    // tatsaechlichen logischen DPI-Wert des Bildschirms, auf dem die
    // 80x25-Flaeche gerendert wird.
    return QFontMetrics(
        font,
        g_console && g_console->viewport()
            ? static_cast<const QPaintDevice *>(g_console->viewport())
            : nullptr
    );
}

QSize console_grid_pixel_size(const QFont &font)
{
    const QFontMetrics fm = console_font_metrics(font);
    const int cellWidth = qMax(1, fm.horizontalAdvance(QLatin1Char('M')));
    const int lineHeight = qMax(1, fm.lineSpacing());

    return QSize(
        DBASE_TEXT_COLUMNS * cellWidth,
        DBASE_TEXT_ROWS * lineHeight
    );
}

QSize current_console_cell_size()
{
    const QFont font = current_console_grid_font();
    const QFontMetrics fm = console_font_metrics(font);
    return QSize(
        qMax(1, fm.horizontalAdvance(QLatin1Char('M'))),
        qMax(1, fm.lineSpacing())
    );
}

int grid_text_baseline(const QFontMetrics &fm, int cellHeight, int row)
{
    const int ch = qMax(1, cellHeight);
    const int textHeight = qMax(1, fm.height());
    const int verticalPad = qMax(0, (ch - textHeight) / 2);
    return row * ch + verticalPad + fm.ascent();
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

        const QFont uiFont = current_console_grid_font();
        setFont(uiFont);
        const QList<QWidget *> widgets = findChildren<QWidget *>();
        for (QWidget *widget : widgets)
            widget->setFont(uiFont);

        // Rahmen- und UI-Font sind dieselbe vom Konsolen-Viewport bereits
        // DPI-aufgeloeste Fontinstanz. Keine separaten Pixelaufschlaege.
        m_borderFont = uiFont;

        m_layout->setContentsMargins(
            m_cellWidth, m_cellHeight, m_cellWidth, m_cellHeight
        );
        m_layout->setHorizontalSpacing(m_cellWidth);
        m_layout->setVerticalSpacing(0);
        for (QLineEdit *edit : {m_userEdit, m_passwordEdit, m_groupEdit})
            edit->setMinimumHeight(m_cellHeight);
        m_loginButton->setMinimumHeight(m_cellHeight);
        m_cancelButton->setMinimumHeight(m_cellHeight);

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
            setProperty("dbaseRemoteMoving", true);
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
            setProperty("dbaseRemoteMoving", false);
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

        const QFontMetrics fm(m_borderFont, this);
        const int cw = qMax(1, m_cellWidth);
        const int ch = qMax(1, m_cellHeight);
        const int topBaseline = grid_text_baseline(fm, ch, 0);
        const int rightX = qMax(0, width() - cw);
        const QString TL(QChar(0x2554));
        const QString TR(QChar(0x2557));
        const QString BL(QChar(0x255A));
        const QString BR(QChar(0x255D));
        const QString H(QChar(0x2550));
        const QString V(QChar(0x2551));

        painter.drawText(0, topBaseline, TL);
        for (int x = cw; x < width() - cw; x += cw)
            painter.drawText(x, topBaseline, H);
        painter.drawText(rightX, topBaseline, TR);

        const int bottomBaseline = grid_text_baseline(
            fm, ch, DBASE_LOGIN_DIALOG_ROWS - 1
        );
        painter.drawText(0, bottomBaseline, BL);
        for (int x = cw; x < width() - cw; x += cw)
            painter.drawText(x, bottomBaseline, H);
        painter.drawText(rightX, bottomBaseline, BR);

        for (int y = ch; y < height() - ch; y += ch) {
            const int baseline = grid_text_baseline(fm, ch, y / ch);
            painter.drawText(0, baseline, V);
            painter.drawText(rightX, baseline, V);
        }

        // Custom-Titlebar: Titel unterbricht die obere Rahmenlinie.
        painter.setFont(m_borderFont);
        const QString title = QStringLiteral(" Login ");
        const QRect titleRect(cw * 2, 0, title.size() * cw, ch);
        painter.fillRect(titleRect, QColor(144, 144, 144));
        painter.setPen(m_moving ? QColor(255, 216, 0) : QColor(255, 255, 255));
        painter.drawText(titleRect, Qt::AlignCenter, title);
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

        // Stage 33: Ein fehlgeschlagener Login beendet den Login-Dialog.
        // Danach erscheint die nicht-modale Warnbox im 80x25-Viewport,
        // sodass insbesondere die Lupen weiter erreichbar bleiben.
        m_passwordEdit->clear();
        QDialog::reject();
        show_runtime_warning(QStringLiteral("Anmeldung fehlgeschlagen."));
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

class WarningDialog final : public QDialog
{
public:
    explicit WarningDialog(const QString &message, QWidget *parent = nullptr)
        : QDialog(parent)
    {
        setObjectName(QStringLiteral("dbaseWarningDialog"));
        setWindowFlags(Qt::Dialog | Qt::FramelessWindowHint);
        // Stage 33: Warnungen duerfen die Hauptanwendung nicht mehr sperren.
        // Insbesondere bleiben die beiden Lupen waehrend der Anzeige aktiv.
        setWindowModality(Qt::NonModal);
        setModal(false);
        setWindowTitle(QStringLiteral("Warnung"));
        setAttribute(Qt::WA_DeleteOnClose, false);

        m_message = new QLabel(message, this);
        m_message->setWordWrap(true);
        m_message->setAlignment(Qt::AlignLeft | Qt::AlignVCenter);
        m_ok = new QPushButton(QStringLiteral("OK"), this);
        m_ok->setDefault(true);
        m_ok->setAutoDefault(true);

        m_layout = new QGridLayout(this);
        m_layout->setSpacing(0);
        m_layout->addWidget(m_message, 1, 1, 3, 6);
        m_layout->addWidget(m_ok, 5, 5, 1, 2);

        setStyleSheet(QStringLiteral(
            "QDialog#dbaseWarningDialog { background-color: #ff0000; color: #000000; border: 0px; }"
            "QLabel { background-color: #ff0000; color: #000000; border: 0px; }"
            "QPushButton { background-color: #909090; color: #000000; border: 1px solid #ffffff; padding: 2px 8px; }"
            "QPushButton:hover { background-color: #b0b0b0; }"
            "QPushButton:pressed { background-color: #707070; color: #ffffff; }"
        ));

        QObject::connect(m_ok, &QPushButton::clicked, this, &QDialog::accept);
        if (g_window)
            g_window->installEventFilter(this);
        if (g_console && g_console->viewport())
            g_console->viewport()->installEventFilter(this);
        updateForGrid(false);
    }

    void setMessage(const QString &message)
    {
        if (m_message)
            m_message->setText(message);
    }

    void updateForGrid(bool preservePosition = true)
    {
        const QSize cell = current_console_cell_size();
        m_cellWidth = qMax(1, cell.width());
        m_cellHeight = qMax(1, cell.height());

        const QFont uiFont = current_console_grid_font();
        setFont(uiFont);
        m_message->setFont(uiFont);
        m_ok->setFont(uiFont);
        m_ok->setMinimumHeight(m_cellHeight);

        m_borderFont = uiFont;

        m_layout->setContentsMargins(m_cellWidth, m_cellHeight, m_cellWidth, m_cellHeight);
        m_layout->setHorizontalSpacing(m_cellWidth);
        m_layout->setVerticalSpacing(0);
        setFixedSize(
            DBASE_WARNING_DIALOG_COLUMNS * m_cellWidth,
            DBASE_WARNING_DIALOG_ROWS * m_cellHeight
        );

        if (!preservePosition || !m_haveGridPosition)
            setInitialGridPosition();
        else
            repositionToStoredGrid();
        update();
    }

protected:
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
            QTimer::singleShot(0, this, [this]() {
                if (isVisible())
                    updateForGrid(true);
            });
        }
        return QDialog::eventFilter(watched, event);
    }

    void mousePressEvent(QMouseEvent *event) override
    {
        if (event->button() == Qt::LeftButton && event->pos().y() < m_cellHeight) {
            m_moving = true;
            setProperty("dbaseRemoteMoving", true);
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
            setProperty("dbaseRemoteMoving", false);
            ensureStoredGridPosition();
            repositionToStoredGrid();
            update();
            event->accept();
            return;
        }
        QDialog::mouseReleaseEvent(event);
    }

    void paintEvent(QPaintEvent *event) override
    {
        QDialog::paintEvent(event);
        QPainter painter(this);
        painter.setRenderHint(QPainter::TextAntialiasing, false);
        painter.setFont(m_borderFont);
        painter.setPen(m_moving ? QColor(255, 216, 0) : QColor(255, 255, 255));

        const QFontMetrics fm(m_borderFont, this);
        const int cw = qMax(1, m_cellWidth);
        const int ch = qMax(1, m_cellHeight);
        const int topBaseline = grid_text_baseline(fm, ch, 0);
        const int rightX = qMax(0, width() - cw);
        const QString TL(QChar(0x2554));
        const QString TR(QChar(0x2557));
        const QString BL(QChar(0x255A));
        const QString BR(QChar(0x255D));
        const QString H(QChar(0x2550));
        const QString V(QChar(0x2551));

        painter.drawText(0, topBaseline, TL);
        for (int x = cw; x < width() - cw; x += cw)
            painter.drawText(x, topBaseline, H);
        painter.drawText(rightX, topBaseline, TR);

        const int bottomBaseline = grid_text_baseline(
            fm, ch, DBASE_WARNING_DIALOG_ROWS - 1
        );
        painter.drawText(0, bottomBaseline, BL);
        for (int x = cw; x < width() - cw; x += cw)
            painter.drawText(x, bottomBaseline, H);
        painter.drawText(rightX, bottomBaseline, BR);

        for (int y = ch; y < height() - ch; y += ch) {
            const int baseline = grid_text_baseline(fm, ch, y / ch);
            painter.drawText(0, baseline, V);
            painter.drawText(rightX, baseline, V);
        }

        painter.setFont(m_borderFont);
        const QString title = QStringLiteral(" Warnung ");
        const QRect titleRect(cw * 2, 0, title.size() * cw, ch);
        painter.fillRect(titleRect, QColor(255, 0, 0));
        painter.setPen(m_moving ? QColor(255, 216, 0) : QColor(255, 255, 255));
        painter.drawText(titleRect, Qt::AlignCenter, title);
    }

private:
    int maxGridColumn() const
    {
        if (!g_console || !g_console->viewport())
            return 0;
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
        const int initialColumn = qMax(
            0,
            (DBASE_TEXT_COLUMNS - DBASE_WARNING_DIALOG_COLUMNS) / 2
        );
        const int initialRow = qMax(
            0,
            (DBASE_TEXT_ROWS - DBASE_WARNING_DIALOG_ROWS) / 2
        );
        setStoredGridPosition(initialColumn, initialRow);
        repositionToStoredGrid();
    }

    QGridLayout *m_layout = nullptr;
    QLabel *m_message = nullptr;
    QPushButton *m_ok = nullptr;
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

class BtxDialog final : public QDialog
{
public:
    explicit BtxDialog(QWidget *parent = nullptr)
        : QDialog(parent)
    {
        setObjectName(QStringLiteral("dbaseBtxDialog"));
        setWindowFlags(Qt::Dialog | Qt::FramelessWindowHint);
        setWindowModality(Qt::NonModal);
        setModal(false);
        setWindowTitle(QStringLiteral("BTX"));
        setAttribute(Qt::WA_DeleteOnClose, false);

        m_screen = new QPlainTextEdit(this);
        m_screen->setObjectName(QStringLiteral("dbaseBtxScreen"));
        m_screen->setReadOnly(true);
        m_screen->setFrameShape(QFrame::NoFrame);
        m_screen->setContentsMargins(0, 0, 0, 0);
        m_screen->document()->setDocumentMargin(0.0);
        m_screen->setLineWrapMode(QPlainTextEdit::NoWrap);
        m_screen->setHorizontalScrollBarPolicy(Qt::ScrollBarAlwaysOff);
        m_screen->setVerticalScrollBarPolicy(Qt::ScrollBarAlwaysOff);
        m_screen->setStyleSheet(QStringLiteral(
            "QPlainTextEdit#dbaseBtxScreen {"
            " background-color: #000000;"
            " color: #c0c0c0;"
            " border: 0px;"
            " padding: 0px;"
            " margin: 0px;"
            "}"
        ));
        m_screen->setPlainText(QStringLiteral("BTX"));

        if (g_window)
            g_window->installEventFilter(this);
        if (g_console && g_console->viewport())
            g_console->viewport()->installEventFilter(this);

        updateForGrid(false);
    }

    void updateForGrid(bool preservePosition = true)
    {
        const QSize cell = current_console_cell_size();
        m_cellWidth = qMax(1, cell.width());
        m_cellHeight = qMax(1, cell.height());
        m_borderFont = current_console_grid_font();
        setFont(m_borderFont);
        m_screen->setFont(m_borderFont);

        // Die eigentliche BTX-Flaeche ist exakt 80x25 Zellen gross. Der
        // Rahmen liegt als je eine zusaetzliche Rasterzelle aussen herum.
        const int contentWidth = DBASE_BTX_COLUMNS * m_cellWidth;
        const int contentHeight = DBASE_BTX_ROWS * m_cellHeight;
        setFixedSize(
            (DBASE_BTX_COLUMNS + 2) * m_cellWidth,
            (DBASE_BTX_ROWS + 2) * m_cellHeight
        );
        m_screen->setGeometry(
            m_cellWidth,
            m_cellHeight,
            contentWidth,
            contentHeight
        );

        if (!preservePosition || !m_haveGridPosition)
            setInitialGridPosition();
        else
            repositionToStoredGrid();
        update();
    }

protected:
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
            QTimer::singleShot(0, this, [this]() {
                if (isVisible())
                    updateForGrid(true);
            });
        }
        return QDialog::eventFilter(watched, event);
    }

    void mousePressEvent(QMouseEvent *event) override
    {
        if (event->button() == Qt::LeftButton && event->pos().y() < m_cellHeight) {
            m_moving = true;
            setProperty("dbaseRemoteMoving", true);
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
            setProperty("dbaseRemoteMoving", false);
            repositionToStoredGrid();
            update();
            event->accept();
            return;
        }
        QDialog::mouseReleaseEvent(event);
    }

    void paintEvent(QPaintEvent *event) override
    {
        QDialog::paintEvent(event);
        QPainter painter(this);
        painter.setRenderHint(QPainter::TextAntialiasing, false);
        painter.setFont(m_borderFont);
        painter.setPen(m_moving ? QColor(255, 216, 0) : QColor(255, 255, 255));

        const QFontMetrics fm(m_borderFont, this);
        const int cw = qMax(1, m_cellWidth);
        const int ch = qMax(1, m_cellHeight);
        const int totalColumns = DBASE_BTX_COLUMNS + 2;
        const int totalRows = DBASE_BTX_ROWS + 2;
        const int rightX = (totalColumns - 1) * cw;
        const int topBaseline = grid_text_baseline(fm, ch, 0);
        const int bottomBaseline = grid_text_baseline(fm, ch, totalRows - 1);
        const QString TL(QChar(0x2554));
        const QString TR(QChar(0x2557));
        const QString BL(QChar(0x255A));
        const QString BR(QChar(0x255D));
        const QString H(QChar(0x2550));
        const QString V(QChar(0x2551));

        painter.drawText(0, topBaseline, TL);
        for (int column = 1; column < totalColumns - 1; ++column)
            painter.drawText(column * cw, topBaseline, H);
        painter.drawText(rightX, topBaseline, TR);

        painter.drawText(0, bottomBaseline, BL);
        for (int column = 1; column < totalColumns - 1; ++column)
            painter.drawText(column * cw, bottomBaseline, H);
        painter.drawText(rightX, bottomBaseline, BR);

        for (int row = 1; row < totalRows - 1; ++row) {
            const int baseline = grid_text_baseline(fm, ch, row);
            painter.drawText(0, baseline, V);
            painter.drawText(rightX, baseline, V);
        }

        const QString title = QStringLiteral(" BTX ");
        const QRect titleRect(cw * 2, 0, title.size() * cw, ch);
        painter.fillRect(titleRect, QColor(0, 0, 0));
        painter.setPen(m_moving ? QColor(255, 216, 0) : QColor(255, 255, 255));
        painter.drawText(titleRect, Qt::AlignCenter, title);
    }

private:
    int maxGridColumn() const
    {
        if (!g_console || !g_console->viewport())
            return 0;
        const int columns = qMax(
            1,
            g_console->viewport()->width() / qMax(1, m_cellWidth)
        );
        return qMax(0, qMin(DBASE_TEXT_COLUMNS, columns) - 2);
    }

    int maxGridRow() const
    {
        if (!g_console || !g_console->viewport())
            return 0;
        const int rows = qMax(
            1,
            g_console->viewport()->height() / qMax(1, m_cellHeight)
        );
        return qMax(0, qMin(DBASE_TEXT_ROWS, rows) - 1);
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
        const QPoint contentOrigin = pos() + QPoint(m_cellWidth, m_cellHeight);
        setStoredGridPosition(
            qRound(static_cast<double>(contentOrigin.x() - origin.x()) / qMax(1, m_cellWidth)),
            qRound(static_cast<double>(contentOrigin.y() - origin.y()) / qMax(1, m_cellHeight))
        );
    }

    void updateViewportClipMask()
    {
        if (!g_console || !g_console->viewport()) {
            clearMask();
            return;
        }
        const QPoint origin = g_console->viewport()->mapToGlobal(QPoint(0, 0));
        QRect allowed(origin, g_console->viewport()->size());
        allowed.adjust(-m_cellWidth, -m_cellHeight, m_cellWidth, m_cellHeight);
        const QRect dialogGlobal(pos(), size());
        const QRect visibleGlobal = dialogGlobal.intersected(allowed);
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
        // m_gridColumn/m_gridRow bezeichnen die obere linke Zelle der echten
        // 80x25-BTX-Flaeche. Der Rahmen liegt genau eine Zelle davor.
        move(
            origin.x() + m_gridColumn * m_cellWidth - m_cellWidth,
            origin.y() + m_gridRow * m_cellHeight - m_cellHeight
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
        setStoredGridPosition(0, 0);
        repositionToStoredGrid();
    }

    QPlainTextEdit *m_screen = nullptr;
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

#ifdef _WIN32

// ---------------------------------------------------------------------------
// Stage 43: zeichenorientierte IPv4-Basis; Stage 44 erweitert den CS-Kanal.
// Stage 45: vollstaendige logische UI-Spiegelung ausschliesslich als Char-Stream.
// Stage 46: identische Dialog-Chrome auf Client/Server sowie rasterfeste,
// koaleszierte Mausuebertragung ohne Move-Rueckstau.
// Stage 47: deterministisches Terminal-RPC-Aufbauprotokoll nach Turbo-Vision-
// Prinzip. Client und Server interpretieren dieselbe kompakte Komponenten-
// Beschreibungssprache; Aufbau: TApplication -> TBackground -> TMainMenu ->
// TStatusBar -> TFrame -> TView -> Controls.
// Keine Bildschirm-Pixel und keine Pixelkoordinaten im Snapshot: Arbeitsraster,
// kompletter Menuebaum, Statusfelder, Dialog-/Popup-Zeilen und Zellpositionen.
// Jeder TCP-Kanal beginnt mit einem D64CS-Anwendungsheader (Frame 'H') mit
// Protokoll-/Anwendungsversion, ServerSoftware, Client-/Server-IP,
// ConnectionID und – sobald SESSION benutzt wird – SessionID.
// ---------------------------------------------------------------------------

// Legacy Stage-45 regression marker: constexpr int D64_REMOTE_PROTOCOL_VERSION = 3;
// Legacy Stage-46 regression marker: constexpr int D64_REMOTE_PROTOCOL_VERSION = 4;
constexpr int D64_REMOTE_PROTOCOL_VERSION = 5;
constexpr int D64_TERMINAL_RPC_VERSION = 1;
constexpr int D64_REMOTE_DEFAULT_COLUMNS = 80;
constexpr int D64_REMOTE_DEFAULT_ROWS = 25;

struct RemoteSocketState {
    SOCKET socket = INVALID_SOCKET;
    QByteArray input;
    QByteArray output;
    bool connecting = false;
    bool connected = false;
    bool headerSent = false;
    bool handshakeComplete = false;
    QString localRole;
    QString localConnectionId;
    QString localSessionId;
    QString peerRole;
    QString peerConnectionId;
    QString peerSessionId;
    QString peerSoftware;
    QString peerApplicationVersion;
    QString localAddress;
    QString remoteAddress;
    QString peerAddress;
    quint16 peerPort = 0;
    QJsonObject snapshot;
    QJsonObject peerMouse;
    QByteArray terminalTemplate;
    QByteArray lastTerminalTemplateSent;
    QByteArray pendingMousePayload;
    char pendingMouseType = 0;
    quint64 lastPeerMouseSequence = 0;
};

SOCKET g_remote_listener = INVALID_SOCKET;
QVector<RemoteSocketState *> g_remote_client_peers;
QTimer *g_remote_client_timer = nullptr;
quint16 g_remote_listener_port = 0;
QString g_remote_listener_address;
QByteArray g_remote_last_snapshot;
bool g_winsock_started = false;
QString g_remote_application_connection_id;
bool g_remote_dispatching_mouse = false;
quint64 g_remote_local_mouse_sequence = 0;
QPointer<QWidget> g_remote_mouse_capture_widget;
class RemoteClientEventFilter;
RemoteClientEventFilter *g_remote_client_event_filter = nullptr;

// ---------------------------------------------------------------------------
// Stage 47 - D64TERM/1
// Kompakte terminalorientierte Beschreibungssprache. Keine Pixelwerte werden
// uebertragen; Geometrie ist immer Spalte/Zeile/Breite/Hoehe in Rasterzellen.
// Die Typnummer ist zwischen Client und Server fest. Die ComponentID bezeichnet
// die konkrete Instanz innerhalb einer laufenden TApplication.
//
// Beispiel:
// T2045_00000105_00000100_012_004_024_001_FFFFFF_008000_NAME%3DUser
// ---------------------------------------------------------------------------
enum TerminalTypeCode {
    TerminalTApplication = 2000,
    TerminalTBackground  = 2001,
    TerminalTMainMenu    = 2002,
    TerminalTStatusBar   = 2003,
    TerminalTFrame       = 2010,
    TerminalTView        = 2011,
    TerminalTButton      = 2040,
    TerminalTLineEdit    = 2045,
    TerminalTCheckBox    = 2046,
    TerminalTComboBox    = 2047,
    TerminalTLabel       = 2048,
    TerminalTMenuItem    = 2050
};

struct TerminalComponentRecord {
    int typeCode = 0;
    quint32 componentId = 0;
    quint32 parentId = 0;
    int column = 0;
    int row = 0;
    int columns = 1;
    int rows = 1;
    QColor foreground = QColor(255, 255, 255);
    QColor background = QColor(0, 0, 0);
    QString payload;
};

class TTerminalComponent
{
public:
    explicit TTerminalComponent(int typeCode) { record.typeCode = typeCode; }
    virtual ~TTerminalComponent() = default;
    TerminalComponentRecord record;
};
class TApplication final : public TTerminalComponent { public: TApplication() : TTerminalComponent(TerminalTApplication) {} };
class TBackground final : public TTerminalComponent { public: TBackground() : TTerminalComponent(TerminalTBackground) {} };
class TMainMenu final : public TTerminalComponent { public: TMainMenu() : TTerminalComponent(TerminalTMainMenu) {} };
class TStatusBar final : public TTerminalComponent { public: TStatusBar() : TTerminalComponent(TerminalTStatusBar) {} };
class TFrame final : public TTerminalComponent { public: TFrame() : TTerminalComponent(TerminalTFrame) {} };
class TView final : public TTerminalComponent { public: TView() : TTerminalComponent(TerminalTView) {} };
class TButton final : public TTerminalComponent { public: TButton() : TTerminalComponent(TerminalTButton) {} };
class TLineEdit final : public TTerminalComponent { public: TLineEdit() : TTerminalComponent(TerminalTLineEdit) {} };
class TCheckBox final : public TTerminalComponent { public: TCheckBox() : TTerminalComponent(TerminalTCheckBox) {} };
class TComboBox final : public TTerminalComponent { public: TComboBox() : TTerminalComponent(TerminalTComboBox) {} };
class TLabel final : public TTerminalComponent { public: TLabel() : TTerminalComponent(TerminalTLabel) {} };
class TMenuItem final : public TTerminalComponent { public: TMenuItem() : TTerminalComponent(TerminalTMenuItem) {} };

QHash<QObject *, quint32> g_terminal_object_ids;
QHash<quint32, QPointer<QObject>> g_terminal_id_objects;
quint32 g_terminal_next_component_id = 100;
QByteArray g_terminal_last_program;
bool g_terminal_template_dirty = true;

QString remote_new_id()
{
    QString value = QUuid::createUuid().toString();
    value.remove(QLatin1Char('{'));
    value.remove(QLatin1Char('}'));
    return value;
}

QString remote_application_version()
{
    QString version = QCoreApplication::applicationVersion().trimmed();
    if (version.isEmpty())
        version = QStringLiteral("Stage47");
    return version;
}

QString remote_server_software()
{
    return QStringLiteral("D64 Workstation Server/Stage47");
}

QString remote_client_software()
{
    QString name = QCoreApplication::applicationName().trimmed();
    if (name.isEmpty())
        name = QFileInfo(QCoreApplication::applicationFilePath()).fileName();
    if (name.isEmpty())
        name = QStringLiteral("d64qt5 Client");
    return name;
}

QString remote_current_session_id()
{
    if (g_active_login_session && !g_active_login_session->sessionId.isEmpty())
        return g_active_login_session->sessionId;
    for (SessionNode *session : g_session_nodes) {
        if (session && !session->sessionId.isEmpty())
            return session->sessionId;
    }
    return QString();
}

bool remote_ensure_winsock()
{
    if (g_winsock_started)
        return true;
    WSADATA data;
    ZeroMemory(&data, sizeof(data));
    if (::WSAStartup(MAKEWORD(2, 2), &data) != 0)
        return false;
    g_winsock_started = true;
    return true;
}

void remote_close_socket(SOCKET &socketValue)
{
    if (socketValue != INVALID_SOCKET) {
        ::shutdown(socketValue, SD_BOTH);
        ::closesocket(socketValue);
        socketValue = INVALID_SOCKET;
    }
}

bool remote_set_nonblocking(SOCKET socketValue)
{
    u_long mode = 1;
    return ::ioctlsocket(socketValue, FIONBIO, &mode) == 0;
}

QString remote_sockaddr_text(const sockaddr_in &address)
{
    char text[INET_ADDRSTRLEN] = {0};
    if (!::inet_ntop(AF_INET, &address.sin_addr, text, sizeof(text)))
        return QString();
    return QString::fromLatin1(text);
}

QString remote_socket_local_ip(SOCKET socketValue)
{
    sockaddr_in address;
    int length = sizeof(address);
    ZeroMemory(&address, sizeof(address));
    if (::getsockname(socketValue, reinterpret_cast<sockaddr *>(&address), &length) != 0)
        return QString();
    return remote_sockaddr_text(address);
}

QString remote_socket_peer_ip(SOCKET socketValue)
{
    sockaddr_in address;
    int length = sizeof(address);
    ZeroMemory(&address, sizeof(address));
    if (::getpeername(socketValue, reinterpret_cast<sockaddr *>(&address), &length) != 0)
        return QString();
    return remote_sockaddr_text(address);
}

void remote_queue_frame(RemoteSocketState *state, char type, const QByteArray &payload)
{
    if (!state || state->socket == INVALID_SOCKET)
        return;
    const quint32 length = static_cast<quint32>(payload.size() + 1);
    char header[4];
    header[0] = static_cast<char>(length & 0xff);
    header[1] = static_cast<char>((length >> 8) & 0xff);
    header[2] = static_cast<char>((length >> 16) & 0xff);
    header[3] = static_cast<char>((length >> 24) & 0xff);
    state->output.append(header, 4);
    state->output.append(type);
    state->output.append(payload);
}

// Stage 46: MouseMove ist ein absoluter Zellzustand, kein Delta. Wenn in einem
// Netzwerk-Tick mehrere Move-Ereignisse entstehen, muss deshalb nur die neueste
// Position uebertragen werden. Press/Release/Double bleiben strikt geordnet.
void remote_queue_mouse_payload(
    RemoteSocketState *state,
    char frameType,
    const QByteArray &payload,
    bool coalesceMove
)
{
    if (!state || state->socket == INVALID_SOCKET)
        return;

    if (coalesceMove) {
        state->pendingMouseType = frameType;
        state->pendingMousePayload = payload;
        return;
    }

    if (!state->pendingMousePayload.isEmpty()) {
        remote_queue_frame(
            state,
            state->pendingMouseType ? state->pendingMouseType : frameType,
            state->pendingMousePayload
        );
        state->pendingMousePayload.clear();
        state->pendingMouseType = 0;
    }
    remote_queue_frame(state, frameType, payload);
}

void remote_flush_pending_mouse(RemoteSocketState *state)
{
    if (!state || state->pendingMousePayload.isEmpty())
        return;
    remote_queue_frame(
        state,
        state->pendingMouseType ? state->pendingMouseType : 'M',
        state->pendingMousePayload
    );
    state->pendingMousePayload.clear();
    state->pendingMouseType = 0;
}

bool remote_flush(RemoteSocketState *state)
{
    if (!state || state->socket == INVALID_SOCKET)
        return false;
    while (!state->output.isEmpty()) {
        const int sent = ::send(
            state->socket,
            state->output.constData(),
            state->output.size(),
            0
        );
        if (sent > 0) {
            state->output.remove(0, sent);
            continue;
        }
        if (sent == SOCKET_ERROR) {
            const int error = ::WSAGetLastError();
            if (error == WSAEWOULDBLOCK)
                return true;
        }
        return false;
    }
    return true;
}

bool remote_receive(RemoteSocketState *state)
{
    if (!state || state->socket == INVALID_SOCKET)
        return false;
    char buffer[8192];
    for (;;) {
        const int received = ::recv(state->socket, buffer, sizeof(buffer), 0);
        if (received > 0) {
            state->input.append(buffer, received);
            continue;
        }
        if (received == 0)
            return false;
        const int error = ::WSAGetLastError();
        if (error == WSAEWOULDBLOCK)
            return true;
        return false;
    }
}

bool remote_take_frame(RemoteSocketState *state, char *type, QByteArray *payload)
{
    if (!state || state->input.size() < 4 || !type || !payload)
        return false;
    const unsigned char *bytes =
        reinterpret_cast<const unsigned char *>(state->input.constData());
    const quint32 length =
        static_cast<quint32>(bytes[0]) |
        (static_cast<quint32>(bytes[1]) << 8) |
        (static_cast<quint32>(bytes[2]) << 16) |
        (static_cast<quint32>(bytes[3]) << 24);
    if (length < 1 || length > 2 * 1024 * 1024) {
        state->input.clear();
        return false;
    }
    if (state->input.size() < static_cast<int>(4 + length))
        return false;
    *type = state->input.at(4);
    *payload = state->input.mid(5, static_cast<int>(length - 1));
    state->input.remove(0, static_cast<int>(4 + length));
    return true;
}

QJsonObject remote_build_tcp_header(RemoteSocketState *state)
{
    QJsonObject header;
    if (!state)
        return header;

    state->localAddress = remote_socket_local_ip(state->socket);
    state->remoteAddress = remote_socket_peer_ip(state->socket);

    const bool localIsServer = state->localRole == QStringLiteral("server");
    header.insert(QStringLiteral("magic"), QStringLiteral("D64CS_TCP_HEADER"));
    header.insert(QStringLiteral("protocolVersion"), D64_REMOTE_PROTOCOL_VERSION);
    header.insert(QStringLiteral("terminalProtocol"), QStringLiteral("D64TERM/1"));
    header.insert(QStringLiteral("terminalRpcVersion"), D64_TERMINAL_RPC_VERSION);
    header.insert(QStringLiteral("applicationVersion"), remote_application_version());
    header.insert(QStringLiteral("serverSoftware"), remote_server_software());
    header.insert(
        QStringLiteral("software"),
        localIsServer ? remote_server_software() : remote_client_software()
    );
    header.insert(QStringLiteral("role"), state->localRole);
    header.insert(QStringLiteral("localIp"), state->localAddress);
    header.insert(QStringLiteral("remoteIp"), state->remoteAddress);
    header.insert(
        QStringLiteral("clientIp"),
        localIsServer ? state->remoteAddress : state->localAddress
    );
    header.insert(
        QStringLiteral("serverIp"),
        localIsServer ? state->localAddress : state->remoteAddress
    );
    header.insert(QStringLiteral("connectionId"), state->localConnectionId);
    header.insert(QStringLiteral("sessionId"), state->localSessionId);
    header.insert(QStringLiteral("gridColumns"), DBASE_TEXT_COLUMNS);
    header.insert(QStringLiteral("gridRows"), DBASE_TEXT_ROWS);
    header.insert(QStringLiteral("streamMode"), QStringLiteral("chars"));
    header.insert(QStringLiteral("coordinateMode"), QStringLiteral("cells"));
    return header;
}

void remote_send_tcp_header(RemoteSocketState *state)
{
    if (!state || state->headerSent || !state->connected)
        return;
    state->localAddress = remote_socket_local_ip(state->socket);
    state->remoteAddress = remote_socket_peer_ip(state->socket);
    remote_queue_frame(
        state,
        'H',
        QJsonDocument(remote_build_tcp_header(state)).toJson(QJsonDocument::Compact)
    );
    state->headerSent = true;
}

bool remote_accept_tcp_header(RemoteSocketState *state, const QByteArray &payload)
{
    if (!state)
        return false;
    QJsonParseError error;
    const QJsonDocument doc = QJsonDocument::fromJson(payload, &error);
    if (error.error != QJsonParseError::NoError || !doc.isObject())
        return false;

    const QJsonObject header = doc.object();
    if (header.value(QStringLiteral("magic")).toString() != QStringLiteral("D64CS_TCP_HEADER"))
        return false;
    if (header.value(QStringLiteral("protocolVersion")).toInt() != D64_REMOTE_PROTOCOL_VERSION)
        return false;
    if (header.value(QStringLiteral("terminalProtocol")).toString() != QStringLiteral("D64TERM/1"))
        return false;
    if (header.value(QStringLiteral("terminalRpcVersion")).toInt() != D64_TERMINAL_RPC_VERSION)
        return false;
    if (header.value(QStringLiteral("streamMode")).toString() != QStringLiteral("chars"))
        return false;
    if (header.value(QStringLiteral("coordinateMode")).toString() != QStringLiteral("cells"))
        return false;

    const QString peerRole = header.value(QStringLiteral("role")).toString();
    if (state->localRole == QStringLiteral("server") && peerRole != QStringLiteral("client"))
        return false;
    if (state->localRole == QStringLiteral("client") && peerRole != QStringLiteral("server"))
        return false;

    const QString connectionId = header.value(QStringLiteral("connectionId")).toString();
    if (connectionId.isEmpty())
        return false;
    if (!state->peerConnectionId.isEmpty() && state->peerConnectionId != connectionId)
        return false;

    state->peerRole = peerRole;
    state->peerConnectionId = connectionId;
    state->peerSessionId = header.value(QStringLiteral("sessionId")).toString();
    state->peerSoftware = header.value(QStringLiteral("software")).toString();
    state->peerApplicationVersion = header.value(QStringLiteral("applicationVersion")).toString();
    state->handshakeComplete = true;
    return true;
}

QSize remote_console_cell_size()
{
    QWidget *device = (g_console && g_console->viewport()) ? g_console->viewport() : g_window;
    const QFont font = current_console_grid_font();
    const QFontMetrics fm(font, device);
    return QSize(
        qMax(1, fm.horizontalAdvance(QLatin1Char('M'))),
        qMax(1, fm.height())
    );
}

QPoint remote_console_global_origin()
{
    if (g_console && g_console->viewport())
        return g_console->viewport()->mapToGlobal(QPoint(0, 0));
    if (g_window)
        return g_window->mapToGlobal(QPoint(0, 0));
    return QPoint();
}

int remote_floor_cell(int value, int cellSize)
{
    return static_cast<int>(std::floor(double(value) / double(qMax(1, cellSize))));
}

QStringList remote_grid_lines()
{
    QStringList lines;
    if (g_console)
        lines = g_console->toPlainText().replace(QLatin1Char('\r'), QString()).split(QLatin1Char('\n'));
    while (lines.size() > DBASE_TEXT_ROWS)
        lines.removeFirst();
    while (lines.size() < DBASE_TEXT_ROWS)
        lines.append(QString());
    for (int i = 0; i < lines.size(); ++i) {
        if (lines[i].size() > DBASE_TEXT_COLUMNS)
            lines[i].truncate(DBASE_TEXT_COLUMNS);
        else if (lines[i].size() < DBASE_TEXT_COLUMNS)
            lines[i] += QString(DBASE_TEXT_COLUMNS - lines[i].size(), QLatin1Char(' '));
    }
    return lines;
}

QString remote_widget_title(QWidget *widget)
{
    if (!widget)
        return QString();
    if (widget == g_login_dialog)
        return QStringLiteral("Login");
    if (widget == g_warning_dialog)
        return QStringLiteral("Warnung");
    if (widget == g_btx_dialog)
        return QStringLiteral("BTX");
    QString title = widget->windowTitle();
    if (title.isEmpty())
        title = QString::fromLatin1(widget->metaObject()->className());
    return title;
}

void remote_write_chars(QStringList &canvas, int column, int row, const QString &text)
{
    if (row < 0 || row >= canvas.size() || column >= canvas[row].size())
        return;
    const int start = qMax(0, column);
    const int sourceOffset = qMax(0, -column);
    for (int i = sourceOffset; i < text.size(); ++i) {
        const int x = start + (i - sourceOffset);
        if (x < 0 || x >= canvas[row].size())
            break;
        QChar ch = text.at(i);
        if (ch == QLatin1Char('\r') || ch == QLatin1Char('\n') || ch == QLatin1Char('\t'))
            ch = QLatin1Char(' ');
        canvas[row][x] = ch;
    }
}

void remote_draw_char_frame(QStringList &canvas, const QString &title)
{
    if (canvas.size() < 2 || canvas.first().size() < 2)
        return;
    const int rows = canvas.size();
    const int columns = canvas.first().size();
    const QChar TL(0x2554); // ╔
    const QChar TR(0x2557); // ╗
    const QChar BL(0x255A); // ╚
    const QChar BR(0x255D); // ╝
    const QChar H(0x2550);  // ═
    const QChar V(0x2551);  // ║

    canvas[0][0] = TL;
    canvas[0][columns - 1] = TR;
    canvas[rows - 1][0] = BL;
    canvas[rows - 1][columns - 1] = BR;
    for (int x = 1; x < columns - 1; ++x) {
        canvas[0][x] = H;
        canvas[rows - 1][x] = H;
    }
    for (int y = 1; y < rows - 1; ++y) {
        canvas[y][0] = V;
        canvas[y][columns - 1] = V;
    }

    if (!title.isEmpty()) {
        QString caption = QStringLiteral(" ") + title + QStringLiteral(" ");
        const int maxTitle = qMax(0, columns - 4);
        if (caption.size() > maxTitle)
            caption.truncate(maxTitle);
        remote_write_chars(canvas, 2, 0, caption);
    }
}

QJsonArray remote_dialog_char_lines(QWidget *dialog, int *columnsOut, int *rowsOut)
{
    QJsonArray result;
    if (!dialog)
        return result;

    const QSize cell = remote_console_cell_size();
    int columns = qBound(8, (dialog->width() + cell.width() - 1) / cell.width(), 160);
    int rows = qBound(3, (dialog->height() + cell.height() - 1) / cell.height(), 80);

    // Fuer die eigenen Rasterdialoge dieselben logischen Dimensionen wie im
    // Client verwenden. Dadurch werden auch die Rahmenzeichen exakt 1:1
    // reproduziert und nicht serverseitig aus Pixelgroessen approximiert.
    if (dialog == g_login_dialog) {
        columns = DBASE_LOGIN_DIALOG_COLUMNS;
        rows = DBASE_LOGIN_DIALOG_ROWS;
    } else if (dialog == g_warning_dialog) {
        columns = DBASE_WARNING_DIALOG_COLUMNS;
        rows = DBASE_WARNING_DIALOG_ROWS;
    } else if (dialog == g_btx_dialog) {
        columns = DBASE_BTX_COLUMNS + 2;
        rows = DBASE_BTX_ROWS + 2;
    }

    if (columnsOut)
        *columnsOut = columns;
    if (rowsOut)
        *rowsOut = rows;

    QStringList canvas;
    for (int row = 0; row < rows; ++row)
        canvas.append(QString(columns, QLatin1Char(' ')));

    remote_draw_char_frame(canvas, remote_widget_title(dialog));

    const QList<QWidget *> children = dialog->findChildren<QWidget *>();
    for (QWidget *child : children) {
        if (!child || !child->isVisible())
            continue;
        QString text;
        if (QLabel *label = qobject_cast<QLabel *>(child)) {
            text = label->text();
        } else if (QLineEdit *edit = qobject_cast<QLineEdit *>(child)) {
            if (edit->echoMode() == QLineEdit::Password || edit->echoMode() == QLineEdit::PasswordEchoOnEdit)
                text = QString(edit->text().size(), QLatin1Char('*'));
            else
                text = edit->text();
        } else if (QPushButton *button = qobject_cast<QPushButton *>(child)) {
            text = QStringLiteral("[") + button->text() + QStringLiteral("]");
        } else if (QComboBox *combo = qobject_cast<QComboBox *>(child)) {
            text = combo->currentText();
        } else {
            continue;
        }
        text.remove(QLatin1Char('&'));
        const QPoint p = child->mapTo(dialog, QPoint(0, 0));
        remote_write_chars(
            canvas,
            remote_floor_cell(p.x(), cell.width()),
            remote_floor_cell(p.y(), cell.height()),
            text
        );
    }

    for (const QString &line : canvas)
        result.append(line);
    return result;
}

quint32 terminal_component_id(QObject *object);
QObject *terminal_object_by_id(quint32 componentId);
void terminal_broadcast_property(QObject *object, const QString &name, const QString &value);
QByteArray terminal_build_application_template();
bool terminal_parse_record_line(const QString &line, TerminalComponentRecord *record);
QString terminal_payload_value(const QString &payload, const QString &name);

QString remote_dialog_style_name(QWidget *dialog)
{
    if (dialog == g_login_dialog)
        return QStringLiteral("login");
    if (dialog == g_warning_dialog)
        return QStringLiteral("warning");
    if (dialog == g_btx_dialog)
        return QStringLiteral("btx");
    return QStringLiteral("standard");
}

QJsonArray remote_dialog_controls(QWidget *dialog)
{
    QJsonArray controls;
    if (!dialog)
        return controls;

    const QSize cell = remote_console_cell_size();
    const QList<QWidget *> children = dialog->findChildren<QWidget *>();
    for (QWidget *child : children) {
        if (!child || !child->isVisible())
            continue;

        QString role;
        QString text;
        bool password = false;
        if (QLineEdit *edit = qobject_cast<QLineEdit *>(child)) {
            role = QStringLiteral("input");
            password = edit->echoMode() == QLineEdit::Password
                || edit->echoMode() == QLineEdit::PasswordEchoOnEdit;
            text = password
                ? QString(edit->text().size(), QLatin1Char('*'))
                : edit->text();
        } else if (QPushButton *button = qobject_cast<QPushButton *>(child)) {
            role = QStringLiteral("button");
            text = button->text();
        } else if (QCheckBox *check = qobject_cast<QCheckBox *>(child)) {
            role = QStringLiteral("checkbox");
            text = check->text();
        } else if (QLabel *label = qobject_cast<QLabel *>(child)) {
            role = QStringLiteral("label");
            text = label->text();
        } else if (QComboBox *combo = qobject_cast<QComboBox *>(child)) {
            role = QStringLiteral("input");
            text = combo->currentText();
        } else {
            continue;
        }

        text.remove(QLatin1Char('&'));
        const QPoint p = child->mapTo(dialog, QPoint(0, 0));
        QJsonObject control;
        control.insert(QStringLiteral("componentId"), static_cast<int>(terminal_component_id(child)));
        control.insert(QStringLiteral("role"), role);
        control.insert(QStringLiteral("text"), text);
        control.insert(QStringLiteral("column"), qRound(double(p.x()) / qMax(1, cell.width())));
        control.insert(QStringLiteral("row"), qRound(double(p.y()) / qMax(1, cell.height())));
        control.insert(QStringLiteral("columns"), qMax(1, qRound(double(child->width()) / qMax(1, cell.width()))));
        control.insert(QStringLiteral("rows"), qMax(1, qRound(double(child->height()) / qMax(1, cell.height()))));
        control.insert(QStringLiteral("focused"), child->hasFocus());
        control.insert(QStringLiteral("enabled"), child->isEnabled());
        control.insert(QStringLiteral("password"), password);
        if (QCheckBox *check = qobject_cast<QCheckBox *>(child))
            control.insert(QStringLiteral("checked"), check->isChecked());
        controls.append(control);
    }
    return controls;
}

QJsonArray remote_popup_char_lines(QMenu *menu, int *columnsOut, int *rowsOut)
{
    QJsonArray result;
    if (!menu)
        return result;

    QStringList itemLines;
    int innerColumns = 1;
    for (QAction *action : menu->actions()) {
        if (!action || !action->isVisible())
            continue;
        QString line;
        if (action->isSeparator()) {
            line = QStringLiteral("-");
        } else {
            line = normalized_menu_text(action->text());
            const QString shortcut = action->shortcut().toString(QKeySequence::NativeText);
            if (!shortcut.isEmpty())
                line += QStringLiteral("  ") + shortcut;
            if (action->menu())
                line += QStringLiteral(" >");
        }
        innerColumns = qMax(innerColumns, line.size());
        itemLines.append(line);
    }

    const int columns = qBound(4, innerColumns + 4, 160);
    const int rows = qBound(3, itemLines.size() + 2, 80);
    if (columnsOut)
        *columnsOut = columns;
    if (rowsOut)
        *rowsOut = rows;

    QStringList canvas;
    for (int row = 0; row < rows; ++row)
        canvas.append(QString(columns, QLatin1Char(' ')));
    remote_draw_char_frame(canvas, QString());
    for (int i = 0; i < itemLines.size() && i + 1 < rows - 1; ++i) {
        if (itemLines.at(i) == QStringLiteral("-"))
            remote_write_chars(canvas, 1, i + 1, QString(columns - 2, QChar(0x2500)));
        else
            remote_write_chars(canvas, 2, i + 1, itemLines.at(i));
    }
    for (const QString &line : canvas)
        result.append(line);
    return result;
}

QJsonObject remote_menu_action_snapshot(QAction *action, const QString &path)
{
    QJsonObject item;
    if (!action)
        return item;
    item.insert(QStringLiteral("path"), path);
    item.insert(QStringLiteral("text"), normalized_menu_text(action->text()));
    item.insert(QStringLiteral("enabled"), action->isEnabled());
    item.insert(QStringLiteral("visible"), action->isVisible());
    item.insert(QStringLiteral("separator"), action->isSeparator());
    item.insert(QStringLiteral("checkable"), action->isCheckable());
    item.insert(QStringLiteral("checked"), action->isChecked());
    item.insert(QStringLiteral("shortcut"), action->shortcut().toString(QKeySequence::NativeText));

    if (QMenu *submenu = action->menu()) {
        QJsonArray children;
        const QList<QAction *> actions = submenu->actions();
        for (int i = 0; i < actions.size(); ++i) {
            QAction *child = actions.at(i);
            if (!child || !child->isVisible())
                continue;
            children.append(remote_menu_action_snapshot(child, path + QLatin1Char('/') + QString::number(i)));
        }
        item.insert(QStringLiteral("children"), children);
    }
    return item;
}

QJsonArray remote_menu_tree()
{
    QJsonArray tree;
    if (!g_menu_bar)
        return tree;
    const QList<QAction *> actions = g_menu_bar->actions();
    for (int i = 0; i < actions.size(); ++i) {
        QAction *action = actions.at(i);
        if (!action || !action->isVisible())
            continue;
        tree.append(remote_menu_action_snapshot(action, QString::number(i)));
    }
    return tree;
}

QJsonArray remote_status_fields()
{
    QJsonArray fields;
    if (!g_status_bar)
        return fields;
    QList<QLabel *> labels = g_status_bar->findChildren<QLabel *>();
    std::sort(labels.begin(), labels.end(), [](QLabel *a, QLabel *b) {
        if (!a || !b)
            return a != nullptr;
        return a->mapTo(g_status_bar, QPoint(0, 0)).x() < b->mapTo(g_status_bar, QPoint(0, 0)).x();
    });
    for (QLabel *label : labels) {
        if (!label || !label->isVisible())
            continue;
        QJsonObject field;
        field.insert(QStringLiteral("text"), label->text());
        field.insert(QStringLiteral("permanent"), label == g_remote_listener_label);
        fields.append(field);
    }
    return fields;
}

QString terminal_color_hex(const QColor &color)
{
    QColor value = color;
    if (!value.isValid())
        value = QColor(0, 0, 0);
    return value.name(QColor::HexRgb).mid(1).toUpper();
}

QString terminal_escape(const QString &text)
{
    const QByteArray bytes = text.toUtf8();
    QByteArray out;
    static const char hex[] = "0123456789ABCDEF";
    for (char raw : bytes) {
        const unsigned char ch = static_cast<unsigned char>(raw);
        const bool safe =
            (ch >= 'A' && ch <= 'Z') ||
            (ch >= 'a' && ch <= 'z') ||
            (ch >= '0' && ch <= '9') ||
            ch == '-' || ch == '.';
        if (safe) {
            out.append(static_cast<char>(ch));
        } else {
            out.append('%');
            out.append(hex[(ch >> 4) & 0x0f]);
            out.append(hex[ch & 0x0f]);
        }
    }
    return QString::fromLatin1(out);
}

QString terminal_unescape(const QString &text)
{
    return QString::fromUtf8(QByteArray::fromPercentEncoding(text.toLatin1()));
}

QString terminal_payload_value(const QString &payload, const QString &name)
{
    const QString prefix = name + QLatin1Char('=');
    const QStringList fields = payload.split(QLatin1Char(';'));
    for (const QString &field : fields) {
        if (field.startsWith(prefix))
            return field.mid(prefix.size());
    }
    return QString();
}

quint32 terminal_component_id(QObject *object)
{
    if (!object)
        return 0;
    const auto found = g_terminal_object_ids.constFind(object);
    if (found != g_terminal_object_ids.constEnd())
        return found.value();

    quint32 id = g_terminal_next_component_id++;
    if (id >= 0x3fffffffU) {
        g_terminal_next_component_id = 100;
        id = g_terminal_next_component_id++;
    }
    g_terminal_object_ids.insert(object, id);
    g_terminal_id_objects.insert(id, QPointer<QObject>(object));
    object->setProperty("d64TerminalComponentId", static_cast<uint>(id));

    QObject::connect(object, &QObject::destroyed, [object, id]() {
        g_terminal_object_ids.remove(object);
        g_terminal_id_objects.remove(id);
        g_terminal_template_dirty = true;
    });

    if (QLineEdit *edit = qobject_cast<QLineEdit *>(object)) {
        if (!edit->property("d64TerminalTextHooked").toBool()) {
            edit->setProperty("d64TerminalTextHooked", true);
            QObject::connect(edit, &QLineEdit::textChanged, [edit](const QString &text) {
                const bool password = edit->echoMode() == QLineEdit::Password
                    || edit->echoMode() == QLineEdit::PasswordEchoOnEdit;
                terminal_broadcast_property(
                    edit,
                    QStringLiteral("TEXT"),
                    password ? QString(text.size(), QLatin1Char('*')) : text
                );
                g_remote_last_snapshot.clear();
            });
        }
    } else if (QComboBox *combo = qobject_cast<QComboBox *>(object)) {
        if (!combo->property("d64TerminalTextHooked").toBool()) {
            combo->setProperty("d64TerminalTextHooked", true);
            QObject::connect(combo, &QComboBox::currentTextChanged, [combo](const QString &text) {
                terminal_broadcast_property(combo, QStringLiteral("TEXT"), text);
                g_remote_last_snapshot.clear();
            });
        }
    } else if (QCheckBox *check = qobject_cast<QCheckBox *>(object)) {
        if (!check->property("d64TerminalCheckedHooked").toBool()) {
            check->setProperty("d64TerminalCheckedHooked", true);
            QObject::connect(check, &QCheckBox::toggled, [check](bool checked) {
                terminal_broadcast_property(
                    check, QStringLiteral("CHECKED"), checked ? QStringLiteral("1") : QStringLiteral("0")
                );
                g_remote_last_snapshot.clear();
            });
        }
    }
    g_terminal_template_dirty = true;
    return id;
}

QObject *terminal_object_by_id(quint32 componentId)
{
    const auto found = g_terminal_id_objects.constFind(componentId);
    if (found == g_terminal_id_objects.constEnd())
        return nullptr;
    return found.value().data();
}

QString terminal_record_line(const TerminalComponentRecord &record)
{
    return QStringLiteral("T%1_%2_%3_%4_%5_%6_%7_%8_%9_%10")
        .arg(record.typeCode, 4, 10, QLatin1Char('0'))
        .arg(record.componentId, 8, 10, QLatin1Char('0'))
        .arg(record.parentId, 8, 10, QLatin1Char('0'))
        .arg(record.column, 3, 10, QLatin1Char('0'))
        .arg(record.row, 3, 10, QLatin1Char('0'))
        .arg(record.columns, 3, 10, QLatin1Char('0'))
        .arg(record.rows, 3, 10, QLatin1Char('0'))
        .arg(terminal_color_hex(record.foreground))
        .arg(terminal_color_hex(record.background))
        .arg(terminal_escape(record.payload));
}

TerminalComponentRecord terminal_make_record(
    int typeCode, quint32 componentId, quint32 parentId,
    int column, int row, int columns, int rows,
    const QColor &foreground, const QColor &background,
    const QString &payload = QString())
{
    TerminalComponentRecord record;
    record.typeCode = typeCode;
    record.componentId = componentId;
    record.parentId = parentId;
    record.column = column;
    record.row = row;
    record.columns = qMax(1, columns);
    record.rows = qMax(1, rows);
    record.foreground = foreground;
    record.background = background;
    record.payload = payload;
    return record;
}

void terminal_append_menu_items(QStringList &program, const QJsonArray &items, quint32 parentId, quint32 &virtualId)
{
    int itemRow = 0;
    for (const QJsonValue &value : items) {
        const QJsonObject item = value.toObject();
        const quint32 id = virtualId++;
        const QString payload = QStringLiteral("TEXT=%1;PATH=%2;ENABLED=%3;CHECKED=%4;SEPARATOR=%5")
            .arg(item.value(QStringLiteral("text")).toString())
            .arg(item.value(QStringLiteral("path")).toString())
            .arg(item.value(QStringLiteral("enabled")).toBool(true) ? 1 : 0)
            .arg(item.value(QStringLiteral("checked")).toBool(false) ? 1 : 0)
            .arg(item.value(QStringLiteral("separator")).toBool(false) ? 1 : 0);
        program.append(terminal_record_line(terminal_make_record(
            TerminalTMenuItem, id, parentId, 0, itemRow++, 1, 1,
            QColor(0, 0, 0), QColor(144, 144, 144), payload
        )));
        const QJsonArray children = item.value(QStringLiteral("children")).toArray();
        if (!children.isEmpty())
            terminal_append_menu_items(program, children, id, virtualId);
    }
}

int terminal_type_for_widget(QWidget *widget)
{
    if (qobject_cast<QLineEdit *>(widget)) return TerminalTLineEdit;
    if (qobject_cast<QPushButton *>(widget)) return TerminalTButton;
    if (qobject_cast<QCheckBox *>(widget)) return TerminalTCheckBox;
    if (qobject_cast<QComboBox *>(widget)) return TerminalTComboBox;
    if (qobject_cast<QLabel *>(widget)) return TerminalTLabel;
    return 0;
}

QString terminal_widget_payload(QWidget *widget)
{
    if (!widget)
        return QString();
    QString text;
    QString extra;
    if (QLineEdit *edit = qobject_cast<QLineEdit *>(widget)) {
        const bool password = edit->echoMode() == QLineEdit::Password
            || edit->echoMode() == QLineEdit::PasswordEchoOnEdit;
        extra = QStringLiteral(";PASSWORD=%1").arg(password ? 1 : 0);
    } else if (QPushButton *button = qobject_cast<QPushButton *>(widget)) {
        text = button->text();
    } else if (QCheckBox *check = qobject_cast<QCheckBox *>(widget)) {
        text = check->text();
        extra = QStringLiteral(";CHECKED=%1").arg(check->isChecked() ? 1 : 0);
    } else if (QComboBox *combo = qobject_cast<QComboBox *>(widget)) {
        text = combo->currentText();
    } else if (QLabel *label = qobject_cast<QLabel *>(widget)) {
        text = label->text();
    }
    text.remove(QLatin1Char('&'));
    return QStringLiteral("NAME=%1;TEXT=%2;ENABLED=%3%4")
        .arg(widget->objectName())
        .arg(text)
        .arg(widget->isEnabled() ? 1 : 0)
        .arg(extra);
}

QByteArray terminal_build_application_template()
{
    QStringList program;
    const QString sessionId = remote_current_session_id().isEmpty()
        ? QStringLiteral("-") : remote_current_session_id();
    program.append(QStringLiteral("D64TERM_%1_%2_%3_%4_%5")
        .arg(D64_TERMINAL_RPC_VERSION)
        .arg(g_remote_application_connection_id)
        .arg(sessionId)
        .arg(DBASE_TEXT_COLUMNS)
        .arg(DBASE_TEXT_ROWS));

    // Exakt definierte Initialisierungsreihenfolge.
    TApplication application;
    application.record = terminal_make_record(
        TerminalTApplication, 1, 0, 0, 0, DBASE_TEXT_COLUMNS, DBASE_TEXT_ROWS,
        g_output_foreground, g_console_background,
        QStringLiteral("TITLE=%1;BORDER=%2")
            .arg(g_window ? g_window->windowTitle() : QString())
            .arg(terminal_color_hex(g_console_border_color))
    );
    program.append(terminal_record_line(application.record));

    TBackground background;
    const bool patterned = g_console_clear_mode == ConsoleClearMode::CharacterPattern
        && g_console_clear_char_code >= 0;
    const int clearChar = patterned ? g_console_clear_char_code : 32;
    const QColor bgFg = patterned ? g_console_clear_char_foreground : g_output_foreground;
    const QColor bgBg = patterned ? g_console_clear_char_background : g_console_background;
    background.record = terminal_make_record(
        TerminalTBackground, 2, 1, 0, 0, DBASE_TEXT_COLUMNS, DBASE_TEXT_ROWS,
        bgFg, bgBg,
        QStringLiteral("CHAR=%1").arg(clearChar, 2, 16, QLatin1Char('0')).toUpper()
    );
    program.append(terminal_record_line(background.record));

    TMainMenu mainMenu;
    mainMenu.record = terminal_make_record(
        TerminalTMainMenu, 3, 1, 0, -1, DBASE_TEXT_COLUMNS, 1,
        QColor(0, 0, 0), QColor(144, 144, 144), QStringLiteral("MAIN")
    );
    program.append(terminal_record_line(mainMenu.record));
    quint32 virtualId = 0x20000000U;
    terminal_append_menu_items(program, remote_menu_tree(), 3, virtualId);

    TStatusBar statusBar;
    QStringList statusTexts;
    for (const QJsonValue &value : remote_status_fields())
        statusTexts.append(value.toObject().value(QStringLiteral("text")).toString());
    statusBar.record = terminal_make_record(
        TerminalTStatusBar, 4, 1, 0, DBASE_TEXT_ROWS, DBASE_TEXT_COLUMNS, 1,
        QColor(0, 0, 0), QColor(144, 144, 144),
        QStringLiteral("TEXT=%1").arg(statusTexts.join(QStringLiteral(" | ")))
    );
    program.append(terminal_record_line(statusBar.record));

    // Danach Frames, deren View und Controls.
    const QSize cell = remote_console_cell_size();
    const QPoint gridOrigin = remote_console_global_origin();
    for (QWidget *widget : QApplication::topLevelWidgets()) {
        if (!widget || widget == g_window
            || widget == reinterpret_cast<QWidget *>(g_server_dialog)
            || widget == reinterpret_cast<QWidget *>(g_remote_cursor_marker)
            || !widget->isVisible() || qobject_cast<QMenu *>(widget))
            continue;

        int frameColumns = 0;
        int frameRows = 0;
        remote_dialog_char_lines(widget, &frameColumns, &frameRows);
        const QPoint delta = widget->mapToGlobal(QPoint(0, 0)) - gridOrigin;
        const int frameColumn = qRound(double(delta.x()) / qMax(1, cell.width()));
        const int frameRow = qRound(double(delta.y()) / qMax(1, cell.height()));
        const quint32 frameId = terminal_component_id(widget);
        const QColor dialogBg = widget == g_warning_dialog ? QColor(255, 0, 0) : QColor(144, 144, 144);

        TFrame frame;
        frame.record = terminal_make_record(
            TerminalTFrame, frameId, 1, frameColumn, frameRow, frameColumns, frameRows,
            QColor(255, 255, 255), dialogBg,
            QStringLiteral("TITLE=%1").arg(remote_widget_title(widget))
        );
        program.append(terminal_record_line(frame.record));

        TView view;
        const quint32 viewId = frameId | 0x40000000U;
        view.record = terminal_make_record(
            TerminalTView, viewId, frameId, 1, 1,
            qMax(1, frameColumns - 2), qMax(1, frameRows - 2),
            QColor(0, 0, 0), dialogBg, QStringLiteral("CLIENTAREA")
        );
        program.append(terminal_record_line(view.record));

        for (QWidget *child : widget->findChildren<QWidget *>()) {
            if (!child || !child->isVisible())
                continue;
            const int typeCode = terminal_type_for_widget(child);
            if (!typeCode)
                continue;
            const QPoint p = child->mapTo(widget, QPoint(0, 0));
            const int cc = qRound(double(p.x()) / qMax(1, cell.width()));
            const int cr = qRound(double(p.y()) / qMax(1, cell.height()));
            const int cw = qMax(1, qRound(double(child->width()) / qMax(1, cell.width())));
            const int ch = qMax(1, qRound(double(child->height()) / qMax(1, cell.height())));
            QColor fg(0, 0, 0);
            QColor bg = dialogBg;
            if (typeCode == TerminalTLineEdit || typeCode == TerminalTComboBox) {
                fg = QColor(255, 255, 255);
                bg = QColor(0, 128, 0);
            }
            program.append(terminal_record_line(terminal_make_record(
                typeCode, terminal_component_id(child), viewId,
                cc, cr, cw, ch, fg, bg, terminal_widget_payload(child)
            )));
        }
    }
    program.append(QStringLiteral("END"));
    return program.join(QLatin1Char('\n')).toUtf8();
}

void terminal_broadcast_property(QObject *object, const QString &name, const QString &value)
{
    if (!object || g_remote_client_peers.isEmpty())
        return;
    const quint32 id = terminal_component_id(object);
    const QString session = remote_current_session_id().isEmpty()
        ? QStringLiteral("-") : remote_current_session_id();

    // Template muss garantiert vor dem ersten Property-RPC auf dem Socket liegen.
    if (g_terminal_template_dirty || g_terminal_last_program.isEmpty()) {
        g_terminal_last_program = terminal_build_application_template();
        g_terminal_template_dirty = false;
    }

    const QByteArray payload = QStringLiteral("P_%1_%2_%3_%4_%5")
        .arg(g_remote_application_connection_id)
        .arg(session)
        .arg(id)
        .arg(terminal_escape(name))
        .arg(terminal_escape(value))
        .toUtf8();
    for (RemoteSocketState *peer : g_remote_client_peers) {
        if (!peer || !peer->connected || !peer->handshakeComplete)
            continue;
        if (peer->lastTerminalTemplateSent != g_terminal_last_program) {
            peer->lastTerminalTemplateSent = g_terminal_last_program;
            remote_queue_frame(peer, 'T', g_terminal_last_program);
        }
        remote_queue_frame(peer, 'R', payload);
    }
}

bool terminal_parse_record_line(const QString &line, TerminalComponentRecord *record)
{
    if (!record || !line.startsWith(QLatin1Char('T')))
        return false;
    const QStringList parts = line.split(QLatin1Char('_'));
    if (parts.size() != 10)
        return false;
    bool ok = false;
    record->typeCode = parts.at(0).mid(1).toInt(&ok); if (!ok) return false;
    record->componentId = parts.at(1).toUInt(&ok); if (!ok) return false;
    record->parentId = parts.at(2).toUInt(&ok); if (!ok) return false;
    record->column = parts.at(3).toInt(&ok); if (!ok) return false;
    record->row = parts.at(4).toInt(&ok); if (!ok) return false;
    record->columns = parts.at(5).toInt(&ok); if (!ok) return false;
    record->rows = parts.at(6).toInt(&ok); if (!ok) return false;
    record->foreground = QColor(QStringLiteral("#") + parts.at(7));
    record->background = QColor(QStringLiteral("#") + parts.at(8));
    record->payload = terminal_unescape(parts.at(9));
    return record->foreground.isValid() && record->background.isValid();
}

QJsonObject remote_build_snapshot()
{
    QJsonObject root;
    if (!g_window)
        return root;

    root.insert(QStringLiteral("protocol"), D64_REMOTE_PROTOCOL_VERSION);
    root.insert(QStringLiteral("terminalProtocol"), QStringLiteral("D64TERM/1"));
    root.insert(QStringLiteral("terminalRpcVersion"), D64_TERMINAL_RPC_VERSION);
    root.insert(QStringLiteral("streamMode"), QStringLiteral("chars"));
    root.insert(QStringLiteral("connectionId"), g_remote_application_connection_id);
    root.insert(QStringLiteral("sessionId"), remote_current_session_id());
    root.insert(QStringLiteral("applicationVersion"), remote_application_version());
    root.insert(QStringLiteral("title"), g_window->windowTitle());
    root.insert(QStringLiteral("gridColumns"), DBASE_TEXT_COLUMNS);
    root.insert(QStringLiteral("gridRows"), DBASE_TEXT_ROWS);
    root.insert(QStringLiteral("consoleBackground"), g_console_background.name(QColor::HexRgb));
    root.insert(QStringLiteral("consoleBorderColor"), g_console_border_color.name(QColor::HexRgb));
    root.insert(QStringLiteral("outputForeground"), g_output_foreground.name(QColor::HexRgb));
    root.insert(QStringLiteral("outputBackground"), g_output_background.name(QColor::HexRgb));

    QJsonArray grid;
    const QStringList lines = remote_grid_lines();
    for (const QString &line : lines)
        grid.append(line);
    root.insert(QStringLiteral("grid"), grid);

    // Vollstaendiger logischer Menuebaum und echte Statusleisten-Texte.
    // Keine Pixelkoordinaten werden dafuer uebertragen.
    root.insert(QStringLiteral("menuTree"), remote_menu_tree());
    root.insert(QStringLiteral("statusFields"), remote_status_fields());

    const QSize cell = remote_console_cell_size();
    const QPoint gridOrigin = remote_console_global_origin();

    QJsonArray windows;
    const QWidgetList topLevels = QApplication::topLevelWidgets();
    for (QWidget *widget : topLevels) {
        if (!widget || widget == g_window || widget == reinterpret_cast<QWidget *>(g_server_dialog) || widget == reinterpret_cast<QWidget *>(g_remote_cursor_marker))
            continue;
        if (!widget->isVisible())
            continue;

        QJsonObject info;
        const QPoint delta = widget->mapToGlobal(QPoint(0, 0)) - gridOrigin;
        info.insert(QStringLiteral("charColumn"), qRound(double(delta.x()) / qMax(1, cell.width())));
        info.insert(QStringLiteral("charRow"), qRound(double(delta.y()) / qMax(1, cell.height())));
        info.insert(QStringLiteral("title"), remote_widget_title(widget));
        QString remoteWindowId = widget->objectName();
        if (remoteWindowId.isEmpty())
            remoteWindowId = QStringLiteral("window-%1").arg(static_cast<qulonglong>(reinterpret_cast<quintptr>(widget)), 0, 16);
        info.insert(QStringLiteral("windowId"), remoteWindowId);
        info.insert(QStringLiteral("active"), widget->isActiveWindow());
        info.insert(QStringLiteral("kind"), qobject_cast<QMenu *>(widget) ? QStringLiteral("menu") : QStringLiteral("dialog"));

        int charColumns = 0;
        int charRows = 0;
        if (QMenu *menu = qobject_cast<QMenu *>(widget)) {
            info.insert(QStringLiteral("charLines"), remote_popup_char_lines(menu, &charColumns, &charRows));
        } else {
            info.insert(QStringLiteral("charLines"), remote_dialog_char_lines(widget, &charColumns, &charRows));
            info.insert(QStringLiteral("dialogStyle"), remote_dialog_style_name(widget));
            info.insert(QStringLiteral("controls"), remote_dialog_controls(widget));
            info.insert(QStringLiteral("moving"), widget->property("dbaseRemoteMoving").toBool());
        }
        info.insert(QStringLiteral("charColumns"), charColumns);
        info.insert(QStringLiteral("charRows"), charRows);
        windows.append(info);
    }
    root.insert(QStringLiteral("windows"), windows);
    return root;
}

class RemoteCursorMarker final : public QWidget
{
public:
    explicit RemoteCursorMarker(QWidget *parent)
        : QWidget(parent, Qt::Tool | Qt::FramelessWindowHint | Qt::WindowStaysOnTopHint)
    {
        setObjectName(QStringLiteral("dbaseRemoteCursorMarker"));
        setAttribute(Qt::WA_TransparentForMouseEvents, true);
        setAttribute(Qt::WA_ShowWithoutActivating, true);
        setAttribute(Qt::WA_TranslucentBackground, true);
        resize(17, 17);
    }

protected:
    void paintEvent(QPaintEvent *) override
    {
        QPainter painter(this);
        painter.setRenderHint(QPainter::Antialiasing, false);
        QPen pen(QColor(255, 255, 0));
        pen.setWidth(2);
        painter.setPen(pen);
        painter.drawLine(8, 0, 8, 16);
        painter.drawLine(0, 8, 16, 8);
        painter.drawRect(5, 5, 6, 6);
    }
};

void remote_show_cursor(const QPoint &globalPoint)
{
    if (!g_window)
        return;
    if (!g_remote_cursor_marker)
        g_remote_cursor_marker = new RemoteCursorMarker(g_window);
    g_remote_cursor_marker->move(globalPoint - QPoint(8, 8));
    g_remote_cursor_marker->show();
    g_remote_cursor_marker->raise();
}

QWidget *remote_target_widget_at(const QPoint &globalPoint)
{
    QWidget *target = QApplication::widgetAt(globalPoint);
    if (target == g_remote_cursor_marker)
        target = nullptr;
    if (target)
        return target;
    if (g_window && QRect(g_window->mapToGlobal(QPoint(0, 0)), g_window->size()).contains(globalPoint))
        return g_window;
    return nullptr;
}

bool remote_command_matches_client(RemoteSocketState *peer, const QJsonObject &command)
{
    if (!peer || !peer->handshakeComplete)
        return false;
    if (command.value(QStringLiteral("targetConnectionId")).toString() != g_remote_application_connection_id)
        return false;
    if (!peer->peerConnectionId.isEmpty() &&
        command.value(QStringLiteral("sourceConnectionId")).toString() != peer->peerConnectionId)
        return false;
    const QString currentSession = remote_current_session_id();
    if (command.value(QStringLiteral("targetSessionId")).toString() != currentSession)
        return false;
    return true;
}

QAction *remote_action_from_path(const QString &path)
{
    if (!g_menu_bar)
        return nullptr;
    const QStringList parts = path.split(QLatin1Char('/'), Qt::SkipEmptyParts);
    if (parts.isEmpty())
        return nullptr;

    bool ok = false;
    int index = parts.first().toInt(&ok);
    if (!ok || index < 0 || index >= g_menu_bar->actions().size())
        return nullptr;
    QAction *action = g_menu_bar->actions().at(index);
    for (int i = 1; action && i < parts.size(); ++i) {
        QMenu *menu = action->menu();
        if (!menu)
            return nullptr;
        index = parts.at(i).toInt(&ok);
        if (!ok || index < 0 || index >= menu->actions().size())
            return nullptr;
        action = menu->actions().at(index);
    }
    return action;
}

void remote_dispatch_menu_command(const QJsonObject &command)
{
    if (g_shutdown_requested)
        return;
    QAction *action = remote_action_from_path(command.value(QStringLiteral("path")).toString());
    if (!action || !action->isVisible() || !action->isEnabled() || action->isSeparator())
        return;
    if (!action->menu())
        action->trigger();
}

void remote_dispatch_mouse_command(const QJsonObject &command)
{
    if (!g_window || !g_console || !g_console->viewport() || g_shutdown_requested)
        return;

    const QSize cell = remote_console_cell_size();
    const int column = command.value(QStringLiteral("column")).toInt();
    const int row = command.value(QStringLiteral("row")).toInt();
    const int subX = qBound(0, command.value(QStringLiteral("subX")).toInt(500), 999);
    const int subY = qBound(0, command.value(QStringLiteral("subY")).toInt(500), 999);
    const QPoint gridOrigin = remote_console_global_origin();
    const QPoint globalPoint(
        gridOrigin.x() + column * cell.width() + (subX * cell.width()) / 1000,
        gridOrigin.y() + row * cell.height() + (subY * cell.height()) / 1000
    );
    remote_show_cursor(globalPoint);

    const QString action = command.value(QStringLiteral("action")).toString();
    QWidget *target = nullptr;
    if ((action == QStringLiteral("move") || action == QStringLiteral("release"))
        && !g_remote_mouse_capture_widget.isNull())
    {
        target = g_remote_mouse_capture_widget.data();
    } else {
        target = remote_target_widget_at(globalPoint);
    }
    if (!target)
        return;

    QEvent::Type type = QEvent::MouseMove;
    if (action == QStringLiteral("press"))
        type = QEvent::MouseButtonPress;
    else if (action == QStringLiteral("release"))
        type = QEvent::MouseButtonRelease;
    else if (action == QStringLiteral("double"))
        type = QEvent::MouseButtonDblClick;

    const Qt::MouseButton button = static_cast<Qt::MouseButton>(command.value(QStringLiteral("button")).toInt());
    const Qt::MouseButtons buttons = static_cast<Qt::MouseButtons>(command.value(QStringLiteral("buttons")).toInt());
    const QPoint localPoint = target->mapFromGlobal(globalPoint);
    QMouseEvent event(
        type,
        QPointF(localPoint),
        QPointF(globalPoint),
        button,
        buttons,
        Qt::NoModifier
    );
    if (action == QStringLiteral("press")) {
        g_remote_mouse_capture_widget = target;
    }

    g_remote_dispatching_mouse = true;
    QApplication::sendEvent(target, &event);
    g_remote_dispatching_mouse = false;

    if (action == QStringLiteral("release")) {
        g_remote_mouse_capture_widget.clear();
    }
}

void remote_dispatch_terminal_key(const QJsonObject &command)
{
    const quint32 componentId = static_cast<quint32>(command.value(QStringLiteral("componentId")).toInt());
    QLineEdit *edit = qobject_cast<QLineEdit *>(terminal_object_by_id(componentId));
    if (!edit || !edit->isVisible() || !edit->isEnabled())
        return;
    const int key = command.value(QStringLiteral("key")).toInt();
    const Qt::KeyboardModifiers modifiers = static_cast<Qt::KeyboardModifiers>(
        command.value(QStringLiteral("modifiers")).toInt()
    );
    const QString text = command.value(QStringLiteral("text")).toString();
    edit->setFocus(Qt::OtherFocusReason);
    QKeyEvent press(QEvent::KeyPress, key, modifiers, text);
    QApplication::sendEvent(edit, &press);
    QKeyEvent release(QEvent::KeyRelease, key, modifiers, text);
    QApplication::sendEvent(edit, &release);
}

void remote_process_client_command(RemoteSocketState *peer, const QByteArray &payload)
{
    QJsonParseError error;
    const QJsonDocument doc = QJsonDocument::fromJson(payload, &error);
    if (error.error != QJsonParseError::NoError || !doc.isObject())
        return;
    const QJsonObject command = doc.object();
    if (!remote_command_matches_client(peer, command))
        return;
    const QString type = command.value(QStringLiteral("type")).toString();
    if (type == QStringLiteral("mouse")) {
        const quint64 sequence = static_cast<quint64>(
            command.value(QStringLiteral("sequence")).toDouble()
        );
        if (sequence != 0 && sequence <= peer->lastPeerMouseSequence)
            return;
        if (sequence != 0)
            peer->lastPeerMouseSequence = sequence;
        remote_dispatch_mouse_command(command);
    } else if (type == QStringLiteral("menu")) {
        remote_dispatch_menu_command(command);
    } else if (type == QStringLiteral("terminalKey")) {
        remote_dispatch_terminal_key(command);
    }
}

void remote_queue_local_mouse(const QString &action, QMouseEvent *event)
{
    if (!event || !g_window || !g_console || !g_console->viewport() || g_remote_dispatching_mouse || g_remote_client_peers.isEmpty())
        return;

    const QSize cell = remote_console_cell_size();
    const QPoint relative = event->globalPos() - remote_console_global_origin();
    const int column = remote_floor_cell(relative.x(), cell.width());
    const int row = remote_floor_cell(relative.y(), cell.height());
    const int withinX = relative.x() - column * cell.width();
    const int withinY = relative.y() - row * cell.height();

    QJsonObject mouse;
    mouse.insert(QStringLiteral("type"), QStringLiteral("mouse"));
    mouse.insert(QStringLiteral("source"), QStringLiteral("client"));
    mouse.insert(QStringLiteral("sequence"), static_cast<double>(++g_remote_local_mouse_sequence));
    mouse.insert(QStringLiteral("connectionId"), g_remote_application_connection_id);
    mouse.insert(QStringLiteral("sessionId"), remote_current_session_id());
    mouse.insert(QStringLiteral("column"), column);
    mouse.insert(QStringLiteral("row"), row);
    mouse.insert(QStringLiteral("subX"), qBound(0, (withinX * 1000) / qMax(1, cell.width()), 999));
    mouse.insert(QStringLiteral("subY"), qBound(0, (withinY * 1000) / qMax(1, cell.height()), 999));
    mouse.insert(QStringLiteral("action"), action);
    mouse.insert(QStringLiteral("button"), static_cast<int>(event->button()));
    mouse.insert(QStringLiteral("buttons"), static_cast<int>(event->buttons()));
    const QByteArray payload = QJsonDocument(mouse).toJson(QJsonDocument::Compact);
    // Legacy regression marker: remote_queue_frame(peer, 'M', payload);
    const bool coalesceMove = action == QStringLiteral("move");
    for (RemoteSocketState *peer : g_remote_client_peers) {
        if (peer && peer->connected && peer->handshakeComplete)
            remote_queue_mouse_payload(peer, 'M', payload, coalesceMove);
    }
}

class RemoteClientEventFilter final : public QObject
{
public:
    explicit RemoteClientEventFilter(QObject *parent = nullptr)
        : QObject(parent)
    {
    }

protected:
    bool eventFilter(QObject *watched, QEvent *event) override
    {
        if (event && (event->type() == QEvent::Show || event->type() == QEvent::Hide
            || event->type() == QEvent::ChildAdded || event->type() == QEvent::ChildRemoved))
            g_terminal_template_dirty = true;
        if (!event || g_remote_dispatching_mouse || g_remote_client_peers.isEmpty())
            return QObject::eventFilter(watched, event);
        QWidget *widget = qobject_cast<QWidget *>(watched);
        if (!widget)
            return QObject::eventFilter(watched, event);
        QWidget *top = widget->window();
        // ServerDialog ist hier nur vorwaertsdeklariert. Deshalb kann der
        // Compiler die Vererbung ServerDialog -> QDialog -> QWidget an dieser
        // Stelle noch nicht fuer einen impliziten Pointervergleich benutzen.
        // Der gespeicherte Zeiger zeigt spaeter auf genau das QWidget-Objekt.
        if (!top
            || top == reinterpret_cast<QWidget *>(g_server_dialog)
            || top == g_remote_cursor_marker)
            return QObject::eventFilter(watched, event);

        QString action;
        switch (event->type()) {
        case QEvent::MouseMove: action = QStringLiteral("move"); break;
        case QEvent::MouseButtonPress: action = QStringLiteral("press"); break;
        case QEvent::MouseButtonRelease: action = QStringLiteral("release"); break;
        case QEvent::MouseButtonDblClick: action = QStringLiteral("double"); break;
        default:
            return QObject::eventFilter(watched, event);
        }
        remote_queue_local_mouse(action, static_cast<QMouseEvent *>(event));
        return QObject::eventFilter(watched, event);
    }
};

void remote_broadcast_session_identity()
{
    const QString sessionId = remote_current_session_id();
    QJsonObject identity;
    identity.insert(QStringLiteral("connectionId"), g_remote_application_connection_id);
    identity.insert(QStringLiteral("sessionId"), sessionId);
    const QByteArray payload = QJsonDocument(identity).toJson(QJsonDocument::Compact);
    for (RemoteSocketState *peer : g_remote_client_peers) {
        if (!peer || !peer->connected || !peer->handshakeComplete)
            continue;
        peer->localSessionId = sessionId;
        remote_queue_frame(peer, 'I', payload);
    }
    g_remote_last_snapshot.clear();
}

quint16 remote_default_port()
{
    QString name = QString::fromWCharArray(D64WorkstationApplicationMutexName());
    const int dot = name.lastIndexOf(QLatin1Char('.'));
    bool ok = false;
    const quint64 hash = (dot >= 0 ? name.mid(dot + 1) : name).toULongLong(&ok, 16);
    return static_cast<quint16>(46000 + (ok ? (hash % 1000) : (GetCurrentProcessId() % 1000)));
}

void remote_client_poll()
{
    if (g_remote_listener != INVALID_SOCKET) {
        for (;;) {
            sockaddr_in address;
            int length = sizeof(address);
            SOCKET accepted = ::accept(g_remote_listener, reinterpret_cast<sockaddr *>(&address), &length);
            if (accepted == INVALID_SOCKET) {
                if (::WSAGetLastError() == WSAEWOULDBLOCK)
                    break;
                break;
            }
            remote_set_nonblocking(accepted);
            RemoteSocketState *peer = new RemoteSocketState();
            peer->socket = accepted;
            peer->connected = true;
            peer->localRole = QStringLiteral("client");
            peer->localConnectionId = g_remote_application_connection_id;
            peer->localSessionId = remote_current_session_id();
            peer->peerAddress = remote_sockaddr_text(address);
            peer->peerPort = ::ntohs(address.sin_port);
            g_remote_client_peers.append(peer);
            remote_send_tcp_header(peer);
            g_terminal_template_dirty = true;
            g_remote_last_snapshot.clear();
        }
    }

    for (int i = g_remote_client_peers.size() - 1; i >= 0; --i) {
        RemoteSocketState *peer = g_remote_client_peers.at(i);
        bool alive = remote_receive(peer);
        char type = 0;
        QByteArray payload;
        while (alive && remote_take_frame(peer, &type, &payload)) {
            if (type == 'H') {
                alive = remote_accept_tcp_header(peer, payload);
                if (alive)
                    remote_broadcast_session_identity();
            } else if (type == 'C' && peer->handshakeComplete) {
                remote_process_client_command(peer, payload);
            }
        }
        if (alive) {
            remote_flush_pending_mouse(peer);
            alive = remote_flush(peer);
        }
        if (!alive) {
            remote_close_socket(peer->socket);
            delete peer;
            g_remote_client_peers.removeAt(i);
        }
    }

    if (!g_remote_client_peers.isEmpty()) {
        // T-Frame muss vor Snapshot und Property-/Text-RPC stehen.
        if (g_terminal_template_dirty || g_terminal_last_program.isEmpty())
            g_terminal_last_program = terminal_build_application_template();
        for (RemoteSocketState *peer : g_remote_client_peers) {
            if (!peer || !peer->handshakeComplete)
                continue;
            if (peer->lastTerminalTemplateSent != g_terminal_last_program) {
                peer->lastTerminalTemplateSent = g_terminal_last_program;
                remote_queue_frame(peer, 'T', g_terminal_last_program);
            }
        }
        g_terminal_template_dirty = false;

        const QByteArray snapshot = QJsonDocument(remote_build_snapshot()).toJson(QJsonDocument::Compact);
        if (snapshot != g_remote_last_snapshot) {
            g_remote_last_snapshot = snapshot;
            for (RemoteSocketState *peer : g_remote_client_peers) {
                if (peer && peer->handshakeComplete)
                    remote_queue_frame(peer, 'S', snapshot);
            }
        }
        for (RemoteSocketState *peer : g_remote_client_peers) {
            remote_flush_pending_mouse(peer);
            remote_flush(peer);
        }
    } else if (g_remote_cursor_marker) {
        g_remote_cursor_marker->hide();
    }
}

void remote_client_start()
{
    if (g_remote_listener != INVALID_SOCKET || !g_app)
        return;
    if (g_remote_application_connection_id.isEmpty())
        g_remote_application_connection_id = remote_new_id();
    if (!remote_ensure_winsock()) {
        if (g_remote_listener_label)
            g_remote_listener_label->setText(QStringLiteral("NET: Winsock-Fehler"));
        return;
    }

    SOCKET listener = ::socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
    if (listener == INVALID_SOCKET)
        return;
    BOOL exclusive = TRUE;
    ::setsockopt(listener, SOL_SOCKET, SO_EXCLUSIVEADDRUSE, reinterpret_cast<const char *>(&exclusive), sizeof(exclusive));

    QString bindAddress = qEnvironmentVariable("D64_REMOTE_BIND").trimmed();
    if (bindAddress.isEmpty())
        bindAddress = QStringLiteral("127.0.0.1");

    quint16 firstPort = remote_default_port();
    bool envOk = false;
    const int envPort = qEnvironmentVariableIntValue("D64_REMOTE_PORT", &envOk);
    if (envOk && envPort > 0 && envPort <= 65535)
        firstPort = static_cast<quint16>(envPort);

    in_addr bindIp;
    const QByteArray bindBytes = bindAddress.toLatin1();
    if (::inet_pton(AF_INET, bindBytes.constData(), &bindIp) != 1) {
        bindAddress = QStringLiteral("127.0.0.1");
        ::inet_pton(AF_INET, "127.0.0.1", &bindIp);
    }

    remote_set_nonblocking(listener);
    quint16 boundPort = 0;
    for (int attempt = 0; attempt < 64; ++attempt) {
        const quint16 candidate = static_cast<quint16>(firstPort + attempt);
        sockaddr_in address;
        ZeroMemory(&address, sizeof(address));
        address.sin_family = AF_INET;
        address.sin_addr = bindIp;
        address.sin_port = ::htons(candidate);
        if (::bind(listener, reinterpret_cast<const sockaddr *>(&address), sizeof(address)) == 0) {
            boundPort = candidate;
            break;
        }
    }
    if (!boundPort || ::listen(listener, SOMAXCONN) != 0) {
        remote_close_socket(listener);
        if (g_remote_listener_label)
            g_remote_listener_label->setText(QStringLiteral("NET: Port belegt"));
        return;
    }

    g_remote_listener = listener;
    g_remote_listener_port = boundPort;
    g_remote_listener_address = bindAddress;
    if (g_remote_listener_label) {
        g_remote_listener_label->setText(
            QStringLiteral("NET %1:%2  CID %3")
                .arg(bindAddress)
                .arg(boundPort)
                .arg(g_remote_application_connection_id.left(8))
        );
        g_remote_listener_label->setToolTip(QStringLiteral(
            "Stage 46 CS-Listener: Zeichenraster/Menue/Dialog-Geometrie und bidirektionale Maus. "
            "ConnectionID/SessionID verhindern Crosslink-Zuordnung."
        ));
    }

    if (!g_remote_client_event_filter) {
        g_remote_client_event_filter = new RemoteClientEventFilter(g_app);
        g_app->installEventFilter(g_remote_client_event_filter);
    }

    g_remote_client_timer = new QTimer(g_app);
    // Legacy regression marker: g_remote_client_timer->setInterval(50);
    g_remote_client_timer->setInterval(16);
    QObject::connect(g_remote_client_timer, &QTimer::timeout, []() { remote_client_poll(); });
    g_remote_client_timer->start();
}

void remote_server_close_dialog();

void remote_client_stop()
{
    remote_server_close_dialog();
    if (g_remote_client_timer) {
        g_remote_client_timer->stop();
        delete g_remote_client_timer;
        g_remote_client_timer = nullptr;
    }
    if (g_remote_client_event_filter && g_app) {
        g_app->removeEventFilter(g_remote_client_event_filter);
        delete g_remote_client_event_filter;
        g_remote_client_event_filter = nullptr;
    }
    for (RemoteSocketState *peer : g_remote_client_peers) {
        if (!peer)
            continue;
        remote_close_socket(peer->socket);
        delete peer;
    }
    g_remote_client_peers.clear();
    remote_close_socket(g_remote_listener);
    g_remote_listener_port = 0;
    g_remote_listener_address.clear();
    g_remote_last_snapshot.clear();
    g_terminal_last_program.clear();
    g_terminal_template_dirty = true;
    g_terminal_object_ids.clear();
    g_terminal_id_objects.clear();
    g_terminal_next_component_id = 100;
    if (g_remote_cursor_marker)
        g_remote_cursor_marker->hide();
    D64WorkstationSetServerClientCount(0);
    if (g_winsock_started) {
        ::WSACleanup();
        g_winsock_started = false;
    }
}

class RemotePreviewWidget final : public QWidget
{
public:
    explicit RemotePreviewWidget(QWidget *parent = nullptr)
        : QWidget(parent)
    {
        setMouseTracking(true);
        setMinimumSize(640, 360);
        setFocusPolicy(Qt::StrongFocus);
    }

    void setSnapshot(const QJsonObject &snapshot)
    {
        m_snapshot = snapshot;
        // Ein vom Server selbst ausgefuehrter Drag wird lokal sofort in
        // Rasterzellen dargestellt. Ein eventuell noch aelterer Client-
        // Snapshot darf diese optimistische Position waehrend gedrueckter
        // Maustaste nicht kurz zurueckspringen lassen.
        if (m_serverDrag.active)
            applyDragPosition(m_serverDrag);
        updateGeometry();
        update();
    }

    void setTerminalProgram(const QByteArray &program)
    {
        m_terminalProgram = program;
        m_terminalComponents.clear();
        const QStringList lines = QString::fromUtf8(program).split(QLatin1Char('\n'));
        for (const QString &line : lines) {
            TerminalComponentRecord record;
            if (terminal_parse_record_line(line, &record))
                m_terminalComponents.insert(record.componentId, record);
        }
        updateGeometry();
        update();
    }

    void applyTerminalRpc(const QByteArray &payload)
    {
        const QStringList parts = QString::fromUtf8(payload).split(QLatin1Char('_'));
        if (parts.size() != 6 || parts.at(0) != QStringLiteral("P"))
            return;
        bool ok = false;
        const quint32 componentId = parts.at(3).toUInt(&ok);
        if (!ok)
            return;
        const QString propertyName = terminal_unescape(parts.at(4));
        const QString propertyValue = terminal_unescape(parts.at(5));
        if (propertyName != QStringLiteral("TEXT")
            && propertyName != QStringLiteral("CHECKED"))
            return;

        QJsonArray windows = m_snapshot.value(QStringLiteral("windows")).toArray();
        for (int wi = 0; wi < windows.size(); ++wi) {
            QJsonObject window = windows.at(wi).toObject();
            QJsonArray controls = window.value(QStringLiteral("controls")).toArray();
            bool changed = false;
            for (int ci = 0; ci < controls.size(); ++ci) {
                QJsonObject control = controls.at(ci).toObject();
                if (static_cast<quint32>(control.value(QStringLiteral("componentId")).toInt()) != componentId)
                    continue;
                if (propertyName == QStringLiteral("TEXT"))
                    control.insert(QStringLiteral("text"), propertyValue);
                else if (propertyName == QStringLiteral("CHECKED"))
                    control.insert(QStringLiteral("checked"), propertyValue == QStringLiteral("1"));
                controls.replace(ci, control);
                changed = true;
                break;
            }
            if (changed) {
                window.insert(QStringLiteral("controls"), controls);
                windows.replace(wi, window);
                m_snapshot.insert(QStringLiteral("windows"), windows);
                break;
            }
        }
        update();
    }

    void setPeerMouse(const QJsonObject &mouse)
    {
        m_peerMouse = mouse;
        // Client -> Server: dieselben absoluten Zellereignisse koennen die
        // sichtbare Dialogposition bereits vor dem naechsten Vollsnapshot
        // aktualisieren. Der folgende Snapshot bestaetigt den Zustand.
        updateDragPrediction(m_peerDrag, mouse);
        update();
    }

    void setZoomPointSize(int pointSize)
    {
        m_zoomPointSize = qBound(DBASE_FONT_MIN_PT, pointSize, DBASE_FONT_MAX_PT);
        updateGeometry();
        update();
    }

    void setCommandSender(const std::function<void(const QJsonObject &)> &sender)
    {
        m_sender = sender;
    }

    QSize preferredCanvasSize() const
    {
        const int columns = qMax(1, m_snapshot.value(QStringLiteral("gridColumns")).toInt(D64_REMOTE_DEFAULT_COLUMNS));
        const int rows = qMax(1, m_snapshot.value(QStringLiteral("gridRows")).toInt(D64_REMOTE_DEFAULT_ROWS));
        QFont font(choose_console_font_family(), m_zoomPointSize);
        font.setStyleHint(QFont::Monospace);
        font.setFixedPitch(true);
        const QFontMetrics fm(font, this);
        return QSize(
            qMax(1, fm.horizontalAdvance(QLatin1Char('M'))) * columns,
            qMax(1, fm.height()) * rows
        );
    }

protected:
    void paintEvent(QPaintEvent *) override
    {
        QPainter painter(this);
        QColor consoleBackground(m_snapshot.value(QStringLiteral("consoleBackground")).toString());
        if (!consoleBackground.isValid())
            consoleBackground = QColor(0, 0, 0);
        painter.fillRect(rect(), consoleBackground);

        const int columns = qMax(1, m_snapshot.value(QStringLiteral("gridColumns")).toInt(D64_REMOTE_DEFAULT_COLUMNS));
        const int rows = qMax(1, m_snapshot.value(QStringLiteral("gridRows")).toInt(D64_REMOTE_DEFAULT_ROWS));
        QFont font(choose_console_font_family(), m_zoomPointSize);
        font.setStyleHint(QFont::Monospace);
        font.setFixedPitch(true);
        const QFontMetrics fm(font, this);
        m_cellWidth = qMax(1, fm.horizontalAdvance(QLatin1Char('M')));
        m_cellHeight = qMax(1, fm.height());

        const qreal naturalWidth = qreal(m_cellWidth * columns);
        const qreal naturalHeight = qreal(m_cellHeight * rows);
        m_scale = qMax<qreal>(0.01, qMin(
            qreal(qMax(1, width())) / qMax<qreal>(1.0, naturalWidth),
            qreal(qMax(1, height())) / qMax<qreal>(1.0, naturalHeight)
        ));
        m_scale = qMin<qreal>(1.0, m_scale);
        m_offset = QPointF(
            (width() - naturalWidth * m_scale) / 2.0,
            (height() - naturalHeight * m_scale) / 2.0
        );

        painter.save();
        painter.translate(m_offset);
        painter.scale(m_scale, m_scale);
        painter.setFont(font);
        QColor outputForeground(m_snapshot.value(QStringLiteral("outputForeground")).toString());
        if (!outputForeground.isValid())
            outputForeground = QColor(169, 169, 169);
        painter.setPen(outputForeground);

        // TBackground ist der erste sichtbare RPC-Baustein. SCREEN CLEAR 0xb0
        // wird dadurch auf beiden Seiten aus demselben CP437-Zeichen und
        // denselben Vorder-/Hintergrundfarben aufgebaut.
        for (auto it = m_terminalComponents.constBegin(); it != m_terminalComponents.constEnd(); ++it) {
            const TerminalComponentRecord &component = it.value();
            if (component.typeCode != TerminalTBackground)
                continue;
            const QRect backgroundRect(
                component.column * m_cellWidth,
                component.row * m_cellHeight,
                component.columns * m_cellWidth,
                component.rows * m_cellHeight
            );
            painter.fillRect(backgroundRect, component.background);
            bool ok = false;
            const int charCode = terminal_payload_value(component.payload, QStringLiteral("CHAR")).toInt(&ok, 16);
            const QChar glyph = ok ? cp437_character(charCode) : QLatin1Char(' ');
            if (!glyph.isNull() && glyph != QLatin1Char(' ')) {
                painter.setPen(component.foreground);
                const QString rowText(component.columns, glyph);
                for (int y = 0; y < component.rows; ++y) {
                    const int baseline = (component.row + y + 1) * m_cellHeight - fm.descent();
                    painter.drawText(component.column * m_cellWidth, baseline, rowText);
                }
            }
            break;
        }
        painter.setPen(outputForeground);

        // Stage 45: Der eigentliche Arbeitsbereich wird ausschließlich aus den
        // vom Client gelieferten Zeichenzeilen aufgebaut. Es werden weder
        // Client-Pixel noch serverseitig rekonstruierte Rahmen uebertragen.
        const QJsonArray grid = m_snapshot.value(QStringLiteral("grid")).toArray();
        for (int row = 0; row < qMin(rows, grid.size()); ++row) {
            const int baseline = (row + 1) * m_cellHeight - fm.descent();
            painter.drawText(0, baseline, grid.at(row).toString());
        }

        // Dialoge und sichtbare Popup-Menues bleiben reine Char-/Zell-Daten.
        // Stage 46 rendert die vom Client mitgelieferten semantischen Controls
        // lokal mit derselben dBase-Chrome: grauer Dialog, gruene Eingabefelder,
        // graue Buttons und identische Rahmenfarben. Es werden keine Pixel
        // uebertragen; nur Rolle/Text/Zellrechteck kommen ueber TCP.
        const QJsonArray windows = m_snapshot.value(QStringLiteral("windows")).toArray();
        for (const QJsonValue &value : windows) {
            const QJsonObject window = value.toObject();
            const int column = window.value(QStringLiteral("charColumn")).toInt();
            const int row = window.value(QStringLiteral("charRow")).toInt();
            const int windowColumns = qMax(1, window.value(QStringLiteral("charColumns")).toInt());
            const int windowRows = qMax(1, window.value(QStringLiteral("charRows")).toInt());
            const QJsonArray charLines = window.value(QStringLiteral("charLines")).toArray();
            const bool isMenu = window.value(QStringLiteral("kind")).toString() == QStringLiteral("menu");

            if (isMenu) {
                const QRect menuRect(
                    column * m_cellWidth,
                    row * m_cellHeight,
                    windowColumns * m_cellWidth,
                    windowRows * m_cellHeight
                );
                painter.fillRect(menuRect, QColor(144, 144, 144));
                painter.setPen(QColor(0, 0, 0));
                for (int i = 0; i < charLines.size(); ++i) {
                    const int baseline = (row + i + 1) * m_cellHeight - fm.descent();
                    painter.drawText(column * m_cellWidth, baseline, charLines.at(i).toString());
                }
                continue;
            }

            const QString dialogStyle = window.value(QStringLiteral("dialogStyle")).toString();
            const QColor dialogBackground =
                dialogStyle == QStringLiteral("warning")
                    ? QColor(255, 0, 0)
                    : QColor(144, 144, 144);
            const QColor dialogForeground(0, 0, 0);
            const QColor frameColor = window.value(QStringLiteral("moving")).toBool()
                ? QColor(255, 216, 0)
                : QColor(255, 255, 255);
            const QRect dialogRect(
                column * m_cellWidth,
                row * m_cellHeight,
                windowColumns * m_cellWidth,
                windowRows * m_cellHeight
            );
            painter.fillRect(dialogRect, dialogBackground);

            // Erst den kompletten vom Client erzeugten Char-Canvas zeichnen.
            // Rand-/Titelzeile verwenden exakt die Client-Rahmenfarbe.
            for (int i = 0; i < charLines.size(); ++i) {
                const QString line = charLines.at(i).toString();
                const int baseline = (row + i + 1) * m_cellHeight - fm.descent();
                for (int j = 0; j < line.size(); ++j) {
                    const bool frameCell =
                        i == 0 || i == charLines.size() - 1
                        || j == 0 || j == line.size() - 1;
                    painter.setPen(frameCell ? frameColor : dialogForeground);
                    painter.drawText(
                        (column + j) * m_cellWidth,
                        baseline,
                        QString(1, line.at(j))
                    );
                }
            }

            // Controls werden aus Zellgeometrie und Text nachgebildet. Die
            // Farben entsprechen den Client-QSS-Werten; keine Geometrie in
            // Pixeln ist Teil des Netzwerkprotokolls.
            const QJsonArray controls = window.value(QStringLiteral("controls")).toArray();
            for (const QJsonValue &controlValue : controls) {
                const QJsonObject control = controlValue.toObject();
                const QString role = control.value(QStringLiteral("role")).toString();
                const int cc = control.value(QStringLiteral("column")).toInt();
                const int cr = control.value(QStringLiteral("row")).toInt();
                const int cwCells = qMax(1, control.value(QStringLiteral("columns")).toInt(1));
                const int chCells = qMax(1, control.value(QStringLiteral("rows")).toInt(1));
                const QRect controlRect(
                    (column + cc) * m_cellWidth,
                    (row + cr) * m_cellHeight,
                    cwCells * m_cellWidth,
                    chCells * m_cellHeight
                );
                const QString text = control.value(QStringLiteral("text")).toString();

                if (role == QStringLiteral("input")) {
                    painter.fillRect(controlRect, QColor(0, 128, 0));
                    QPen borderPen(
                        control.value(QStringLiteral("focused")).toBool()
                            ? QColor(255, 255, 0)
                            : QColor(255, 255, 255)
                    );
                    borderPen.setWidth(1);
                    painter.setPen(borderPen);
                    painter.drawRect(controlRect.adjusted(0, 0, -1, -1));
                    painter.setPen(QColor(255, 255, 255));
                    painter.drawText(
                        controlRect.adjusted(2, 0, -2, 0),
                        Qt::AlignLeft | Qt::AlignVCenter,
                        text
                    );
                } else if (role == QStringLiteral("button")) {
                    painter.fillRect(controlRect, QColor(144, 144, 144));
                    QPen borderPen(QColor(255, 255, 255));
                    borderPen.setWidth(1);
                    painter.setPen(borderPen);
                    painter.drawRect(controlRect.adjusted(0, 0, -1, -1));
                    painter.setPen(QColor(0, 0, 0));
                    painter.drawText(controlRect, Qt::AlignCenter, text);
                } else if (role == QStringLiteral("checkbox")) {
                    painter.fillRect(controlRect, dialogBackground);
                    painter.setPen(QColor(0, 0, 0));
                    const QString mark = control.value(QStringLiteral("checked")).toBool()
                        ? QStringLiteral("[X] ") : QStringLiteral("[ ] ");
                    painter.drawText(controlRect, Qt::AlignLeft | Qt::AlignVCenter, mark + text);
                } else if (role == QStringLiteral("label")) {
                    painter.setPen(QColor(0, 0, 0));
                    painter.drawText(controlRect, Qt::AlignLeft | Qt::AlignVCenter, text);
                }
            }
        }

        drawMouseMarker(painter, m_peerMouse, QColor(0, 255, 255));
        drawMouseMarker(painter, m_serverMouse, QColor(255, 255, 0));
        painter.restore();
    }

    void mouseMoveEvent(QMouseEvent *event) override
    {
        sendMouse(QStringLiteral("move"), event);
    }

    void mousePressEvent(QMouseEvent *event) override
    {
        if (event) {
            setFocus(Qt::MouseFocusReason);
            selectTerminalInputAt(event->pos());
        }
        sendMouse(QStringLiteral("press"), event);
    }

    void mouseReleaseEvent(QMouseEvent *event) override
    {
        sendMouse(QStringLiteral("release"), event);
    }

    void mouseDoubleClickEvent(QMouseEvent *event) override
    {
        sendMouse(QStringLiteral("double"), event);
    }

    void keyPressEvent(QKeyEvent *event) override
    {
        if (!event || !m_sender || !m_focusedTerminalComponentId) {
            QWidget::keyPressEvent(event);
            return;
        }
        QJsonObject command;
        command.insert(QStringLiteral("type"), QStringLiteral("terminalKey"));
        command.insert(QStringLiteral("componentId"), static_cast<int>(m_focusedTerminalComponentId));
        command.insert(QStringLiteral("key"), event->key());
        command.insert(QStringLiteral("modifiers"), static_cast<int>(event->modifiers()));
        command.insert(QStringLiteral("text"), event->text());
        m_sender(command);
        event->setAccepted(true);
    }

private:
    void selectTerminalInputAt(const QPoint &position)
    {
        m_focusedTerminalComponentId = 0;
        if (m_snapshot.isEmpty() || m_scale <= 0.0 || m_cellWidth <= 0 || m_cellHeight <= 0)
            return;
        const QPointF logical = (QPointF(position) - m_offset) / m_scale;
        const int column = static_cast<int>(std::floor(logical.x() / qreal(m_cellWidth)));
        const int row = static_cast<int>(std::floor(logical.y() / qreal(m_cellHeight)));
        const QJsonArray windows = m_snapshot.value(QStringLiteral("windows")).toArray();
        for (int wi = windows.size() - 1; wi >= 0; --wi) {
            const QJsonObject window = windows.at(wi).toObject();
            const int wc = window.value(QStringLiteral("charColumn")).toInt();
            const int wr = window.value(QStringLiteral("charRow")).toInt();
            const QJsonArray controls = window.value(QStringLiteral("controls")).toArray();
            for (int ci = controls.size() - 1; ci >= 0; --ci) {
                const QJsonObject control = controls.at(ci).toObject();
                if (control.value(QStringLiteral("role")).toString() != QStringLiteral("input"))
                    continue;
                const int x = wc + control.value(QStringLiteral("column")).toInt();
                const int y = wr + control.value(QStringLiteral("row")).toInt();
                const int w = qMax(1, control.value(QStringLiteral("columns")).toInt(1));
                const int h = qMax(1, control.value(QStringLiteral("rows")).toInt(1));
                if (column >= x && column < x + w && row >= y && row < y + h) {
                    m_focusedTerminalComponentId = static_cast<quint32>(
                        control.value(QStringLiteral("componentId")).toInt()
                    );
                    return;
                }
            }
        }
    }

    struct DragPrediction {
        bool active = false;
        QString windowId;
        int pressColumn = 0;
        int pressRow = 0;
        int startColumn = 0;
        int startRow = 0;
        int lastColumn = 0;
        int lastRow = 0;
    };

    bool beginDragPrediction(DragPrediction &drag, const QJsonObject &mouse)
    {
        if (m_snapshot.isEmpty())
            return false;
        if (mouse.value(QStringLiteral("button")).toInt() != static_cast<int>(Qt::LeftButton))
            return false;

        const int column = mouse.value(QStringLiteral("column")).toInt();
        const int row = mouse.value(QStringLiteral("row")).toInt();
        const QJsonArray windows = m_snapshot.value(QStringLiteral("windows")).toArray();
        // Letztes Element liegt in der Snapshot-Reihenfolge optisch vorne.
        for (int i = windows.size() - 1; i >= 0; --i) {
            const QJsonObject window = windows.at(i).toObject();
            if (window.value(QStringLiteral("kind")).toString() != QStringLiteral("dialog"))
                continue;
            const int wc = window.value(QStringLiteral("charColumn")).toInt();
            const int wr = window.value(QStringLiteral("charRow")).toInt();
            const int ww = qMax(1, window.value(QStringLiteral("charColumns")).toInt());
            // Client-Dialoge beginnen den Drag ausschliesslich in der ersten
            // Zeichenzeile (Titlebar/Rahmen). Genau dieselbe Logik gilt hier.
            if (row != wr || column < wc || column >= wc + ww)
                continue;
            drag.active = true;
            drag.windowId = window.value(QStringLiteral("windowId")).toString();
            drag.pressColumn = column;
            drag.pressRow = row;
            drag.startColumn = wc;
            drag.startRow = wr;
            drag.lastColumn = column;
            drag.lastRow = row;
            return !drag.windowId.isEmpty();
        }
        return false;
    }

    void applyDragPosition(const DragPrediction &drag)
    {
        if (!drag.active || drag.windowId.isEmpty() || m_snapshot.isEmpty())
            return;
        const int columns = qMax(1, m_snapshot.value(QStringLiteral("gridColumns")).toInt(D64_REMOTE_DEFAULT_COLUMNS));
        const int rows = qMax(1, m_snapshot.value(QStringLiteral("gridRows")).toInt(D64_REMOTE_DEFAULT_ROWS));
        const int targetColumn = qBound(
            0,
            drag.startColumn + (drag.lastColumn - drag.pressColumn),
            qMax(0, columns - 2)
        );
        const int targetRow = qBound(
            0,
            drag.startRow + (drag.lastRow - drag.pressRow),
            qMax(0, rows - 1)
        );

        QJsonArray windows = m_snapshot.value(QStringLiteral("windows")).toArray();
        for (int i = 0; i < windows.size(); ++i) {
            QJsonObject window = windows.at(i).toObject();
            if (window.value(QStringLiteral("windowId")).toString() != drag.windowId)
                continue;
            window.insert(QStringLiteral("charColumn"), targetColumn);
            window.insert(QStringLiteral("charRow"), targetRow);
            window.insert(QStringLiteral("moving"), true);
            windows.replace(i, window);
            m_snapshot.insert(QStringLiteral("windows"), windows);
            break;
        }
    }

    void finishDragPrediction(DragPrediction &drag)
    {
        if (!drag.active)
            return;
        applyDragPosition(drag);
        drag = DragPrediction();
    }

    void updateDragPrediction(DragPrediction &drag, const QJsonObject &mouse)
    {
        const QString action = mouse.value(QStringLiteral("action")).toString();
        if (action == QStringLiteral("press")) {
            beginDragPrediction(drag, mouse);
            return;
        }
        if (!drag.active)
            return;

        drag.lastColumn = mouse.value(QStringLiteral("column")).toInt();
        drag.lastRow = mouse.value(QStringLiteral("row")).toInt();
        if (action == QStringLiteral("move")) {
            applyDragPosition(drag);
        } else if (action == QStringLiteral("release")) {
            finishDragPrediction(drag);
        }
    }

    void drawMouseMarker(QPainter &painter, const QJsonObject &mouse, const QColor &color)
    {
        if (mouse.isEmpty())
            return;
        const int column = mouse.value(QStringLiteral("column")).toInt();
        const int row = mouse.value(QStringLiteral("row")).toInt();
        const int subX = qBound(0, mouse.value(QStringLiteral("subX")).toInt(500), 999);
        const int subY = qBound(0, mouse.value(QStringLiteral("subY")).toInt(500), 999);
        const int x = column * m_cellWidth + (subX * m_cellWidth) / 1000;
        const int y = row * m_cellHeight + (subY * m_cellHeight) / 1000;
        QPen pen(color);
        pen.setWidth(2);
        painter.setPen(pen);
        painter.drawLine(x - 8, y, x + 8, y);
        painter.drawLine(x, y - 8, x, y + 8);
        painter.drawRect(x - 3, y - 3, 6, 6);
    }

    void sendMouse(const QString &action, QMouseEvent *event)
    {
        if (!event || !m_sender || m_snapshot.isEmpty() || m_scale <= 0.0 || m_cellWidth <= 0 || m_cellHeight <= 0)
            return;
        const QPointF logical = (QPointF(event->pos()) - m_offset) / m_scale;
        const int columns = qMax(1, m_snapshot.value(QStringLiteral("gridColumns")).toInt(D64_REMOTE_DEFAULT_COLUMNS));
        const int rows = qMax(1, m_snapshot.value(QStringLiteral("gridRows")).toInt(D64_REMOTE_DEFAULT_ROWS));
        const int column = static_cast<int>(std::floor(logical.x() / qreal(m_cellWidth)));
        const int row = static_cast<int>(std::floor(logical.y() / qreal(m_cellHeight)));
        if (column < 0 || row < 0 || column >= columns || row >= rows)
            return;
        const qreal withinX = logical.x() - column * m_cellWidth;
        const qreal withinY = logical.y() - row * m_cellHeight;

        QJsonObject command;
        command.insert(QStringLiteral("type"), QStringLiteral("mouse"));
        command.insert(QStringLiteral("source"), QStringLiteral("server"));
        command.insert(QStringLiteral("sequence"), static_cast<double>(++m_mouseSequence));
        command.insert(QStringLiteral("action"), action);
        command.insert(QStringLiteral("column"), column);
        command.insert(QStringLiteral("row"), row);
        command.insert(QStringLiteral("subX"), qBound(0, qRound(withinX * 1000.0 / qMax(1, m_cellWidth)), 999));
        command.insert(QStringLiteral("subY"), qBound(0, qRound(withinY * 1000.0 / qMax(1, m_cellHeight)), 999));
        command.insert(QStringLiteral("button"), static_cast<int>(event->button()));
        command.insert(QStringLiteral("buttons"), static_cast<int>(event->buttons()));
        m_serverMouse = command;
        updateDragPrediction(m_serverDrag, command);
        update();
        m_sender(command);
    }

    QJsonObject m_snapshot;
    QJsonObject m_peerMouse;
    QByteArray m_terminalProgram;
    QHash<quint32, TerminalComponentRecord> m_terminalComponents;
    quint32 m_focusedTerminalComponentId = 0;
    QJsonObject m_serverMouse;
    std::function<void(const QJsonObject &)> m_sender;
    int m_zoomPointSize = 10;
    int m_cellWidth = 8;
    int m_cellHeight = 16;
    qreal m_scale = 1.0;
    QPointF m_offset;
    quint64 m_mouseSequence = 0;
    DragPrediction m_peerDrag;
    DragPrediction m_serverDrag;
};

class ServerDialog final : public QDialog
{
public:
    explicit ServerDialog(QWidget *parent = nullptr)
        : QDialog(parent)
    {
        setObjectName(QStringLiteral("dbaseServerDialog"));
        setWindowTitle(QStringLiteral("D64 Workstation Server"));
        setWindowFlags(Qt::Dialog | Qt::WindowStaysOnTopHint);
        m_serverConnectionId = remote_new_id();
        m_fontPointSize = g_font_point_size;

        auto *root = new QVBoxLayout(this);
        root->setContentsMargins(0, 0, 0, 0);
        root->setSpacing(0);

        m_header = new QWidget(this);
        m_header->setObjectName(QStringLiteral("dbaseServerHeader"));
        auto *headerLayout = new QHBoxLayout(m_header);
        headerLayout->setContentsMargins(5, 3, 5, 0);
        headerLayout->setSpacing(3);
        m_zoomIn = make_zoom_button(true, m_header);
        m_zoomOut = make_zoom_button(false, m_header);
        headerLayout->addWidget(m_zoomIn, 0, Qt::AlignBottom);
        headerLayout->addWidget(m_zoomOut, 0, Qt::AlignBottom);
        headerLayout->addSpacing(4);
        m_tabBar = new QTabBar(m_header);
        m_tabBar->setObjectName(QStringLiteral("dbaseServerTabBar"));
        m_tabBar->setDrawBase(false);
        m_tabBar->setExpanding(false);
        m_tabBar->setMovable(false);
        m_tabBar->setUsesScrollButtons(true);
        m_tabBar->addTab(QStringLiteral("Verbindung"));
        headerLayout->addWidget(m_tabBar, 1, Qt::AlignBottom);
        root->addWidget(m_header, 0);

        m_frame = new QFrame(this);
        m_frame->setObjectName(QStringLiteral("dbaseServerFrame"));
        auto *frameLayout = new QVBoxLayout(m_frame);
        frameLayout->setContentsMargins(0, 0, 0, 0);
        frameLayout->setSpacing(0);
        root->addWidget(m_frame, 1);

        m_menuBar = new QMenuBar(m_frame);
        m_menuBar->setObjectName(QStringLiteral("dbaseServerMenu"));
        m_menuBar->setNativeMenuBar(false);
        frameLayout->addWidget(m_menuBar, 0);
        buildServerControlMenu();

        m_connectPanel = new QWidget(m_frame);
        m_connectPanel->setObjectName(QStringLiteral("dbaseServerConnectPanel"));
        auto *connectRow = new QHBoxLayout(m_connectPanel);
        connectRow->setContentsMargins(5, 3, 5, 3);
        connectRow->setSpacing(4);
        connectRow->addWidget(new QLabel(QStringLiteral("IPv4:"), m_connectPanel));
        m_ip = new QLineEdit(QStringLiteral("127.0.0.1"), m_connectPanel);
        m_ip->setMaximumWidth(150);
        connectRow->addWidget(m_ip);
        connectRow->addWidget(new QLabel(QStringLiteral("Port:"), m_connectPanel));
        m_port = new QLineEdit(m_connectPanel);
        m_port->setMaximumWidth(80);
        m_port->setPlaceholderText(QStringLiteral("46xxx"));
        connectRow->addWidget(m_port);
        m_connect = new QPushButton(QStringLiteral("Verbinden"), m_connectPanel);
        m_disconnect = new QPushButton(QStringLiteral("Trennen"), m_connectPanel);
        connectRow->addWidget(m_connect);
        connectRow->addWidget(m_disconnect);
        connectRow->addStretch(1);
        frameLayout->addWidget(m_connectPanel, 0);

        m_preview = new RemotePreviewWidget(m_frame);
        m_preview->setZoomPointSize(m_fontPointSize);
        frameLayout->addWidget(m_preview, 1);
        m_preview->setCommandSender([this](const QJsonObject &command) {
            sendToSelected(command);
        });

        m_statusBar = new QStatusBar(m_frame);
        m_statusBar->setObjectName(QStringLiteral("dbaseServerStatusBar"));
        m_statusBar->setSizeGripEnabled(false);
        m_status = new QLabel(QStringLiteral("Kein Client verbunden."), m_statusBar);
        m_status->setObjectName(QStringLiteral("dbaseServerStatus"));
        m_statusBar->addWidget(m_status, 1);
        frameLayout->addWidget(m_statusBar, 0);

        QObject::connect(m_connect, &QPushButton::clicked, [this]() { connectClient(); });
        QObject::connect(m_disconnect, &QPushButton::clicked, [this]() { disconnectSelected(); });
        QObject::connect(m_zoomIn, &QToolButton::clicked, [this]() { changeServerFontSize(+1); });
        QObject::connect(m_zoomOut, &QToolButton::clicked, [this]() { changeServerFontSize(-1); });
        QObject::connect(m_tabBar, &QTabBar::currentChanged, [this](int index) {
            if (index <= 0) {
                m_selected = nullptr;
                m_preview->setSnapshot(QJsonObject());
                m_preview->setTerminalProgram(QByteArray());
                m_preview->setPeerMouse(QJsonObject());
                m_connectPanel->show();
                syncClientChrome();
                updateStatus();
            } else {
                m_connectPanel->hide();
                selectClient(index - 1);
            }
        });

        applyServerStyleAndFont();
        resizeForCurrentGrid();

        m_timer = new QTimer(this);
        m_timer->setInterval(16);
        QObject::connect(m_timer, &QTimer::timeout, [this]() { poll(); });
        m_timer->start();
    }

    ~ServerDialog() override
    {
        disconnectAll();
    }

    void selectClient(int index)
    {
        QVector<RemoteSocketState *> connected = connectedSessions();
        if (index < 0 || index >= connected.size()) {
            m_selected = nullptr;
            m_preview->setSnapshot(QJsonObject());
            m_preview->setTerminalProgram(QByteArray());
            m_preview->setPeerMouse(QJsonObject());
            updateStatus();
            return;
        }
        m_selected = connected.at(index);
        const int tabIndex = index + 1;
        if (m_tabBar->currentIndex() != tabIndex)
            m_tabBar->setCurrentIndex(tabIndex);
        m_connectPanel->hide();
        m_preview->setSnapshot(m_selected->snapshot);
        m_preview->setTerminalProgram(m_selected->terminalTemplate);
        m_preview->setPeerMouse(m_selected->peerMouse);
        syncClientChrome();
        resizeForCurrentGrid();
        updateStatus();
    }

protected:
    void closeEvent(QCloseEvent *event) override
    {
        disconnectAll();
        QDialog::closeEvent(event);
    }

private:
    void clearMirroredStatus()
    {
        for (QLabel *label : m_mirroredStatusLabels) {
            if (!label)
                continue;
            m_statusBar->removeWidget(label);
            delete label;
        }
        m_mirroredStatusLabels.clear();
    }

    void buildServerControlMenu()
    {
        if (!m_menuBar)
            return;
        m_menuBar->clear();
        QMenu *serverMenu = new AsciiPopupMenu(QStringLiteral("Server"), m_menuBar);
        static_cast<AsciiPopupMenu *>(serverMenu)->setPointSize(m_fontPointSize);
        QAction *connectAction = serverMenu->addAction(QStringLiteral("Verbinden"));
        QAction *disconnectAction = serverMenu->addAction(QStringLiteral("Trennen"));
        m_menuBar->addMenu(serverMenu);
        QObject::connect(connectAction, &QAction::triggered, [this]() { connectClient(); });
        QObject::connect(disconnectAction, &QAction::triggered, [this]() { disconnectSelected(); });
    }

    void populateMirroredMenu(QMenu *parentMenu, const QJsonArray &children)
    {
        if (!parentMenu)
            return;
        for (const QJsonValue &value : children) {
            const QJsonObject item = value.toObject();
            if (!item.value(QStringLiteral("visible")).toBool(true))
                continue;
            if (item.value(QStringLiteral("separator")).toBool()) {
                parentMenu->addSeparator();
                continue;
            }
            const QString text = item.value(QStringLiteral("text")).toString();
            const QString path = item.value(QStringLiteral("path")).toString();
            const QJsonArray nested = item.value(QStringLiteral("children")).toArray();
            QAction *action = nullptr;
            if (!nested.isEmpty()) {
                AsciiPopupMenu *submenu = new AsciiPopupMenu(text, parentMenu);
                submenu->setPointSize(m_fontPointSize);
                parentMenu->addMenu(submenu);
                populateMirroredMenu(submenu, nested);
                action = submenu->menuAction();
            } else {
                action = parentMenu->addAction(text);
                const QString shortcut = item.value(QStringLiteral("shortcut")).toString();
                if (!shortcut.isEmpty())
                    action->setShortcut(QKeySequence(shortcut));
                QObject::connect(action, &QAction::triggered, [this, path]() {
                    QJsonObject command;
                    command.insert(QStringLiteral("type"), QStringLiteral("menu"));
                    command.insert(QStringLiteral("path"), path);
                    sendToSelected(command);
                });
            }
            if (action) {
                action->setEnabled(item.value(QStringLiteral("enabled")).toBool(true));
                action->setCheckable(item.value(QStringLiteral("checkable")).toBool(false));
                if (action->isCheckable())
                    action->setChecked(item.value(QStringLiteral("checked")).toBool(false));
            }
        }
    }

    void syncMirroredMenu(const QJsonObject &snapshot)
    {
        if (!m_menuBar)
            return;
        const QJsonArray tree = snapshot.value(QStringLiteral("menuTree")).toArray();
        const QByteArray signature = QJsonDocument(tree).toJson(QJsonDocument::Compact);
        if (signature == m_lastMenuSignature)
            return;
        m_lastMenuSignature = signature;
        m_menuBar->clear();
        for (const QJsonValue &value : tree) {
            const QJsonObject item = value.toObject();
            if (!item.value(QStringLiteral("visible")).toBool(true))
                continue;
            const QString text = item.value(QStringLiteral("text")).toString();
            const QString path = item.value(QStringLiteral("path")).toString();
            const QJsonArray children = item.value(QStringLiteral("children")).toArray();
            if (!children.isEmpty()) {
                AsciiPopupMenu *menu = new AsciiPopupMenu(text, m_menuBar);
                menu->setPointSize(m_fontPointSize);
                populateMirroredMenu(menu, children);
                QAction *container = m_menuBar->addMenu(menu);
                container->setEnabled(item.value(QStringLiteral("enabled")).toBool(true));
            } else if (item.value(QStringLiteral("separator")).toBool()) {
                continue;
            } else {
                QAction *action = m_menuBar->addAction(text);
                action->setEnabled(item.value(QStringLiteral("enabled")).toBool(true));
                QObject::connect(action, &QAction::triggered, [this, path]() {
                    QJsonObject command;
                    command.insert(QStringLiteral("type"), QStringLiteral("menu"));
                    command.insert(QStringLiteral("path"), path);
                    sendToSelected(command);
                });
            }
        }
    }

    void syncMirroredStatus(const QJsonObject &snapshot)
    {
        if (!m_statusBar || !m_status)
            return;
        const QJsonArray fields = snapshot.value(QStringLiteral("statusFields")).toArray();
        const QByteArray signature = QJsonDocument(fields).toJson(QJsonDocument::Compact);
        if (signature == m_lastStatusSignature)
            return;
        m_lastStatusSignature = signature;
        clearMirroredStatus();
        if (fields.isEmpty()) {
            m_status->show();
            m_status->setText(QString());
            return;
        }
        m_status->hide();
        for (const QJsonValue &value : fields) {
            const QJsonObject field = value.toObject();
            QLabel *label = new QLabel(field.value(QStringLiteral("text")).toString(), m_statusBar);
            label->setObjectName(QStringLiteral("dbaseServerMirroredStatus"));
            label->setFont(font());
            if (field.value(QStringLiteral("permanent")).toBool())
                m_statusBar->addPermanentWidget(label, 0);
            else
                m_statusBar->addWidget(label, 0);
            m_mirroredStatusLabels.append(label);
        }
    }

    void syncClientChrome()
    {
        if (!m_selected) {
            m_lastMenuSignature.clear();
            m_lastStatusSignature.clear();
            clearMirroredStatus();
            m_status->show();
            buildServerControlMenu();
            setWindowTitle(QStringLiteral("D64 Workstation Server"));
            return;
        }
        syncMirroredMenu(m_selected->snapshot);
        syncMirroredStatus(m_selected->snapshot);
        const QString mirroredTitle = m_selected->snapshot.value(QStringLiteral("title")).toString();
        if (!mirroredTitle.isEmpty())
            setWindowTitle(mirroredTitle);
        applyServerStyleAndFont();
    }

    QVector<RemoteSocketState *> connectedSessions() const
    {
        QVector<RemoteSocketState *> result;
        for (RemoteSocketState *session : m_sessions) {
            if (session && session->connected && session->handshakeComplete)
                result.append(session);
        }
        return result;
    }

    void applyServerStyleAndFont()
    {
        QFont fixedFont(choose_console_font_family(), m_fontPointSize);
        fixedFont.setStyleHint(QFont::Monospace);
        fixedFont.setFixedPitch(true);
        setFont(fixedFont);
        const QList<QWidget *> widgets = findChildren<QWidget *>();
        for (QWidget *widget : widgets) {
            if (widget)
                widget->setFont(fixedFont);
        }
        if (m_statusBar)
            m_statusBar->setFixedHeight(QFontMetrics(fixedFont, m_statusBar).height() + 4);

        QString borderColor = QStringLiteral("#ffffff");
        if (m_selected) {
            const QString mirrored = m_selected->snapshot.value(QStringLiteral("consoleBorderColor")).toString();
            QColor parsed(mirrored);
            if (parsed.isValid())
                borderColor = parsed.name(QColor::HexRgb);
        }
        setStyleSheet(QStringLiteral(
            "QDialog#dbaseServerDialog, QWidget#dbaseServerHeader { background-color:#000000; color:#a9a9a9; }"
            "QFrame#dbaseServerFrame { background-color:#000000; border:3px solid %1; }"
            "QTabBar { background-color:#000000; color:#a9a9a9; }"
            "QTabBar::tab { background-color:#111111; color:#a9a9a9; border:1px solid #505050; border-bottom:0px; padding:5px 14px; min-width:72px; }"
            "QTabBar::tab:selected { background-color:#000000; color:#c0c0c0; }"
            "QMenuBar { background-color:#909090; color:#000000; border:0px; padding:1px 3px; }"
            "QMenuBar::item { background-color:transparent; color:#000000; padding:3px 8px; }"
            "QMenuBar::item:selected, QMenuBar::item:pressed { background-color:#b0b0b0; color:#000000; }"
            "QMenu { background-color:#909090; color:#000000; border:0px; }"
            "QMenu::item { color:#000000; padding:4px 24px 4px 10px; }"
            "QMenu::item:selected { background-color:#b0b0b0; color:#000000; }"
            "QWidget#dbaseServerConnectPanel { background-color:#909090; color:#000000; }"
            "QWidget#dbaseServerConnectPanel QLabel { background-color:#909090; color:#000000; }"
            "QWidget#dbaseServerConnectPanel QLineEdit { background-color:#008000; color:#ffffff; border:1px solid #ffffff; padding:0px; margin:0px; }"
            "QWidget#dbaseServerConnectPanel QLineEdit:focus { border:1px solid #ffff00; }"
            "QPushButton { background-color:#909090; color:#000000; border:1px solid #ffffff; padding:2px 8px; }"
            "QPushButton:hover { background-color:#b0b0b0; }"
            "QPushButton:pressed { background-color:#707070; color:#ffffff; }"
            "QStatusBar#dbaseServerStatusBar { background-color:#909090; color:#000000; border-style:solid; border-color:%1; border-width:2px 0px 0px 0px; margin:0px; padding:0px; }"
            "QStatusBar#dbaseServerStatusBar QLabel { background-color:#909090; color:#000000; }"
        ).arg(borderColor));
    }

    void changeServerFontSize(int delta)
    {
        const int next = qBound(DBASE_FONT_MIN_PT, m_fontPointSize + delta, DBASE_FONT_MAX_PT);
        if (next == m_fontPointSize)
            return;
        m_fontPointSize = next;
        m_preview->setZoomPointSize(m_fontPointSize);
        applyServerStyleAndFont();
        resizeForCurrentGrid();
    }

    void resizeForCurrentGrid()
    {
        QSize preferred = m_preview->preferredCanvasSize();
        int widthValue = preferred.width() + 12;
        int heightValue = preferred.height() + 100;
#ifdef _WIN32
        const int maxWidth = qMax(700, GetSystemMetrics(SM_CXSCREEN) - 100);
        const int maxHeight = qMax(450, GetSystemMetrics(SM_CYSCREEN) - 100);
        widthValue = qBound(700, widthValue, maxWidth);
        heightValue = qBound(450, heightValue, maxHeight);
#else
        widthValue = qMax(700, widthValue);
        heightValue = qMax(450, heightValue);
#endif
        resize(widthValue, heightValue);
    }

    void refreshClientUi()
    {
        QVector<RemoteSocketState *> connected = connectedSessions();
        while (m_tabBar->count() > 1)
            m_tabBar->removeTab(1);
        for (int i = 0; i < connected.size(); ++i) {
            QString title = connected.at(i)->snapshot.value(QStringLiteral("title")).toString();
            if (title.isEmpty())
                title = connected.at(i)->peerAddress + QLatin1Char(':') + QString::number(connected.at(i)->peerPort);
            m_tabBar->addTab(QStringLiteral("SRV-PC %1 - %2").arg(i + 1).arg(title));
        }
        int selectedIndex = connected.indexOf(m_selected);
        if (selectedIndex < 0 && !connected.isEmpty()) {
            m_selected = connected.first();
            selectedIndex = 0;
        }
        if (selectedIndex >= 0) {
            m_tabBar->setCurrentIndex(selectedIndex + 1);
            m_connectPanel->hide();
            m_preview->setSnapshot(m_selected->snapshot);
            m_preview->setTerminalProgram(m_selected->terminalTemplate);
            m_preview->setPeerMouse(m_selected->peerMouse);
        } else {
            m_tabBar->setCurrentIndex(0);
            m_connectPanel->show();
            m_preview->setSnapshot(QJsonObject());
            m_preview->setTerminalProgram(QByteArray());
            m_preview->setPeerMouse(QJsonObject());
        }
        D64WorkstationSetServerClientCount(connected.size());
        syncClientChrome();
        resizeForCurrentGrid();
        updateStatus();
    }

    void updateStatus()
    {
        if (!m_selected) {
            m_status->show();
            m_status->setText(
                QStringLiteral("SERVER CID %1 | Kein Client verbunden | Default-Raster 80x25")
                    .arg(m_serverConnectionId.left(8))
            );
            m_statusBar->setToolTip(QString());
            return;
        }

        // Bei aktivem SRV-PC ist die sichtbare Statusleiste exakt die vom
        // Client gesendete Zeichenleiste. Verbindungsdaten liegen nur noch im
        // Tooltip und veraendern den gespiegelten Bildschirm nicht.
        const QString title = m_selected->snapshot.value(QStringLiteral("title")).toString();
        m_statusBar->setToolTip(
            QStringLiteral("%1 | ConnectionID %2 | SessionID %3 | %4:%5 | %6")
                .arg(title.isEmpty() ? QStringLiteral("Client") : title)
                .arg(m_selected->peerConnectionId)
                .arg(m_selected->peerSessionId.isEmpty() ? QStringLiteral("-") : m_selected->peerSessionId)
                .arg(m_selected->peerAddress)
                .arg(m_selected->peerPort)
                .arg(m_selected->peerSoftware)
        );
    }

    void connectClient()
    {
        if (!remote_ensure_winsock())
            return;
        const QString ip = m_ip->text().trimmed();
        bool ok = false;
        const int portValue = m_port->text().toInt(&ok);
        if (!ok || portValue < 1 || portValue > 65535) {
            m_status->setText(QStringLiteral("Ungueltiger IPv4-Port."));
            return;
        }
        in_addr ipv4;
        const QByteArray ipBytes = ip.toLatin1();
        if (::inet_pton(AF_INET, ipBytes.constData(), &ipv4) != 1) {
            m_status->setText(QStringLiteral("Ungueltige IPv4-Adresse."));
            return;
        }

        SOCKET socketValue = ::socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
        if (socketValue == INVALID_SOCKET) {
            m_status->setText(QStringLiteral("Socket konnte nicht erstellt werden."));
            return;
        }
        remote_set_nonblocking(socketValue);
        sockaddr_in address;
        ZeroMemory(&address, sizeof(address));
        address.sin_family = AF_INET;
        address.sin_addr = ipv4;
        address.sin_port = ::htons(static_cast<u_short>(portValue));
        const int result = ::connect(
            socketValue,
            reinterpret_cast<const sockaddr *>(&address),
            static_cast<int>(sizeof(address))
        );
        const int error = result == 0 ? 0 : ::WSAGetLastError();
        if (result != 0 && error != WSAEWOULDBLOCK && error != WSAEINPROGRESS && error != WSAEINVAL) {
            remote_close_socket(socketValue);
            m_status->setText(QStringLiteral("Verbindung fehlgeschlagen (%1).").arg(error));
            return;
        }

        RemoteSocketState *session = new RemoteSocketState();
        session->socket = socketValue;
        session->connecting = result != 0;
        session->connected = result == 0;
        session->localRole = QStringLiteral("server");
        session->localConnectionId = m_serverConnectionId;
        session->localSessionId.clear();
        session->peerAddress = ip;
        session->peerPort = static_cast<quint16>(portValue);
        m_sessions.append(session);
        if (session->connected) {
            remote_send_tcp_header(session);
            m_status->setText(QStringLiteral("TCP verbunden; D64CS-Header wird ausgetauscht ..."));
        } else {
            m_status->setText(QStringLiteral("Verbindung zu %1:%2 wird aufgebaut ...").arg(ip).arg(portValue));
        }
    }

    bool finishConnect(RemoteSocketState *session)
    {
        if (!session || !session->connecting)
            return session && session->connected;
        fd_set writeSet;
        fd_set exceptSet;
        FD_ZERO(&writeSet);
        FD_ZERO(&exceptSet);
        FD_SET(session->socket, &writeSet);
        FD_SET(session->socket, &exceptSet);
        timeval timeout = {0, 0};
        const int ready = ::select(0, nullptr, &writeSet, &exceptSet, &timeout);
        if (ready <= 0)
            return true;
        int socketError = 0;
        int length = sizeof(socketError);
        ::getsockopt(session->socket, SOL_SOCKET, SO_ERROR, reinterpret_cast<char *>(&socketError), &length);
        if (socketError != 0 || FD_ISSET(session->socket, &exceptSet))
            return false;
        session->connecting = false;
        session->connected = true;
        remote_send_tcp_header(session);
        return true;
    }

    bool acceptSnapshot(RemoteSocketState *session, const QJsonObject &snapshot)
    {
        if (!session || !session->handshakeComplete)
            return false;
        if (snapshot.value(QStringLiteral("connectionId")).toString() != session->peerConnectionId)
            return false;
        if (snapshot.value(QStringLiteral("sessionId")).toString() != session->peerSessionId)
            return false;
        return true;
    }

    bool acceptPeerMouse(RemoteSocketState *session, const QJsonObject &mouse)
    {
        if (!session || !session->handshakeComplete)
            return false;
        if (mouse.value(QStringLiteral("connectionId")).toString() != session->peerConnectionId ||
            mouse.value(QStringLiteral("sessionId")).toString() != session->peerSessionId)
            return false;
        const quint64 sequence = static_cast<quint64>(
            mouse.value(QStringLiteral("sequence")).toDouble()
        );
        if (sequence != 0 && sequence <= session->lastPeerMouseSequence)
            return false;
        if (sequence != 0)
            session->lastPeerMouseSequence = sequence;
        return true;
    }

    void poll()
    {
        bool changed = false;
        for (int i = m_sessions.size() - 1; i >= 0; --i) {
            RemoteSocketState *session = m_sessions.at(i);
            bool alive = finishConnect(session);
            if (alive && session->connected) {
                remote_send_tcp_header(session);
                alive = remote_receive(session);
            }
            char type = 0;
            QByteArray payload;
            while (alive && session->connected && remote_take_frame(session, &type, &payload)) {
                if (type == 'H') {
                    alive = remote_accept_tcp_header(session, payload);
                    changed = true;
                    continue;
                }
                if (!session->handshakeComplete)
                    continue;

                if (type == 'T') {
                    session->terminalTemplate = payload;
                    changed = true;
                    if (session == m_selected)
                        m_preview->setTerminalProgram(payload);
                    continue;
                }
                if (type == 'R') {
                    const QStringList parts = QString::fromUtf8(payload).split(QLatin1Char('_'));
                    const QString expectedSession = session->peerSessionId.isEmpty()
                        ? QStringLiteral("-") : session->peerSessionId;
                    if (parts.size() == 6
                        && parts.at(0) == QStringLiteral("P")
                        && parts.at(1) == session->peerConnectionId
                        && parts.at(2) == expectedSession
                        && session == m_selected)
                    {
                        m_preview->applyTerminalRpc(payload);
                    }
                    continue;
                }

                QJsonParseError error;
                const QJsonDocument doc = QJsonDocument::fromJson(payload, &error);
                if (error.error != QJsonParseError::NoError || !doc.isObject())
                    continue;
                const QJsonObject object = doc.object();

                if (type == 'I') {
                    if (object.value(QStringLiteral("connectionId")).toString() != session->peerConnectionId) {
                        alive = false;
                        break;
                    }
                    session->peerSessionId = object.value(QStringLiteral("sessionId")).toString();
                    changed = true;
                } else if (type == 'S') {
                    if (acceptSnapshot(session, object)) {
                        session->snapshot = object;
                        changed = true;
                        if (session == m_selected) {
                            m_preview->setSnapshot(session->snapshot);
                            syncClientChrome();
                            resizeForCurrentGrid();
                        }
                    }
                } else if (type == 'M') {
                    if (acceptPeerMouse(session, object)) {
                        session->peerMouse = object;
                        if (session == m_selected)
                            m_preview->setPeerMouse(session->peerMouse);
                    }
                }
            }
            if (alive && session->connected) {
                remote_flush_pending_mouse(session);
                alive = remote_flush(session);
            }
            if (!alive) {
                if (m_selected == session)
                    m_selected = nullptr;
                remote_close_socket(session->socket);
                delete session;
                m_sessions.removeAt(i);
                changed = true;
            }
        }
        if (changed)
            refreshClientUi();
    }

    void sendToSelected(QJsonObject command)
    {
        if (!m_selected || !m_selected->connected || !m_selected->handshakeComplete)
            return;
        command.insert(QStringLiteral("sourceConnectionId"), m_serverConnectionId);
        command.insert(QStringLiteral("targetConnectionId"), m_selected->peerConnectionId);
        command.insert(QStringLiteral("targetSessionId"), m_selected->peerSessionId);
        const QByteArray payload = QJsonDocument(command).toJson(QJsonDocument::Compact);
        const bool mouseMove =
            command.value(QStringLiteral("type")).toString() == QStringLiteral("mouse")
            && command.value(QStringLiteral("action")).toString() == QStringLiteral("move");
        remote_queue_mouse_payload(m_selected, 'C', payload, mouseMove);
        if (!mouseMove) {
            remote_flush_pending_mouse(m_selected);
            remote_flush(m_selected);
        }
    }

    void disconnectSelected()
    {
        if (!m_selected)
            return;
        const int index = m_sessions.indexOf(m_selected);
        if (index >= 0) {
            remote_close_socket(m_selected->socket);
            delete m_selected;
            m_sessions.removeAt(index);
        }
        m_selected = nullptr;
        refreshClientUi();
    }

    void disconnectAll()
    {
        for (RemoteSocketState *session : m_sessions) {
            if (!session)
                continue;
            remote_close_socket(session->socket);
            delete session;
        }
        m_sessions.clear();
        m_selected = nullptr;
        if (m_preview) {
            m_preview->setSnapshot(QJsonObject());
            m_preview->setTerminalProgram(QByteArray());
            m_preview->setPeerMouse(QJsonObject());
        }
        D64WorkstationSetServerClientCount(0);
    }

    QWidget *m_header = nullptr;
    QToolButton *m_zoomIn = nullptr;
    QToolButton *m_zoomOut = nullptr;
    QTabBar *m_tabBar = nullptr;
    QFrame *m_frame = nullptr;
    QMenuBar *m_menuBar = nullptr;
    QWidget *m_connectPanel = nullptr;
    QLineEdit *m_ip = nullptr;
    QLineEdit *m_port = nullptr;
    QPushButton *m_connect = nullptr;
    QPushButton *m_disconnect = nullptr;
    QStatusBar *m_statusBar = nullptr;
    QLabel *m_status = nullptr;
    QVector<QLabel *> m_mirroredStatusLabels;
    QByteArray m_lastMenuSignature;
    QByteArray m_lastStatusSignature;
    RemotePreviewWidget *m_preview = nullptr;
    QTimer *m_timer = nullptr;
    QVector<RemoteSocketState *> m_sessions;
    RemoteSocketState *m_selected = nullptr;
    QString m_serverConnectionId;
    int m_fontPointSize = 10;
};

void remote_server_close_dialog()
{
    if (!g_server_dialog)
        return;
    ServerDialog *dialog = g_server_dialog;
    g_server_dialog = nullptr;
    dialog->close();
    delete dialog;
}

void workstation_server_requested()
{
    if (!g_app || g_shutdown_requested || !D64WorkstationOwnsDesktop())
        return;
    QTimer::singleShot(0, []() {
        if (g_shutdown_requested)
            return;
        if (!g_server_dialog) {
            ServerDialog *dialog = new ServerDialog(nullptr);
            g_server_dialog = dialog;
            QObject::connect(dialog, &QDialog::finished, [dialog](int) {
                if (g_server_dialog == dialog)
                    g_server_dialog = nullptr;
                dialog->deleteLater();
            });
        }
        g_server_dialog->show();
        if (g_server_dialog->winId()) {
            SetPropW(
                reinterpret_cast<HWND>(g_server_dialog->winId()),
                L"D64Workstation.ToolWindow",
                reinterpret_cast<HANDLE>(1)
            );
        }
        g_server_dialog->raise();
        g_server_dialog->activateWindow();
    });
}

void workstation_server_client_requested(int clientIndex)
{
    if (!g_app || g_shutdown_requested)
        return;
    QTimer::singleShot(0, [clientIndex]() {
        if (g_shutdown_requested)
            return;
        if (!g_server_dialog) {
            workstation_server_requested();
            QTimer::singleShot(0, [clientIndex]() {
                if (g_server_dialog)
                    g_server_dialog->selectClient(clientIndex);
            });
            return;
        }
        g_server_dialog->show();
        if (g_server_dialog->winId()) {
            SetPropW(
                reinterpret_cast<HWND>(g_server_dialog->winId()),
                L"D64Workstation.ToolWindow",
                reinterpret_cast<HANDLE>(1)
            );
        }
        g_server_dialog->selectClient(clientIndex);
        g_server_dialog->raise();
        g_server_dialog->activateWindow();
    });
}


#endif // _WIN32

void show_btx_dialog()
{
    if (!g_window || g_shutdown_requested)
        return;

    if (g_btx_dialog) {
        g_btx_dialog->updateForGrid(true);
        g_btx_dialog->show();
        g_btx_dialog->raise();
        g_btx_dialog->activateWindow();
        return;
    }

    BtxDialog *dialog = new BtxDialog(g_window);
    g_btx_dialog = dialog;
    QObject::connect(dialog, &QDialog::finished, [dialog](int) {
        if (g_btx_dialog == dialog)
            g_btx_dialog = nullptr;
        dialog->deleteLater();
    });
    dialog->show();
    dialog->raise();
    dialog->activateWindow();
}

bool confirm_runtime_exit()
{
    if (!g_app || g_shutdown_requested)
        return true;

    QDialog dialog(nullptr);
    dialog.setObjectName(QStringLiteral("dbaseExitConfirmDialog"));
    dialog.setWindowTitle(QStringLiteral("Beenden"));
    dialog.setWindowFlags(
        Qt::Dialog |
        Qt::FramelessWindowHint |
        Qt::WindowStaysOnTopHint
    );
    dialog.setWindowModality(Qt::ApplicationModal);

    const QFont uiFont = current_console_grid_font();
    dialog.setFont(uiFont);
    const QFontMetrics fm(
        uiFont,
        g_console && g_console->viewport()
            ? static_cast<const QPaintDevice *>(g_console->viewport())
            : static_cast<const QPaintDevice *>(&dialog)
    );
    const int cw = qMax(1, fm.horizontalAdvance(QLatin1Char('M')));
    const int ch = qMax(1, fm.lineSpacing());
    dialog.setFixedSize(46 * cw, 7 * ch);
    dialog.setStyleSheet(QStringLiteral(
        "QDialog#dbaseExitConfirmDialog { background-color: #909090; border: 2px solid #ffffff; }"
        "QLabel { color: #000000; background: transparent; }"
        "QPushButton { background-color: #909090; color: #000000; border: 1px solid #ffffff; padding: 2px 12px; }"
        "QPushButton:focus { border: 1px solid #ffff00; }"
    ));

    auto *layout = new QVBoxLayout(&dialog);
    layout->setContentsMargins(cw, ch, cw, ch);
    layout->setSpacing(qMax(1, ch / 2));

    auto *question = new QLabel(
        QStringLiteral("Moechten Sie die Anwendung schliessen?"),
        &dialog
    );
    question->setAlignment(Qt::AlignCenter);
    layout->addWidget(question, 1);

    auto *buttons = new QHBoxLayout();
    buttons->addStretch(1);
    auto *yes = new QPushButton(QStringLiteral("JA"), &dialog);
    auto *no = new QPushButton(QStringLiteral("NEIN"), &dialog);
    no->setDefault(true);
    buttons->addWidget(yes);
    buttons->addSpacing(cw);
    buttons->addWidget(no);
    buttons->addStretch(1);
    layout->addLayout(buttons);

    QObject::connect(yes, &QPushButton::clicked, &dialog, &QDialog::accept);
    QObject::connect(no, &QPushButton::clicked, &dialog, &QDialog::reject);

    if (g_window) {
        dialog.move(
            g_window->geometry().center() -
            QPoint(dialog.width() / 2, dialog.height() / 2)
        );
    }
    no->setFocus(Qt::OtherFocusReason);
    return dialog.exec() == QDialog::Accepted;
}

void workstation_exit_requested()
{
    QTimer::singleShot(0, []() {
        if (g_shutdown_requested || g_exit_confirmation_open)
            return;

        g_exit_confirmation_open = true;
        const bool accepted = confirm_runtime_exit();
        g_exit_confirmation_open = false;
        if (!accepted)
            return;

        g_exit_authorized = true;
        if (g_window)
            g_window->close();
        else
            request_runtime_shutdown();
    });
}

void launch_btx_executable()
{
    if (g_shutdown_requested)
        return;

    QString path = QDir(QCoreApplication::applicationDirPath()).filePath(
        QStringLiteral("BTX.exe")
    );
    if (!QFileInfo::exists(path)) {
        const QString currentCandidate = QDir::current().filePath(
            QStringLiteral("BTX.exe")
        );
        if (QFileInfo::exists(currentCandidate))
            path = currentCandidate;
    }

    if (!QFileInfo::exists(path)) {
        show_runtime_warning(QStringLiteral("BTX.exe wurde nicht gefunden."));
        return;
    }

#ifdef _WIN32
    const std::wstring exe = QDir::toNativeSeparators(path).toStdWString();
    const std::wstring cwd = QDir::toNativeSeparators(
        QFileInfo(path).absolutePath()
    ).toStdWString();
    if (!D64WorkstationLaunchProgram(exe.c_str(), cwd.c_str()))
        show_runtime_warning(QStringLiteral("BTX.exe konnte nicht gestartet werden."));
#else
    if (!QProcess::startDetached(path, QStringList(), QFileInfo(path).absolutePath()))
        show_runtime_warning(QStringLiteral("BTX.exe konnte nicht gestartet werden."));
#endif
}

void workstation_btx_requested()
{
    QTimer::singleShot(0, []() {
        launch_btx_executable();
    });
}

void workstation_db_requested()
{
    QTimer::singleShot(0, []() {
        if (!g_window || g_shutdown_requested)
            return;

        if (!g_window->isVisible()) {
            // Stage 42: fuer die Rasterkorrektur kurz logisch anzeigen, aber
            // noch nicht auf dem sichtbaren Workstation-Desktop zeichnen.
            g_window->setAttribute(Qt::WA_DontShowOnScreen, true);
            g_window->show();
            enforce_console_80x25_grid();
            if (g_app)
                g_app->processEvents(QEventLoop::ExcludeUserInputEvents);
            g_window->hide();
            g_window->setAttribute(Qt::WA_DontShowOnScreen, false);
            g_window->show();
        }

        g_owner_restore_activated_window = false;
        restore_owner_application_windows();
        if (!g_owner_restore_activated_window) {
            g_window->raise();
            g_window->activateWindow();
        }
        if (g_app)
            g_app->processEvents();
    });
}

void show_runtime_warning(const QString &message)
{
    if (!g_window || g_shutdown_requested)
        return;

    // Stage 33: Warnungen sind persistent nicht-modal. Eine bereits sichtbare
    // Warnung wird wiederverwendet, damit nicht mehrere Warnfenster gestapelt
    // werden und die Hauptansicht samt Lupen weiter bedienbar bleibt.
    if (g_warning_dialog) {
        g_warning_dialog->setMessage(message);
        g_warning_dialog->updateForGrid(true);
        g_warning_dialog->show();
        g_warning_dialog->raise();
        g_warning_dialog->activateWindow();
        return;
    }

    WarningDialog *dialog = new WarningDialog(message, g_window);
    g_warning_dialog = dialog;
    QObject::connect(dialog, &QDialog::finished, [dialog](int) {
        if (g_warning_dialog == dialog)
            g_warning_dialog = nullptr;
        dialog->deleteLater();
    });
    dialog->show();
    dialog->raise();
    dialog->activateWindow();
}

void cancel_login_dialog()
{
    if (g_login_dialog)
        g_login_dialog->reject();
}

void close_database_tables(DatabaseNode *database)
{
    Q_UNUSED(database)
    // Stage 30 reserviert diesen zentralen Hook fuer die kommende TABLE-/DBF-
    // Ebene. Alle an DATABASE gebundenen Tabellen werden hier geschlossen,
    // bevor die eigentliche Datenbankverbindung abgebaut wird.
}

#ifdef _WIN32
QString database_odbc_diagnostic(SQLSMALLINT handleType, SQLHANDLE handle)
{
    SQLWCHAR state[6] = {0};
    SQLINTEGER nativeError = 0;
    SQLWCHAR text[512] = {0};
    SQLSMALLINT textLength = 0;
    if (SQLGetDiagRecW(handleType, handle, 1, state, &nativeError, text, 511, &textLength) == SQL_SUCCESS) {
        Q_UNUSED(nativeError)
        return QString::fromWCharArray(reinterpret_cast<const wchar_t *>(text), textLength);
    }
    return QStringLiteral("Unbekannter ODBC-Fehler.");
}
#endif

void database_close_internal(DatabaseNode *database)
{
    if (!database)
        return;
    close_database_tables(database);
#ifdef _WIN32
    if (database->odbcDbc != SQL_NULL_HDBC) {
        if (database->active)
            SQLEndTran(SQL_HANDLE_DBC, database->odbcDbc, SQL_ROLLBACK);
        SQLDisconnect(database->odbcDbc);
        SQLFreeHandle(SQL_HANDLE_DBC, database->odbcDbc);
        database->odbcDbc = SQL_NULL_HDBC;
    }
    if (database->odbcEnv != SQL_NULL_HENV) {
        SQLFreeHandle(SQL_HANDLE_ENV, database->odbcEnv);
        database->odbcEnv = SQL_NULL_HENV;
    }
#endif
    database->active = false;
    database->odbc = false;
    database->resolvedPath.clear();
}

int database_open_internal(DatabaseNode *database, bool showWarning)
{
    if (!database || g_shutdown_requested)
        return 0;
    if (database->active)
        return 1;

    if (!database->session || !g_session_nodes.contains(database->session) || !database->session->authenticated) {
        if (showWarning)
            show_runtime_warning(QStringLiteral("Die Datenbank kann nicht geoeffnet werden: keine legitimierte SESSION ist zugewiesen."));
        return 0;
    }

    if (!database->alias.trimmed().isEmpty()) {
#ifndef _WIN32
        if (showWarning)
            show_runtime_warning(QStringLiteral("ODBC-Aliasverbindungen stehen nur unter Windows zur Verfuegung."));
        return 0;
#else
        if (SQLAllocHandle(SQL_HANDLE_ENV, SQL_NULL_HANDLE, &database->odbcEnv) != SQL_SUCCESS) {
            if (showWarning)
                show_runtime_warning(QStringLiteral("ODBC-Umgebung konnte nicht erzeugt werden."));
            return 0;
        }
        if (SQLSetEnvAttr(database->odbcEnv, SQL_ATTR_ODBC_VERSION, reinterpret_cast<SQLPOINTER>(SQL_OV_ODBC3), 0) != SQL_SUCCESS
            || SQLAllocHandle(SQL_HANDLE_DBC, database->odbcEnv, &database->odbcDbc) != SQL_SUCCESS)
        {
            database_close_internal(database);
            if (showWarning)
                show_runtime_warning(QStringLiteral("ODBC-Verbindung konnte nicht vorbereitet werden."));
            return 0;
        }

        QString connection = QStringLiteral("DSN={%1}").arg(database->alias.trimmed());
        if (!database->databaseName.trimmed().isEmpty())
            connection += QStringLiteral(";DATABASE={%1}").arg(database->databaseName.trimmed());
        if (!database->userName.isEmpty())
            connection += QStringLiteral(";UID={%1}").arg(database->userName);
        if (!database->passwordValue.isEmpty())
            connection += QStringLiteral(";PWD={%1}").arg(database->passwordValue);
        connection += QLatin1Char(';');

        std::wstring connectionWide = connection.toStdWString();
        SQLWCHAR output[1024] = {0};
        SQLSMALLINT outputLength = 0;
        const SQLRETURN rc = SQLDriverConnectW(
            database->odbcDbc,
            nullptr,
            reinterpret_cast<SQLWCHAR *>(&connectionWide[0]),
            SQL_NTS,
            output,
            1023,
            &outputLength,
            SQL_DRIVER_NOPROMPT
        );
        if (!connectionWide.empty())
            SecureZeroMemory(&connectionWide[0], connectionWide.size() * sizeof(wchar_t));
        connection.fill(QChar(0));

        if (!(rc == SQL_SUCCESS || rc == SQL_SUCCESS_WITH_INFO)) {
            const QString detail = database_odbc_diagnostic(SQL_HANDLE_DBC, database->odbcDbc);
            database_close_internal(database);
            if (showWarning)
                show_runtime_warning(QStringLiteral("Die ODBC-Datenbankverbindung konnte nicht hergestellt werden.\n%1").arg(detail));
            return 0;
        }

        SQLSetConnectAttr(database->odbcDbc, SQL_ATTR_AUTOCOMMIT,
                          reinterpret_cast<SQLPOINTER>(SQL_AUTOCOMMIT_OFF), SQL_IS_UINTEGER);
        database->odbc = true;
        database->active = true;
        return 1;
#endif
    }

    const QString requestedPath = database->path.trimmed();
    if (requestedPath.isEmpty()) {
        if (showWarning)
            show_runtime_warning(QStringLiteral("Die Datenbank kann nicht geoeffnet werden: DATABASE.path ist leer."));
        return 0;
    }

    QDir directory(requestedPath);
    if (!directory.exists()) {
        if (showWarning)
            show_runtime_warning(QStringLiteral("Der Datenbankpfad existiert nicht:\n%1").arg(requestedPath));
        return 0;
    }

    // Fuer DBF/MDX/NDX/DBT ist DATABASE zunaechst ein Verzeichnis-Kontext.
    // databaseName bleibt der logische Datenbankname; existiert darunter ein
    // gleichnamiges Unterverzeichnis, wird dieses als Tabellenwurzel benutzt.
    QString resolved = directory.absolutePath();
    if (!database->databaseName.trimmed().isEmpty()) {
        QDir child(directory.filePath(database->databaseName.trimmed()));
        if (child.exists())
            resolved = child.absolutePath();
    }
    database->resolvedPath = resolved;
    database->odbc = false;
    database->active = true;
    return 1;
}

int database_commit_internal(DatabaseNode *database, bool showWarning)
{
    if (!database || !database->active) {
        if (showWarning)
            show_runtime_warning(QStringLiteral("COMMIT ist nicht moeglich: die DATABASE ist nicht aktiv."));
        return 0;
    }
#ifdef _WIN32
    if (database->odbc && database->odbcDbc != SQL_NULL_HDBC) {
        if (SQLEndTran(SQL_HANDLE_DBC, database->odbcDbc, SQL_COMMIT) != SQL_SUCCESS) {
            if (showWarning)
                show_runtime_warning(QStringLiteral("ODBC-COMMIT ist fehlgeschlagen."));
            return 0;
        }
    }
#endif
    // Lokale DBF-Aenderungen werden in der kommenden TABLE-Stufe hier
    // gemeinsam geflusht. Ohne offene Tabellen ist COMMIT erfolgreich.
    return 1;
}

void close_runtime_data_files()
{
    for (DatabaseNode *database : g_database_nodes) {
        database_close_internal(database);

        // Zugangsdaten gehoeren zur Anwendung und duerfen nach einem
        // Application-Close nicht im weiterlaufenden Prozessspeicher liegen.
        if (!database->passwordValue.isEmpty()) {
            database->passwordValue.fill(QChar(0));
            database->passwordValue.clear();
        }
    }
}

void invalidate_runtime_sessions()
{
    // Handles werden erst in DBaseQtShutdown() geloescht, damit ein gerade
    // aus einer lokalen Dialog-Eventloop zurueckkehrender generierter Aufruf
    // keinen dangling pointer sieht. Logisch sind die Sessions ab hier aber
    // geschlossen und alle Identitaetsdaten werden entfernt.
    for (SessionNode *session : g_session_nodes) {
        if (!session)
            continue;
        session->authenticated = false;
        session->username.clear();
        session->group.clear();
        session->sessionId.clear();
    }

    g_active_login_session = nullptr;
#ifdef _WIN32
    remote_broadcast_session_identity();
#endif
    set_login_session_state(false);
}

void hide_owner_application_windows()
{
    if (!g_app || !g_window)
        return;

    QWidget *activeWindow = QApplication::activeWindow();
    if (activeWindow && activeWindow != g_window && activeWindow != g_server_dialog)
        g_owner_hidden_active_window = activeWindow;
    else
        g_owner_hidden_active_window.clear();

    // Nur Fenster markieren, die zu diesem Zeitpunkt wirklich sichtbar sind.
    // Beim DB-Restore werden ausschliesslich diese wieder eingeblendet. Damit
    // werden absichtlich verborgene Dialoge nicht versehentlich sichtbar.
    const QWidgetList topLevels = QApplication::topLevelWidgets();
    for (QWidget *widget : topLevels) {
        if (!widget || widget == g_window || widget == g_server_dialog || !widget->isVisible())
            continue;

        widget->setProperty("dbaseHiddenWithMainWindow", true);
        widget->hide();
    }

    if (g_app) {
        g_app->sendPostedEvents();
        g_app->processEvents(QEventLoop::AllEvents);
    }
}

void restore_owner_application_windows()
{
    g_owner_restore_activated_window = false;
    if (!g_app || !g_window || !g_window->isVisible())
        return;

    QWidget *firstRestored = nullptr;
    const QWidgetList topLevels = QApplication::topLevelWidgets();
    for (QWidget *widget : topLevels) {
        if (!widget || widget == g_window)
            continue;
        if (!widget->property("dbaseHiddenWithMainWindow").toBool())
            continue;

        widget->setProperty("dbaseHiddenWithMainWindow", false);
        widget->show();
        if (!firstRestored)
            firstRestored = widget;
    }

    // War beim Verstecken z. B. das Passwortfeld im Login-Dialog aktiv,
    // bekommt dessen top-level Fenster direkt den Fokus. Wichtig: Das
    // Hauptfenster wurde vorher absichtlich nicht aktiviert, damit zwischen
    // MainWindow und Login-Dialog kein sichtbarer Z-Order-Wechsel entsteht.
    QWidget *active = g_owner_hidden_active_window.data();
    if (!active)
        active = firstRestored;

    if (active) {
        active->show();
        active->raise();
        active->activateWindow();
        g_owner_restore_activated_window = true;
    }
    g_owner_hidden_active_window.clear();
}

void close_runtime_application_windows()
{
    // Fokussierte/modale Qt-Dialoge zuerst explizit rejecten. hide() ist
    // zusaetzlich absichtlich gesetzt: selbst ein Dialog mit eigenem
    // closeEvent(), das close() ignoriert, darf nach Application-Close nicht
    // sichtbar auf der Workstation zurueckbleiben.
    cancel_login_dialog();

    // finished() kann die globalen Dialogzeiger synchron auf nullptr setzen.
    // Darum zuerst ausblenden und reject() jeweils nur als letzten Zugriff
    // auf den globalen Zeiger ausfuehren.
    if (g_warning_dialog)
        g_warning_dialog->hide();
    if (g_warning_dialog)
        g_warning_dialog->reject();

    if (g_btx_dialog)
        g_btx_dialog->hide();
    if (g_btx_dialog)
        g_btx_dialog->reject();

    const QWidgetList topLevels = QApplication::topLevelWidgets();
    for (QWidget *widget : topLevels) {
        if (!widget || widget == g_window)
            continue;

        QPointer<QWidget> guard(widget);
        guard->hide();

        if (QDialog *dialog = qobject_cast<QDialog *>(guard.data()))
            dialog->reject();

        // reject()/finished() darf das Objekt via delete/deleteLater abbauen.
        // Nur noch schliessen, wenn es danach weiterhin existiert.
        if (guard)
            widget->close();
    }

#ifdef _WIN32
    // Auch native Win32-Dialoge/Popupfenster derselben Anwendung, die nicht
    // als QApplication::topLevelWidgets() registriert sind, sofort aus der
    // Workstation entfernen und normal per WM_CLOSE beenden.
    HWND mainWindow = nullptr;
    if (g_window && g_window->winId())
        mainWindow = reinterpret_cast<HWND>(g_window->winId());
    D64WorkstationCloseApplicationWindows(mainWindow);
#endif

    if (g_app) {
        g_app->sendPostedEvents();
        g_app->processEvents(QEventLoop::AllEvents);
    }
}

void request_runtime_shutdown()
{
    // Mehrfache Close-/Quit-Signale duerfen keinen zweiten Cleanup starten.
    g_shutdown_requested = true;
    if (g_shutdown_in_progress)
        return;

    g_shutdown_in_progress = true;
    g_owner_hidden_active_window.clear();

#ifdef _WIN32
    /*
     * Nur der OWNER darf die globale Workstation verlassen bzw. den Input-
     * Desktop zurueckschalten. JOINED baut ausschliesslich seine eigene
     * Anwendung ab; D64WorkstationBeginLeave() beruecksichtigt diesen Fall.
     */
    D64WorkstationBeginLeave();
#endif

    // Stage 40: Der Application-Close ist ab hier transaktional. Erst wird
    // jede sichtbare UI der Anwendung entfernt, danach werden externe
    // Ressourcen geschlossen und Sessions invalidiert. Der generierte
    // Cleanup-Pfad ruft anschliessend DBaseQtShutdown() und VirtualFree auf.
    close_runtime_application_windows();
    close_runtime_data_files();
    invalidate_runtime_sessions();

    // Falls bereits die normale QApplication::exec()-Schleife laeuft, wird
    // sie sofort beendet. Eine lokale Dialog-QEventLoop wurde oben bereits
    // durch reject()/close() verlassen.
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

    const QFont font = make_console_grid_font();

    if (g_console)
        g_console->setFont(font);
    if (g_debug)
        g_debug->setFont(font);
    if (g_debug_input)
        g_debug_input->setFont(font);

    // Menue/Status/Popup-Rahmen folgen der vom Benutzer gewaehlten
    // Punktgroesse. Das eigentliche 80x25-Raster und alle Dialograhmen
    // verwenden ab Stage 37 dieselbe DPI-aufgeloeste Konsolenfont.
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
        // Stage 44: QStatusBar-Kindwidgets erben die Font je nach Windows-/Qt-
        // Style nicht zuverlaessig. Deshalb Statusfelder explizit mitskalieren.
        const QList<QWidget *> statusChildren = g_status_bar->findChildren<QWidget *>();
        for (QWidget *child : statusChildren) {
            if (child)
                child->setFont(chromeFont);
        }
        if (g_remote_listener_label)
            g_remote_listener_label->setFont(chromeFont);
        const int lineHeight = QFontMetrics(chromeFont, g_status_bar).height();
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

void enforce_console_80x25_grid()
{
    if (!g_console || !g_window)
        return;

    // Das Fenster ist fuer den Benutzer fest. Fuer die interne Neuberechnung
    // des 80x25-Rasters wird es kurz geloest und danach sofort wieder auf
    // die neu berechnete Groesse festgesetzt.
    unlock_window_for_grid_resize();

    // Stage 37: keine +/-1-Pixel-Korrektur mehr. Die Punktgroesse wird von Qt
    // mit dem DPI des realen Viewports aufgeloest. Fenster und Dialoge benutzen
    // danach exakt dieselben FontMetrics und Zellabmessungen.
    apply_output_font();
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
    if (g_warning_dialog)
        g_warning_dialog->updateForGrid(true);
    if (g_btx_dialog)
        g_btx_dialog->updateForGrid(true);
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
    if (editor == g_console && g_console_clear_mode == ConsoleClearMode::CharacterPattern) {
        g_console_clear_mode = ConsoleClearMode::None;
        g_terminal_template_dirty = true;
        g_remote_last_snapshot.clear();
    }

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

#ifdef _WIN32
    // Stage 35/39: der Thread muss VOR QApplication/QWidget/Hook an den
    // Workstation-Desktop gebunden werden. Stage 39 entscheidet dabei ueber
    // den Windows-globalen Singleton: erste Instanz = OWNER, weitere Prozesse
    // = JOINED auf demselben Desktop. Sichtbar geschaltet wird nur der OWNER
    // in DBaseQtShowWindow(), nachdem ein natives Hauptfenster existiert.
    if (!existing && !D64WorkstationIsActive()) {
        if (!D64WorkstationPrepare())
            return 0;
    }
#endif

    if (existing) {
        g_app = existing;
    } else {
        static int argc = 1;
        static char arg0[] = "dBase";
        static char *argv[] = { arg0, nullptr };
        g_app = new QApplication(argc, argv);
        g_owns_app = true;
    }

    if (!g_app) {
#ifdef _WIN32
        D64WorkstationBeginLeave();
        D64WorkstationFinalizeLeave();
#endif
        return 0;
    }

    // Eine erneute Initialisierung im selben Host-Prozess beginnt mit einem
    // sauberen Shutdown-Zustand.
    g_shutdown_requested = false;
    g_shutdown_in_progress = false;
    g_exit_authorized = false;
    g_exit_confirmation_open = false;

#ifdef _WIN32
    D64WorkstationSetExitCallback(&workstation_exit_requested);
    D64WorkstationSetBtxCallback(&workstation_btx_requested);
    D64WorkstationSetDbCallback(&workstation_db_requested);
    D64WorkstationSetServerCallback(&workstation_server_requested);
    D64WorkstationSetServerClientCallback(&workstation_server_client_requested);
#endif

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
    g_remote_listener_label = new QLabel(g_status_bar);
    g_remote_listener_label->setObjectName(QStringLiteral("dbaseRemoteListener"));
    g_remote_listener_label->setText(QStringLiteral("NET: aus"));
    g_status_bar->addPermanentWidget(g_remote_listener_label, 0);
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
#ifdef _WIN32
    remote_client_start();
#endif
    return 1;
}

extern "C" D64QT5_API void DBaseQtShowWindow(void)
{
    if (!g_window || g_shutdown_requested)
        return;

    HWND workstation_hwnd = nullptr;
#ifdef _WIN32
    // JOINED liegt bereits auf dem sichtbaren Workstation-Desktop. Den ersten
    // Frame deshalb offscreen komplett layouten, dann nur einmal real zeigen.
    if (D64WorkstationJoinedExisting()) {
        g_window->setAttribute(Qt::WA_DontShowOnScreen, true);
        g_window->show();
        enforce_console_80x25_grid();
        workstation_hwnd = reinterpret_cast<HWND>(g_window->winId());
        if (g_app)
            g_app->processEvents(QEventLoop::ExcludeUserInputEvents);
        g_window->hide();
        g_window->setAttribute(Qt::WA_DontShowOnScreen, false);
    } else {
        g_window->show();
        enforce_console_80x25_grid();
        workstation_hwnd = reinterpret_cast<HWND>(g_window->winId());
    }
#else
    g_window->show();
    enforce_console_80x25_grid();
#endif

#ifdef _WIN32
    if (!g_window->isVisible())
        g_window->show();
    if (D64WorkstationIsActive()) {
        if (!D64WorkstationActivate(workstation_hwnd)) {
            request_runtime_shutdown();
            return;
        }
    }
#endif

    g_window->raise();
    g_window->activateWindow();
    if (g_app)
        g_app->processEvents();
#ifdef _WIN32
    if (D64WorkstationIsVisible())
        D64WorkstationInstallKeyboardGuard(workstation_hwnd);
#endif
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
    g_terminal_template_dirty = true;
    g_remote_last_snapshot.clear();
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
    g_terminal_template_dirty = true;
    g_remote_last_snapshot.clear();
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
    g_terminal_template_dirty = true;
    g_remote_last_snapshot.clear();
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
    g_terminal_template_dirty = true;
    g_remote_last_snapshot.clear();
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
    g_terminal_template_dirty = true;
    g_remote_last_snapshot.clear();
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
    g_terminal_template_dirty = true;
    g_remote_last_snapshot.clear();
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
    session->sessionId = QUuid::createUuid().toString();
    session->sessionId.remove(QLatin1Char('{'));
    session->sessionId.remove(QLatin1Char('}'));
    g_session_nodes.append(session);
    g_active_login_session = session;
#ifdef _WIN32
    g_terminal_template_dirty = true;
    remote_broadcast_session_identity();
#endif
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

extern "C" D64QT5_API void *DBaseQtDatabaseCreate(void *parent)
{
    if (g_shutdown_requested)
        return nullptr;
    DatabaseNode *database = new DatabaseNode();
    database->parent = parent;
    g_database_nodes.append(database);
    return database;
}

QString database_text_from_bytes(const char *text, int length)
{
    if (!text || length <= 0)
        return QString();
    return QString::fromLocal8Bit(text, length);
}

void database_set_text_property(DatabaseNode *database, QString *property, const char *text, int length)
{
    if (!database || !property)
        return;
    if (database->active)
        database_close_internal(database);
    *property = database_text_from_bytes(text, length);
}

extern "C" D64QT5_API void DBaseQtDatabaseSetPath(void *handle, const char *text, int length)
{
    DatabaseNode *database = static_cast<DatabaseNode *>(handle);
    if (database && g_database_nodes.contains(database))
        database_set_text_property(database, &database->path, text, length);
}

extern "C" D64QT5_API void DBaseQtDatabaseSetDatabaseName(void *handle, const char *text, int length)
{
    DatabaseNode *database = static_cast<DatabaseNode *>(handle);
    if (database && g_database_nodes.contains(database))
        database_set_text_property(database, &database->databaseName, text, length);
}

extern "C" D64QT5_API void DBaseQtDatabaseSetUserName(void *handle, const char *text, int length)
{
    DatabaseNode *database = static_cast<DatabaseNode *>(handle);
    if (database && g_database_nodes.contains(database))
        database_set_text_property(database, &database->userName, text, length);
}

extern "C" D64QT5_API void DBaseQtDatabaseSetPassword(void *handle, const char *text, int length)
{
    DatabaseNode *database = static_cast<DatabaseNode *>(handle);
    if (!database || !g_database_nodes.contains(database))
        return;
    if (database->active)
        database_close_internal(database);
    if (!database->passwordValue.isEmpty())
        database->passwordValue.fill(QChar(0));
    database->passwordValue = database_text_from_bytes(text, length);
}

extern "C" D64QT5_API void DBaseQtDatabaseSetAlias(void *handle, const char *text, int length)
{
    DatabaseNode *database = static_cast<DatabaseNode *>(handle);
    if (database && g_database_nodes.contains(database))
        database_set_text_property(database, &database->alias, text, length);
}

extern "C" D64QT5_API void DBaseQtDatabaseSetSession(void *handle, void *sessionHandle)
{
    DatabaseNode *database = static_cast<DatabaseNode *>(handle);
    SessionNode *session = static_cast<SessionNode *>(sessionHandle);
    if (!database || !g_database_nodes.contains(database))
        return;
    if (database->active)
        database_close_internal(database);
    database->session = (session && g_session_nodes.contains(session)) ? session : nullptr;
}

extern "C" D64QT5_API int DBaseQtDatabaseSetActive(void *handle, int active)
{
    DatabaseNode *database = static_cast<DatabaseNode *>(handle);
    if (!database || !g_database_nodes.contains(database))
        return 0;
    if (active)
        return database_open_internal(database, true);
    database_close_internal(database);
    return 1;
}

extern "C" D64QT5_API int DBaseQtDatabaseOpen(void *handle)
{
    DatabaseNode *database = static_cast<DatabaseNode *>(handle);
    if (!database || !g_database_nodes.contains(database))
        return 0;
    return database_open_internal(database, true);
}

extern "C" D64QT5_API void DBaseQtDatabaseClose(void *handle)
{
    DatabaseNode *database = static_cast<DatabaseNode *>(handle);
    if (database && g_database_nodes.contains(database))
        database_close_internal(database);
}

extern "C" D64QT5_API int DBaseQtDatabaseCommit(void *handle)
{
    DatabaseNode *database = static_cast<DatabaseNode *>(handle);
    if (!database || !g_database_nodes.contains(database))
        return 0;
    return database_commit_internal(database, true);
}

extern "C" D64QT5_API void DBaseQtEnsureDefaultMenu(void)
{
    create_standard_menu();
    if (g_app)
        g_app->processEvents();
}

extern "C" D64QT5_API void *DBaseQtMenuCreate(void *owner)
{
#ifdef _WIN32
    g_terminal_template_dirty = true;
#endif
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
#ifdef _WIN32
    g_terminal_template_dirty = true;
#endif
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
#ifdef _WIN32
    g_terminal_template_dirty = true;
#endif
    MenuNode *node = menu_node_from_handle(handle);
    QAction *action = menu_node_action(node);
    if (action)
        action->setSeparator(separator != 0);
}

extern "C" D64QT5_API void DBaseQtMenuSetShortcut(void *handle, const char *text, int length)
{
#ifdef _WIN32
    g_terminal_template_dirty = true;
#endif
    MenuNode *node = menu_node_from_handle(handle);
    QAction *action = menu_node_action(node);
    if (!action)
        return;
    const QString shortcut = menu_text_from_bytes(text, length);
    action->setShortcut(QKeySequence(shortcut));
}

extern "C" D64QT5_API void DBaseQtMenuSetOnClick(void *handle, void (*callback)(void))
{
#ifdef _WIN32
    g_terminal_template_dirty = true;
#endif
    MenuNode *node = menu_node_from_handle(handle);
    if (node)
        node->callback = callback;
}

// -------------------------------------------------------------------------
// Stage 34 / WFM FORM-OOP Runtime
// -------------------------------------------------------------------------
static QString wfm_text(const char *text, int length)
{
    if (!text || length <= 0)
        return QString();
    return QString::fromUtf8(text, length);
}

static QWidget *wfm_widget(void *handle)
{
    return static_cast<QWidget *>(handle);
}

static void wfm_apply_widget_style(QWidget *widget)
{
    if (!widget)
        return;
    QStringList css;
    const QVariant back = widget->property("dbaseBackColor");
    if (back.isValid() && !back.toString().isEmpty())
        css << QStringLiteral("background-color:%1;").arg(back.toString());
    const QVariant borderColor = widget->property("dbaseBorderColor");
    const int borderWidth = qMax(0, widget->property("dbaseBorderWidth").toInt());
    if (borderWidth > 0) {
        const QString color = borderColor.isValid() && !borderColor.toString().isEmpty()
            ? borderColor.toString() : QStringLiteral("#7A7A7A");
        css << QStringLiteral("border:%1px solid %2;").arg(borderWidth).arg(color);
    } else {
        css << QStringLiteral("border:none;");
    }
    const int radius = qMax(0, widget->property("dbaseRadius").toInt());
    if (radius > 0)
        css << QStringLiteral("border-radius:%1px;").arg(radius);
    widget->setStyleSheet(css.join(QLatin1Char(' ')));
}

extern "C" D64QT5_API void *DBaseQtFormCreate(const char *className, int classNameLength)
{
    if (!g_app || g_shutdown_requested)
        return nullptr;
    QDialog *form = new QDialog(nullptr);
    form->setObjectName(wfm_text(className, classNameLength));
    form->setWindowTitle(form->objectName().isEmpty() ? QStringLiteral("dBase Form") : form->objectName());
    form->setModal(false);
    form->setMinimumSize(1, 1);
    form->setProperty("dbaseBorderWidth", 0);
    form->setProperty("dbaseRadius", 0);
    g_wfm_forms.append(form);
    return form;
}

extern "C" D64QT5_API void *DBaseQtControlCreate(const char *className, int classNameLength, void *parentHandle)
{
    QWidget *parent = wfm_widget(parentHandle);
    if (!parent || g_shutdown_requested)
        return nullptr;
    const QString type = wfm_text(className, classNameLength).trimmed().toUpper();
    QWidget *widget = nullptr;
    if (type == QStringLiteral("PUSHBUTTON") || type == QStringLiteral("BUTTON")) {
        widget = new QPushButton(parent);
    } else if (type == QStringLiteral("CONTAINER") || type == QStringLiteral("PANEL")) {
        QFrame *frame = new QFrame(parent);
        frame->setFrameShape(QFrame::NoFrame);
        frame->setFrameShadow(QFrame::Plain);
        widget = frame;
    } else if (type == QStringLiteral("LABEL") || type == QStringLiteral("TEXT")) {
        widget = new QLabel(parent);
    } else if (type == QStringLiteral("LINEEDIT") || type == QStringLiteral("EDIT")) {
        widget = new QLineEdit(parent);
    } else {
        // Erweiterbarer Fallback: unbekannte Designer-Komponenten bleiben als
        // sichtbarer QWidget-Platzhalter erhalten, statt den Formaufbau abzubrechen.
        widget = new QWidget(parent);
    }
    widget->setProperty("dbaseBorderWidth", 0);
    widget->setProperty("dbaseRadius", 0);
    widget->show();
    return widget;
}

extern "C" D64QT5_API void DBaseQtWidgetSetGeometry(void *handle, int left, int top, int width, int height)
{
    QWidget *widget = wfm_widget(handle);
    if (!widget)
        return;
    widget->setGeometry(left, top, qMax(1, width), qMax(1, height));
}

extern "C" D64QT5_API void DBaseQtWidgetSetText(void *handle, const char *text, int length)
{
    QWidget *widget = wfm_widget(handle);
    if (!widget)
        return;
    const QString value = wfm_text(text, length);
    if (QPushButton *button = qobject_cast<QPushButton *>(widget))
        button->setText(value);
    else if (QLabel *label = qobject_cast<QLabel *>(widget))
        label->setText(value);
    else if (QLineEdit *edit = qobject_cast<QLineEdit *>(widget))
        edit->setText(value);
    else
        widget->setWindowTitle(value);
}

extern "C" D64QT5_API void DBaseQtWidgetSetBackColor(void *handle, const char *text, int length)
{
    QWidget *widget = wfm_widget(handle);
    if (!widget)
        return;
    widget->setProperty("dbaseBackColor", wfm_text(text, length));
    wfm_apply_widget_style(widget);
}

extern "C" D64QT5_API void DBaseQtWidgetSetBorderColor(void *handle, const char *text, int length)
{
    QWidget *widget = wfm_widget(handle);
    if (!widget)
        return;
    widget->setProperty("dbaseBorderColor", wfm_text(text, length));
    wfm_apply_widget_style(widget);
}

extern "C" D64QT5_API void DBaseQtWidgetSetBorderWidth(void *handle, int width)
{
    QWidget *widget = wfm_widget(handle);
    if (!widget)
        return;
    widget->setProperty("dbaseBorderWidth", qMax(0, width));
    wfm_apply_widget_style(widget);
}

extern "C" D64QT5_API void DBaseQtWidgetSetRadius(void *handle, int radius)
{
    QWidget *widget = wfm_widget(handle);
    if (!widget)
        return;
    widget->setProperty("dbaseRadius", qMax(0, radius));
    wfm_apply_widget_style(widget);
}

extern "C" D64QT5_API void DBaseQtWidgetSetFont(
    void *handle,
    const char *family,
    int familyLength,
    int pointSize,
    int bold,
    int italic,
    int underline,
    int strikeout)
{
    QWidget *widget = wfm_widget(handle);
    if (!widget)
        return;
    QFont font(widget->font());
    const QString familyText = wfm_text(family, familyLength);
    if (!familyText.isEmpty())
        font.setFamily(familyText);
    font.setPointSize(qMax(1, pointSize));
    font.setBold(bold != 0);
    font.setItalic(italic != 0);
    font.setUnderline(underline != 0);
    font.setStrikeOut(strikeout != 0);
    widget->setFont(font);
}

extern "C" D64QT5_API void DBaseQtFormOpen(void *handle)
{
    QWidget *form = wfm_widget(handle);
    if (!form)
        return;
    form->show();
    form->raise();
    form->activateWindow();
    if (g_app)
        g_app->processEvents();
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

#ifdef _WIN32
    remote_client_stop();
    g_remote_application_connection_id.clear();
#endif

    // Datenbank-/Tabellenkontexte werden vor dem Zerlegen der Objekt-/GUI-
    // Strukturen geschlossen. DATABASE.active wird dabei auf false gesetzt;
    // die kommende TABLE-/DBF-Schicht benutzt denselben zentralen Hook.
    close_runtime_data_files();

    // Stage 34: Top-Level-WFM-Forms besitzen keinen g_window-Parent und
    // werden deshalb explizit vor QApplication abgebaut.
    for (QWidget *form : g_wfm_forms) {
        if (form) {
            form->close();
            delete form;
        }
    }
    g_wfm_forms.clear();

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
    g_remote_listener_label = nullptr;
    g_zoom_in = nullptr;
    g_zoom_out = nullptr;
    g_login_dialog = nullptr;
    g_warning_dialog = nullptr;
    g_btx_dialog = nullptr;
    g_server_dialog = nullptr;
    g_remote_cursor_marker = nullptr;
    g_security_file_menu = nullptr;
    g_login_action = nullptr;
    g_quit_action = nullptr;
    g_active_login_session = nullptr;
    g_login_session = false;
    g_debug_visible = false;
    g_program_finished = false;
    g_default_menu_created = false;
    g_font_point_size = 10;
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
    for (DatabaseNode *database : g_database_nodes) {
        if (!database->passwordValue.isEmpty())
            database->passwordValue.fill(QChar(0));
        delete database;
    }
    g_database_nodes.clear();
    for (SessionNode *session : g_session_nodes)
        delete session;
    g_session_nodes.clear();

    if (g_owns_app) {
        delete g_app;
        g_app = nullptr;
        g_owns_app = false;
    }

#ifdef _WIN32
    // Panel-Callback zuerst loesen; danach sind alle d64qt5-Fenster und Hooks
    // weg und der GUI-Thread darf auf den Originaldesktop zurueck.
    D64WorkstationSetExitCallback(nullptr);
    D64WorkstationSetBtxCallback(nullptr);
    D64WorkstationSetDbCallback(nullptr);
    D64WorkstationSetServerCallback(nullptr);
    D64WorkstationSetServerClientCallback(nullptr);
    D64WorkstationSetServerClientCount(0);
    D64WorkstationFinalizeLeave();
#endif

    g_exit_authorized = false;
    g_exit_confirmation_open = false;

    // Nach vollstaendigem Abbau darf ein Host die Bridge spaeter erneut
    // initialisieren. Bis hierhin bleibt g_shutdown_requested bewusst wahr,
    // damit kein nachlaufender Runtime-Aufruf neue UI erzeugt.
    g_shutdown_in_progress = false;
}
