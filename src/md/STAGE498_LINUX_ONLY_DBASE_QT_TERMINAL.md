# Stage 498 – dBASE Qt5 Terminal nur unter Linux

Verbindliche Grundlage: Stage 497 (`d64_dism_asm_497.zip`).

## Änderung

Der zusätzliche selbstständige Dialog **„dBASE Qt5 Terminal“** mit grauem Rahmen,
blauem Hintergrund (`#000080`) und gelber Schrift (`#ffff00`) wird nur von der
Linux-Shared-Library `d64qt5_linux_form.cpp` verwendet.

Unter **Windows** wird kein zweiter Terminaldialog mehr angelegt:

- `DBaseQtAppendConsole` schreibt WFM-Ausgaben wie vor Stage 490 in das bestehende
  `append_wfm_output`-Dialogfenster und im normalen Konsolenmodus in den
  vorhandenen Console-Tab.
- `DBaseQtConsoleWrite` (`?` / `??`) nutzt im Windows-WFM-Modus wieder den
  vorhandenen Qt5-Ausgabedialog und respektiert die Zeilenumbruchsteuerung.
- Workstation-Runner-/Pipe-Weiterleitung, `SET DEBUG ON/OFF` und das
  Aussehen des vorhandenen Debug-Ausgabedialogs bleiben erhalten.
- Die Windows-spezifischen zusätzlichen Qt5-Terminal-Globals, die Funktion
  `append_dbase_qt_terminal` und deren Shutdown-Cleanup sind entfernt.
  Damit ist auch die aus Stage 495/496 gemeldete Vorwärtsdeklarationsfrage
  hinfällig: Unter Windows wird dieser Funktionsname nirgends mehr referenziert.
- Qt5-Fokus-Ereignisse `OnGotFocus` und `OnLostFocus` bleiben unverändert.

Unter **Linux** bleiben `DBaseTerminalDialog`, `DBaseQtRunConsoleJson`,
`DBaseQtRunFormJson`, die Farben und `QPlainTextEdit` erhalten. Die Linux-C++-Datei
wurde nicht verändert.

## Build-Trennung

Die Projektdatei `d64qt5_bridge.pro` kompiliert unter Windows
`d64qt5_bridge.cpp` (und `d64_workstation.cpp`), unter Linux ausschließlich
`d64qt5_linux_form.cpp` als Qt5-Shared-Library. Die beiden Terminalverhalten
sind damit auf Source-Ebene getrennt; im Windows-Build wird kein Linux-Terminal
über einen symbolischen `#ifdef` zugeschaltet.

## Tests und Einschränkungen

`test_stage498_linux_only_qt_terminal.py` prüft die Windows-Ausgaberouten und
die Linux-Terminaldefinitionen. Die älteren Stage-490/496/497-Tests, die
explizit den inzwischen unerwünschten *zusätzlichen Windows-Dialog* verlangten,
wurden für das neue, vom Benutzer gewünschte Verhalten aktualisiert.

Eine komplette native Qt5-MinGW- oder Ubuntu-Übersetzung sowie interaktives
GUI-Verhalten können in dieser Umgebung ohne Qt5-Entwicklungspakete nicht
bestätigt werden.
