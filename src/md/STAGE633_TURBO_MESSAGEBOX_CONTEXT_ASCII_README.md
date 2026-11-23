# Stage 633 – Turbo-Vision-Dialog, ASCII-Tabelle, Kontextmenüs und Taschenrechner

**Verbindliche Basis:** d64_dism_stage632.zip. Alle anderen Programmteile bleiben erhalten.

## MessageBox (`d64qt5/d64_turbo_messagebox.hpp`)

- Die zentrale `D64TurboMessageBox` bleibt modal und unterstützt weiter frei konfigurierbare Aktionsbuttons (OK, Speichern, Verwerfen, Abbrechen usw.).
- Dragging der eigenen Titelleiste mit linker Maustaste (Mausereignisse auf Hintergrund und Titeltext).
- Schriftfamilien in Prioritätsfolge **Consolas → Courier New → Courier**; monospace 10 pt.
- Grauer Hintergrund `#bdbdbd`, dunklere Titelleiste `#8c8c8c`, schwarze Schrift.
- **2 px** Rahmen (`#525252`) und **2 px** sichtbarer Schatten rechts/unten (`#666666`); der Frame wird innerhalb eines frameless Qt-Dialogs angeordnet.
- Eigenes `×` rechts in der Titelleiste schließt den Dialog mit Resultat `Cancel`; weder Max-/Restore-Buttons noch native Titelbuttons.
- Die 3-px-Drückanimation der Aktionsbuttons wurde unverändert übernommen.

## ASCII-Zeichentabelle (`d64qt5/d64_turbo_tools.hpp`)

`QTableWidget` verwendet jetzt horizontal und vertikal jeweils `D64TurboArrowScrollBar` mit sichtbaren Pfeilen, punktierter Laufbahn und Thumb-Clamping aus Stage 630. Beide Leisten sind auch bei vollständig sichtbaren Tabellenbereichen vorhanden. Auswahl, CP437-Darstellung und Doppelklick-zum-Kopieren bleiben erhalten.

## Graue Kontextmenüs (`d64qt5/d64_turbo_context_menu.hpp`)

Beide Kontextmenüs werden aus einem gemeinsamen Stylesheet gezeichnet: hellgrauer Hintergrund `#c6c6c6`, schwarze Schrift, graue Selektion. Dadurch sehen das Editor-Kontextmenü und das Kontextmenü des Taschenrechners gleich aus. Das deutsche Rechner-Menü ist am Formeleditor und an der freien Rechnerfläche verfügbar und bietet Rückgängig, Wiederherstellen, Ausschneiden, Kopieren, Einfügen, Löschen und Alles auswählen mit den entsprechenden Shortcuts.

## Taschenrechner

- Auf den Zifferntasten `0`–`9` und dem Dezimalpunkt wird der Handcursor (`Qt::PointingHandCursor`) verwendet; die anderen Cursorformen bleiben unverändert.
- Die bisher unter dem Tastenfeld angezeigte Hinweiszeile „Punkt vor Strich · Klammern · Enter =“ wurde entfernt.
- Die Rechenlogik (einschließlich Punkt-vor-Strich, Klammern, Fehlerbehandlung) bleibt unverändert.

## Windows-Build

1. EXE-Anwendungen schließen, die `libd64_qt5.dll` geladen haben.
2. Im entpackten Projekt **`build_and_deploy_dbase_editor_stage633.bat`** ausführen.
3. Die neu gebaute DLL wird standardmäßig nach `runtime\dbase\pe32` kopiert. Optional kann dem Skript das Zielverzeichnis als erstes Argument übergeben werden.
4. Die GUI neu starten. Die dBASE-EXE muss für diese reine DLL-/GUI-Erweiterung nicht neu kompiliert werden.

## Tests

98 automatisierte Prüfungen der Stages 620, 621, 622, 628, 629, 630, 631, 632 und 633 bestanden. Darunter eine C++-Kompilierungs-/Ausführungsprobe des Taschenrechner-Parsers; alle GUI-Tests sind hier nur statische Integrationstests. **Nicht bestätigt:** Vollständiger nativer Qt5-/MinGW32-Build und die visuelle Bedienung auf Windows.
