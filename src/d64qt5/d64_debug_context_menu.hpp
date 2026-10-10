// Stage 324 – German DEBUG menu with true Qt shortcut columns and stable localization markers.
#pragma once

#include <QAction>
#include <QContextMenuEvent>
#include <QMenu>
#include <QKeySequence>
#include <QPalette>
#include <QPlainTextEdit>
#include <QTextCursor>
#include <QTextDocument>
#include <QScrollBar>

#include <functional>
#include <utility>

// Read-only DEBUG output remains a QPlainTextEdit, including its built-in
// Ctrl+C and Ctrl+A keyboard handling. Only the popup is customized.
class D64DebugOutputTextEdit final : public QPlainTextEdit
{
public:
    explicit D64DebugOutputTextEdit(QWidget *parent = nullptr)
        : QPlainTextEdit(parent)
    {
        setContextMenuPolicy(Qt::DefaultContextMenu);
        setProperty("d64DebugContextMenuLocalization", true);
    }

    // Runtime/Runner can pause their output repaint and foreground watchdog
    // for the complete lifespan of the popup, including QAction callbacks.
    void setContextMenuStateHandler(std::function<void(bool)> callback)
    {
        contextMenuStateHandler_ = std::move(callback);
    }

    // Called BEFORE clearing the editor so that buffered runner output is
    // discarded and does not immediately reappear after the popup closes.
    void setDebugClearHandler(std::function<void()> callback)
    {
        clearHandler_ = std::move(callback);
    }

    void setDebugContextDark(bool dark)
    {
        darkContextMenu_ = dark;
        setProperty("d64DebugContextDark", dark);
    }

protected:
    void contextMenuEvent(QContextMenuEvent *event) override
    {
        if (!event)
            return;

        QMenu menu(this);
        // Stable selectors for future localization and independent QSS.
        menu.setObjectName(QStringLiteral("d64DebugContextMenu"));
        menu.setProperty("d64LocalizationKey", QStringLiteral("debug.context.menu"));

        // Stage 328: first command clears the document AND any pending
        // asynchronous output. Stable identifiers support later localization.
        QAction *clearAction = menu.addAction(QStringLiteral("Bereinigen"));
        clearAction->setObjectName(QStringLiteral("d64DebugContextClear"));
        clearAction->setProperty("d64LocalizationKey", QStringLiteral("debug.context.clear"));
        QObject::connect(clearAction, &QAction::triggered, this, [this]() {
            if (clearHandler_)
                clearHandler_();
            clear();
            QTextCursor cursor = textCursor();
            cursor.movePosition(QTextCursor::Start);
            setTextCursor(cursor);
            if (QScrollBar *vertical = verticalScrollBar())
                vertical->setValue(vertical->minimum());
            if (QScrollBar *horizontal = horizontalScrollBar())
                horizontal->setValue(horizontal->minimum());
            // Both bars already use ScrollBarAsNeeded: the empty document
            // naturally removes them; never force-hide the widgets because
            // later DEBUG output must make them visible again when needed.
            updateGeometry();
            viewport()->update();
        });
        QAction *clearSeparator = menu.addSeparator();
        clearSeparator->setObjectName(QStringLiteral("d64DebugContextClearSeparator"));

        // QAction titles contain ONLY the labels; Qt draws shortcuts in
        // the dedicated right-hand column of QMenu automatically.
        QAction *copyAction = menu.addAction(QStringLiteral("Kopieren"));
        copyAction->setShortcut(QKeySequence(QKeySequence::Copy));
        copyAction->setProperty("d64ShortcutLabel", QStringLiteral("STRG + C"));
        copyAction->setObjectName(QStringLiteral("d64DebugContextCopy"));
        copyAction->setProperty("d64LocalizationKey", QStringLiteral("debug.context.copy"));
        copyAction->setEnabled(textCursor().hasSelection());
        QObject::connect(copyAction, &QAction::triggered, this, [this]() { copy(); });

        QAction *selectAllAction = menu.addAction(QStringLiteral("Alles makieren"));
        selectAllAction->setShortcut(QKeySequence(QKeySequence::SelectAll));
        selectAllAction->setProperty("d64ShortcutLabel", QStringLiteral("STRG + A"));
        selectAllAction->setObjectName(QStringLiteral("d64DebugContextSelectAll"));
        selectAllAction->setProperty("d64LocalizationKey", QStringLiteral("debug.context.select_all"));
        selectAllAction->setEnabled(!document()->isEmpty());
        QObject::connect(selectAllAction, &QAction::triggered, this, [this]() { selectAll(); });

        // Never let the native Windows popup override DEBUG's selected theme.
        if (darkContextMenu_) {
            menu.setStyleSheet(QStringLiteral(
                "QMenu#d64DebugContextMenu{background:#171717;color:#eeeeee;"
                "border:1px solid #5f5f5f;padding:4px;}"
                "QMenu#d64DebugContextMenu::item{color:#eeeeee;"
                "background:transparent;padding:6px 24px 6px 12px;}"
                "QMenu#d64DebugContextMenu::item:selected{background:#0b2f63;color:#ffffff;}"
                "QMenu#d64DebugContextMenu::item:disabled{color:#808080;}"
                "QMenu#d64DebugContextMenu::separator{height:1px;background:#515151;margin:4px 7px;}"
            ));
        } else {
            menu.setStyleSheet(QStringLiteral(
                "QMenu#d64DebugContextMenu{background:#f3f3f3;color:#141414;"
                "border:1px solid #a2a2a2;padding:4px;}"
                "QMenu#d64DebugContextMenu::item{color:#141414;"
                "background:transparent;padding:6px 24px 6px 12px;}"
                "QMenu#d64DebugContextMenu::item:selected{background:#c4daf3;color:#101010;}"
                "QMenu#d64DebugContextMenu::item:disabled{color:#808080;}"
                "QMenu#d64DebugContextMenu::separator{height:1px;background:#b6b6b6;margin:4px 7px;}"
            ));
        }

        // exec() runs a nested Qt event loop. Inform the Runner BEFORE it
        // starts so its 500-ms foreground watchdog cannot close the popup;
        // resume only AFTER QAction::triggered has completed.
        if (contextMenuStateHandler_)
            contextMenuStateHandler_(true);
        menu.exec(event->globalPos());
        if (contextMenuStateHandler_)
            contextMenuStateHandler_(false);
        event->accept();
    }

private:
    bool darkContextMenu_ = false;
    std::function<void(bool)> contextMenuStateHandler_;
    std::function<void()> clearHandler_;
};
