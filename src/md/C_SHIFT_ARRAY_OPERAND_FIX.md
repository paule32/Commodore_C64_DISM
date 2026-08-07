# C-Shift mit Array-Operanden

## Fehler

Die C64-Grafiklaufzeit verwendet beim Wiederherstellen einer 16-Bit-X-Koordinate:

```c
return GfxFloodXLow[index] |
       (GfxFloodXHigh[index] << 8);
```

Die ausgelieferte C-Grammar besitzt noch keine eigene Shift-Ebene. Der
Compiler senkt `<<` und `>>` deshalb vor dem ANTLR-Lauf auf interne
Funktionsformen ab. Bisher akzeptierte diese Absenkung links und rechts nur
einfache Bezeichner oder Zahlen. `GfxFloodXHigh[index]` blieb daher stehen und
der Parser las das erste `<` als relationalen Operator.

## Korrektur

Die Shift-Absenkung erkennt nun auch Arrayzugriffe:

```text
GfxFloodXHigh[index] << 8
    -> __d64_shl(GfxFloodXHigh[index], 8)
    -> __d64_shl(__d64_arr_get_1(GfxFloodXHigh, index), 8)
```

Zusätzlich erzeugen beide Backends echten Shift-Code:

- MOS 6510: 16-Bit-Schleife mit `ASL/ROL` beziehungsweise `LSR/ROR`;
- Motorola 68000: `LSL.W`, `LSR.W` oder bei vorzeichenbehaftetem Rechts-Shift
  `ASR.W`.

Damit funktioniert die Korrektur nicht nur in `graphics_api.c`, sondern auch
in normalen C-Programmen mit festen Arrays.

## Array-Codeerzeugung

Die internen Aufrufe `__d64_arr_get_N` und `__d64_arr_store_*_N` werden nun
vor der Codeerzeugung in normale `DesignatorExpression`-/
`AssignmentStatement`-Knoten umgewandelt. Mehrdimensionale C-Arrays werden
dabei row-major auf den bereits reservierten flachen Speicherbereich
abgebildet.
