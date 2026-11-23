# Stage 666 – Turbo-Vision-Hilfe: garantierter Abstand einer DOS-Zeichenspalte

**Verbindliche Grundlage:** `d64_dism_stage665.zip`.

## Fehlerursache in Stage 665

Der seit Stage 664/665 gewünschte Texteinzug wurde nur über ein CSS-`padding-left` im
`<body>` des an `QTextBrowser::setHtml()` übergebenen HTML-Dokuments umgesetzt.
Der Qt5-Rich-Text-Renderer wertet dieses CSS nicht auf allen Systemen zuverlässig
als tatsächlichen linken Abstand aus. Das Resultat: Der erste Buchstabe liegt
weiterhin direkt am inneren linken Fensterrand.

## Korrektur

Die Datei `d64qt5/d64_turbo_help_window.hpp` besitzt nun die zentrale Methode
`setHelpHtml(const QString &source)`:

1. Sie erzeugt das formatierte Dokument über `browser_->setHtml(renderMarkup(source))`.
2. **Danach** holt sie den wirklichen Dokumentrahmen mit
   `browser_->document()->rootFrame()`.
3. Mit `QTextFrameFormat::setLeftMargin(qMax(1, gridCellWidth_))` setzt sie einen
   vollständigen Zeichenblock als Abstand zwischen Fensterinnenkante und Text.
4. Die übrigen Dokumentränder (`top`, `right`, `bottom`) bleiben bei 0.
5. Der geänderte Rahmen wird durch `root->setFrameFormat(format)` tatsächlich auf
   das Layout angewendet.

Es bleibt somit stets **eine durchgehend cyanfarbene Leer-Spalte** zwischen
linkem Fensterrahmen und Hilfetext. Diese Leerspalte gilt auch für Links,
Nummern-Themen und Fehlermeldungen. Die Größe einer Zeichenspalte wird aus
`gridCellWidth_` übernommen und beim Wechsel der DOS-Konsolenschrift neu gesetzt.

Das bisherige HTML-`padding-left` wurde auf `padding:0` zurückgesetzt, damit
keine doppelte Einrückung bei anderen Qt-Versionen entstehen kann.

## Unverändertes Verhalten

- Gelber Außenrahmen 2 Pixel, harter Schatten +5/+5 Pixel.
- Titelleiste `Hilfe:  <Hilfethema>`.
- Hilfethemen über Namen und numerische Hilfenummern.
- Rasterweises Verschieben und Größenändern.
- Pfeil-Scrollbalken und Linknavigation.
- `.hlp`/`.mo`-Dateiformat, Hilfecompiler sowie Gutter/Minimap unverändert.

## Windows-Build

Nach Entpacken im bestehenden C64-Frontend-Verzeichnis:

```bat
build_and_deploy_dbase_editor_stage666.bat
```

Nur `libd64_qt5.dll` muss neu erstellt und eingesetzt werden. Die `.thlp`
Quellen und `.hlp` Hilfedateien müssen nicht erneut kompiliert werden.
Stelle sicher, dass die tatsächlich verwendete Laufzeitumgebung die neue DLL
lädt (Programm nach DLL-Tausch neu starten).

## Verifikation

- 111 Tests aus Stage 650–659 und 661–666 erfolgreich (inklusive fünf neuen
  Prüfungen für die Positionierung auf dem `QTextDocument`-Root-Frame).
- Python-Testprüfungen der früheren CSS-Annahme aus Stage 664/665 wurden an die
  jetzt verwendete Qt5-Rahmenformatierung angepasst.
- Archiv-CRC geprüft.
- **Kein nativer Windows-/Qt5-GUI-Test in dieser Umgebung**; visuelle Prüfung
  nach dem Neuaufbau der DLL ist noch erforderlich.
