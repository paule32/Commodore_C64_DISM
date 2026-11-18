# Stage 619 – dBASE ? / ?? auf DEBUG-Ausgabe umgestellt

Basis: `d64_dism_stage618.zip`.

## Änderung

- Ohne explizite Vorgabe schreiben `?` und `??` jetzt in den **DEBUG-Kanal**.
- `? "Hihi"` ergibt `Hihi` mit CR/LF.
- Der Qt5-Bridge-Quellcode verwendet für normale dBASE-PRG-Programme den bereits bestehenden eigenständigen DEBUG-QDialog, nicht mehr den eingebetteten DEBUG-Tab.
- `SET FORMAT TO CONSOLE` und `SET DEBUG OFF` schreiben weiterhin in die bisherige native Windows-Konsole; `SET DEBUG ON` bzw. `SET FORMAT TO SCREEN` wählen wieder DEBUG (sofern keine ausdrückliche DEBUG-OFF-Überschreibung aktiv ist).
- `??` gibt ohne Zeilenende aus.
- Der statische `transcript`/`debug_transcript`-Analysestand wurde an die Standardausgabe angepasst. Die Einstellungen gelten auch für aufgerufene Funktionen/Prozeduren zur Laufzeit.

## Wichtig: vorhandene Qt5-DLL ist ein Binary

**Die Änderungen am C++-Quellcode wirken erst nach Neubau von `libd64_qt5.dll`.** Die aus `packed(10).zip` mitgelieferte DLL hat noch den alten Qt-Code; die EXE/DLL aus `packed(10).zip` wurde nicht verändert.

Auf Windows mit MSYS2 MinGW32 und Qt5:

1. `d64qt5\build_d64qt5_mingw32.bat` ausführen (siehe zugehöriges d64qt5 README für Abhängigkeiten).
2. Die neu gebaute `libd64_qt5.dll` an den Ort der PE32-EXE kopieren (und ggf. für PE32+ die passende 64-Bit-DLL entsprechend bauen).
3. dBASE-Programm mit Stage 619 **neu kompilieren / assemblieren / linken**. Nur `Start` zu drücken verwendet noch den alten EXE-Code.
4. Mit `Start` die erzeugte EXE aus dem in den Projekteinstellungen angegebenen `runtime/dbase/pe32`-Verzeichnis ausführen.

Die `c64_dbase_runtime.dll` muss für diese Änderung **nicht** neu gebaut werden; sie bleibt für explizite CONSOLE-Ausgabe zuständig.

## Prüffälle

```dbase
? "Hihi"
?? "Hallo "
? "Welt"
```

Erwartete DEBUG-Ausgabe: `Hihi` plus Zeilenumbruch, danach `Hallo Welt` plus Zeilenumbruch.

```dbase
SET FORMAT TO CONSOLE
? "Konsole"
SET FORMAT TO SCREEN
? "Debug"
```

Hier erscheint `Konsole` in der nativen Console und `Debug` im DEBUG-Dialog.

**Teststatus:** statische und Python-Compiler-Regressionstests wurden unter Linux ausgeführt. Qt5/Win32-Laufzeittest und DLL-Neubau sind dort nicht möglich; nach dem lokalen DLL-Neubau unter Windows prüfen.
