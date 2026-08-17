# Stage 80 – Localize Vollfläche + C64 Disassembler/ASM-Hilfe

Basis: Stage 79. Die vorhandenen Docking-, C64-Disassembly- und Editorpfade bleiben erhalten; die Änderungen sind additiv.

## Localize PO/MO

Beim Öffnen von `Werkzeuge -> Localize PO->Mo ...` werden das linke Dateisystem-Dock und der normale zentrale Dokumentbereich temporär ausgeblendet. Das `Localize PO/MO`-Dock erhält anschließend mit `resizeDocks(..., 100000, ...)` die komplette verbleibende QMainWindow-Arbeitsfläche. Sichtbare rechte/untere Docks werden weiterhin von Qt respektiert.

Beim Schließen werden der Localize-Zustand gespeichert und die zuvor sichtbaren Bereiche wiederhergestellt.

## C64-Disassembly: Bytecode + Beschreibung

Die bekannte Call-Tabelle enthält weiterhin:

```python
("JSR", 0x5344): "Bildschirm löschen"
```

Aus den Bytes `20 44 53` wird jetzt z. B.:

```asm
    JSR $5344        ; Bildschirm löschen | $0801: 20 44 53
```

Die semantische Beschreibung ersetzt also nicht mehr Adresse/Bytecode, sondern wird davor ergänzt. Die Kommentarspalte bleibt `längste Anweisung + 8 Leerzeichen`.

Für die Editorhilfe werden die Textformen `JSR $5344`, `JSR #$5344` und die gewünschte Alias-Schreibweise `JSR #5344` erkannt. Das ändert nicht die 6510-Adressierungsregeln des Assemblers; `#5344` ist nur ein Dokumentations-Lookup-Alias.

## ASM-Syntaxfarben

Im navy/dunklen Assemblereditor:

- Mnemonics wie `JSR`, `LDA`, `STA`: gelb `#FFD84D`, fett
- Operanden wie `$5344`, `#$20`, `$0400,X`: weiß `#FFFFFF`
- Kommentare: grau
- vorhandene Sprungziel-/Label-Navigation bleibt erhalten

## Live-Befehlsbeschreibung

`SourceTextEdit` besitzt nun ein nicht-modales Info-Overlay `assembler_instruction_help_frame`.

Es wird aktualisiert:

- während der Eingabe über `textChanged`,
- bei Cursorbewegung über `cursorPositionChanged`,
- nach Linksklick auf eine Assemblerzeile/Mnemonic.

Beispiel für `JSR $5344`:

```text
JSR    $hhhh    Aktuell: $5344
Ruft ein Unterprogramm auf und legt die Rücksprungadresse auf dem Stack ab.
Zielbeschreibung: Bildschirm löschen
```

Das Overlay folgt Scrollen/Resize und verschwindet bei Fokusverlust bzw. wenn die aktuelle Zeile kein bekanntes Assembler-Mnemonic enthält.

## Tests

- Stage-80-spezifisch + Stage 78/79 direkt: 21/21 OK
- Gesamtsuite: 770/770 OK
- Python-Compile: OK
- Native PyQt5-Windows-Visualprüfung: in dieser Containerumgebung nicht verfügbar
