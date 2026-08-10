# dBase Qt5 GUI – Stage 5

Der dBase-Compiler erzeugt fuer PE32 und PE32+ jetzt ein Windows-GUI-Programm,
das seine Ausgabe ueber `d64qt5.dll` direkt in Qt5-Widgets schreibt.

## GUI

- QMainWindow
- QTabWidget
- Tab `Konsole`: ein rahmenloses, read-only QPlainTextEdit
- Tab `DEBUG`: ein rahmenloses, read-only QPlainTextEdit plus QLineEdit
- DEBUG ist initial verborgen.
- `SET DEBUG ON` blendet DEBUG ein und leitet `?`/`??` dorthin.
- `SET DEBUG OFF` blendet DEBUG aus und leitet `?`/`??` wieder nach Konsole.
- `SET FORMAT TO SCREEN` bleibt als kompatibler DEBUG-Ausgabekanal erhalten.

Nach dem Aufbau der GUI wird `DBaseQtShowWindow` und `DBaseQtProcessEvents`
aufgerufen. Erst danach folgt der erzeugte dBase-Programmcode. Nach dessen Ende
ruft die EXE `DBaseQtMarkProgramFinished` und `DBaseQtExec` auf. Dadurch bleibt
das Fenster offen, bis der Benutzer es schliesst. Die Eingabezeile im DEBUG-Tab
bleibt aktiv und protokolliert Return/Enter-Eingaben im Debug-Editor.

## ASM-ABI

Die generierte EXE importiert aus `d64qt5.dll`:

- DBaseQtInitialize
- DBaseQtShowWindow
- DBaseQtProcessEvents
- DBaseQtSetDebugVisible
- DBaseQtAppendConsole
- DBaseQtAppendDebug
- DBaseQtMarkProgramFinished
- DBaseQtExec
- DBaseQtShutdown

PE32 verwendet C/cdecl. PE32+ verwendet die Windows-x64-ABI.

Der Assembler importiert bewusst nicht direkt C++-Mangled-Names aus
Qt5Widgets.dll. `d64qt5.dll` stellt eine stabile C-ABI bereit und benutzt intern
Qt5Core, Qt5Gui und Qt5Widgets.

## Qt5 Runtime bauen

Unter Windows muss eine passende Qt5-Development-Toolchain vorhanden sein.
Optional kann `D64_QMAKE` auf die gewuenschte qmake.exe gesetzt werden. Beim
Start eines dBase-Programms versucht d64_dism, `d64qt5.dll` automatisch zu
bauen und zusammen mit Qt5Core.dll, Qt5Gui.dll, Qt5Widgets.dll sowie
`platforms/qwindows.dll` neben die EXE zu deployen.

PE32 benoetigt eine 32-Bit-Qt5-Toolchain; PE32+ eine 64-Bit-Qt5-Toolchain.
