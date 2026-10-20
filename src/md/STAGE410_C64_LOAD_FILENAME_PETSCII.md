# Stage 410 – C64 BASIC LOAD: Dateinamen als PETSCII

**Basis:** `d64_dism_asm_409.zip`.

## Verifizierter Fehler

Der BASIC-Compiler nutzte `_petscii_bytes()` für `LOAD "sprites.spr",8,1`.
Daher enthielt das kompilierten PRG die **ASCII**-Bytes:

```
73 70 72 69 74 65 73 2E 73 70 72     sprites.spr
```

Der Stage-409-D64-Schreiber legte die PRG-Datei dagegen unter diesen PETSCII-Bytes ab:

```
53 50 52 49 54 45 53 2E 53 50 52     SPRITES.SPR
```

CBM-DOS vergleicht Dateinamen anhand der PETSCII-Bytewerte (Groß-/Kleinschreibung unterscheidbar).
Der Byte-Unterschied erklärt, warum `LOAD` den Sprite-Eintrag nicht findet.

## Änderungen

- `c64basic/compiler.py`: `_petscii_filename_bytes()` kodiert Host-ASCII-Kleinbuchstaben **nur im Kontext eines LOAD-Literaldateinamens** in das übliche PETSCII-Alphabet `$41..$5A`.
- `add_literal_bytes()`: Symbolpool verwendet tatsächliche Stringbytes. Allgemeine BASIC-Stringliterale, z. B. `PRINT "sprites.spr"`, bleiben unverändert (und werden nicht versehentlich mit dem LOAD-Namen gepoolt).
- `LOAD N$,8,1` und zusammengesetzte Dateinamen erhalten eine kleine `_basic_load_normalize_name`-Subroutine. Diese verändert nur die temporäre Kopie `__basic_string_expr`, **nicht die Stringvariable**. Sie wandelt die Bytewerte `$61..$7A` in `$41..$5A` um.
- Explizite Direct-PETSCII-Zeichen `U+E000..U+E0FF` in **LOAD-Literalen** bleiben unverändert, sodass sie nicht unbemerkt in ASCII übersetzt werden.
- Der direkte BASIC-VICE-Keyboardtransfer hatte diese Normalisierung bereits und wurde nicht geändert.
- Der D64-Diskettenschreiber aus Stage 409 bleibt unverändert. Kein Eingriff in Originalspritedaten oder vorhandene D64-Dateien.

**Spezialfall dynamischer Namen:** Die Normalisierung `$61..$7A` im temporären Laufzeit-Dateinamen ist für typische Host-Editor-Buchstaben vorgesehen; gezielt aus Grafiksymbolen mit genau diesen PETSCII-Bytewerten zusammengesetzte Namen sind davon nicht unterscheidbar und sollten als explizite Literaldateinamen übergeben werden.

## Tests

- 7 neue Tests in `test_stage410_c64_load_filename_petscii.py`: genaue Bytes im erzeugten PRG und D64, keine PRINT-Veränderung, Symbol-Pooling, Direkt-PETSCII, variable Dateinamen, VICE-Keyboardtransfer und Sprite-Beispiel.
- 19 bereits vorhandene Tests aus Stages 401, 408, 409: zusammen **26 Tests mit OK**.
- Compiler/Assembler-Ausgaben aus der hochgeladenen `Sprite_A(1).bas` wurden neu generiert und in einem eigenständigen Testpaket mit ladbarer Sprite-Diskette abgelegt.
- Ein **VICE-Windows-End-to-End-Test** wurde hier noch nicht durchgeführt.

## Startablauf

1. `Sprite_A.bas` mit Stage 410 neu kompilieren und assemblieren. **Alte PRG-Datei aus Stage 409 nicht erneut verwenden**.
2. d64_dism erzeugt ein neues D64 mit `SPRITE_A` und `SPRITES.SPR` und startet VICE mit eingelegtem D64.
3. Mit `LOAD "sprites.spr",8,1` können die Sprite-Daten an `$3000` geladen werden, ohne dass Name und Disk-Eintrag byteweise auseinanderlaufen.
