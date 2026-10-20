# Stage 420: CALL reducer (MOS6510 Runtime Dead-Code-Elimination)

Verbindliche Grundlage: `d64_dism_asm_419.zip`.

## GUI und Speicherung

Unter **Projekt-Einstellungen → C=64 → 68000/68010/68020/68030 → Compiler → Optimizer**
steht nun eine standardmäßig deaktivierte Checkbox **CALL reducer** direkt unter **STA reducer**.

Die Einstellung wird pro Profil im vorhandenen Abschnitt
`Settings.C64.<Profil>.Compiler.Optimizer` als `CALLReducer=true/false`
gespeichert und bei erneutem Öffnen des Projekts wieder eingelesen. Der
aktuelle Checkbox-Zustand steuert den Compile-Button und wird über
`compile_basic_to_assembly(..., call_reducer=...)` an den Compiler übergeben.
CALL reducer und STA reducer sind unabhängig voneinander schaltbar; die
PRINT-Optimizer-Auswahl wird unverändert beibehalten.

## Implementierung

- Modul `c64basic/call_reducer.py`, Funktion `reduce_runtime_calls`.
- Nach der BASIC-Codegenerierung und vor dem Ausgeben der Daten/CBSS wird nur
  der von der Compiler-Runtime erzeugte Code analysiert.
- Alle Symbole, die von außerhalb dieses Bereichs referenziert werden, sind
  Einstiegspunkte. Innerhalb der Runtime werden `JSR`, `JMP`, bedingte Sprünge
  und normaler Fallthrough aufgelöst. `RTS`, `RTI` und unbedingte Sprünge
  beenden den linearen Kontrollfluss.
- Adressreferenzen auf Code-Labels in sonstigen Operanden werden konservativ
  als weitere Einstiegspunkte betrachtet (z.B. indirekte Funktionszeiger,
  selbstmodifizierender Code).
- Nicht erreichbare Assemblerzeilen und ihre Labels werden entfernt. Keine
  Sprunganweisung der erreichbaren Runtime wird umgeschrieben.
- Konstantentabellen, Screen/Sprite-Ressourcen, Datenfelder und `.cbss` liegen
  außerhalb des Reduktionsbereichs und bleiben vorhanden.
- Enthält die Runtime künftig `.byte`-/`.word`-Daten oder unbekannte Assembler-
  Direktiven, bleibt der gesamte Bereich unverändert (sicherer Fallback).
- Der Compiler meldet die Zahl entfernter Assembler-Anweisungen und Labels in
  `C64BasicCompileResult.notes`.

## Grenzen

Die Analyse bezieht sich auf die **vom C64-BASIC-Compiler erzeugte Runtime**,
nicht auf beliebige selbstgeschriebene Assemblerprogramme. Handgeschriebene
`SYS`-Adressen, die ohne symbolischen Verweis direkt in den generierten
Runtime-Code springen, können statisch nicht erkannt werden. Für derartige
Spezialfälle den CALL reducer deaktivieren.

## Vergleich (intern assemblerte PRGs)

| BASIC-Test | Ohne | Mit | Einsparung |
|---|---:|---:|---:|
| `10 END` | 899 B | 127 B | 772 B |
| `10 PRINT "HALLO"` / `END` | 915 B | 177 B | 738 B |
| `SCREEN ON / SPRITE SOFTWARE ON / SCREEN OFF` | 1.214 B | 436 B | 778 B |

Die Größen umfassen den PRG-Header und den BASIC-SYS-Startstub.

## Tests

- 6 neue gezielte Unit-Tests, einschließlich realer Assemblierung.
- Frühere Stage-418-/419-Tests für STA reducer und Bitmap-Initialisierung.
- Frühere Stage-411-/413-/417-Tests für SETNAM, Host-Sprites und Software-Sprites.
- 36 zusätzliche Assembler-Smoke-Varianten (9 BASIC-Szenarien × 4 PRINT-Strategien).
- Python-Syntaxprüfung und ZIP-Integrität.

Ein kompletter Windows-VICE-GUI-Laufzeittest wurde hier nicht durchgeführt.
