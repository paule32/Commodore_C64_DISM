# Stage 484 – GNU AT&T: FNSTCW / FLDCW brauchen WORD-Speicher

Verbindliche Grundlage: `d64_dism_asm_483.zip`.

## Behobener Fehler

Die Umwandlung von Intel nach AT&T war bereits richtig:

```asm
fnstcw word ptr [esp]    ; Intel
fnstcw (%esp)            # AT&T
```

Beim anschließenden Rückweg zum internen PE32-/PE64-COFF-Assembler ging aber die **16-Bit-Speicherbreite** verloren. Dadurch entstand `fnstcw [esp]`, und der interne Encoder brach ab mit `FNSTCW erwartet WORD-Speicher.`

Stage 484 rekonstruiert bei **`FNSTCW`** und **`FLDCW`** die erforderliche explizite `word ptr`-Breite:

```asm
fnstcw (%esp)            # AT&T         -> fnstcw word ptr [esp]
fldcw 4(%esp)            # AT&T         -> fldcw word ptr [esp+4]
fnstcw (%rsp)            # AT&T, PE64   -> fnstcw word ptr [rsp]
fldcw 4(%rsp)            # AT&T, PE64   -> fldcw word ptr [rsp+4]
```

Auch symbolische Speicheroperanden (`fnstcw symbol`, `fldcw symbol+2`) erhalten `word ptr`. Zeilen- und Kommentarzuordnung sowie `%include` und die übrigen Makros bleiben unverändert.

## Betroffene Dateien

- `windows_asm_att.py`: 16-Bit-Speicherbreite bei x87-Control-Word-Befehlen nach der GNU-Operandenkonvertierung.
- `test_stage484_att_x87_control_word.py`: neun Regressionstests, einschließlich realer interner PE32-/PE64-Assemblierung, Vergleich des erzeugten Maschinencodes und vollständigem COFF-/PE-Linking.

## Verifikation

Der fokussierte Testlauf mit Stage 479 und Stage 483 ergab 38 bestandene Tests (`pytest -q test_stage484_att_x87_control_word.py test_stage483_att_wfm_entry_regression.py test_stage479_output_paths_att.py`).

Ein breiterer historischer Testlauf erreichte das Zeitlimit und wurde daher **nicht** als erfolgreich abgeschlossen gewertet. Kein nativer Windows-Qt5-Interaktionstest möglich.
