# Stage 497 – Windows-Qt5-Terminal / MinGW-Build

Das vom Nutzer berichtete Fehlerprotokoll nennt die Zeilen 8561/8566 und entspricht dem Code von Stage 495. In Stage 496 lagen die betreffenden Aufrufe auf 8564/8569; dort existierte bereits eine Vorwärtsdeklaration auf Zeile 7606. Beim erneuten Fehler wird offenbar noch die alte Quelldatei kompiliert.

Die Vorwärtsdeklaration wird in Stage 497 unmittelbar vor `DBaseQtAppendConsole()` gesetzt:

```cpp
static void append_dbase_qt_terminal(const QString &text, bool newline);
extern "C" D64QT5_API void DBaseQtAppendConsole(const char *text, int length)
```

Das Terminal gehört auch zur Windows-Bridge und darf nicht mit einem Linux-only-Guard versteckt werden.

## Windows-Aktualisierung

Ersetze die Datei `d64qt5/d64qt5_bridge.cpp` unterhalb deines Projektstammordners. Entweder nutze das vollständige `d64_dism_asm_497.zip`, das kleine `d64qt5_bridge_stage497_patch.zip` (enthält die richtige relative Struktur), oder kopiere die Einzeldatei `d64qt5_bridge_stage497.cpp` unter dem Namen `d64qt5_bridge.cpp` in dein lokales `d64qt5`-Verzeichnis.

Baue danach im Verzeichnis `d64qt5` sauber neu:

```sh
qmake d64qt5_bridge.pro CONFIG+=release
mingw32-make clean
mingw32-make release
```

Dieser Stand ist mit Quelltext-/Regressionsprüfungen validiert, jedoch nicht durch einen realen MinGW-/Qt5-Windows-Build.
