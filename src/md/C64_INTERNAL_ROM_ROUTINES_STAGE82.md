# Stage 82 - interne C64 BASIC-/KERNAL-ROM-Routinen

Stage 82 erweitert die in Stage 81 eingeführte Kommentierung der offiziellen
C64-KERNAL-Jump-Table um einen separaten Satz interner ROM-Einsprungpunkte.

## Grundsatz

Die 39 Einträge `$FF81` bis `$FFF3` bleiben die offizielle KERNAL-API.
Direkte Sprünge in BASIC- oder KERNAL-ROM werden davon getrennt behandelt:

- `INTERN BASIC` - Routine aus BASIC 2.0 / BASIC-Initialisierung.
- `INTERN KERNAL` - direkte Routine aus dem KERNAL-ROM.
- `nicht API-stabil` - kein offizieller portabler KERNAL-Jump-Table-Einstieg.

Die Quellenbasis ist der klassische C64-ROM-Stand BASIC 901226-01 und
KERNAL 901227-03 sowie der Commodore 64 Programmer's Reference Guide.
Die interne Liste ist bewusst konservativ und wird in weiteren Stufen
additiv erweitert.

## BASIC intern

| Adresse | Name | Beschreibung |
|---|---|---|
| `$A474` | `RESTART` | BASIC-Eingabeschleife neu starten |
| `$A560` | `LNKPRG` | BASIC-Zeilenzeiger neu verketten |
| `$A613` | `CRUNCH` | BASIC-Quellzeile tokenisieren |
| `$A69C` | `LIST` | BASIC-Programm auflisten |
| `$A742` | `FOR` | FOR-Anweisung ausführen |
| `$A7AE` | `SCRTCH` | NEW: BASIC-Programm und Variablen löschen |
| `$A81D` | `RESTORE` | DATA-Lesezeiger zurücksetzen |
| `$A82F` | `STOP` | STOP-Anweisung ausführen |
| `$A831` | `END` | END-Anweisung ausführen |
| `$A871` | `RUN` | BASIC-Programm starten |
| `$A883` | `GOSUB` | GOSUB-Anweisung ausführen |
| `$A8A0` | `GOTO` | GOTO-Anweisung ausführen |
| `$A8D2` | `RETURN` | RETURN-Anweisung ausführen |
| `$A8F8` | `DATA` | DATA-Anweisung überspringen/verarbeiten |
| `$A928` | `IF` | IF-Anweisung auswerten |
| `$A93B` | `REM` | REM-Anweisung überspringen |
| `$A94B` | `ON` | ON ... GOTO/GOSUB ausführen |
| `$A9A5` | `LET` | LET/Zuweisung ausführen |
| `$ABA5` | `INPUT#` | INPUT# von geöffnetem Kanal ausführen |
| `$ABBF` | `INPUT` | INPUT von Tastatur/Kanal ausführen |
| `$AC06` | `READ` | READ-Anweisung aus DATA ausführen |
| `$AD1E` | `NEXT` | NEXT-Anweisung ausführen |
| `$B081` | `DIM` | DIM-Anweisung ausführen |
| `$B391` | `GIVAYF` | Integerwert in BASIC-Fließkomma-Akkumulator wandeln |
| `$B82D` | `WAIT` | WAIT-Anweisung ausführen |
| `$BDCD` | `LINPRT` | Positiven Integer dezimal ausgeben |
| `$BDDD` | `FOUT` | Fließkomma-Akkumulator in ASCII-Text wandeln |
| `$E37B` | `PANIC` | BASIC-Warmstart ausführen |
| `$E394` | `INIT` | BASIC-Kaltstart und Initialisierung ausführen |

## KERNAL intern

| Adresse | Name | Beschreibung |
|---|---|---|
| `$E544` | `CLSR` | Bildschirm löschen |
| `$E566` | `NXTD` | Cursor auf HOME (Zeile 0, Spalte 0) setzen |
| `$EA31` | `IRQ` | Standard-KERNAL-IRQ-Routine ausführen |
| `$EA81` | `IRQRTI` | IRQ-Register restaurieren und mit RTI zurückkehren |

## Disassembler

Interne Routinen werden im Rohdaten-ASM sichtbar markiert, ohne Adresse und
Bytecode zu verlieren:

```asm
    JSR $A474        ; BASIC-Eingabeschleife neu starten [INTERN BASIC RESTART] | $0801: 20 74 A4
    JSR $E544        ; Bildschirm löschen [INTERN KERNAL CLSR] | $0804: 20 44 E5
    JSR $FFD2        ; CHROUT: Zeichen an den aktuellen Ausgabekanal schreiben | $0807: 20 D2 FF
```

Die gemeinsame Kommentar-Fluchtlinie aus Stage 78 bleibt erhalten.

## Live-Hilfe

`c64_assembler_call_description()` bleibt kompatibel und liefert weiterhin
die kurze Zielbeschreibung. Neu ist:

```python
c64_assembler_call_stability("JSR", "$FFD2")
# -> "KERNAL-API"

c64_assembler_call_stability("JSR", "$A474")
# -> "INTERN BASIC - nicht API-stabil"

c64_assembler_call_stability("JSR", "$E544")
# -> "INTERN KERNAL - nicht API-stabil"
```

Bei einer internen Routine zeigt die vorhandene Assembler-Live-Hilfe nun
zusätzlich:

```text
Hinweis: interne ROM-Routine; nicht Teil der stabilen KERNAL-Jump-Table.
```

## Kompatibilität

- `C64_KERNAL_JSR_ROUTINES` bleibt unverändert bei 39 Einträgen.
- `C64_INTERNAL_JSR_ROUTINES` bleibt als Sammelname erhalten und kombiniert
  jetzt BASIC- und KERNAL-Interna.
- Stage 80/81 `JSR $E544` liefert weiterhin die kurze Beschreibung
  `Bildschirm löschen` über `c64_assembler_call_description()`.
- `$5344` bleibt ausdrücklich ohne Clear-Screen-Zuordnung.
