# Stage 636 – MessageBox: Qt5-Ereignisse, Escape und Consolas

**Verbindliche Ausgangsbasis:** `d64_dism_stage635.zip`.

## Fehlerbild

Die interne graue MessageBox blieb nach Stage 635 bei Windows ohne wirksame Maus- und Tastaturbedienung (kein Drag, OK, × und Esc ohne Wirkung). Außerdem wurde Consolas nicht zuverlässig sichtbar verwendet.

## Ursache und Änderung

* `D64TurboModalLayer` besitzt einen **anwendungsweiten Eventfilter**. In Qt5 treffen Eingabe-Events zunächst auch auf **native QWindow-/QWidgetWindow-Empfänger**. Der ursprüngliche Filter hielt sie für außerhalb der eingebetteten Ebene und verwarf sie vor der Qt-Weitergabe an `QWidget`. Jetzt werden Events an native, nicht vom QWidget-Typ abgeleitete Empfänger durchgelassen, sodass sie die internen Bedienelemente erreichen. Erst bei der Weitergabe an andere QWidget-Ziele werden fremde Eingaben blockiert.
* **Escape** erhält eine zusätzliche Behandlung für Eingaben an native Eventempfänger. Die bisherige `keyPressEvent`-Behandlung der MessageBox bleibt erhalten.
* **Titelleiste**: Beim Ziehen wird die Maus erfasst (`grabMouse`) und beim Loslassen wieder freigegeben. Die Positionsberechnung bleibt auf den Konsolen-Viewport begrenzt.
* **OK/×**: Beide Buttons rufen weiterhin `done` auf; ihre Events werden durch den korrigierten Filter nicht mehr im Vorfeld blockiert.
* **Schrift**: Font-Auswahl in der Reihenfolge `Consolas` → `Courier New` → `Courier`. Die ermittelte Schrift wird als `QFont` auf sämtliche Text-Widgets gesetzt und als explizite `font-family` im **lokalen Stylesheet** hinterlegt, damit die globalen Qt5-Styles den Font nicht überschreiben.
* Die MessageBox bleibt ein **eingebettetes QWidget** mit modaler Ebene, 2-Pixel-Rahmen und Schatten. Weitere Runtime-DLL-Exporte werden nicht hinzugefügt.

## Installation (Windows 32 Bit / MinGW32 / Qt5)

1. Alle laufenden Anwendungen schließen, die `libd64_qt5.dll` verwenden.
2. Aus dem entpackten Stage-636-Projekt `build_and_deploy_dbase_editor_stage636.bat` starten.
3. Eine dBASE-EXE starten, `Hilfe` → `Über ...` aufrufen.
4. **Drag**, **OK**, **×**, **Escape** nacheinander ausprobieren (Dialog jeweils neu öffnen).
5. Text an Titel, Inhalt und Buttons auf **Consolas** prüfen. Falls Consolas auf dem Host nicht installiert ist, wird auf Courier New / Courier zurückgegriffen.
6. Einen geänderten Editor schließen und die Speicherabfrage per Buttons sowie Escape testen.

## Tests und Grenzen

Die neuen Tests prüfen die Trennung von nativen Qt-Events und QWidget-Events, den Escape-Fallback, die Drag-Funktionen, die verdrahteten Dialogbuttons sowie die Font-Zuweisungen. Frühere Regressionstests werden ebenfalls ausgeführt. Diese strukturellen Tests **ersetzen keinen nativen Win32-/Qt5-GUI-Lauf**; die tatsächliche Bedienung kann erst nach dem DLL-Neubau unter Windows bestätigt werden.
