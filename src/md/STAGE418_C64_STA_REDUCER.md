# Stage 418 – STA reducer in den C=64-Projekteinstellungen

Basis: `d64_dism_asm_417.zip`. Beibehalten: C64 BASIC Compiler, Screen-/Software-Sprite Runtime, D64-/VICE-Ladewege, Hardware- und Bitmap-Sprite-Editoren.

## Projektoption

`Projekt-Einstellungen → C=64 → [Profil 68000/68010/68020/68030] → Compiler → Optimizer → STA reducer`

- Checkbox standardmäßig AUS (identischer Compiler-Output wie Stage 417 für Software-Sprite-STA-Befehle).
- Bei Aktivierung erzeugt `SPRITE DRAW`/`SPRITE ERASE` bei sinnvoller Ersparnis binäre Lookup-Tabellen für **exakt dieselben geänderten VIC-II-Bytes**. Unrentable kleine/sparse Änderungen bleiben unverändert als direkte STA-Befehle.
- Unabhängig vom Schalter `Enable Optimizer` für PRINT/String-Optimierungen.
- Getrennte Einstellung je C64-Profil; Speicherung im Projekt unter `Settings.C64.<Profil>.Compiler.Optimizer`, Schlüssel `STAReducer=true/false`. Fehlender Schlüssel alter Projektdateien => AUS.
- Im BASIC-Compile-Knopf wird der Schalter explizit an `compile_basic_to_assembly(..., sta_reducer=...)` weitergereicht.

## Tabellenformat (MOS 6510)

Ein Eintrag ist `[count][address low][address high][bytes...]`:

- `1..127`: Literal-Block; anschließend exakt `count` Werte.
- `129..255`: RLE-Füllblock; Länge `256-count`, anschließend **ein** wiederholter Wert.
- `0`: Ende der Tabelle.
- Keine Lücken werden beschrieben; Block-Adressen dürfen beliebige 16-Bit-RAM-Adressen enthalten.
- RAM-Zeiger `$FB/$FC` (Quelle), `$FD/$FE` (Ziel); 1 CBSS-Byte als Wiederholungswert.

Das gemeinsame Unterprogramm `__basic_sta_reducer_apply` interpretiert die Tabellen. Bei deaktivierter Checkbox wird es gar nicht emittiert. Bei wiederholten, benachbarten Farbwerten ersetzt z.B. ein RLE-Datensatz von 4 Bytes bis zu 127 einzelne STA-Befehle. Ein 180-Byte-Füllbereich braucht zwei RLE-Datensätze (9 Tabellenbytes inklusive Terminator) statt 540 Maschinenbytes allein für die direkten STA-Befehle.

Die Tabellen und die einmalige Routine kosten selbst RAM und CPU-Laufzeit. Eine Größenabschätzung verhindert die Verwendung bei kurzen/sparsamen Deltas; es gibt keine garantierte Ersparnis für jede Sprite-Sequenz. Die Kodierung wird unverändert in die PRG eingebettet, **nicht** als Windows-Datei geladen.

## Prüfungen

- `python -m unittest -v test_stage418_sta_reducer` (4 Tests)
- Direkter vs. komprimierter Sprite-PRG-Vergleich
- Sektor-unabhängige, byteweise Prüfung von RLE/Literal-/Grenzübergängen, auch Farb-RAM
- Ausführung der generierten Reduzier-Routine in einer 6510-CPU-Simulation
- Python Syntax-/Assemblerprüfung und Projekt-ZIP-Integrität
- Windows-/VICE-GUI-End-to-End-Test weiterhin nötig
