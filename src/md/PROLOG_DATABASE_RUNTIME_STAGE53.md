# PROLOG Database Runtime – Stage 53

## Fehlerbild

`arzt_mit_fachwissen.exe` stürzte unter GDB reproduzierbar bei
`0x00401245` ab. Laut Symbol-Map ist das `__rt_deref+5`.

Der Fehler trat in der Wissensregel

```prolog
hoher_blutdruck(Patient) :-
    blutdruck(Patient, Systolisch, _),
    Systolisch > 140.
```

nach erfolgreicher Auswertung des Vergleichs auf.

## Ursache

`__rt_solve_goals` hält in `EBX` die verbleibende Goal-Chain. Die
arithmetischen Vergleichs-Builtins `<`, `=<`, `>` und `>=` verwendeten jedoch
`EBX` als Scratch-Register für den ausgewerteten linken Zahlen-Term:

```asm
mov ebx, eax
...
__rt_bi_gt_ok:
push ebx
call __rt_solve_goals
```

Bei einem wahren Vergleich wurde dadurch nicht die Restkette, sondern ein
INTEGER/FLOAT-Term an `__rt_solve_goals` übergeben. Dieser wurde wie ein
`NODE_LINK` gelesen; dessen `+8`-Feld ist bei einem Integer kein Goal-Term und
enthielt typischerweise `INVALID` (`0xFFFFFFFF`). Anschließend landete dieser
ungültige Handle in `__rt_deref`, was den SIGSEGV bei `0x00401245` erklärt.

## Korrektur

Der linke ausgewertete Zahlen-Term wird nun in `ESI` gehalten. Nach `get2()`
wird der ursprüngliche Vergleichs-Goal-Term in `ESI` nicht mehr benötigt, und
`__rt_eval_arith` erhält `ESI` gemäß Runtime-Konvention.

Neu:

```asm
call __rt_eval_arith
...
mov esi, eax
...
push ecx        ; rechter Zahlen-Term
push esi        ; linker Zahlen-Term
call __rt_numeric_compare
...
__rt_bi_gt_ok:
push ebx        ; unveränderte Rest-Goal-Chain
call __rt_solve_goals
```

Damit bleibt `EBX` während `<`, `=<`, `>` und `>=` unverändert.

## Regressionen

Neue Stage-53-Tests prüfen:

1. alle vier Vergleichs-Builtins benutzen `ESI` statt `EBX` als numerischen Scratch;
2. `__rt_bi_gt_ok` setzt die ursprüngliche `EBX`-Restkette fort;
3. PE32+ verwendet dieselbe Registerregel;
4. `arzt_mit_fachwissen.pl` linkt weiterhin vollständig als PE32 und PE32+.

Gesamtlauf:

```text
Ran 555 tests
OK
```

## Referenz-Binaries

Unter `examples/prolog_database/generated_stage53/` liegen frisch erzeugte
PE32-Dateien, Assemblerlisten und Symbol-Maps für:

- `arzt_patient.exe`
- `arzt_mit_fachwissen.exe`

Beide PE32-Dateien sind 28.160 Bytes groß. Der große Stage-50-Nullblock bleibt
beseitigt.
