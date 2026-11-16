# Stage 589 – Pascal-Stackframe-Slots und ASM-Sprungziel-Hitbox

**Basis:** `d64_dism_stage588.zip`

## Änderungen

### Assembler-Hilfe (`SourceTextEdit`)

- Beim Hover über `mov dword ptr [ebp-4], edx` erkennt die PE32-Hilfe einen vorausgehenden `push ebp` / `mov ebp, esp`-Prolog und `sub esp, 4`. Der Tooltip erklärt die Übertragung des 32-Bit-Werts von EDX in den lokalen Stack-Slot. Dort kann z. B. ein Pascal-Stack-Cookie liegen. `SUB` reserviert nur, `MOV` schreibt den Wert.
- Beim Hover über die zusammengehörige Folge `mov ebx, dword ptr [ebp-8]`, `mov esi, dword ptr [ebp-12]`, `mov edi, dword ptr [ebp-16]` erklärt der Tooltip die Wiederherstellung der zuvor mit `push ebx` / `push esi` / `push edi` gesicherten Register. Die Erkennung prüft die erwartete Stackbelegung; abweichende Offsets werden nicht fälschlich als die genannten Register-Slots bezeichnet.
- **Fachliche Präzisierung:** Die genannten negativen EBP-Offsets sind keine Funktionsparameter. Bei einem klassischen x86-EBP-Frame beginnen Stackparameter typischerweise bei `[ebp+8]`, `[ebp+12]`, ... .
- Kein Eingriff in Compiler, Runtime-DLL oder PE64-Codegenerierung. Vorhandene Prolog-/Epilog- und SUB-Tooltips bleiben bestehen.

### Sprung- und CALL-Links

- `_jump_target_at_point` prüft die sichtbaren Pixelgrenzen des `target`-Textes per `QTextCursor`/`cursorRect`.
- Bereiche rechts vom letzten Zeichen des Zielnamens sind nicht mehr klickbar oder als Link-Cursor erkennbar.
- `CALL`, `JNE`, `JMP` und weitere durch den vorhandenen `JUMP_TARGET_PATTERN` abgedeckte Befehle behalten ihre bisherige Navigationslogik; nur die Maushitbox wird eingeschränkt.

## Geänderte Dateien

- `d64_dism.py`
- `asm_stack_frame_tooltips.py`
- `test_stage586.py` (Testisolierung kennt die neue Hilfsfunktion)
- `test_stage589.py` (neu)

## Prüfungen

- `python -m unittest -q test_stage586 test_stage587 test_stage588 test_stage589`: **37 Tests erfolgreich** (vor der finalen Suchweitenanpassung).
- `python -m unittest -q test_stage586 test_stage588 test_stage589`: **22 Tests erfolgreich** (nach der finalen Suchweitenanpassung).
- AST-Validierung von `d64_dism.py` erfolgreich, Python-Syntaxprüfung der Hilfs-/Testdateien erfolgreich.
- Ein realer PyQt5-Hover- und Klicktest unter Windows ist noch ausstehend, da PyQt5 in der Testumgebung nicht verfügbar ist.
