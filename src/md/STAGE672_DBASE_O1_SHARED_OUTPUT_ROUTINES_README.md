# Stage 672 – O1: Wiederholte dBASE-Ausgaberoutinen zusammenfassen

**Verbindliche Grundlage:** Stage 671. Keine Änderung an der Projektdatei oder an den RadioButtons.

## Verhalten

Die bestehende Auswahl **Compiler → dBASE → Optimierung → O0/O1** bleibt erhalten:

- **O0 (Standard):** `optimize_dbase_size_assembly` ist eine strikte Identität; weder Branch-Peepholes noch Ausgaberoutinen-Zusammenfassung.
- **O1 (Längen Optimierung):** Nach der Stage-671-Sprungoptimierung reduziert ein neuer Pass (`dbase_output_compactor.py`) wiederholte statische `?/??`-Ausgabeblöcke. Er verlangt mindestens drei vollständige, unveränderte, vom dBASE-Compiler erzeugte Auswahlblöcke.

Die bisherigen dBASE-Routinen wählen pro Ausgabe dynamisch zwischen dem Debug-Tab (`DBaseQtAppendDebug`) und der Windows-Konsole (`DBaseConsoleWrite`). Die Entscheidung beachtet zuerst `SET DEBUG ON/OFF` (Override), sonst `SET FORMAT TO SCREEN/CONSOLE`. Der Debug-Tab wird nur beim ersten benötigten Schreiben eingeblendet (`DBaseQtSetDebugVisible`).

Statt bei jeder statischen Textausgabe denselben Entscheidungs-/Sichtbarkeits-Code zu emittieren, übergibt O1 nur noch **statischen Textzeiger und Textlänge** an `__dbase_o1_output_write`. Der gemeinsame Helfer prüft die aktuellen Laufzeit-Schalter und führt genau einen Ausgabeaufruf durch. Der gesamte Helper wird **einmal pro Objektdatei** als **lokales Symbol** emittiert; die bisherige Namenstrennung zwischen COFF-Modulen bleibt bestehen.

### PE32-Aufruf

```asm
    push 5
    push __dbase_text_1
    call __dbase_o1_output_write
    add esp, 8
```

Der Helfer übernimmt das alte cdecl-Aufrufschema und lädt beide Parameter korrekt von seinem Stack. Durch dieselbe Kopie der Override-/Sichtbarkeits-Logik bleiben Seiteneffekte der Ausgabe erhalten.

### PE32+-Aufruf

```asm
    mov rcx, __dbase_text_1
    mov edx, 5
    sub rsp, 40
    call __dbase_o1_output_write
    add rsp, 40
```

Der 64-Bit-Helfer reserviert seinen eigenen 32-Byte-Shadow-Space plus lokale Slots (`sub rsp, 56`), sichert `RCX` und `EDX` vor dem Sichtbarkeitsaufruf und stellt sie anschließend für den eigentlichen Debug-/Konsolenaufruf wieder her.

### Sicherheit und Grenzen

- Es werden **nur** exakte, vollständige vom Compiler erzeugte statische Textausgabeblöcke erkannt. Abweichungen bleiben unverändert.
- Ausgaben dynamischer Variablen, numerischer Formatpuffer oder frei formulierter ASM-Blöcke bleiben vorerst unberührt. Ihre Parameter werden bewusst erst **nach** `DBaseQtSetDebugVisible` geladen; frühzeitiges Laden könnte bei GUI-Callbacks einen anderen Wert verwenden.
- Die fünf ursprünglichen internen Branch-Labels bleiben in den Zeilen erhalten; externe Querverweise verhindern eine Zusammenfassung.
- Jede ursprüngliche Zeile bleibt an derselben Zeilennummer, indem wegfallende Anweisungen in Kommentare umgewandelt werden. Der Helper steht **hinter** dem bisherigen ASM-Ende in einer neuen `.text`-Sektion, sodass die bisherigen Zeilen-/Source-Map-Nummern unverändert bleiben.
- `.data`, `.bss`, Runtime-Imports, VMTs und Exception-Handling werden nicht verändert.
- Bei weniger als drei passenden Ausgaben oder wenn die tatsächliche Anzahl der Maschineninstruktionen nicht sinkt, findet diese neue Optimierung nicht statt.
- Die native Runtime-DLL wird durch Stage 672 nicht geändert (Anforderungen aus Stage 670 bezüglich der VMT-ABI bleiben bestehen).

## Messung am hochgeladenen App001-Beispiel

Die Testbasis sind `App001.generated.pe32.asm` (1.110 Zeilen) und `App001.generated.pe32.extern.inc` aus dem Nutzerupload. Beide Dateien liegen als Test-Fixtures im ZIP; das optimierte ASM und die zugehörige Include-Datei stehen unter `examples/dbase/`.

| Variante | `.text`-Bytes (COFF32) | Gelinkte EXE |
|---|---:|---:|
| O0 (keine Optimierung) | 3.711 | 6.144 Byte |
| O1 (bisher Stage 671) | 3.701 | 6.144 Byte |
| O1 (neu Stage 672) | **2.626** | **5.120 Byte** |

In Stage 672 werden im Beispiel **10** Ausgabe-Sites zusammengefasst. Die `.text`-Einsparung gegenüber O0 beträgt **1.085 Byte (29,2 %)**, die PE-Datei ist wegen Section-Alignment um **1.024 Byte (16,7 %)** kleiner. Die Anzahl der Imports bleibt unverändert. Die EXEs wurden durch die echten internen COFF32-/PE32-Routinen erstellt (MZ/PE); ein nativer Windows-Ausführungstest ist damit nicht ersetzt.

## Tests

- `test_stage672.py`: **12 Tests** – O0-Identität, PE32/PE32+-Codegen, idempotente O1-Ausgabe, keine verfrühte dynamische Parameterladung, Querverweis-Schutz, Original-App001-COFF32/PE32-Link und zwei kombinierte COFF32-/COFF64-Module mit identischen lokalen Helpern.
- `test_stage671.py`: **8 Tests** – alte Sprungoptimierungen, `.pro`-Persistenz und Quellzeilennummern (angepasster Test für den nur angehängten Helper).
- `test_stage670.py` und `test_stage609.py`: **19 Tests, 8 Subtests** – VMT und Peepholes.
- `test_stage669.py`: **8 Tests** – Objekt-Assembler und Runtime-Imports.
- `test_stage668.py` (gezielt): **3 Tests** – zwei Module/PE32-/PE32+-Links und Sammelzuweisung.

**50 geprüfte Tests** (plus 8 Subtests) bestanden. Ein ungeteilter, sehr großer historischer Gesamttest lief zuvor in ein Zeitlimit; deshalb ist ein vollständiger GUI-/Windows-Regressionstest nicht bestätigt.

## Dateien

- `dbase_output_compactor.py` – neuer, ABI-spezifischer O1-Transformationspass.
- `dbase_size_optimizer.py` – bindet den Pass hinter den bereits vorhandenen Sprungoptimierungen ein.
- `test_stage672.py` – neue gezielte Regressionstests.
- `test_stage671.py` – aktualisierte Zeilennummernprüfung.
- `tests/fixtures/App001.generated.pe32.extern.inc` – die nun mitgelieferte Runtime-Import-Fixture.
- `examples/dbase/App001.generated.pe32.O1.asm` und `.extern.inc` – nachvollziehbare Beispielausgabe.
