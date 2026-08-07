# Kommandozeilencompiler

Ohne Compileroption startet `d64_dism.py` weiterhin die grafische Oberfläche.
`--write-c64` erzeugt ein C64-PRG, `--write-amiga` ein eigenständig bootfähiges
Amiga-ADF. Beide Befehle speichern zusätzlich den generierten Assemblercode.

```powershell
python d64_dism.py --write-c64 examples\c64pascal\hello.pas
python d64_dism.py --write-amiga examples\amiga\bitmap_text_c.c
```

Ein abweichender Image-Name wird mit `-o` oder `--output` angegeben:

```powershell
python d64_dism.py --write-amiga demo.pas -o build\demo.adf
```

`-Fi` beziehungsweise `--include-path` ist wiederholbar und gilt für
Pascal-Units/PUI und C-Header:

```powershell
python d64_dism.py --write-c64 main.pas -Fi units -Fi shared -o main.prg
python d64_dism.py --write-amiga main.c --include-path include -o main.adf
```

Vordefinierte Präprozessormakros können optional mit `-DNAME` oder
`-DNAME=WERT` gesetzt werden. Ohne `-o` entstehen `<quelle>.prg` oder
`<quelle>.adf`. Die ASM-Dateien heißen `<quelle>.generated.asm` für den C64
und `<quelle>.generated.amiga.asm` für den Amiga.

## Pascal-Unit direkt übersetzen

Eine `.pas`-Datei, die mit `unit` beginnt, wird von `--write-amiga` und
`--write-c64` als Unit erkannt. Dabei entstehen die PUI-Datei und ein separates
Unit-ASM-Modul; es wird kein bootfähiges Programmabbild erzeugt.

```powershell
python d64_dism.py --write-amiga c64pascal/units/System/Graphics.pas
```

Für `System.Graphics` wird zusätzlich das in der PUI eingetragene Modul
`System/Graphics.amiga.asm` in die erzeugte
`System/Graphics.generated.amiga.asm` übernommen. Ein Pascal-Programm mit
`uses System.Graphics` erhält dasselbe Modul automatisch beim statischen
ASM-Linkschritt.

## Getrennte C-Dateien

C-Header oder Hauptdateien können Implementierungsmodule anfordern:

```c
#pragma link "module.c"
```

Der Pfad wird relativ zur Datei des Pragmas aufgelöst. Das C-Modul wird separat
übersetzt und vor der Erzeugung von PRG beziehungsweise ADF statisch gelinkt.
Die Ausgabestatistik zeigt die Anzahl unter `C-Module`. Siehe außerdem
`C_PRAGMA_LINK.md` und `examples/c_link/`.


## Erweiterte C-Typen und rekursionsfeste Funktionen

Der C-Compiler unterstützt automatische Stackvariablen, lokale persistente
`static`-Variablen, Block-Scopes, rekursive Funktionen, `typedef`, `enum`,
16-Bit-Set-Typen und Strukturen. Ein vollständiges Beispiel liegt unter:

```text
examples/c_advanced/advanced_types.c
examples/c_advanced/recursive_module.c
```

Amiga:

```powershell
python d64_dism.py --write-amiga examples\c_advanced\advanced_types.c
```

C64:

```powershell
python d64_dism.py --write-prg examples\c_advanced\advanced_types.c
```

Die genaue Syntax und die noch bestehenden Grenzen beschreibt
`C_ADVANCED_FEATURES.md`.
