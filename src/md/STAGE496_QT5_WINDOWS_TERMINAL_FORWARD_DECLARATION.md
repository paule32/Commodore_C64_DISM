# Stage 496 – Qt5-Windows-DLL: fehlende Vorwärtsdeklaration

**Basis:** d64_dism_asm_495.zip.

## Build-Fehler

MinGW32 stoppt beim Kompilieren von `d64qt5/d64qt5_bridge.cpp` innerhalb
`DBaseQtAppendConsole()` (im ursprünglichen Quellstand um Zeile 8561/8566):

```
'append_dbase_qt_terminal' was not declared in this scope
```

Die Funktion ist in derselben Windows-Bridge-Datei erst weiter unten definiert.
Ein plattformspezifisches `#ifdef LINUX` wäre hier falsch: die Windows-DLL
benötigt den Qt5-Terminaldialog für dBASE-Ausgaben ebenfalls. Die Linux-`so`
verwendet bereits eine getrennte Quelldatei (`d64qt5_linux_form.cpp`).

## Korrektur

Direkt bei den vorhandenen Vorwärtsdeklarationen:

```cpp
static void show_wfm_output_dialog(QWidget *reference);
static void append_wfm_output(const QString &value, bool newline);
static void append_dbase_qt_terminal(const QString &text, bool newline);
static void apply_wfm_debug_theme();
```

Die eigentliche `append_dbase_qt_terminal`-Definition und alle Ausgabewege
bleiben unverändert. Die Deklaration ist für beide Plattformen verfügbar, falls
`d64qt5_bridge.cpp` künftig auf einer anderen Plattform kompiliert würde.

## Build unter Windows / MSYS2 MinGW32

Im `d64qt5`-Verzeichnis:

```sh
qmake d64qt5_bridge.pro CONFIG+=release
mingw32-make release
```

Oder das vorhandene Skript `build_d64qt5_mingw32.bat` verwenden.

## Testgrenzen

Die Python-Regression prüft die Reihenfolge der Deklaration, ihre Signatur,
die beiden Ausgabeaufrufe sowie die unveränderte Qt-Projekttrennung. Ein
vollständiger nativer Qt5/MinGW32-Build ist in dieser Umgebung mangels
Qt5-/MinGW32-Toolchain nicht möglich; daher muss der Windows-Build noch
praktisch bestätigt werden.
