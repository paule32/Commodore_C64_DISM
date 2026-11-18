#pragma once
// Stage 633: gleicher grauer Kontextmenue-Stil fuer Editor und Rechner.
// Nimmt keine Aenderung an den globalen Turbo-Vision-Menues vor.
#include <QString>

inline QString d64TurboGreyContextMenuStyle()
{
    return QStringLiteral(
        "QMenu{background:#c6c6c6;color:#000000;border:2px solid #626262;"
        "padding:3px;}"
        "QMenu::item{background:transparent;color:#000000;padding:5px 28px 5px 10px;}"
        "QMenu::item:selected{background:#888888;color:#ffffff;}"
        "QMenu::item:disabled{color:#656565;}"
        "QMenu::separator{height:1px;background:#858585;margin:4px 7px;}"
    );
}
