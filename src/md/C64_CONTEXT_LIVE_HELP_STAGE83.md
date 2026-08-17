# Stage 83 – C64 Kontext-Disassembly + Live-Hilfe-Layout

Basis: Stage 82. Die vorhandenen C64-ROM-Kommentare, die gemeinsame Kommentarflucht und der Hex-Bytecode hinter jeder Anweisung bleiben erhalten.

## Live-Hilfe

- `Aktuell: ...` steht nicht mehr in der gelben Kopfzeile, sondern in einer eigenen Zeile direkt darunter.
- `Aktuell: ...` wird grün dargestellt.
- Mnemonic und Operandensignatur bleiben gelb/fett.
- Wenn `Mnemonic + Operandensignatur` nicht in die verfügbare Breite der Live-Hilfe passen, beginnt die komplette Operandensignatur in der nächsten Zeile.
- Vor `Hinweis: interne ROM-Routine; ...` wird eine zusätzliche Leerzeile ausgegeben.

Beispiel:

```text
JSR    $hhhh
Aktuell: $E544
Ruft ein Unterprogramm auf und legt die Rücksprungadresse auf dem Stack ab.
Zielbeschreibung: Bildschirm löschen

Hinweis: interne ROM-Routine; nicht Teil der stabilen KERNAL-Jump-Table.
```

## Kontextanalyse des C64-Disassemblers

Stage 83 erkennt nun direkt aufeinanderfolgende Opcode-Paare:

```asm
LDA #$nn
STA $hhhh
```

Die Erkennung basiert auf den tatsächlichen 6510-Bytes (`A9 nn` gefolgt von `8D ll hh`) und nicht nur auf formatiertem Text.

### Bildschirm-RAM

Für Standard-Bildschirm-RAM `$0400-$07E7` wird der geladene Screen-Code und die Zielposition kommentiert.

```asm
    LDA #$01         ; Bildschirmcode für "A" | $0801: A9 01
    STA $0400        ; linke obere Bildschirmposition | $0803: 8D 00 04
```

### Farb-RAM

Für Farb-RAM `$D800-$DBE7` wird der Farbwert und die Zielposition kommentiert.

```asm
    LDA #$01         ; Farbe weis | $0801: A9 01
    STA $D800        ; Farbe der linken oberen Position | $0803: 8D 00 D8
```

Bei anderen Zellen innerhalb der 40x25-Bereiche wird Zeile/Spalte angegeben.

## Bytecode bleibt erhalten

Neue semantische Kommentare werden immer vor den vorhandenen Hex-Bytecode gesetzt:

```text
<Anweisung> ; <Semantik> | $Adresse: <Hexbytes>
```

Der Hex-Bytecode wird nicht ersetzt oder entfernt.

## Direktheit des Musters

Ein tatsächlich ausgeführter Opcode zwischen `LDA #imm` und `STA abs` trennt den Zusammenhang. Beispiel:

```asm
LDA #$01
NOP
STA $0400
```

wird nicht als zusammengehöriges Lade-/Speicherpaar kommentiert.
