# Stage 588 – Kontext-Tooltip für lokale Stackreservierungen

Verbindliche Grundlage: `d64_dism_stage587.zip`.

## Was neu ist

Im bestehenden Assembler-Editor `SourceTextEdit` wird beim Hover über das
Mnemonic `sub` der zugehörige Funktionsprolog erkannt, wenn direkt davor
(nur Leerzeilen und reine Kommentarzeilen dazwischen) steht:

```asm
push ebp
mov ebp, esp
sub esp, 4
```

Die gemeinsame Hilfe erklärt:

- `push ebp`: den bisherigen Frame-Pointer auf dem Stack sichern;
- `mov ebp, esp`: einen neuen Stackframe mit EBP als Basis einrichten;
- `sub esp, 4`: ESP um vier Bytes **verringern**, wodurch vier Bytes
  zusätzlicher lokaler Speicher auf dem nach unten wachsenden Stack
  reserviert werden, z. B. für eine lokale 32-Bit-Variable (`[ebp-4]`).
  Es wird dadurch noch **kein** Wert geschrieben oder initialisiert.

Ein Rückbau geschieht beim Epilog `mov esp, ebp` / `pop ebp`.
Der bereits vorhandene Tooltip für die ersten zwei Befehle und der Epilog-
Tooltip bleiben unverändert. Die Kontext-Hilfe greift wie zuvor nur beim
Hover auf das Mnemonic beziehungsweise Textcursor auf dem Mnemonic und folgt
den Projekt-Einstellungen für Assembler-Tooltips und Dark/Light-Mode.

Auch andere positive Byte-Anzahlen (`sub esp, 16`, `sub esp, 0x10`) sowie die
PE64-Variante mit `push rbp` / `mov rbp, rsp` / `sub rsp, 8` werden erkannt.
PE32-/PE64-Code muss exakt zueinander passen; C64-/Amiga-Assembler bleibt
unverändert. Andere Anweisungen oder Labels zwischen dem Prolog und `sub`
verhindern den speziellen Tooltip.

## Geänderte Dateien

- `asm_stack_frame_tooltips.py`: neue Qt-unabhängige Funktion
  `stack_frame_allocation_tooltip`.
- `d64_dism.py`: Kontextaufruf in `SourceTextEdit` für die dritte Anweisung.
- `test_stage586.py`: vorhandene Prolog-Erkennungstests mit neuer Erweiterung
  kompatibel gehalten.
- `test_stage588.py`: neue Unit- und Editor-Kontexttests.

## Tests

- `python -m unittest -v test_stage586.py test_stage588.py`: 14 Tests erfolgreich.
- `python -m unittest -q test_stage585.py test_stage587.py test_stage588.py`:
  25 Tests erfolgreich.
- Kein nativer PyQt5-GUI-Hovertest; die Erkennung im realen Editor wurde
  isoliert mittels AST-Test geprüft.

Keine Änderung an Compiler, Stackframe-Optimierung, DLL, CES oder Loader.
