# Stage 628 – Turbo-Vision-Mehrfenstereditor

**Verbindliche Grundlage:** Stage 627, unveränderte Runtime-Schnittstelle (keine neue Exportfunktion).

## Fensteroberfläche

* `D64TurboEditorWidget` in `d64qt5/d64_turbo_editor.hpp` verwendet einen gelben Doppelrahmen, blauen Zeichenbereich, weiße Schrift, eine etwas hellere blaue Titelleiste und einen Schatten.
* Rechts oben: Maximieren/Wiederherstellen; auch Doppelklick auf Titelleiste.
* Links oben: `×` schließt **nur nach Doppelklick**. Jedes Schließen passiert durch `closeEvent()` mit Prüfung auf ungespeicherte Inhalte.
* Rechts unten: Griff für Größenänderung in ganzen DOS-Zeichenzellen; Position, Fenstergröße und Max/Restore berücksichtigen die aktuellen Font-Zellen und den Zoomfaktor.
* Vertikal rechts: klickbare Pfeile oben/unten. Horizontal: im unteren Fensterstreifen, mit Pfeilen links/rechts. Unten links auf derselben Zeile: `Zeile : Spalte`.
* Die Pfeile (`D64TurboArrowScrollBar` in `d64qt5/d64_turbo_scrollbar.hpp`) sind auf die nativen QScrollBar-Schaltflächen gemalt; Qt übernimmt Scrollen und Maus-/Thumb-Interaktion. Die grünen Ausgabescrollbars benutzen denselben Widget-Typ mit grüner Farbgebung.
* Deutsches Kontextmenü mit Rückgängig/Strg+Z, Wiederherstellen/Strg+Y, Ausschneiden/Strg+X, Kopieren/Strg+C, Einfügen/Strg+V, Löschen/Entf, Alles auswählen/Strg+A. Nicht verfügbare Aktionen sind deaktiviert.

## Mehrere Editoren

`d64qt5/d64qt5_bridge.cpp` verwaltet `g_turbo_editors` (QPointer-Liste) und `g_turbo_editor` als aktuell aktive Instanz. **Datei → Neu** erstellt bei jedem Klick ein eigenständiges Editorfenster mit eigenem Text, Undo-Stack und Datei. **Datei → Öffnen** öffnet eine Datei in einem neuen Fenster. Dateispeicher- und Bearbeitenaktionen betreffen nur die aktive Instanz. **Alle Schließen** fragt jedes bearbeitete Dokument ab und bricht bei „Abbrechen“ ab. Beim Beenden des Hauptfensters werden alle ungespeicherten Dokumente geprüft.

## Modale Schließabfrage und VFS

* Geänderte Dokumente: modale, farblich angepasste Abfrage „Speichern“, „Verwerfen“, „Abbrechen“.
* „Speichern“ öffnet für das Schließen immer den VFS-Dateidialog (auch bei bereits benannten Dateien), damit die Zweiteilung links Ordner / rechts Dateien zur Auswahl bereitsteht.
* VFS: pro EXE festes Host-Verzeichnis, Pfadvalidierung und QSaveFile/UTF-8 unverändert aus Stage 626.
* Bei „Abbrechen“ bleibt das Editorfenster geöffnet und der Text erhalten.

## Installation

Die Datei `build_and_deploy_dbase_editor_stage628.bat` baut die Qt5-Bridge mit `d64qt5/build_d64qt5_mingw32.bat` und kopiert die DLL nach `runtime\dbase\pe32` (optional anderer Zielpfad als Argument). Die dBASE-EXE braucht für eine reine Änderung dieser Widget-DLL keinen neuen Compilerlauf, sofern sie die gleiche DLL-Laufzeit-ABI benutzt.

## Prüfstatus

Quellcode- und Python-Regressionstests; ein nativer Qt5-MinGW32-Build und eine Maus-/Zoom-Sichtprüfung müssen unter Windows stattfinden.
