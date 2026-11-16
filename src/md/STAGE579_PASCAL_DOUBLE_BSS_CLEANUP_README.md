# Stage 579 – Pascal Double-BSS-Bereinigung (PE32 und PE64)

**Verbindliche Basis:** Stage 578 (`d64_dism_stage578.zip`). Keine Änderung an
Pascal-Unit-Imports/Runtime-DLL-Exports aus Stage 578.

## Fundstellen und Ursache

In `c64pascal/compiler.py` wurden bei `uses_double_runtime` drei globale
Hilfssymbole pauschal in `.bss` angelegt:

```asm
__pas_double_scratch: resq 1       ; 8 Bytes, im gesamten Codegenerator ungenutzt
__pas_double_int_scratch: resd 1   ; 4 Bytes, bisher für PE32 Integer -> Double
__pas_double_buffer: resb 64       ; 64 Bytes, im gesamten Codegenerator ungenutzt
```

PE32 und PE64 emittierten diese drei Definitionen in `_emit_data()`; der
PE64-Code enthielt zusätzlich denselben überflüssigen Block in
`_emit_external_declarations()`. In der mitgelieferten
`test_raise.generated.pe32.asm` war keiner der drei Bezeichner jenseits der
BSS-Definitionen referenziert. Das Beispiel ist ein älterer gespeicherter
Assemblerstand, kein neuer vollständiger Windows-Compile.

## Korrektur

- Die drei BSS-Reservierungen wurden in allen drei Emissionsstellen entfernt.
- PE32 wandelt einen Integer für x87 nun mit einem temporären Stackoperanden
  um, statt 4 Bytes global zu reservieren:

  ```asm
  push eax
  fild dword ptr [esp]
  add esp, 4
  ```

  `fild` liest den **signed 32-bit Integer** vom Stack und erzeugt denselben
  x87-Double-Wert wie zuvor. `add esp, 4` entfernt ausschließlich das
  temporäre 4-Byte-Argument. Das Verfahren ist reentrant; verschiedene Threads
  teilen keine mutable Scratch-Variable mehr.
- Der `uses_double_runtime`-Teil der BSS-Sektionsbedingung wurde entfernt:
  ein Double-Literal allein verursacht keine leere BSS-Sektion mehr.
- Die drei unreferenzierten BSS-Zeilen im mitgelieferten historischen
  `runtime/pascal/test/test_raise.generated.pe32.asm` wurden entfernt.
  Dieser Schritt ist **keine** behauptete Windows-Neugenerierung.
- Bestehende globale Pascal-Variablen, Cookie-Speicher, Exception-Frames,
  PE64-Call-Temporaries, Double-Literale und die echte Double-Codegenerierung
  bleiben erhalten.

## Einsparung

**76 Bytes** BSS-Reservierung pro betroffenem PE32/PE64-Modul, das zuvor
`uses_double_runtime` verwendete (8 + 4 + 64). Die tatsächliche PE-Sektions-
belegung kann sich wegen Alignment und Dateilayout anders ändern. `.bss` ist
nicht dateigestützte Nullinitialisierung; eine Verringerung der EXE-Dateigröße
um genau 76 Bytes ist daher **nicht** zugesichert.

Das `push`/`fild`/`add`-Verfahren braucht kurzzeitig 4 Bytes Stack und zwei
zusätzliche Instruktionen verglichen mit einem globalen `fild`-Operanden.

## Überprüfung

```bash
python -m unittest -v test_stage579
python -m unittest -v test_stage578 test_stage537 test_stage538 test_stage545 test_stage546 test_stage535 test_stage539 test_stage551
python -m py_compile c64pascal/compiler.py
```

Die Tests generieren realen PE32/PE64-Assembler auf AST-Ebene ohne ANTLR.
Windows-Binärbuild/Laufzeitprüfung mit NASM, MinGW und Wine/Windows stehen in
dieser Umgebung nicht zur Verfügung. Nach der Übernahme muss ein bestehender
Assembler-/Objektcache für das Pascal-Programm neu gebaut werden, bevor eine
neue EXE die Einsparung widerspiegelt. **Runtime-DLL-Neubau aus Stage 578 bleibt
für `IntToStr`/`StrToInt` weiterhin notwendig.**

## Teststatus dieses Pakets

- **52/52** Tests erfolgreich: Stage 579, 578, 537, 538, 545, 546, 535, 539, 551 und 532.
- Zusätzlich vier direkte Stage-532-Smoketests erfolgreich.
- Ein separater Legacy-Testlauf mit `test_stage544`, `test_stage541`,
  `test_stage542` und `test_stage543` enthält **11 bereits vorhandene
  Fehlschläge und 1 bereits vorhandenen Fehler** in `test_stage544`.
  Der identische Lauf auf der unveränderten Stage 578 liefert dieselben
  11 Fehlschläge und denselben Fehler (veraltete Erwartungen an die seit
  Stage 551 ausgelagerte Konsole). Es handelt sich nicht um eine neue
  Regression durch Stage 579.
