# Stage 641 – Managed Exceptions in nativen dBL-Klassenmethoden

**Basis:** `d64_dism_stage640.zip` (unverändert übernommen, abgesehen von den aufgelisteten Änderungen).

## Problem

In Stage 640 funktionierten `TRY`, `CATCH`, `FINALLY`, `ENDTRY`, `THROW` und echte `TObject`-Exception-Instanzen im dBASE-Programm und in regulären Routinen, aber nicht zuverlässig im nativen Emitter für `CLASS`-Methoden. Methodenaufrufe innerhalb eines äußeren `TRY` konnten zudem beim Parser an die falsche Stelle gelangen.

## Implementierung

- Neuer `d64dbase/native_method_exceptions.py`: lexikalisch verschachtelte `TRY`-/`CATCH`-/`FINALLY`-Blöcke in nativen Methoden für Windows PE32 und PE64. Typisierte Handler vergleichen die tatsächliche Exception-Klasse inklusive Vererbungsbeziehungen.
- `THROW NEW EType(message)` verwendet die vorhandene Stage-640-Objekt- und Runtime-Infrastruktur (`JitVmt`/`TObject`). `THROW e` und `THROW` im Handler erhalten denselben Exception-Objektzeiger und den ursprünglichen Typ.
- `e.Message`, `e.error` und `e.ClassName` sind innerhalb nativer Methoden verfügbar. Die Zuweisung an `e.Message` benutzt den geerbten nativen Setter.
- Ein `FINALLY`-Block läuft bei normalem Durchlauf, `RETURN`, Fehlerweitergabe und erneutem `THROW`. Bei mehreren Blöcken wird von innen nach außen abgearbeitet.
- Exceptions aus `self.AndereMethode(...)`, geerbten Methoden sowie Aufrufen aus dem Hauptprogramm werden über den bestehenden verwalteten Exception-Status weitergereicht. Die generierten Methoden verwenden lokale Stack-Slots für CATCH-Bindungen.
- `NEW`/native Methoden-/Property-Anweisungen innerhalb `TRY` und `IF` werden nicht mehr aus dem Block herausgezogen; das gilt auch für Aufrufe aus den Methoden der Basisklasse `TObject` wie `Free()`.
- Einfache Programme ohne Exception-Code behalten den bisherigen Emitter und den bisherigen Klassen-ABI-Pfad bei.

## Beispiel

Siehe `examples/dbase/stage641_method_exceptions.prg`. Der Test enthält eine native `TWorker`-Klasse mit Konstruktor, `Fail` und `Run`; `Run` fängt `EWorkerFailure` ab, gibt sie erneut weiter, und der aufrufende PRG-Block fängt sie schließlich ab.

## Bewusste Grenzen

1. **Native Windows-SEH-Ausnahmen** (z. B. Zugriffsschutzfehler, Hardware-Ausnahmen) sind weiterhin **nicht** angebunden. PE32-SEH-Registrierung und PE64-`.pdata`/`.xdata`-Unwind-Metadaten gehören zu einer separaten, noch offenen Entwicklungsaufgabe.
2. **Unabhängig gelinkte Klassen-DLLs:** Eine gemeinsame Prozess-/DLL-übergreifende Managed-Exception-ABI fehlt. Der DLL-Compiler meldet deshalb für `TRY`/`THROW` in einer eigenständigen Klassen-DLL einen ausdrücklichen Fehler, statt eine scheinbar funktionierende DLL mit ungültigen Exception-Zuständen zu erzeugen. In dBASE-**EXE**-Klassenmethoden funktioniert die hier beschriebene Funktionalität.
3. Der native Emitter unterstützt den bisher implementierten Klassenmethoden-Sprachumfang; damit sind etwa keine vollständigen beliebigen dBL-Statements wie alle Schleifentypen in CLASS-Methoden zugesichert. Das Exception-Verhalten ist für die implementierten Methoden-Anweisungen ausgeführt.
4. Ein **echter Windows-Laufzeittest** der erzeugten EXE-Dateien wurde in dieser Umgebung nicht durchgeführt. Python-Tests, PE32-/PE64-Assembler-/COFF- und Linktests ersetzen diesen nicht.

## Dateien

- Geändert: `d64dbase/compiler.py`, `d64dbase/derived_class_abi.py`, `d64dbase/dll_backend.py`.
- Neu: `d64dbase/native_method_exceptions.py`, `test_stage641.py`, `examples/dbase/stage641_method_exceptions.prg`, diese Dokumentation.
- Keine Änderungen an `d64qt5`/Qt5-DLL erforderlich.

## Tests

In einem ausgepackten Projektverzeichnis:

```shell
python -m unittest -q test_stage600 test_stage602 test_stage612 test_stage615 test_stage638 test_stage639 test_stage640 test_stage641
```

`test_stage641.py` prüft die PE32-/PE64-Codegenerierung, das Matching der Handler und Vererbung, Konstruktoren, `THROW e`, `FINALLY` und `RETURN`, die lexikalische Platzierung von `NEW`/Property/Free in `TRY`, die ABI-Grenze eigenständiger DLLs sowie echte interne COFF-/PE-Linker-Smoke-Tests. Für den **reduzierten Testassembler** wird dabei nur im Test `fninit` durch `nop` ersetzt; im ausgelieferten Compiler bleibt `fninit` unverändert erhalten.
