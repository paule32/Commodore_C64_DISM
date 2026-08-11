# dBase Qt5 C++ Bridge – Stage 12

Die Qt5-Runtime der generierten dBase-Anwendung wird als native C++-DLL
`d64qt5.dll` gebaut. Der dBase-Codegenerator ruft Qt5 nicht direkt auf, sondern
verwendet eine stabile C-ABI.

## Bridge-ABI

- `DBaseQtInitialize(const char *title)`
- `DBaseQtShowWindow()`
- `DBaseQtProcessEvents()`
- `DBaseQtSetDebugVisible(int visible)`
- `DBaseQtAppendConsole(const char *text, int length)`
- `DBaseQtAppendDebug(const char *text, int length)`
- `DBaseQtMarkProgramFinished()`
- `DBaseQtExec()`
- `DBaseQtShutdown()`

PE32 verwendet cdecl. PE32+ verwendet die Windows-x64-ABI.

## GUI-Aufbau

Die Bridge verwendet absichtlich **kein QTabWidget-Corner-Widget** mehr. Die
stabile Struktur lautet:

```
QMainWindow
  QWidget root
    QVBoxLayout
      QWidget header
        QHBoxLayout
          Lupe +
          Lupe -
          QTabBar: Konsole | DEBUG
      QStackedWidget
        consolePage -> QPlainTextEdit
        debugPage   -> QPlainTextEdit + QLineEdit
```

`Konsole` ist immer vorhanden. `DEBUG` wird durch `DBaseQtSetDebugVisible(1)`
hinzugefügt und durch `DBaseQtSetDebugVisible(0)` entfernt.

## Layout-Fix

Die vorherige Bridge konnte den Editor bei bestimmten Qt5-Styles verschieben:
`ensureCursorVisible()` scrollte bei `NoWrap` horizontal bis zum Ende langer
Zeilen. Stage 12 setzt deshalb nach jeder Ausgabe die horizontale Scrollbar auf
links und nur die vertikale Scrollbar ans Ende.

## Farben und Schrift

- Hintergrund: `#000000`
- Text: `#A9A9A9`
- Font: Consolas, Fallback Courier New, Courier, System Fixed Font
- Zoom: 9 bis 75 pt

## Manuelles Bauen

Die DLL wird **nicht** durch den Start-Button von d64_dism gebaut.

Verwende für PE32 eine 32-Bit-Qt5-Toolchain und für PE32+ eine 64-Bit-Qt5-
Toolchain. Die Dateien sind:

- `d64qt5/d64qt5_bridge.cpp`
- `d64qt5/d64qt5_bridge.h`
- `d64qt5/d64qt5_bridge.def`
- `d64qt5/d64qt5_bridge.pro`

Mit einem passenden Qt5-qmake-Kit kann die DLL außerhalb von d64_dism gebaut
werden. Danach müssen `d64qt5.dll` und die passenden Qt5-Runtime-DLLs neben der
generierten EXE bzw. im Windows-DLL-Suchpfad liegen.

## Generator

Der vorhandene Generator benötigt keine ABI-Änderung. Beispiel:

```dbase
? "Ausgabe in Konsole"
SET DEBUG ON
? "Ausgabe in DEBUG"
SET DEBUG OFF
? "Wieder Ausgabe in Konsole"
```

liefert sowohl PE32- als auch PE32+-ASM. Referenzdateien liegen unter
`examples/dbase/qt5_bridge_stage12.generated.pe32.asm` und `.pe64.asm`.
