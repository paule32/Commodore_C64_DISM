# Stage 401 – C64 BASIC V2: LOAD ueber KERNAL

Basis: `d64_dism_asm_400.zip` (keine anderen Entwicklungszweige).

## Fehler

Vorher: `BASIC-Zeile 50: BASIC-Anweisung wird nicht unterstützt: LOAD`.
`c64basic/compiler.py` kannte nur das abweichende `LOAD SCREEN`.

## Korrektur

Die Compilerklasse `_BasicCompiler` stellt die Funktion `compile_load()` bereit.
Sie uebersetzt

```basic
10 LOAD "SPRITES",8,1
```

in KERNAL-Aufrufe: `$FFBD` (SETNAM), `$FFBA` (SETLFS), `$FFD5` (LOAD).
`A=0` bedeutet Laden statt Verify; `X/Y=$0801` gilt fuer Sekundaeradresse 0.
Bei Sekundaeradresse 1 stammt die Ladeadresse aus den ersten beiden Bytes
in der PRG-Datei (z. B. `$3000`).

Unterstuetzt werden `LOAD "NAME"`, `LOAD "NAME",8`, `LOAD "NAME",8,1`
und Stringausdruecke/Stringvariablen fuer den Dateinamen sowie numerische
Ausdruecke fuer Geraet und Sekundaeradresse.

Bei KERNAL-Fehlern (Carry=1) wird `?LOAD ERROR <nummer>` ausgegeben und
die kompilierte Programmausfuehrung beendet, statt so weiterzulaufen,
als waeren die Daten vorhanden. `LOAD SCREEN` bleibt separat und unveraendert.

## C64/VICE-Betrieb

- Eine Sprite-Rohdatei `.spr` enthaelt **keinen** 2-Byte-PRG-Ladeheader.
  Fuer `LOAD "SPRITES",8,1` muss ein korrekt erzeugtes `SPRITES.PRG`
  auf dem an Geraet 8 angehaengten Disk-Image bzw. Laufwerk liegen.
- Bei Start ueber VICE Binary Monitor werden die Daten vom C64-KERNAL
  aus dem Laufwerk gelesen; keine Hostdatei wird beim BASIC-Kompilieren
  in das Programm eingebettet.
- Weder laden nach `$3000` noch der damit verbundene Speicherbereich darf
  bereits vom kompilierten Programm oder seinen Daten belegt sein.
- Fehlende Sprungziele (z. B. `GOTO 100` ohne BASIC-Zeile 100) bleiben
  unabhaengige Compilerfehler.
- BASIC-Kontextmenue `Ausfuehren` kann weiterhin den BASIC-Interpreter
  in VICE verwenden; dies ist nicht dasselbe wie die hier erweiterte
  native Compiler-Ausgabe.

## Tests

`python -m unittest -v test_stage401_c64_basic_load.py`: 7 bestanden.
Verifiziert wurden Syntax, mehrere LOADs, Variable als Name, Standardparameter,
KERNAL-Call-Sequenz, Zusammenbau des resultierenden MOS6510-Programms,
Fehler-Ausgabe und Unveraendertheit von LOAD SCREEN.

Ein echter Laufzeittest mit VICE bzw. echter C64-Hardware ist hier nicht erfolgt.
