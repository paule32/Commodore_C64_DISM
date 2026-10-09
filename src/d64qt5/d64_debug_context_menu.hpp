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
            ));
        } else {
            menu.setStyleSheet(QStringLiteral(
                "QMenu#d64DebugContextMenu{background:#f3f3f3;color:#141414;"
                "border:1px solid #a2a2a2;padding:4px;}"
                "QMenu#d64DebugContextMenu::item{color:#141414;"
                "background:transparent;padding:6px 24px 6px 12px;}"
                "QMenu#d64DebugContextMenu::item:selected{background:#c4daf3;color:#101010;}"
                "QMenu#d64DebugContextMenu::item:disabled{color:#808080;}"
            ));
        }

        menu.exec(event->globalPos());
        event->accept();
    }

private:
    bool darkContextMenu_ = false;
};
