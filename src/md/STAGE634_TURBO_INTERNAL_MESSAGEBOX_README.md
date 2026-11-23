# Stage 634 – MessageBox als internes Turbo-Vision-Fenster

**Verbindliche Basis:** `d64_dism_stage633.zip`.

## Ursache

Bisher entstand `D64TurboMessageBox` durch `QDialog(parent, Qt::Dialog | Qt::FramelessWindowHint)` als eigenes Betriebssystem-/Qt-Dialogfenster. Die MessageBox soll stattdessen Teil der Turbo-Vision-Oberfläche im DOS-Konsolenviewport sein.

## Implementation

- `d64qt5/d64_turbo_messagebox.hpp`: `D64TurboMessageBox` bleibt wiederverwendbar, wird jetzt aber explizit als `Qt::Widget | Qt::FramelessWindowHint` eingebettet (inkl. `setWindowFlags`, weil QDialog je nach Qt5-Implementierung `Qt::Dialog` ergänzt).
- `consoleDesktop()` findet das `QPlainTextEdit` mit dem Objektnamen `dbaseConsole` ausgehend von der Menüleiste/Hauptanwendung, einem Editor oder einem Werkzeug und verwendet **dessen `viewport()`** als Ziel.
- `D64TurboModalLayer` ist ein Kind genau dieses Viewports. Der Layer wird nur für die Lebensdauer der MessageBox erzeugt und fängt Mausklicks, Tastendrücke und globale Shortcuts ab, die nicht in den Dialog gehören. Dadurch ist das Fenster modal, **ohne eine eigene Windows-Fensterinstanz** zu öffnen.
- Die `showMessage()`-Routine zentriert die MessageBox im Viewport und führt ein lokales `QEventLoop` aus, bis eine Schaltfläche, Escape oder das `×` den Dialog beendet. Das Ergebnis der Buttons wird wie bisher zurückgegeben.
- Das Ziehen an der Titelleiste ist auf die Maße des Konsolenviewports begrenzt; beim Resize des Viewports wird die modale Ebene mit angepasst.
- Vorhandene Eigenschaften bleiben erhalten: graue Farbe, dunklere Titelleiste, Consolas/Courier-New/Courier-Fallback, 2-Pixel-Rahmen, 2-Pixel-Schatten, Schließen-Button, 3-Pixel-Klickeffekt, variable Schaltflächen.

## Call-Sites

- `d64qt5/d64qt5_bridge.cpp`: `Hilfe → Über ...` übergibt den Konsolenviewport, falls vorhanden.
- `d64qt5/d64_turbo_editor.hpp`: Die Abfrage ungespeicherter Änderungen verwendet `D64TurboMessageBox::showMessage()` statt einer direkten `QDialog::exec()`-Instanz. Die Entscheidungen `Speichern`, `Verwerfen`, `Abbrechen` und der virtuelle Speicherdialog bleiben erhalten.
- Taschenrechner- und Puzzle-Hinweise verwenden schon die zentrale `information()`-Methode und profitieren automatisch von der neuen Einbettung.

## Windows-Build

Alle EXEs beenden, die `libd64_qt5.dll` geladen haben. Danach im entpackten Projektverzeichnis `build_and_deploy_dbase_editor_stage634.bat` ausführen. Die aktualisierte DLL wird nach `runtime\dbase\pe32` kopiert (optionaler erster Parameter: anderes Verzeichnis). Eine dBASE-EXE muss für diese reine GUI-Änderung nicht neu compiliert oder gelinkt werden.

## Tests und Grenzen

106 gezielte automatisierte Integrations- und Regressionstests bestanden (Stages 620–622, 628–634). Drei alte Test-Erwartungen wurden angepasst, weil sie ausdrücklich die bisherige **native** Qt-Modalität verlangten. Ein vollständiger Qt5-/MinGW32-Build und die visuelle Interaktion auf Windows können in dieser Linux-Umgebung nicht bestätigt werden.
