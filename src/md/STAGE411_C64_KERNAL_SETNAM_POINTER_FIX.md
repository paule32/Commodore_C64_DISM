# Stage 411 – C64 BASIC: SETNAM-Zeiger korrigiert

**Verbindliche Basis:** `d64_dism_asm_410.zip`.

## Ursache des weiterhin gemeldeten `LOAD ERROR 4`

Die Dateinamen-Kodierung aus Stage 410 war korrekt, aber der interne MOS6510-Assembler interpretiert Ausdrücke der Form `#>label+1` als `(high(label)) + 1`. Das ist *nicht* `high(label + 1)`.

Das nachweislich erzeugte Stage-410-Programm hat `SPRITES.SPR` mit elf PETSCII-Bytes bei `$0CD5`, gibt aber mit `LDX #$D5; LDY #$0D` den Zeiger `$0DD5` an KERNAL `SETNAM` (`$FFBD`) weiter. Der Zeiger liegt eine komplette Seite zu hoch. Dies kann sowohl seltsame Dateinamen-Zeichen im VICE als auch `LOAD ERROR 4` verursachen.

## Umsetzung

In `c64basic/compiler.py` sind sämtliche bekannten vom Compiler erzeugten Low-/High-Immediate-Zeiger mit `+1` jetzt eindeutig geklammert:

```asm
    LDX #<(name+1)
    LDY #>(name+1)
    JSR $FFBD
```

Betroffen sind:

- `LOAD` mit Literaldateinamen (`__basic_string_N+1`)
- `LOAD` mit dynamischem Dateinamen (`__basic_string_expr+1`)
- `OPEN` mit Dateinamen (`__basic_string_expr+1`)
- `INPUT` numerische Feldkonvertierung (`__basic_field_buffer+1`)

**Keine Änderung** der Stage-410-PETSCII-Dateinamenlogik, D64-Sektoren, Sprite-Rohdaten oder VICE-Einstellungen.

## Nachweis

Die Tests `test_stage411_c64_setnam_pointer.py` lesen die tatsächlich generierten Maschinenbytes aus dem PRG aus und vergleichen die 16-Bit-Adresse, die bei `JSR $FFBD` in X/Y übergeben wird, mit der Adresse der literal kodierten Daten beziehungsweise dem CBSS-Symbol. Die Tests prüfen außerdem `OPEN`, variable `LOAD`-Namen, die numerische Eingabefeldadresse sowie die Assembler-Präzedenz.

- 6 neue Stage-411-Tests: OK.
- 7 Stage-410-PETSCII-Tests: OK.
- 6 Stage-408-Konvertierungstests: OK.
- ZIP-Integrität und Python-Syntax: geprüft.
- Kein echter VICE-Windows-End-to-End-Test; der Benutzer muss das aktualisierte PRG oder D64 in VICE prüfen.

## Test

Das beigefügte `Sprite_A_411_Test.zip` enthält ein mit Stage 411 neu generiertes PRG und ein D64 mit `SPRITE_A` und `SPRITES.SPR`. **Alte PRGs/D64s (Stages 409/410) ersetzen** und in VICE das neue D64 einlegen. Die originale Sprite-Datei bleibt unverändert.
