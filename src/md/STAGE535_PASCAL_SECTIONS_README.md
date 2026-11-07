# Stage 535: Windows-Pascal-Sektionen `.text`, `.data`, `.bss`

Basis: `d64_dism_stage534.zip`.

## Problem

Der PE32-/PE32+-Pascal-Generator setzte bisher vor `_emit_data()` keine
`section .data`-Direktive. Dadurch landeten Pascal-Variablen sowie
Klassen-Metadaten und Literal-Daten im Default-Abschnitt `.text`.
Große uninitialisierte Records und Arrays wurden als lange `db 0, 0, ...`
Bytefolgen in einer dateigestützten Sektion gespeichert.

Zwei Beispiele aus dem archivierten PE32-Testassembler
`runtime/pascal/test/test_raise.generated.pe32.asm`:

- `__pas_local_global_runmessageloop_msg_14`: `TMsg`, 28 Byte
- `__pas_local_twindow_create_winclass_25`: `TWndClassA`, 40 Byte

## Änderung

In `c64pascal/compiler.py` verwenden `_PE32CodeGenerator._emit_data()` und
`_PE64CodeGenerator._emit_data()` jetzt folgende Aufteilung:

- **`.text`**: ausführbare Funktionen/Methoden, Programm-Startcode und Stubs.
- **`.data`**: initialisierte Pascal-Variablen (Nichtnull-Initialwerte),
  String-/Double-Literale und Klassen-/VMT-Metadaten, ferner die bisherigen
  statisch initialisierten Runtime-Werte.
- **`.bss`**: Variablen ohne statischen Nichtnull-Initialwert (auch Record-
  und Array-Speicher), sowie die bisherigen Runtime-Puffer/Stack-Cookies.

Beispiel nach Neukompilierung:

```asm
section .data
align 4
; Klassenmetadaten, Literale, statisch initialisierte Werte ...

section .bss
align 4
__pas_local_global_runmessageloop_msg_14: resb 28
__pas_local_twindow_create_winclass_25: resb 40
```

Die Namen/Indizes der Labels hängen von der jeweiligen Quelltext-Version ab.

Ein `.bss`-Bereich belegt zur Laufzeit weiterhin virtuellen Speicher, wird
beim Prozessstart aber ohne entsprechende Null-Bytes in der EXE initialisiert.
Eine Reduktion der Dateigröße hängt von File-/Section-Alignment und einer
möglichen nachgelagerten Pack-/Kompressionsstufe ab; sie ist nicht zwingend
exakt gleich der Summe der ausgesparten Null-Bytes.

**Wichtig:** Die `.bss`-Platzierung verändert nicht die bestehende Art, wie
der Compiler Pascal-Lokalvariablen anlegt (teilweise statisch pro Modul statt
pro Aufruf). Reentranzprobleme werden dadurch nicht behoben.

## Kompatibilität

Der integrierte COFF32-/COFF64-Assembler/Linker kennt `.data`, `.bss` und
`resb`. Die Änderung betrifft die Windows-Pascal-Codegeneratoren. C64-/Amiga-
und andere Compiler-Frontends bleiben unverändert.

`test_raise.generated.pe32.asm` im Projekt ist ein **altes generiertes
Referenzartefakt** von Stage 534. Zur Prüfung der neuen Ausgabe neu kompilieren;
die archivierte Datei wurde nicht vorgetäuscht als frisch generiert ersetzt.

## Prüfungen

- Python-Syntaxprüfung (`py_compile`): erfolgreich.
- `test_stage535.py`: 3 Testmethoden, 8 Architektur-/Ausgabevarianten,
  Sektionstrennung für PE32/PE64, Unit, DLL und aktivierte Stack-Cookies:
  erfolgreich.
- `test_stage532.py`: 4/4 bestanden.
- `test_stage533.py`: 2/2 bestanden.
- `test_stage534.py`: 6/6 bestanden.
- `test_stage531.py`: 6/6 bestanden.
- `test_stage530.py`: 8/8 bestanden.
- Der ältere Testlauf `test_stage529.py` hat das Zeitlimit überschritten und
  wird **nicht** als bestanden gewertet.
- Native PE32-/PE32+-EXE-Erstellung und Ausführung unter Windows sowie eine
  tatsächliche Dateigrößenmessung von `test_raise.exe` bleiben nachzuholen.

## Dateien

- `c64pascal/compiler.py` (angepasst)
- `test_stage535.py` (neu)
- `STAGE535_PASCAL_SECTIONS_README.md` (neu)

Alle anderen Dateien aus Stage 534 bleiben unverändert.
