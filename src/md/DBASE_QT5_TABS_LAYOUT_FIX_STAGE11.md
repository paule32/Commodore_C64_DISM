# dBase Qt5 Tabs/Layout Fix – Stage 11

## Ziel

Die erzeugte dBase-Qt5-Anwendung zeigt den Tab `Konsole` immer an. Der Tab `DEBUG`
wird ausschliesslich zur Laufzeit durch `SET DEBUG ON` eingeblendet und durch
`SET DEBUG OFF` wieder entfernt.

## Layout-Fix

Die Qt5-Bridge verwendet jetzt einen Root-Container mit `QVBoxLayout`. Das
`QTabWidget`, beide Tab-Seiten und beide `QPlainTextEdit`-Komponenten verwenden
explizit eine expandierende SizePolicy. Die DEBUG-Eingabezeile expandiert
horizontal und bleibt nur in der Hoehe fixiert.

Die Lupen-Steuerung in der linken Ecke der Tab-Leiste ist auf 58 Pixel Breite
begrenzt. Dadurch kann sie die Tab-Leiste oder den Editorbereich nicht mehr auf
einen kleinen linken oberen Bereich zusammendruecken.

## Tab-Semantik

- Beim Start: `Konsole` sichtbar, `DEBUG` unsichtbar.
- `SET DEBUG ON`: `DEBUG` wird hinzugefuegt; `Konsole` bleibt sichtbar.
- `SET DEBUG OFF`: nur `DEBUG` wird entfernt; `Konsole` bleibt sichtbar.
- Jede Ausgabe ueber `DBaseQtAppendConsole` stellt den Konsolen-Tab vorsorglich
  wieder her.
- Die Tab-Leiste wird mit `setTabBarAutoHide(false)` immer sichtbar gehalten.

## Start/Build

Der bereits korrigierte No-Build-Startpfad bleibt unveraendert: der Start-Button
startet ausschliesslich die bereits intern gelinkte EXE. Es gibt keinen
automatischen qmake-/mingw32-make-Aufruf.

## Tests

Der Gesamtbestand umfasst 205 erfolgreiche Tests, darunter 5 neue Stage-11-Tests
fuer Tab-Sichtbarkeit, Layout-Ausdehnung, Zoom-Corner und DEBUG ON/OFF-Codegen.
