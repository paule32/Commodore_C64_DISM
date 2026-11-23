# Stage 635 – Interaktive Turbo-Vision-MessageBox

**Verbindliche Basis:** `d64_dism_stage634.zip`.

## Fehlerbild und Ursache

Unter Windows wurde die interne MessageBox zwar geöffnet, jedoch waren der graue
2-Pixel-Rahmen nicht sichtbar, die Titelleiste nicht verschiebbar und weder
`OK` noch der Schließen-Button `×` reagierten. Stage 634 erbte weiterhin von
`QDialog` und stellte ihn mittels `Qt::Widget`-Flags als Kindfenster dar. Das
ist für die gewünschte interne, überlagerte Turbo-Vision-Meldungsbox unnötig
anfällig: `QDialog` besitzt eine eigene Fenster- und Ergebnissteuerung. Zudem
kann ein beim Aufruf noch offenes `QMenu` die Maus weiterhin exklusiv erfassen.

## Umsetzung

Geändert: `d64qt5/d64_turbo_messagebox.hpp`.

* `D64TurboMessageBox` ist nun ein echtes `QWidget` ohne native Dialog- oder
  Fensterflags, eingebettet in `D64TurboModalLayer` auf
  `QPlainTextEdit::viewport()`. Das ist **kein zweites Windows-Fenster**.
* Der 2-Pixel-Rahmen (`#525252`) und der 2-Pixel-Schatten (`#666666`) werden
  direkt mit `QPainter` gezeichnet. Das Inhaltslayout bleibt innerhalb des
  Rahmens. Die Farbtöne und die Schrift-Fallbacks Consolas → Courier New →
  Courier bleiben erhalten.
* Ein `MousePress` auf die Titelleiste oder deren Text aktiviert Drag & Drop;
  `MouseMove` verschiebt das Widget innerhalb des Viewports; `MouseRelease`
  beendet die Verschiebung.
* `OK` und die übrigen Ergebnis-Buttons rufen unmittelbar `done(result)` auf.
  Der rechte obere `×`-Button und die Esc-Taste liefern `Cancel`. Ein eigener
  Callback beendet die lokale Qt-Ereignisschleife; die fehleranfällige Bindung
  an `QDialog::finished` entfällt.
* Der 3-Pixel-Drückeffekt des Buttons bleibt erhalten. Bei `MouseRelease`
  werden die lokalen Event-Koordinaten nach der Rückverschiebung angepasst, um
  den Klick auch nach dem optischen Versetzen sicher zu erkennen.
* Ein aktives Qt-Popup-Menü wird vor dem Öffnen der MessageBox geschlossen,
  damit das Popup den Maus-Grab nicht behält. Der Overlay-Ereignisfilter
  blockiert weiterhin Eingaben außerhalb der MessageBox.
* Bestehende Aufrufstellen für **Hilfe → Über ...**, Taschenrechner, Puzzle
  sowie Speichern/Verwerfen/Abbrechen des Editors bleiben kompatibel. Die
  VFS-Logik, andere Turbo-Vision-Fenster und die dBASE-Runtime-Exports werden
  nicht verändert.

## Windows-Testfolge

1. Laufende dBASE-EXE-Prozesse beenden.
2. `build_and_deploy_dbase_editor_stage635.bat` ausführen. Dadurch wird
   `libd64_qt5.dll` neu erstellt und nach `runtime\dbase\pe32` kopiert
   (optional: Zielverzeichnis als erster Parameter).
3. dBASE-EXE starten, `Hilfe → Über ...` öffnen. Sichtbaren Rahmen prüfen,
   an der Titelzeile ziehen, dann `OK` klicken. Die Box muss verschwinden.
4. Box erneut öffnen und mit dem `×`-Button schließen.
5. Einen Texteditor ändern und schließen. Die Entscheidungen Speichern,
   Verwerfen und Abbrechen separat prüfen.

## Nachweise / Grenzen

Die fokussierten Stage-635-Tests und die Regressionstests der Stages
620–622, 628–634 wurden erfolgreich ausgeführt. Dabei werden unter anderem
Aufrufpfade, Mausereignisbehandlung, Rahmen-/Schatten-Geometrie und
Callback-Verdrahtung per Quelltextanalyse geprüft. Die automatisierte
Testumgebung verfügt nicht über Qt5-Entwicklungsheader oder MinGW32 und kann
deshalb **weder einen echten Windows-DLL-Build noch den interaktiven
Mauslaufzeittest** ersetzen.

Die im vorherigen Stand gemeldete native Fehlfunktion ist somit im Quellcode
behoben, unter Windows aber noch zu verifizieren.
