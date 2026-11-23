# Stage 644 – Interner Datei-Öffnen-/Speichern-Dialog: Titelleiste, Maus und Breite

**Verbindliche Basis:** `d64_dism_stage643.zip`. Alle VFS-Mounts, Rechteprüfungen, die Datei-Öffnen-Logik, die Editor-Mehrfensterverwaltung und die Qt5-Runtime bleiben unverändert.

## Oberflächenänderungen

* **Hellere blaue Titelleiste:** `#2256CF` statt der bisherigen dunkelblauen Fläche; im Light Mode entsprechend hellblau.
* **Drei Pixel weniger Dialogbreite:** der voreingestellte Wert beträgt 767 statt 770 Pixel. Auch der im `exec()` aus dem Konsolen-Viewport berechnete Wert wird um drei Pixel reduziert; die minimale Breite ist entsprechend 557 statt 560 Pixel.
* **Schließen links oben:** Ein `×`-Button (`dbaseVirtualFileClose`) in der Titelleiste bricht die Auswahl ab. Die Aktion liefert wie „Abbrechen“ `Rejected` zurück. Bei **Datei → Öffnen** entsteht daher kein Editor.
* **Verschieben:** Ein Linksklick mit Ziehen auf Titelleiste, Text oder rechter Ausgleichsfläche verschiebt das interne Fenster **in ganzen DOS-Zeichenblöcken**. Grundlage ist das aktuelle Zeichenraster der `QPlainTextEdit`-Konsole einschließlich Zoom. Die Position wird in den Properties `d64GridCol`/`d64GridRow` gespeichert, sodass die Modalschicht sie bei Font-/Viewportänderungen rekonstruieren kann. Die Titelleiste kann wie in den bestehenden Turbo-Vision-Fenstern bis Zeile 24 reichen; rechts darf der Fensterrumpf über den sichtbaren Bereich hinausragen, mindestens zehn Titelspalten bleiben erreichbar.
* **Kein Kontextmenü:** Die Qt-Kontextmenüs sind am Dialog, dessen vorhandenen Unterwidgets einschließlich Eingabezeilen/Listen und in eingebetteten Eingabe-/Bestätigungsdialogen deaktiviert. `QEvent::ContextMenu` wird durch den Dialogfilter verbraucht.
* **Mauszeiger:** Auf freien Flächen, Titelleiste, Eingabezeilen, Splitter und Scrollleisten der normale Pfeil (`Qt::ArrowCursor`). Über **tatsächlichen** Datei-/Verzeichniseinträgen links und rechts wechselt der Cursor zu `Qt::PointingHandCursor`; über leerem Listenraum wieder zum Pfeil. Unten zeigen „Verz. Hinzufügen“, „Löschen“, „OK“, „Abbrechen“, „Hilfe“ und der Titel-`×`-Button den Handcursor. Die Eingabe-/Bestätigungsdialoge haben ebenfalls Handcursor auf ihren Buttons.

## Technische Änderungen

`d64qt5/d64_turbo_editor.hpp`: ausschließlich `D64VirtualFileDialog` und der benötigte `QContextMenuEvent`-Include. Die neue Titelleiste ist ein internes `QWidget`, keine neue native OS-Dialogbox. Die Schleife bleibt `D64TurboModalLayer` + `QEventLoop`.

**Unverändert:** `D64ApplicationVfs` und die Benutzertrennung (`/Alle Benutzer` sowie private `/Dokumente`), `..`-Navigation, der Datei-Öffnen-Menüpfad, Dateiformate `.prg`/`.wfm`, doppelklickbares Öffnen, Speichern, Löschen sowie alle anderen Fenster und Editoren.

## Installation

1. Laufende dBASE-EXE(s) beenden.
2. `build_and_deploy_dbase_editor_stage644.bat [optional: Ausgabeverzeichnis]` im Projektverzeichnis auf Windows ausführen.
3. Neue Anwendung starten, „Datei → Öffnen...“ aufrufen, Titelleiste verschieben und über `×` abbrechen. Dabei darf kein Editor entstehen.
4. Jeweils auf einen Verzeichniseintrag, freien Listenraum, Dateieintrag und unteren Button zeigen; Cursorform kontrollieren; Rechtsklick in Eingabezeilen/Listen darf kein Kontextmenü öffnen.
5. Optional Zoom wechseln, Dialog neu öffnen/verschieben und prüfen, dass jede Bewegung auf das Zeichenraster einrastet.

## Prüfstatus

Automatisierte Python-Quellcode-/Integrations- und Regressionstests sind enthalten. **Wichtig:** Diese Tests ersetzen keinen nativen Qt5-/MinGW32-Build oder interaktiven Windows-GUI-Test. Der echte GUI-Lauf muss auf Windows geprüft werden.
