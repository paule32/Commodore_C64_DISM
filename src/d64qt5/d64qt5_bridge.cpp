#define D64QT5_BRIDGE_EXPORTS 1
#include "d64qt5_bridge.h"

#include <QApplication>
#include <QColor>
#include <QCoreApplication>
#include <QFont>
#include <QFontDatabase>
#include <QFrame>
#include <QHBoxLayout>
#include <QIcon>
#include <QLineEdit>
#include <QMainWindow>
#include <QPainter>
#include <QPixmap>
#include <QPlainTextEdit>
#include <QTabWidget>
#include <QTextCursor>
#include <QToolButton>
#include <QVBoxLayout>
#include <QWidget>
#include <QString>
#include <QStringList>

namespace {
QApplication *g_app = nullptr;
bool g_owns_app = false;
QMainWindow *g_window = nullptr;
QTabWidget *g_tabs = nullptr;
QWidget *g_console_page = nullptr;
QWidget *g_debug_page = nullptr;
QPlainTextEdit *g_console = nullptr;
QPlainTextEdit *g_debug = nullptr;
QLineEdit *g_debug_input = nullptr;
QWidget *g_zoom_widget = nullptr;
QToolButton *g_zoom_in_button = nullptr;
QToolButton *g_zoom_out_button = nullptr;
bool g_program_finished = false;
int g_font_point_size = 10;
QString g_console_font_family;

const int DBASE_FONT_MIN_PT = 9;
const int DBASE_FONT_MAX_PT = 75;

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
        if (families.contains(candidate, Qt::CaseInsensitive)) {
            for (const QString &actual : families) {
                if (actual.compare(candidate, Qt::CaseInsensitive) == 0)
                    return actual;
            }
            return candidate;
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

    QPen pen(QColor(170, 170, 170));
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

void apply_output_font()
{
    if (g_console_font_family.isEmpty())
        g_console_font_family = choose_console_font_family();

    if (g_font_point_size < DBASE_FONT_MIN_PT)
        g_font_point_size = DBASE_FONT_MIN_PT;
    if (g_font_point_size > DBASE_FONT_MAX_PT)
        g_font_point_size = DBASE_FONT_MAX_PT;

    QFont font(g_console_font_family, g_font_point_size);
    font.setStyleHint(QFont::Monospace);
    font.setFixedPitch(true);

    if (g_console)
        g_console->setFont(font);
    if (g_debug)
        g_debug->setFont(font);
    if (g_debug_input)
        g_debug_input->setFont(font);
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

    g_font_point_size = next;
    apply_output_font();
}

void install_zoom_controls()
{
    if (!g_tabs || g_zoom_widget)
        return;

    g_zoom_widget = new QWidget(g_tabs);
    g_zoom_widget->setObjectName(QStringLiteral("dbaseZoomBar"));

    auto *layout = new QHBoxLayout(g_zoom_widget);
    layout->setContentsMargins(2, 0, 4, 0);
    layout->setSpacing(1);

    g_zoom_in_button = new QToolButton(g_zoom_widget);
    g_zoom_in_button->setObjectName(QStringLiteral("dbaseZoomIn"));
    g_zoom_in_button->setAutoRaise(true);
    g_zoom_in_button->setIcon(create_zoom_icon(true));
    g_zoom_in_button->setIconSize(QSize(20, 20));
    g_zoom_in_button->setFixedSize(26, 24);
    g_zoom_in_button->setToolTip(
        QStringLiteral("Text vergrößern (maximal 75 pt)")
    );

    g_zoom_out_button = new QToolButton(g_zoom_widget);
    g_zoom_out_button->setObjectName(QStringLiteral("dbaseZoomOut"));
    g_zoom_out_button->setAutoRaise(true);
    g_zoom_out_button->setIcon(create_zoom_icon(false));
    g_zoom_out_button->setIconSize(QSize(20, 20));
    g_zoom_out_button->setFixedSize(26, 24);
    g_zoom_out_button->setToolTip(
        QStringLiteral("Text verkleinern (minimal 9 pt)")
    );

    layout->addWidget(g_zoom_in_button);
    layout->addWidget(g_zoom_out_button);

    QObject::connect(g_zoom_in_button, &QToolButton::clicked, []() {
        change_font_size(+1);
    });
    QObject::connect(g_zoom_out_button, &QToolButton::clicked, []() {
        change_font_size(-1);
    });

    // Die Lupen sitzen direkt links in der Tab-Leiste oberhalb der beiden
    // QPlainTextEdit-Ausgaben.
    g_tabs->setCornerWidget(g_zoom_widget, Qt::TopLeftCorner);
}

void apply_dark_console_style()
{
    if (!g_window)
        return;

    g_window->setStyleSheet(QStringLiteral(
        "QMainWindow, QWidget {"
        "  background-color: #000000;"
        "  color: #a9a9a9;"
        "}"
        "QTabWidget::pane {"
        "  border: 0px;"
        "  background-color: #000000;"
        "}"
        "QTabBar::tab {"
        "  background-color: #111111;"
        "  color: #a9a9a9;"
        "  border: 0px;"
        "  padding: 5px 12px;"
        "}"
        "QTabBar::tab:selected {"
        "  background-color: #000000;"
        "  color: #c0c0c0;"
        "}"
        "QTabBar::tab:hover {"
        "  background-color: #1a1a1a;"
        "}"
        "QPlainTextEdit {"
        "  background-color: #000000;"
        "  color: #a9a9a9;"
        "  border: 0px;"
        "  selection-background-color: #404040;"
        "  selection-color: #ffffff;"
        "  padding: 4px;"
        "}"
        "QLineEdit {"
        "  background-color: #000000;"
        "  color: #a9a9a9;"
        "  border: 0px;"
        "  border-top: 1px solid #303030;"
        "  selection-background-color: #404040;"
        "  selection-color: #ffffff;"
        "  padding: 4px;"
        "}"
        "QToolButton {"
        "  background-color: #000000;"
        "  border: 0px;"
        "  padding: 1px;"
        "}"
        "QToolButton:hover {"
        "  background-color: #202020;"
        "}"
        "QToolButton:pressed {"
        "  background-color: #303030;"
        "}"
    ));
}

void append_text(QPlainTextEdit *editor, const char *text, int length)
{
    if (!editor || !text || length <= 0)
        return;

    const QString value = QString::fromLocal8Bit(text, length);
    QTextCursor cursor(editor->document());
    cursor.movePosition(QTextCursor::End);
    cursor.insertText(value);
    editor->setTextCursor(cursor);
    editor->ensureCursorVisible();
}

int debug_index()
{
    return (g_tabs && g_debug_page) ? g_tabs->indexOf(g_debug_page) : -1;
}

void install_debug_tab()
{
    if (!g_tabs || !g_debug_page || debug_index() >= 0)
        return;
    g_tabs->addTab(g_debug_page, QStringLiteral("DEBUG"));
}

void remove_debug_tab()
{
    if (!g_tabs)
        return;
    const int index = debug_index();
    if (index >= 0)
        g_tabs->removeTab(index);
}
}

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
    g_window->resize(840, 520);
    g_window->setWindowTitle(
        title && *title ? QString::fromLocal8Bit(title)
                        : QStringLiteral("dBase Qt5 Console / DEBUG")
    );

    g_tabs = new QTabWidget(g_window);
    g_tabs->setDocumentMode(true);
    g_window->setCentralWidget(g_tabs);

    g_console_page = new QWidget(g_tabs);
    auto *console_layout = new QVBoxLayout(g_console_page);
    console_layout->setContentsMargins(0, 0, 0, 0);
    console_layout->setSpacing(0);
    g_console = new QPlainTextEdit(g_console_page);
    g_console->setObjectName(QStringLiteral("dbaseConsole"));
    g_console->setReadOnly(true);
    g_console->setFrameShape(QFrame::NoFrame);
    g_console->setLineWrapMode(QPlainTextEdit::NoWrap);
    console_layout->addWidget(g_console, 1);
    g_tabs->addTab(g_console_page, QStringLiteral("Konsole"));

    g_debug_page = new QWidget(g_tabs);
    auto *debug_layout = new QVBoxLayout(g_debug_page);
    debug_layout->setContentsMargins(0, 0, 0, 0);
    debug_layout->setSpacing(0);
    g_debug = new QPlainTextEdit(g_debug_page);
    g_debug->setObjectName(QStringLiteral("dbaseDebug"));
    g_debug->setReadOnly(true);
    g_debug->setFrameShape(QFrame::NoFrame);
    g_debug->setLineWrapMode(QPlainTextEdit::NoWrap);
    debug_layout->addWidget(g_debug, 1);

    g_debug_input = new QLineEdit(g_debug_page);
    g_debug_input->setObjectName(QStringLiteral("dbaseDebugInput"));
    g_debug_input->setPlaceholderText(
        QStringLiteral("Eingabe / Debug-Befehl ...")
    );
    debug_layout->addWidget(g_debug_input, 0);

    install_zoom_controls();
    apply_dark_console_style();
    apply_output_font();

    QObject::connect(g_debug_input, &QLineEdit::returnPressed, []() {
        if (!g_debug_input || !g_debug)
            return;
        const QString input = g_debug_input->text();
        if (!input.isEmpty()) {
            QTextCursor cursor(g_debug->document());
            cursor.movePosition(QTextCursor::End);
            cursor.insertText(QStringLiteral("> ") + input + QLatin1Char('\n'));
            g_debug->setTextCursor(cursor);
            g_debug->ensureCursorVisible();
        }
        g_debug_input->clear();
    });

    // DEBUG ist zu Beginn aus. SET DEBUG ON bzw. SET FORMAT TO SCREEN
    // fuegt den Tab zur Laufzeit wieder ein.
    return 1;
}

extern "C" D64QT5_API void DBaseQtShowWindow(void)
{
    if (g_window)
        g_window->show();
}

extern "C" D64QT5_API void DBaseQtProcessEvents(void)
{
    if (g_app)
        g_app->processEvents();
}

extern "C" D64QT5_API void DBaseQtSetDebugVisible(int visible)
{
    if (visible) {
        install_debug_tab();
    } else {
        remove_debug_tab();
    }
    if (g_app)
        g_app->processEvents();
}

extern "C" D64QT5_API void DBaseQtAppendConsole(const char *text, int length)
{
    append_text(g_console, text, length);
}

extern "C" D64QT5_API void DBaseQtAppendDebug(const char *text, int length)
{
    install_debug_tab();
    append_text(g_debug, text, length);
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
    // Die eigentliche dBase-Ausfuehrung ist zu diesem Zeitpunkt beendet.
    // Der Qt-Eventloop haelt das Fenster und die Eingabezeile weiterhin am
    // Leben, bis der Benutzer das Fenster schliesst.
    return g_app->exec();
}

extern "C" D64QT5_API void DBaseQtShutdown(void)
{
    delete g_window;
    g_window = nullptr;
    g_tabs = nullptr;
    g_console_page = nullptr;
    g_debug_page = nullptr;
    g_console = nullptr;
    g_debug = nullptr;
    g_debug_input = nullptr;
    g_zoom_widget = nullptr;
    g_zoom_in_button = nullptr;
    g_zoom_out_button = nullptr;
    g_console_font_family.clear();
    g_font_point_size = 10;
    g_program_finished = false;

    if (g_owns_app) {
        delete g_app;
        g_app = nullptr;
        g_owns_app = false;
    }
}
