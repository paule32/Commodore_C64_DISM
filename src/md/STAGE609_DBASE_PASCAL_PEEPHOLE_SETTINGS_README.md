# Stage 609 – Gemeinsame dBASE-/Pascal-Peephole-Optimierung

**Verbindliche Grundlage:** Stage 608. PE32 und PE64 werden getrennt konfiguriert.

## Neue und bestehende Projekt-Einstellungen

Unter `Windows → 32-Bit / 64-Bit → Compiler → dBASE` zeigt die
synchronisierte **Übersicht** nun die drei Blöcke
`Eingabe-Verzeichnis`, `Ausgabe-Verzeichnis` und `Optimierung`.
Die bisherigen echten Unterseiten bleiben unverändert aufrufbar.

Unter `Compiler → dBASE → Optimierung` befindet sich neben den bestehenden
Gruppen `Visuelle Elemente` und `Variablen und Speicher` eine neue GroupBox
**Peephole Optimierung** mit:

- **Registerbreite**: aktiviert die registerbreitenbewusste Prüfung für `EAX`/`RAX`; keine unsichere `AX`-Verkürzung.
- **Prozessorflags**: erlaubt `MOV` → `XOR`/`INC` nur, wenn entlang des nachfolgenden geradlinigen Pfades sicher keine EFLAGS-Leseoperation vor dem Überschreiben oder Rücksprung auftritt. Sprünge, Labels, Aufrufe und unbekannte Befehle sind Barrieren.
- **Stackzustand**: erlaubt `MOV EAX/RAX, 1` → balanciertes `PUSH 1`/`POP EAX/RAX` ausschließlich unmittelbar vor `RET`; EFLAGS bleiben erhalten.

Die GroupBox wird automatisch auch in der Übersicht `Compiler → dBASE`
und in der übergeordneten `Compiler`-Übersicht angezeigt. Die drei Ansichten
verwenden bidirektional synchronisierte Qt-Checkbox-Klone; maßgeblich sind die
originalen Controls auf der Optimierungsseite.

**Sicherheit:** `Registerbreite` muss zusammen mit wenigstens einer der
beiden anderen Optionen aktiviert werden. Einzeln aktivierte Sicherheitsregeln
führen **nicht** zu einer Code-Änderung. Die Optimierung ist für alte und neue
Projekte standardmäßig *aus* und verhält sich ohne Häkchen wie Stage 608.

## Tatsächliche ASM-Optimierung

Die `windows_peephole.py` wird beim Kompilieren von dBASE und Pascal auf den
PE32/PE64-ASM-Text angewendet, mit Quellzeilenabbildung für Pascal. Die
Compiler-APIs akzeptieren optional `peephole_options`.
Die IDE prüft zusätzlich vor dem Assemblieren/Linken die aktuelle Auswahl gegen
die Kompilierauswahl und führt auf dem tatsächlichen Intel-ASM-Input
abschließend einen idempotenten Peephole-Durchlauf aus. Bei geänderter Auswahl
zwischen Compiler- und Linklauf wird ausdrücklich ein **Neu-Kompilieren**
verlangt (statt alte optimierte ASM-Dateien irreführend als ungepackt zu linken).
Der AT&T-Ausgabemodus wird vor der Umwandlung aus Intel-ASM optimiert.

**Beispiele für x86 PE32:**

```
mov eax, 0            ; 5 Bytes
xor eax, eax          ; 2 Bytes (falls EFLAGS als tot bewiesen)

mov eax, 1            ; 5 Bytes
push 1                ; 2 Bytes
pop eax               ; 1 Byte  (nur vor RET mit Stackzustand)
```

Bei PE64 wird `POP RAX` statt `POP EAX` erzeugt. Das Schreiben von `EAX`
setzt unter PE64 die oberen 32 Bit von RAX auf 0.
Ersetzungen außerhalb `.text`, unbekannte Registerbreiten und Fälle mit
unsicherer Flags-/Stackanalyse werden übersprungen.

## Persistenz

Die drei Einstellungen werden in den vorhandenen **pro-Architektur**
`Settings.Windows.32Bit.Compiler.dBASE.Optimierung` bzw.
`Settings.Windows.64Bit.Compiler.dBASE.Optimierung`-INI-Abschnitten gespeichert:

```
PeepholeRegisterWidth = true
PeepholeProcessorFlags = true
PeepholeStackState = true
```

Die jeweils zugehörigen internen `.pro`-Einträge lauten
`__windows_pe32_dbase_peephole_*__` bzw.
`__windows_pe64_dbase_peephole_*__`. Fehlen sie in älteren Projekten,
werden alle drei deaktiviert geladen. Ein neues bzw. geschlossenes Projekt
setzt die drei Optionen zurück; die Windows-Architekturen bleiben unabhängig.

Die bestehenden Pascal-O0/O1/O2/O3-Optimierungsstufen werden **nicht** verändert.
Die neuen Peephole-Optionen wirken auf beide PE-Sprachen, unabhängig von
Pascal O0. Es wird nicht in Pascal-Objektdateien eingegriffen, die bereits
vor Änderung der Einstellungen aus externen Builds vorliegen.

## Tests / Grenzen

`test_stage609.py` testet Register-/Flags-/Stack-Sicherheit,
Quellzeilen-Zuordnung, dBASE-DLL-Kompilierung und Projekt-Integration.
`test_stage609_link.py` baut die RuntimeDB-DLL mit dem tatsächlichen
integrierten PE32-/PE64-COFF-Linker und kontrolliert Exporte/Imports.
Die bisherige API-/Projekt-Regression wird ergänzend getestet.

Ein visueller Qt-Test, ein vollständiger Pascal-Build mit lokal kompatibler
ANTLR-4.13.2-Runtime sowie Windows `LoadLibrary`-Tests stehen aus.
