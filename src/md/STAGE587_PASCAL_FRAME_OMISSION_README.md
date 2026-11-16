# Stage 587 – Pascal: No Stack Frames mit Stackhöhen-Nachweis

**Verbindliche Grundlage:** `d64_dism_stage586.zip`.

## Grundsatz

`push ebp; mov ebp, esp` bzw. `push rbp; mov rbp, rsp` sichern den alten
Frame-Pointer und etablieren einen neuen Stackframe; sie sichern **nicht**
den vollständigen Stack. Ein Compiler kann diese zwei Instruktionen und
ihre zugehörigen Epiloge auslassen, sofern keine Routine den Frame-Pointer
benötigt und die Calling Convention, Registerwiederherstellung sowie
Exception-Unwind unverändert korrekt bleiben.

Die Checkbox **Windows → 32/64-Bit → Compiler → Pascal → Optimierung → Stack:
No Stack Frames** bleibt die Schaltstelle; die Einstellung gilt unabhängig
von O0, O1, O2 und O3. Standard bleibt OFF. Es wurden keine neuen Optionen
hinzugefügt und keine bestehenden Einstellungen überschrieben.

## Verbesserte PE32-Optimierung

Die bisherige Stage-538-Prüfung lehnte jede Routine mit `CALL`, `PUSH` oder
`POP` pauschal ab – sogar bei korrekt ausgeglichener Stackhöhe. Stage 587
untersucht nun die erreichbaren Kontrollflusszweige und berechnet die
ESP-Differenz bis zu jedem Epilog. Nur wenn **alle** Pfade mit korrekt
balanciertem Stack ankommen, wird transformiert.

- Bei `CALL`-Routinen, korrekt gepaarten `PUSH`/`POP` und `ADD/SUB ESP` mit
  nachvollziehbarer Stackbilanz kann das EBP-Frame entfallen.
- `EBX`, `ESI`, `EDI` werden weiterhin korrekt gesichert. Der bisherige
  EBP-basierte Wiederherstellungsblock wird zu symmetrischem
  `pop edi; pop esi; pop ebx` umgebaut.
- Positive Parameterzugriffe, z. B. `[ebp+8]`, werden passend zur
  berechneten Stackhöhe nach `[esp+offset]` umgerechnet. Dies funktioniert
  auch bei O0/O1-Parametermaterialisierung **vor** dem Register-Prolog.
- `ret N` für `stdcall` bleibt unverändert.
- Jeder erhaltene Assemblerbefehl behält seine Source-Map-Verknüpfung.

### Beispiel: PE32 mit `WriteLn`

Vorher:

```asm
push ebp
mov ebp, esp
push ebx
push esi
push edi
mov eax, 3
call __pas_print_int
call __pas_print_newline
mov ebx, dword ptr [ebp-4]
mov esi, dword ptr [ebp-8]
mov edi, dword ptr [ebp-12]
mov esp, ebp
pop ebp
ret
```

Mit **No Stack Frames = ON**:

```asm
push ebx
push esi
push edi
mov eax, 3
call __pas_print_int
call __pas_print_newline
pop edi
pop esi
pop ebx
ret
```

### Beispiel: PE32 mit Parameter

```asm
; alt: mov eax, [ebp+8]
; neu nach drei Register-PUSH: mov eax, [esp+16]
```

Die konkrete Verschiebung hängt von der zum Instruktionszeitpunkt
nachgewiesenen Stackhöhe ab.

## Verbesserte PE64-Optimierung

Echte Windows-x64-**Leaf**-Routinen, die keine CALLs, Stackallokation und
keine Sicherung nichtflüchtiger Register benötigen, dürfen jetzt auch ihre
Parameter-Home-Slots direkt relativ zu `RSP` adressieren:

```asm
; alt (Home-Slot auf der Caller-Seite):
push rbp
mov rbp, rsp
mov qword ptr [rbp+16], rcx
mov rsp, rbp
pop rbp
ret

; neu:
mov qword ptr [rsp+8], rcx
ret
```

Dies gilt **nicht** für Win64-Routinen mit `CALL`, Shadow Space, Stack-Locals
oder nichtflüchtigen Registern: Hier bleiben Prolog/Epilog erhalten, damit
keine falsche Stackausrichtung/Exception-Unwind-Situation entsteht.

## Sicherheits- und ABI-Grenzen

Der Frame wird NICHT entfernt bei:

- aktivem **Stack-Protector-Cookie**, solange die Routine instrumentiert wird;
- echten lokalen/temporären Stackvariablen mit negativen `EBP/RBP`-Offsets;
- TRY/EXCEPT/FINALLY- bzw. Exception-Handlern;
- unbalancierten oder nicht beweisbaren `PUSH`/`POP`-/ESP-Pfaden;
- unbekannten Sprungzielen, Spezial-Stackoperationen und ESP-basierten
  Speicherzugriffen, deren Bedeutung sich durch das Entfernen verändert;
- Win64-Nonleaf-Funktionen mit Calls, Stackallokation oder erforderlichen
  Unwind-Daten;
- nicht erfassten internen DLL-Entry- und ABI-Wrappern.

Auch wenn das Checkbox-Häkchen aktiv ist, dürfen also in korrekt erzeugtem
Assembler weiterhin EBP-/RBP-Prologe auftauchen. Ein pauschales Entfernen
würde Speicherzugriffe und Rücksprünge beschädigen.

## Geänderte Dateien

- `pascal_optimizer.py` – neue PE32-Stackhöhen-Analyse und PE64-Leaf-Rebase
- `d64_dism.py` – präziser Tooltip für die bestehende Checkbox
- `test_stage538.py` – bisherige Nachweise an die sicheren neuen Fälle angepasst
- `test_stage587.py` – neue Regressionstests

Keine DLL-Exports, Runtime-ABI, CES-Einstellungen, Loader-Dateien oder
Projektdateiformate verändert.

## Prüfungen

- `python -m unittest -q test_stage587.py test_stage538.py` – **24/24 bestanden**.
- `python -m unittest -q test_stage537.py test_stage539.py test_stage540.py test_stage579.py test_stage581.py` – **15/15 bestanden**.
- `python -m unittest -q test_stage583.py test_stage585.py test_stage586.py` – **12/12 bestanden**.
- Eine kombinierte Testsuite mit `test_stage578.py` meldete die Tests als
  bestanden, ließ jedoch den Testprozess nicht sauber enden; deshalb wird
  dieser Lauf **nicht** als vollständig erfolgreicher Lauf gewertet.
- `python -m py_compile pascal_optimizer.py c64pascal/compiler.py test_stage587.py` – erfolgreich.

Ein Windows-Native-Build und der PE32/PE64-Ausführungstest wurden in dieser
Umgebung nicht durchgeführt. Entsprechend ist die Laufzeitkorrektheit auf
Windows mit dem individuellen Linker noch gegenzuprüfen.
