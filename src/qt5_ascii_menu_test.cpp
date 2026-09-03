// ---------------------------------------------------------------------------
// File: qt5_ascii_submenu_frame_test.cpp
//
// Hauptmenue:
//   normale QMenuBar ohne ASCII-/Terminal-Rahmen.
//
// Untermenues:
//   eigene QMenu-Unterklasse, deren Popup-Rand mit CP437-artigen
//   Box-Drawing-Zeichen gezeichnet wird.
//
// Verwendete CP437-Entsprechungen:
//   B9 = ╣   BA = ║   BB = ╗   BC = ╝
//   C8 = ╚   C9 = ╔   CA = ╩   CB = ╦
//   CC = ╠   CD = ═   CE = ╬
// ---------------------------------------------------------------------------

#include <QAction>
#include <QApplication>
#include <QFont>
#include <QFontDatabase>
#include <QFontMetrics>
#include <QKeySequence>
#include <QMainWindow>
#include <QMenu>
#include <QMenuBar>
#include <QPainter>
#include <QPaintEvent>
#include <QPlainTextEdit>
#include <QStatusBar>
#include <QVBoxLayout>
#include <QWidget>


static QString chooseBorderFont()
{
    QFontDatabase db;
    const QStringList families = db.families();

    if (families.contains(
            QStringLiteral("Terminal"),
            Qt::CaseInsensitive))
    {
        return QStringLiteral("Terminal");
    }

    if (families.contains(
            QStringLiteral("Courier New"),
            Qt::CaseInsensitive))
    {
        return QStringLiteral("Courier New");
    }

    return QFontDatabase::systemFont(
        QFontDatabase::FixedFont
    ).family();
}


static QString chooseUiFont()
{
    QFontDatabase db;
    const QStringList families = db.families();

    if (families.contains(
            QStringLiteral("Consolas"),
            Qt::CaseInsensitive))
    {
        return QStringLiteral("Consolas");
    }

    if (families.contains(
            QStringLiteral("Courier New"),
            Qt::CaseInsensitive))
    {
        return QStringLiteral("Courier New");
    }

    return QFontDatabase::systemFont(
        QFontDatabase::FixedFont
    ).family();
}


// ---------------------------------------------------------------------------
// Nur diese Klasse zeichnet den Zeichenrahmen.
//
// Die QMenuBar selbst bleibt unveraendert.
// ---------------------------------------------------------------------------
class AsciiPopupMenu final : public QMenu
{
public:
    explicit AsciiPopupMenu(
        const QString &title,
        QWidget *parent = nullptr
    )
        : QMenu(title, parent)
    {
        const QString borderFamily =
            chooseBorderFont();

        m_borderFont = QFont(
            borderFamily,
            10
        );

        m_borderFont.setFixedPitch(true);
        m_borderFont.setStyleHint(
            QFont::TypeWriter
        );

        QFontMetrics fm(m_borderFont);

        m_cellWidth = qMax(
            1,
            fm.horizontalAdvance(
                QString(QChar(0x2550))  // ═
            )
        );

        m_cellHeight = qMax(
            1,
            fm.height()
        );

        // Platz fuer den Zeichenrahmen reservieren.
        //
        // Dadurch werden die echten QAction-Eintraege nicht unter
        // ╔ ═ ╗ ║ ╚ ╝ gezeichnet.
        setContentsMargins(
            m_cellWidth,
            m_cellHeight,
            m_cellWidth,
            m_cellHeight
        );

        QFont menuFont(
            chooseUiFont(),
            10
        );

        menuFont.setFixedPitch(true);
        menuFont.setStyleHint(
            QFont::TypeWriter
        );

        setFont(menuFont);

        setStyleSheet(QStringLiteral(R"(
            QMenu {
                background-color: #909090;
                color: #000000;

                /* Kein normaler Qt-Rahmen. */
                border: 0px;

                margin: 0px;
                padding: 0px;
            }

            QMenu::item {
                background-color: transparent;
                color: #000000;

                padding:
                    3px
                    34px
                    3px
                    8px;
            }

            QMenu::item:selected {
                background-color: #000080;
                color: #FFFFFF;
            }

            QMenu::item:disabled {
                color: #505050;
            }

            QMenu::separator {
                height: 1px;
                background-color: #505050;
                margin: 3px 6px 3px 6px;
            }
        )"));
    }

protected:
    void paintEvent(
        QPaintEvent *event
    ) override
    {
        // Zuerst Hintergrund + QAction-Eintraege von Qt zeichnen.
        QMenu::paintEvent(event);

        // Danach den Zeichenrahmen darueberlegen.
        QPainter painter(this);

        painter.setRenderHint(
            QPainter::TextAntialiasing,
            false
        );

        painter.setFont(m_borderFont);
        painter.setPen(Qt::black);

        QFontMetrics fm(m_borderFont);

        const int widthPx  = width();
        const int heightPx = height();

        if (widthPx <= m_cellWidth * 2 ||
            heightPx <= m_cellHeight * 2)
        {
            return;
        }

        // Unicode-Entsprechungen der CP437-Zeichen.
        const QString TL(QChar(0x2554)); // ╔  C9
        const QString TR(QChar(0x2557)); // ╗  BB
        const QString BL(QChar(0x255A)); // ╚  C8
        const QString BR(QChar(0x255D)); // ╝  BC
        const QString H (QChar(0x2550)); // ═  CD
        const QString V (QChar(0x2551)); // ║  BA

        const int ascent  = fm.ascent();
        const int descent = fm.descent();

        // --------------------------------------------------------------
        // obere Kante
        // --------------------------------------------------------------
        const int topBaseline = ascent;

        painter.drawText(
            0,
            topBaseline,
            TL
        );

        for (int x = m_cellWidth;
             x < widthPx - m_cellWidth;
             x += m_cellWidth)
        {
            painter.drawText(
                x,
                topBaseline,
                H
            );
        }

        painter.drawText(
            widthPx - m_cellWidth,
            topBaseline,
            TR
        );

        // --------------------------------------------------------------
        // untere Kante
        // --------------------------------------------------------------
        const int bottomBaseline =
            heightPx - descent;

        painter.drawText(
            0,
            bottomBaseline,
            BL
        );

        for (int x = m_cellWidth;
             x < widthPx - m_cellWidth;
             x += m_cellWidth)
        {
            painter.drawText(
                x,
                bottomBaseline,
                H
            );
        }

        painter.drawText(
            widthPx - m_cellWidth,
            bottomBaseline,
            BR
        );

        // --------------------------------------------------------------
        // linke + rechte Kante
        // --------------------------------------------------------------
        for (int y = m_cellHeight;
             y < heightPx - m_cellHeight;
             y += m_cellHeight)
        {
            const int baseline =
                y + ascent;

            painter.drawText(
                0,
                baseline,
                V
            );

            painter.drawText(
                widthPx - m_cellWidth,
                baseline,
                V
            );
        }
    }

private:
    QFont m_borderFont;

    int m_cellWidth  = 8;
    int m_cellHeight = 16;
};


class TestWindow final
    : public QMainWindow
{
public:
    explicit TestWindow(
        QWidget *parent = nullptr
    )
        : QMainWindow(parent)
    {
        setWindowTitle(
            QStringLiteral(
                "dBase Qt5 - nur Untermenue mit ASCII-Rahmen"
            )
        );

        resize(
            900,
            560
        );

        // --------------------------------------------------------------
        // Hauptmenue:
        // KEIN Zeichenrahmen.
        // --------------------------------------------------------------
        QMenuBar *mainMenu =
            menuBar();

        QFont mainMenuFont(
            chooseUiFont(),
            10
        );

        mainMenuFont.setFixedPitch(true);
        mainMenuFont.setStyleHint(
            QFont::TypeWriter
        );

        mainMenu->setFont(
            mainMenuFont
        );

        mainMenu->setStyleSheet(
            QStringLiteral(R"(
                QMenuBar {
                    background-color: #909090;
                    color: #000000;

                    border: 0px;
                    margin: 0px;
                    padding: 0px;
                }

                QMenuBar::item {
                    background-color: transparent;
                    color: #000000;

                    padding:
                        4px
                        9px;
                }

                QMenuBar::item:selected {
                    background-color: #C0C0C0;
                    color: #000000;
                }
            )")
        );

        // --------------------------------------------------------------
        // Fenster-Menue:
        // Nur dieses Popup hat den Zeichenrahmen.
        // --------------------------------------------------------------
        AsciiPopupMenu *windowMenu =
            new AsciiPopupMenu(
                QStringLiteral("&Fenster"),
                mainMenu
            );

        mainMenu->addMenu(
            windowMenu
        );

        QAction *cascade =
            windowMenu->addAction(
                QStringLiteral(
                    "Ü&berlappend"
                )
            );

        QAction *horizontal =
            windowMenu->addAction(
                QStringLiteral(
                    "&Horizontal anordnen"
                )
            );

        QAction *vertical =
            windowMenu->addAction(
                QStringLiteral(
                    "&Vertikal anordnen"
                )
            );

        QAction *icons =
            windowMenu->addAction(
                QStringLiteral(
                    "&Symbole anordnen"
                )
            );

        windowMenu->addSeparator();

        QAction *closeAction =
            windowMenu->addAction(
                QStringLiteral(
                    "Sch&ließen"
                )
            );

        closeAction->setShortcut(
            QKeySequence(
                QStringLiteral(
                    "Ctrl+F4"
                )
            )
        );

        QAction *closeAll =
            windowMenu->addAction(
                QStringLiteral(
                    "&Alle schließen"
                )
            );

        // --------------------------------------------------------------
        // Zweites Hauptmenue zum Vergleich.
        // Auch dessen Popup bekommt den Zeichenrahmen.
        // --------------------------------------------------------------
        AsciiPopupMenu *helpMenu =
            new AsciiPopupMenu(
                QStringLiteral("&Hilfe"),
                mainMenu
            );

        mainMenu->addMenu(
            helpMenu
        );

        QAction *about =
            helpMenu->addAction(
                QStringLiteral(
                    "&Über..."
                )
            );

        // --------------------------------------------------------------
        // Zentraler Konsolenbereich.
        // --------------------------------------------------------------
        QWidget *central =
            new QWidget(this);

        QVBoxLayout *layout =
            new QVBoxLayout(central);

        layout->setContentsMargins(
            3, 3, 3, 3
        );

        layout->setSpacing(
            0
        );

        QPlainTextEdit *console =
            new QPlainTextEdit(
                central
            );

        console->setReadOnly(
            true
        );

        console->setLineWrapMode(
            QPlainTextEdit::NoWrap
        );

        console->setContentsMargins(
            0, 0, 0, 0
        );

        console->document()->
            setDocumentMargin(
                0.0
            );

        QFont consoleFont(
            chooseUiFont(),
            10
        );

        consoleFont.setFixedPitch(
            true
        );

        consoleFont.setStyleHint(
            QFont::TypeWriter
        );

        console->setFont(
            consoleFont
        );

        console->setPlainText(
            QStringLiteral(
                "Das Hauptmenü oben hat keinen Zeichenrahmen.\n"
                "\n"
                "Klicke auf \"Fenster\" oder \"Hilfe\".\n"
                "Nur das aufgeklappte QMenu wird mit\n"
                "╔ ═ ╗ ║ ╚ ╝ gerahmt.\n"
            )
        );

        console->setStyleSheet(
            QStringLiteral(R"(
                QPlainTextEdit {
                    background-color: #000000;
                    color: #A9A9A9;

                    border: 3px solid #FFFFFF;
                    margin: 0px;
                    padding: 0px;
                }
            )")
        );

        layout->addWidget(
            console,
            1
        );

        QStatusBar *status =
            new QStatusBar(
                central
            );

        status->setSizeGripEnabled(
            false
        );

        status->setFont(
            consoleFont
        );

        status->showMessage(
            QStringLiteral(
                "Bereit - ASCII-Rahmen nur an Untermenüs"
            )
        );

        status->setStyleSheet(
            QStringLiteral(R"(
                QStatusBar {
                    background-color: #909090;
                    color: #000000;

                    border: 0px;
                    margin: 0px;
                    padding: 0px;
                }
            )")
        );

        layout->addWidget(
            status,
            0
        );

        setCentralWidget(
            central
        );

        // Nur damit die Actions nicht unbenutzt erscheinen.
        connect(
            cascade,
            &QAction::triggered,
            this,
            [status]() {
                status->showMessage(
                    QStringLiteral(
                        "Überlappend"
                    )
                );
            }
        );

        connect(
            horizontal,
            &QAction::triggered,
            this,
            [status]() {
                status->showMessage(
                    QStringLiteral(
                        "Horizontal anordnen"
                    )
                );
            }
        );

        connect(
            vertical,
            &QAction::triggered,
            this,
            [status]() {
                status->showMessage(
                    QStringLiteral(
                        "Vertikal anordnen"
                    )
                );
            }
        );

        connect(
            icons,
            &QAction::triggered,
            this,
            [status]() {
                status->showMessage(
                    QStringLiteral(
                        "Symbole anordnen"
                    )
                );
            }
        );

        connect(
            closeAction,
            &QAction::triggered,
            this,
            [status]() {
                status->showMessage(
                    QStringLiteral(
                        "Schließen"
                    )
                );
            }
        );

        connect(
            closeAll,
            &QAction::triggered,
            this,
            [status]() {
                status->showMessage(
                    QStringLiteral(
                        "Alle schließen"
                    )
                );
            }
        );

        connect(
            about,
            &QAction::triggered,
            this,
            [status]() {
                status->showMessage(
                    QStringLiteral(
                        "Über..."
                    )
                );
            }
        );
    }
};


int main(
    int argc,
    char **argv
)
{
    QApplication app(
        argc,
        argv
    );

    TestWindow window;

    window.show();

    return app.exec();
}
