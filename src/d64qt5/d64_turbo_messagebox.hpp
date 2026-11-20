#pragma once
// Stage 635: wiederverwendbares, vollstaendig eingebettetes Turbo-Vision-Fenster.
// QWidget statt QDialog: der Dialog ist kein Qt-Top-Level-Fenster.
// Rahmen/Schatten werden explizit gemalt und Schliessen/Drag/Buttons
// verwenden ihre eigenen QWidget-Ereignisse (ohne Q_OBJECT/MOC).
#include <QDialog> // andere Runtime-Header erwarten Qt5-QDialog-Deklarationen
#include <QCloseEvent>
#include <QApplication>
#include <QPointer>
#include <functional>
#include <QPushButton>
#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QLabel>
#include <QPainter>
#include <QPen>
#include <QMouseEvent>
#include <QEvent>
#include <QKeyEvent>
#include <QList>
#include <QPair>
#include <QFont>
#include <QPoint>
#include <QToolButton>
#include <QFontDatabase>
#include <QPaintEvent>
#include <QWidget>
#include <QAbstractScrollArea>
#include <QResizeEvent>
#include <QEventLoop>
#include <QCoreApplication>
#include <QSize>
#include <QFontMetrics>
#include <QVariant>

// Stage 637: Die MessageBox benutzt GENAU das DOS-Raster des Console-
// QPlainTextEdit (inkl. Zoom) und NICHT ihren eigenen Consolas-Dialogfont.
// X kann rechts ueber den sichtbaren Viewport hinausragen. Erreichbar
// bleiben mindestens zehn Titelzeichen; die Titelzeile reicht bis Reihe 24.
namespace d64_turbo_message_grid {
inline QSize cellSize(const QWidget *desktop)
{
    if (!desktop) return QSize(8, 16);
    const QWidget *console = desktop->parentWidget();
    const QFont gridFont = console ? console->font() : desktop->font();
    const QFontMetrics metrics(gridFont, desktop);
    return QSize(qMax(1, metrics.horizontalAdvance(QLatin1Char('M'))),
                 qMax(1, metrics.lineSpacing()));
}

inline int roundCells(int pixels, int cell)
{
    cell = qMax(1, cell);
    return pixels >= 0 ? (pixels + cell / 2) / cell
                       : -((-pixels + cell / 2) / cell);
}

inline QPoint clampCells(int col, int row, const QWidget *desktop)
{
    if (!desktop) return QPoint(qMax(0, col), qMax(0, row));
    const QSize cell = cellSize(desktop);
    const int viewportCols = qMax(1, desktop->width() / cell.width());
    const int viewportRows = qMax(1, desktop->height() / cell.height());
    const int visibleTitleCols = qMin(10, viewportCols);
    const int maxCol = qMin(79, qMax(0, viewportCols - visibleTitleCols));
    const int maxRow = qMin(24, qMax(0, viewportRows - 1));
    return QPoint(qBound(0, col, maxCol), qBound(0, row, maxRow));
}

inline QPoint gridPixels(const QPoint &cells, const QWidget *desktop)
{
    const QSize cell = cellSize(desktop);
    return QPoint(cells.x() * cell.width(), cells.y() * cell.height());
}
} // namespace d64_turbo_message_grid

// Die Modalschicht ist ein Kind des DOS-Desktops (QPlainTextEdit::viewport()).
// Sie faengt Mausklicks auf andere Turbo-Vision-Fenster ab und bleibt beim
// Resize des Consolen-Viewports exakt auf dessen Flaeche beschraenkt.
class D64TurboModalLayer final : public QWidget {
public:
    explicit D64TurboModalLayer(QWidget *desktop) : QWidget(desktop)
    {
        setObjectName(QStringLiteral("dbaseTurboModalLayer"));
        setAttribute(Qt::WA_StyledBackground, true);
        setAutoFillBackground(false);
        setFocusPolicy(Qt::StrongFocus);
        if (desktop) {
            setGeometry(desktop->rect());
            desktop->installEventFilter(this);
            // FontChange am QPlainTextEdit wird bei Zoom ausgeloest.
            // Die Dialog-Position wird dann in denselben Zellkoordinaten
            // mit den neuen Breiten/Hoehen wieder aufgebaut.
            if (desktop->parentWidget())
                desktop->parentWidget()->installEventFilter(this);
        }
        if (QCoreApplication::instance())
            QCoreApplication::instance()->installEventFilter(this);
    }
protected:
    void paintEvent(QPaintEvent *) override
    {
        QPainter painter(this);
        painter.fillRect(rect(), QColor(0, 0, 0, 48));
    }
public:
    // Bei Qt5 gehen echte Eingaben zunaechst an ein natives QWidgetWindow
    // (QObject/QWindow), ERST DANACH werden sie an das Ziel-QWidget verteilt.
    // Ein anwendungsweiter Filter darf diese erste Phase nicht verschlucken:
    // sonst reagieren weder Titelleiste noch Buttons noch die Escape-Taste.
    void setEscapeHandler(std::function<void()> handler)
    { escapeHandler_ = std::move(handler); }
protected:
    bool eventFilter(QObject *watched, QEvent *event) override
    {
        if (!event)
            return QWidget::eventFilter(watched, event);
        if (!watched || !watched->isWidgetType()) {
            // QWindow/Input-Ereignisse zur Widget-Verteilung durchlassen.
            // Escape hier zusaetzlich direkt behandeln, damit auch die
            // native Fokuskette die eingebettete MessageBox schliessen kann.
            if (event->type() == QEvent::KeyPress && escapeHandler_) {
                auto *key = static_cast<QKeyEvent *>(event);
                if (key->key() == Qt::Key_Escape) {
                    escapeHandler_();
                    event->accept();
                    return true;
                }
            }
            // Auf QAction/QShortcut darf trotzdem keine Aktion im
            // Hauptfenster ausgeloest werden, solange die Box offen ist.
            if (event->type() == QEvent::Shortcut) {
                event->accept();
                return true;
            }
            return QWidget::eventFilter(watched, event);
        }
        const bool viewportResized = (watched == parentWidget()
                                      && event->type() == QEvent::Resize);
        const bool consoleFontChanged = (parentWidget()
                                         && watched == parentWidget()->parentWidget()
                                         && event->type() == QEvent::FontChange);
        if (viewportResized || consoleFontChanged) {
            if (viewportResized) setGeometry(parentWidget()->rect());
            // Die letzte logische Position ueberlebt Zoom- und
            // Viewport-Aenderungen. Nicht auf die Fensterbreite/-hoehe
            // begrenzen: nur die Titelleiste muss erreichbar bleiben.
            for (QObject *child : children()) {
                QWidget *window = qobject_cast<QWidget *>(child);
                if (!window || !window->property("d64GridCol").isValid()) continue;
                const QPoint cells = d64_turbo_message_grid::clampCells(
                    window->property("d64GridCol").toInt(),
                    window->property("d64GridRow").toInt(), parentWidget());
                window->setProperty("d64GridCol", cells.x());
                window->setProperty("d64GridRow", cells.y());
                window->move(d64_turbo_message_grid::gridPixels(cells, parentWidget()));
            }
        }
        // Applicationweit echte Modalitaet, ohne ein eigenes OS-Dialogfenster:
        // Menue-Leiste, Editoren, Werkzeuge und deren Shortcuts blockieren,
        // solange die Turbo-Vision-MessageBox angezeigt wird.
        switch (event->type()) {
        case QEvent::MouseButtonPress:
        case QEvent::MouseButtonRelease:
        case QEvent::MouseButtonDblClick:
        case QEvent::Wheel:
        case QEvent::KeyPress:
        case QEvent::KeyRelease:
        case QEvent::Shortcut:
        case QEvent::ShortcutOverride:
            if (watched != this && !isAncestorOf(qobject_cast<QWidget *>(watched))) {
                event->accept();
                return true;
            }
            break;
        default: break;
        }
        return QWidget::eventFilter(watched, event);
    }
private:
    std::function<void()> escapeHandler_;
};

// Beim Druecken wird der Button um drei Pixel nach rechts/unten versetzt;
// beim Verlassen und bei Freigabe zurueckgesetzt.
class D64TurboDialogButton final : public QPushButton {
public:
    explicit D64TurboDialogButton(const QString &caption, QWidget *parent = nullptr)
      : QPushButton(caption, parent)
    {
        setObjectName(QStringLiteral("dbaseTurboDialogButton"));
        setCursor(Qt::ArrowCursor);
        setMinimumWidth(84);
        setMinimumHeight(28);
        setMouseTracking(true);
    }
protected:
    void mousePressEvent(QMouseEvent *event) override
    {
        // Erst den gedrueckt-Zustand setzen; danach das visuelle 3px-Offset.
        // So bleibt QPushButton::clicked() nach MouseRelease zuverlaessig.
        QPushButton::mousePressEvent(event);
        if (event->button() == Qt::LeftButton && !shifted_) {
            shift(3);
            shifted_ = true;
        }
    }
    void mouseReleaseEvent(QMouseEvent *event) override
    {
        // Vor der Click-Hit-Pruefung an die Originalposition zurueck.
        // Die Event-Koordinaten stammen noch aus der verschobenen Position.
        // Deshalb MouseRelease in die korrigierte lokale Position umrechnen.
        const QPoint global = event->globalPos();
        if (shifted_) { shift(-3); shifted_ = false; }
        QMouseEvent corrected(QEvent::MouseButtonRelease,
                              QPointF(mapFromGlobal(global)), QPointF(global),
                              event->button(), event->buttons(), event->modifiers());
        QPushButton::mouseReleaseEvent(&corrected);
    }
    void leaveEvent(QEvent *event) override
    {
        if (shifted_) { shift(-3); shifted_ = false; }
        QPushButton::leaveEvent(event);
    }
private:
    void shift(int pixels) { move(pos() + QPoint(pixels, pixels)); }
    bool shifted_ = false;
};

class D64TurboMessageBox final : public QWidget {
public:
    enum Button { Cancel = 0, Ok = 1, Help = 2, Save = 3, Discard = 4 };
    using ButtonSpec = QPair<QString, int>;

    explicit D64TurboMessageBox(QWidget *parent, const QString &title,
                                const QString &message, const QList<ButtonSpec> &buttons,
                                Qt::Alignment textAlignment = Qt::AlignLeft | Qt::AlignVCenter)
        : QWidget(parent)
    {
        // WICHTIG: Qt::Widget ohne Window-/Dialog-Flags. QDialog wuerde auch
        // mit geaenderten Flags Dialog-Fokus und Top-Level-Verhalten behalten.
        // Nur ein echtes QWidget empfaengt die Ereignisse des DOS-Viewports.
        setWindowFlags(Qt::Widget);
        setObjectName(QStringLiteral("dbaseTurboMessageBox"));
        setWindowTitle(title);
        setFocusPolicy(Qt::StrongFocus);
        setMouseTracking(true);
        setAttribute(Qt::WA_TranslucentBackground, false);
        setAttribute(Qt::WA_NoSystemBackground, true);
        setMinimumWidth(380);
        setMaximumWidth(640);

        // Verfuegbare Schriftfamilien in dieser Reihenfolge auswaehlen.
        QFontDatabase fonts;
        QString family = QStringLiteral("Courier");
        for (const QString &candidate : {
             QStringLiteral("Consolas"), QStringLiteral("Courier New"),
             QStringLiteral("Courier")}) {
            if (fonts.hasFamily(candidate)) { family = candidate; break; }
        }
        QFont mono(family, 10);
        // Ein globales Qt5-Stylesheet kann ein geerbtes QWidget::setFont()
        // auf QLabel/QPushButton wieder ueberschreiben. Die Font-Familie
        // deshalb fuer JEDE Unterkomponente auch im lokalen QSS erzwingen.
        mono.setStyleHint(QFont::TypeWriter);
        mono.setStyleStrategy(QFont::PreferMatch);
        setFont(mono);
        const QString monoStyle = QStringLiteral(
            "QWidget#dbaseTurboMessageBox,"
            "QWidget#dbaseTurboMessageFrame,"
            "QWidget#dbaseTurboMessageHeading,"
            "QLabel#dbaseTurboMessageTitle,"
            "QLabel#dbaseTurboMessageText,"
            "QToolButton#dbaseTurboMessageClose,"
            "QPushButton#dbaseTurboDialogButton"
            "{font-family:'%1';font-size:10pt;}"
        ).arg(family);

        setStyleSheet(monoStyle + QStringLiteral(
            "QWidget#dbaseTurboMessageBox{background:transparent;color:#000000;border:none;}"
            "QWidget#dbaseTurboMessageFrame{background:#bdbdbd;color:#000000;"
            "border:none;}"
            "QWidget#dbaseTurboMessageHeading{background:#8c8c8c;color:#000000;border:none;}"
            "QLabel#dbaseTurboMessageTitle{background:#8c8c8c;color:#000000;"
            "font-weight:bold;padding:5px 10px;border:none;}"
            "QLabel#dbaseTurboMessageText{background:#bdbdbd;color:#000000;"
            "padding:12px;border:none;}"
            "QToolButton#dbaseTurboMessageClose{background:#ababab;color:#000000;"
            "border:1px solid #525252;font-weight:bold;padding:0px;}"
            "QToolButton#dbaseTurboMessageClose:hover{background:#dedede;}"
            "QPushButton#dbaseTurboDialogButton{background:#d0d0d0;color:#000000;"
            "border:2px outset #eeeeee;padding:4px 10px;}"
            "QPushButton#dbaseTurboDialogButton:hover{background:#dedede;}"
            "QPushButton#dbaseTurboDialogButton:pressed{background:#a8a8a8;}"
        ));

        auto *outer = new QVBoxLayout(this);
        // 2px gemalter Rahmen links/oben und 2px Rahmen + Schatten rechts/unten.
        // Der Inhalts-Frame liegt vollstaendig INNERHALB des gemalten Rahmens.
        outer->setContentsMargins(2, 2, 4, 4);
        outer->setSpacing(0);
        auto *frame = new QWidget(this);
        frame->setObjectName(QStringLiteral("dbaseTurboMessageFrame"));
        frame->setFont(mono);
        frame->setAutoFillBackground(true);
        outer->addWidget(frame);
        auto *layout = new QVBoxLayout(frame);
        layout->setContentsMargins(2, 2, 2, 2);
        layout->setSpacing(0);

        auto *heading = new QWidget(frame);
        heading->setObjectName(QStringLiteral("dbaseTurboMessageHeading"));
        heading->setFont(mono);
        heading->setCursor(Qt::SizeAllCursor);
        auto *titleRow = new QHBoxLayout(heading);
        titleRow->setContentsMargins(0, 0, 5, 0);
        titleRow->setSpacing(0);
        title_ = new QLabel(title.isEmpty() ? QStringLiteral("Information") : title, heading);
        title_->setObjectName(QStringLiteral("dbaseTurboMessageTitle"));
        QFont titleFont(mono);
        titleFont.setBold(true);
        title_->setFont(titleFont);
        title_->setMinimumHeight(29);
        title_->setCursor(Qt::SizeAllCursor);
        titleRow->addWidget(title_, 1);
        auto *closeButton = new QToolButton(heading);
        closeButton->setObjectName(QStringLiteral("dbaseTurboMessageClose"));
        closeButton->setFont(mono);
        closeButton->setText(QStringLiteral("×"));
        closeButton->setToolTip(QStringLiteral("Schließen"));
        closeButton->setCursor(Qt::ArrowCursor);
        closeButton->setFocusPolicy(Qt::NoFocus);
        closeButton->setFixedSize(23, 22);
        QObject::connect(closeButton, &QToolButton::clicked, this,
                         [this]() { done(Cancel); });
        titleRow->addWidget(closeButton);
        heading->installEventFilter(this);
        title_->installEventFilter(this);
        dragHeading_ = heading;
        layout->addWidget(heading);

        auto *content = new QLabel(message, frame);
        content->setObjectName(QStringLiteral("dbaseTurboMessageText"));
        content->setFont(mono);
        content->setWordWrap(true);
        // Optional zentrierter Text fuer Hilfe -> Ueber; die uebrigen
        // MessageBoxen behalten ihre bisherige linksbuendige Ausrichtung.
        content->setAlignment(textAlignment);
        content->setTextInteractionFlags(Qt::TextSelectableByMouse);
        // Stage 651: Im zentrierten "Hilfe -> Über ..."-Dialog weder ein
        // Textauswahl-Kontextmenü noch ein geerbtes QWidget-Kontextmenü.
        // Andere MessageBoxen behalten ihr bisheriges Verhalten.
        if (textAlignment & Qt::AlignHCenter) {
            setContextMenuPolicy(Qt::NoContextMenu);
            frame->setContextMenuPolicy(Qt::NoContextMenu);
            heading->setContextMenuPolicy(Qt::NoContextMenu);
            title_->setContextMenuPolicy(Qt::NoContextMenu);
            content->setContextMenuPolicy(Qt::NoContextMenu);
        }
        content->setMinimumHeight(78);
        layout->addWidget(content, 1);
        auto *row = new QHBoxLayout();
        row->setContentsMargins(12, 8, 12, 13);
        row->setSpacing(12);
        row->addStretch(1);
        for (const ButtonSpec &spec : buttons) {
            auto *button = new D64TurboDialogButton(spec.first, frame);
            button->setFont(mono);
            if (spec.second == Ok || spec.second == Save) button->setDefault(true);
            QObject::connect(button, &QPushButton::clicked, this,
                             [this, result = spec.second]() { done(result); });
            row->addWidget(button);
        }
        layout->addLayout(row);
        resize(440, 175);
    }

    // Position der MessageBox ist ein DOS-Zellenpaar, unabhaengig von
    // Pixelgroesse und vom Schriftfont des Dialogs.
    void setGridPosition(int column, int row)
    {
        QWidget *desktop = parentWidget() ? parentWidget()->parentWidget() : nullptr;
        const QPoint cells = d64_turbo_message_grid::clampCells(column, row, desktop);
        gridColumn_ = cells.x();
        gridRow_ = cells.y();
        setProperty("d64GridCol", gridColumn_);
        setProperty("d64GridRow", gridRow_);
        if (desktop)
            move(d64_turbo_message_grid::gridPixels(cells, desktop));
    }

    // Bei der QWidget-Variante steuert die Runtime das Ergebnis selbst.
    // Kein QDialog::done(), keine QDialog::finished-Signale und keine nativen
    // Fenster-/Modality-Ereignisse, die Klicks blockieren koennten.
    int result() const { return result_; }
    void setFinishedCallback(std::function<void(int)> callback)
    { onFinished_ = std::move(callback); }
    void done(int answer)
    {
        if (finished_) return;
        finished_ = true;
        result_ = answer;
        if (dragging_) {
            dragging_ = false;
            if (QWidget::mouseGrabber() == this) releaseMouse();
        }
        hide();
        if (onFinished_) onFinished_(answer);
    }

    // Den Desktop unabhaengig davon finden, ob der Aufruf von der
    // Hauptfenster-Menueleiste, einem Editor oder einem Werkzeug kommt.
    static QWidget *consoleDesktop(QWidget *origin)
    {
        if (!origin) return nullptr;
        for (QWidget *candidate = origin; candidate; candidate = candidate->parentWidget()) {
            if (candidate->objectName() == QLatin1String("dbaseConsole")) {
                if (auto *area = qobject_cast<QAbstractScrollArea *>(candidate))
                    return area->viewport();
            }
        }
        if (auto *area = origin->findChild<QAbstractScrollArea *>(
                QStringLiteral("dbaseConsole")))
            return area->viewport();
        // Auch fuer andere Runtime-Widgets nutzbar, ohne ein OS-Fenster
        // zu erzeugen: im aufrufenden QWidget einbetten.
        return origin;
    }

    static int showMessage(QWidget *parent, const QString &title,
                           const QString &message, const QList<ButtonSpec> &buttons,
                           Qt::Alignment textAlignment = Qt::AlignLeft | Qt::AlignVCenter)
    {
        QWidget *desktop = consoleDesktop(parent);
        if (!desktop) return Cancel;

        // Aufruf z.B. aus Hilfe -> Ueber ... erfolgt noch INNERHALB
        // von QMenu::triggered. Ein offenes Popup haelt unter Qt5 das
        // Mouse-Grab und wuerde sonst saemtliche Klicks im Dialog abfangen.
        if (QWidget *popup = QApplication::activePopupWidget())
            popup->close();

        // Stack-Lebensdauer: Dialog und Modalschicht werden beim Schliessen
        // gemeinsam freigegeben. Keine unverwalteten Top-Level-Fenster.
        D64TurboModalLayer layer(desktop);
        layer.setGeometry(desktop->rect());
        layer.show();
        layer.raise();
        D64TurboMessageBox box(&layer, title, message, buttons, textAlignment);
        const int availableWidth = qMax(1, layer.width() - 12);
        const int availableHeight = qMax(1, layer.height() - 12);
        box.setMinimumWidth(qMin(box.minimumWidth(), availableWidth));
        box.setMaximumWidth(qMin(box.maximumWidth(), availableWidth));
        box.resize(qMin(box.width(), availableWidth),
                   qMin(box.height(), availableHeight));
        // Zentrieren, aber sofort auf ganze DOS-Zeichenzellen rastern.
        const QSize grid = d64_turbo_message_grid::cellSize(desktop);
        box.setGridPosition(
            d64_turbo_message_grid::roundCells((layer.width() - box.width()) / 2,
                                               grid.width()),
            d64_turbo_message_grid::roundCells((layer.height() - box.height()) / 2,
                                               grid.height()));
        QEventLoop modalLoop;
        box.setFinishedCallback([&modalLoop](int) { modalLoop.quit(); });
        layer.setEscapeHandler([&box]() { box.done(Cancel); });
        box.show();
        box.raise();
        box.setFocus(Qt::OtherFocusReason);
        // Nested Qt-Eventloop verarbeitet MousePress/Release und Repaints
        // fuer die eingebetteten Widgets genauso wie fuer normale Editoren.
        modalLoop.exec(QEventLoop::AllEvents);
        return box.result();
    }
    static void information(QWidget *parent, const QString &message,
                            const QString &title = QStringLiteral("Information"),
                            Qt::Alignment textAlignment = Qt::AlignLeft | Qt::AlignVCenter)
    {
        showMessage(parent, title, message, {{QStringLiteral("OK"), Ok}}, textAlignment);
    }
    static int confirmSave(QWidget *parent)
    {
        return showMessage(parent, QStringLiteral("Information"),
                 QStringLiteral("Der Editorinhalt wurde geändert. Vor dem Schließen speichern?"),
                 {{QStringLiteral("Speichern"), Save},
                  {QStringLiteral("Verwerfen"), Discard},
                  {QStringLiteral("Abbrechen"), Cancel}});
    }
protected:
    void paintEvent(QPaintEvent *) override
    {
        // Der Rahmen ist eigene QWidget-Malerei (NICHT von Qt-Stylesheets
        // abhaengig). Der 2px-Schatten ragt rechts und unten aus dem Rahmen.
        QPainter painter(this);
        const QRect face = rect().adjusted(0, 0, -2, -2);
        painter.fillRect(rect(), Qt::transparent);
        painter.fillRect(rect().adjusted(2, 2, 0, 0), QColor(0x66, 0x66, 0x66));
        painter.fillRect(face, QColor(0xbd, 0xbd, 0xbd));
        QPen borderPen(QColor(0x52, 0x52, 0x52), 2);
        painter.setPen(borderPen);
        painter.drawRect(face.adjusted(1, 1, -1, -1));
    }
    bool eventFilter(QObject *watched, QEvent *event) override
    {
        if (watched == title_ || watched == dragHeading_) {
            switch (event->type()) {
            case QEvent::MouseButtonPress: {
                auto *mouse = static_cast<QMouseEvent *>(event);
                if (mouse->button() == Qt::LeftButton) {
                    dragging_ = true;
                    dragStartGlobal_ = mouse->globalPos();
                    dragStartWindow_ = pos();
                    dragStartColumn_ = gridColumn_;
                    dragStartRow_ = gridRow_;
                    // Mit explizitem Mouse-Grab erreichen auch Bewegungen
                    // ausserhalb des Titel-Labels weiter dieses Fenster.
                    grabMouse();
                    return true;
                }
                break;
            }
            case QEvent::MouseMove: {
                auto *mouse = static_cast<QMouseEvent *>(event);
                if (dragging_ && (mouse->buttons() & Qt::LeftButton)) {
                    updateDragPosition(mouse->globalPos());
                    return true;
                }
                break;
            }
            case QEvent::MouseButtonRelease: {
                auto *mouse = static_cast<QMouseEvent *>(event);
                if (dragging_ && mouse->button() == Qt::LeftButton) {
                    dragging_ = false;
                    if (QWidget::mouseGrabber() == this) releaseMouse();
                    return true;
                }
                break;
            }
            default: break;
            }
        }
        return QWidget::eventFilter(watched, event);
    }
    void mouseMoveEvent(QMouseEvent *event) override
    {
        if (dragging_ && (event->buttons() & Qt::LeftButton)) {
            updateDragPosition(event->globalPos());
            event->accept();
            return;
        }
        QWidget::mouseMoveEvent(event);
    }
    void mouseReleaseEvent(QMouseEvent *event) override
    {
        if (dragging_ && event->button() == Qt::LeftButton) {
            updateDragPosition(event->globalPos());
            dragging_ = false;
            if (QWidget::mouseGrabber() == this) releaseMouse();
            event->accept();
            return;
        }
        QWidget::mouseReleaseEvent(event);
    }
    void keyPressEvent(QKeyEvent *event) override
    {
        if (event->key() == Qt::Key_Escape) {
            done(Cancel);
            event->accept();
            return;
        }
        QWidget::keyPressEvent(event);
    }
    void closeEvent(QCloseEvent *event) override
    {
        done(Cancel);
        event->accept();
    }
private:
    void updateDragPosition(const QPoint &global)
    {
        QWidget *desktop = parentWidget() ? parentWidget()->parentWidget() : nullptr;
        if (!desktop) return;
        const QSize grid = d64_turbo_message_grid::cellSize(desktop);
        const QPoint delta = global - dragStartGlobal_;
        setGridPosition(
            dragStartColumn_ + d64_turbo_message_grid::roundCells(delta.x(), grid.width()),
            dragStartRow_ + d64_turbo_message_grid::roundCells(delta.y(), grid.height()));
    }
    int result_ = Cancel;
    bool finished_ = false;
    std::function<void(int)> onFinished_;
    QWidget *dragHeading_ = nullptr;
    QLabel *title_ = nullptr;
    bool dragging_ = false;
    QPoint dragStartGlobal_;
    QPoint dragStartWindow_;
    int gridColumn_ = 0;
    int gridRow_ = 0;
    int dragStartColumn_ = 0;
    int dragStartRow_ = 0;
};
