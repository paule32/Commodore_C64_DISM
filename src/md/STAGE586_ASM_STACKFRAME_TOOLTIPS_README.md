# Stage 586 – Kontexthilfe für x86-Stackframe-Prolog/Epilog

**Verbindliche Grundlage:** `d64_dism_stage585.zip`.

## Umsetzung

Die vorhandene Assembler-Hilfe im `SourceTextEdit` wurde erweitert. Sobald der
Benutzer den Mauszeiger über das Mnemonic einer der beiden zusammengehörigen
Anweisungen bewegt oder den Text-Cursor dort positioniert, zeigt das bereits
vorhandene Hilfefenster die Erklärungen beider Befehle und ihre gemeinsame
Wirkung. Es wird kein zweites Fenster angelegt. Die vorhandene Projektoption
für ASM-Tooltips sowie Dark-/Light-Mode bleiben wirksam.

### Prolog (PE32)

```asm
push ebp
mov ebp, esp
```

- `push ebp`: legt den bisherigen Frame-Pointer `EBP` auf den Stack;
  `ESP` wird um vier Bytes verringert.
- `mov ebp, esp`: setzt `EBP` auf den aktuellen Stackpointer und richtet
  damit die Basis des neuen Stackframes ein.
- Beide Befehle bewahren den alten Frame-Pointer und richten einen
  neuen Stackframe ein. Sie kopieren **nicht den gesamten Stack**.

### Epilog (PE32)

```asm
mov esp, ebp
pop ebp
```

- `mov esp, ebp`: setzt `ESP` zur Stackframe-Basis zurück und gibt so
  die lokalen Stack-Reservierungen dieses Frames frei.
- `pop ebp`: stellt den zuvor gesicherten Frame-Pointer wieder her;
  `ESP` wird um vier Bytes erhöht.
- Dies löst den zuvor mit `push ebp` und `mov ebp, esp`
  eingerichteten Stackframe wieder auf.

Gleichzeitig werden für PE64 die äquivalenten Folgen
`push rbp` / `mov rbp, rsp` und `mov rsp, rbp` / `pop rbp`
mit acht Byte Stackbreite erkannt.

## Erkennungsregeln

- Die zwei Befehle müssen unmittelbar aufeinander folgen. Reine Leerzeilen
  oder ganze Kommentarzeilen dürfen dazwischen liegen (maximal vier).
- Groß-/Kleinschreibung, Leerzeichen am Komma, trailing `;`-Kommentare und
  optionale Labels direkt vor einem Befehl sind erlaubt.
- Bei anderen Befehlen, vertauschter Reihenfolge, isolierten Mnemonics oder
  Treffern in Kommentaren wird kein spezieller Stackframe-Tooltip gezeigt.
  Die normale Opcode-Hilfe bleibt dann erhalten.
- Die Erweiterung ist auf die x86-Targets `pe32` und `pe64` begrenzt.

## Geänderte/zusätzliche Dateien

- `d64_dism.py`: Nutzung der vorhandenen Assembler-Hilfe für die
  Befehlspaare, sowohl Hover- als auch Cursor-Kontext.
- `asm_stack_frame_tooltips.py`: Qt-unabhängiger Parser und Beschreibungstexte.
- `test_stage586.py`: Unit- und Integrationsprüfungen für die Erkennung.

## Tests

- `python -m unittest -v test_stage586.py`: **8 erfolgreich**.
- `python -m pytest -q test_stage584.py test_stage585.py test_stage586.py`:
  **16 Tests erfolgreich**, dazu sechs erfolgreiche Subtests.
- `d64_dism.py`: Python-Syntax geprüft, indem ausschließlich für die
  Prüfung die schon vorhandenen Python-3.15-`lazy`-Imports durch normale
  Imports ersetzt wurden (die originale Datei ist unverändert an diesen Stellen).
- Kein nativer PyQt5-GUI-Test in dieser Umgebung (PyQt5 nicht installiert).

**Unverändert:** Assembler-Codegenerierung, Linker, CES, Pascal-Runtime-DLL,
MSZIP-Loader und weitere Projektfunktionen.
