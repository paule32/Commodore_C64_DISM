# Stage 441 – LEN/LTRIM/RTRIM/TRIM im dBASE-Compiler

## Verbindliche Basis
`d64_dism_asm_440.zip`

## Eingebaute Funktionen
- `LEN(<String-Ausdruck>)` gibt eine numerische Zeichenkettenlänge zurück. Die vorhandene native dBASE-Zeichenablage benutzt CP1252 (1 Byte je darstellbarem Zeichen); LEN arbeitet darum zur Laufzeit über die tatsächliche Länge des Value-Slots. Python-Vorschau und Konstantfaltung verwenden dieselbe CP1252-Semantik. Nicht in CP1252 darstellbare Zeichen werden wie die bestehenden Stringliterale ersetzt.
- `LTRIM(<String-Ausdruck>)` entfernt ausschließlich führende normale Leerzeichen (`0x20`).
- `RTRIM(<String-Ausdruck>)` entfernt rechts `0x20`, Tab (`0x09`), LF (`0x0A`), Backspace (`0x08`) und CR (`0x0D`).
- `TRIM(<String-Ausdruck>)` entfernt an beiden Enden `0x20`, `0x09`, `0x0A`, `0x08`, `0x0D`.

Alle Namen sind unabhängig von Groß-/Kleinschreibung und erwarten **genau einen String-/Char-Ausdruck**. Keine numerischen Parameter. Verschachtelung, lokale/globale Memory-Variablen, `#define`-Makro-Strings und String-Rückgabewerte benutzerdefinierter `FUNCTION` werden über die normale Ausdrucksanalyse verarbeitet.

## Implementierung
- `d64dbase/compiler.py`: neue Builtins in Analyse, Konstant-/Python-Auswertung, PE32/PE32+-Erzeugung für numerische und String-Ergebnisse sowie `?/??`-Ausgabe.
- `d64dbase/string_length_trim.py`: String-Helfer und nativer Trim-Assembler für beide Zielarchitekturen; Scans werden durch die explizite gespeicherte Stringlänge begrenzt und kopieren in neu allokierten Speicher (Quellwerte bleiben unverändert).
- `examples/dbase_len_trim_stage441.prg`: ausführbare Syntaxbeispiele.
- `test_stage441_dbase_len_trim.py`: Funktionalitäts-, Typprüfungs-, Zielarchitektur- und Regressionsfälle.

## Grenzen der Verifikation
Die Compiler-Vorschau und die erzeugte Assemblerstruktur wurden getestet. Kein tatsächlicher Windows-PE32/PE32+-Ausführungsnachweis auf diesem Linux-Rechner.
