# Stage 631 – Turbo-Vision-Werkzeuge, Fensterverwaltung und MessageBox

**Verbindliche Basis:** Stage 630. Keine Änderungen am dBL-Parser, Assembler oder Linker. Die Runtime-Erweiterung benötigt einen Neubau von `libd64_qt5.dll`.

## Menü `=`

- **Taschenrechner:** separates blaues DOS-Fenster, Eingabefeld und Zahlentasten. Unterstützt `+`, `-`, `*`, `/`, Vorzeichen, Dezimalpunkt, Klammern und Punkt-vor-Strich. `Enter` oder `=` berechnet. Sichere eigene rekursive Grammatik (keine dynamische Codeausführung); Division durch null wird gemeldet.
- **ASCII-Zeichentabelle:** 16×16-Matrix mit allen DOS-CP437-Zeichencodes 0–255. Auswahl zeigt Dezimal- und Hexwert; Doppelklick kopiert das Zeichen in die Zwischenablage. Glyphen stammen aus der bereits in Stage 622 vorhandenen `D64TurboOutputWidget::dosCharacter`-Tabelle.
- **Puzzle:** klassisches 4×4-Schiebepuzzle mit 15 Steinen. Mischen durch 180 gültige Verschiebungen aus dem gelösten Zustand, deshalb lösbar. Klick auf einen direkt benachbarten Stein verschiebt ihn in das freie Feld. Anzeige der Züge und Meldung beim Lösen.

Alle drei sind eigenständige, verschiebbare und maximierbare Turbo-Vision-Fenster im vorhandenen 80×25-QPlainTextEdit-Viewport. Sie nehmen an der Zoom- und Zeichenrasterlogik teil. Bestehende Editoren und die grüne Ausgabe bleiben geöffnet.

## Hauptmenü `Fenster`

- **Kaskadieren:** ordnet die derzeit sichtbaren Turbo-Vision-Fenster versetzt an.
- **Nebeneinander:** kachelt die Fenster im verfügbaren Zeichenraster.
- Nach dem Separator steht eine **dynamisch aufgebaute Liste** aller sichtbaren Editor-, Ausgabe- und Werkzeugfenster. Ein Klick aktiviert das gewählte Fenster und bringt es vor die anderen.
- Die Liste wird nach Öffnen/Schließen neu aufgebaut und vor jeder Anzeige aktualisiert.

## Hauptmenü `Hilfe` → `Über ...`

Zentrale Klasse `D64TurboMessageBox` in `d64qt5/d64_turbo_messagebox.hpp`:
- frameless, modal, graue Fläche und etwas dunklere graue Titelleiste; schwarze Schrift; normaler Rahmen;
- Titel `Information`; keine Maximieren-, Wiederherstellen- oder Schließen-Schaltflächen;
- standardmäßig `OK` mit `clicked()` → Schließen; durch andere Buttonlisten auch `Speichern`, `Verwerfen`, `Abbrechen`, `Hilfe` etc.;
- bei Maustastendruck wird die Schaltfläche um 3 px nach rechts/unten versetzt, bei Loslassen/Verlassen zurückgestellt.

Die Editor-Schließabfrage verwendet dieselbe Klasse. Bei `Speichern` öffnet sich weiterhin der zweigeteilte virtuelle Dateidialog, bei `Abbrechen` bleibt der Editor geöffnet.

## Mauszeiger

- Beide Editor-Scrollleisten haben explizit `Qt::ArrowCursor`.
- Das editierbare `QPlainTextEdit` und sein Viewport verwenden `Qt::IBeamCursor`.
- Die übrigen Cursor (Fensterverschieben, Größenanfasser, Titelleistenbuttons) bleiben erhalten.

## Dateien

Geändert: `d64qt5/d64qt5_bridge.cpp`, `d64qt5/d64_turbo_editor.hpp`, `d64qt5/d64_turbo_output.hpp`.

Neu: `d64qt5/d64_turbo_tools.hpp`, `d64qt5/d64_turbo_messagebox.hpp`, `d64qt5/d64_turbo_calculator_expression.hpp`, `test_stage631.py`, `build_and_deploy_dbase_editor_stage631.bat`, diese Dokumentation.

## Build unter Windows

```bat
build_and_deploy_dbase_editor_stage631.bat
```

Optional kann ein anderes Runtime-Verzeichnis als erster Parameter angegeben werden. Alle laufenden dBASE-EXE-Prozesse vorher beenden. Für diese reine GUI-Änderung ist kein erneuter EXE-Link erforderlich.

## Prüfstatus

Der Ausdrucksparser wird nativ mit `g++ -std=c++17 -Wall -Wextra -Werror` getestet. GUI- und Regressionstests sind statische Quellcode-/Schnittstellenprüfungen. Native Qt5-/MinGW32-Kompilierung und visuelle Mausprüfung sind hier nicht verfügbar und müssen auf Windows bestätigt werden.
