# Stage 647 — geerbte dBASE-Felder über SUPER() und String + DWORD

**Verbindliche Basis:** hochgeladene `d64_dism_stage646(1).zip`.
Die Dateien und übrigen Funktionen aus Stage 646 bleiben erhalten.

## Fehlerursache

In Stage 646 erkennt der Ausdruckslexer nach `super()` keinen Punkt.
Der einzige in Klassenmethoden behandelte SUPER-Fall war `super().__ini__(...)`.
Außerdem akzeptierte der native Emitter `Code`, aber noch nicht `self.Code`,
und die Stringverkettung war auf maximal drei Stringbestandteile beschränkt.

## Änderungen

- Der Ausdrucksparser akzeptiert `super().Code` und löst das Mitglied nur
  in der Vererbungskette der Elternklasse auf. Eigene oder unbekannte
  Felder erzeugen eine nachvollziehbare Compilerdiagnose.
- `self.Code` und `this.Code` werden ebenfalls auf die eigene Instanz bezogen.
- Native Stringverkettung unterstützt auch mehr als drei Bestandteile.
  Numerische Felder (einschließlich des DWORD `Code`) werden als **unsigned
  32-Bit-Dezimalzahl** in ANSI-Text konvertiert. Zwischenpuffer werden nach
  Verwendung freigegeben; das String-Property übernimmt das Endergebnis.
- Fortsetzungszeilen, die mit `+` beginnen, gehören zum vorherigen
  abgeschlossenen nativen Klassenmethoden-Ausdruck.
- Bei explizitem `Win32Raise` / `Win32FileRaise` / `Win32CheckFile` mit einer
  tatsächlich definierten Win32Exception-Klasse wird das Code-Feld jetzt
  in einem gesonderten, ABI-kompatiblen Factory-Pfad **vor** `__ini__`
  gesetzt. Damit kann `super().Code` im Konstruktor den richtigen Fehlercode
  lesen. Der reguläre `NEW`-Factory-Pfad bleibt unverändert.
- `runtime/dbase/src/System.SysUtils.prg` enthält jetzt die vom Benutzer
  vorgegebene `Win32Exception.__ini__`-Meldung mit Code und Text. Eine
  separate Testkopie befindet sich unter
  `examples/dbase/stage647_user_sysutils.prg`.

## Geänderte Dateien

- `d64dbase/compiler.py`
- `d64dbase/derived_class_abi.py`
- `runtime/dbase/src/System.SysUtils.prg`

## Neu

- `test_stage647.py`
- `examples/dbase/stage647_user_sysutils.prg`
- `STAGE647_DBASE_SUPER_CODE_README.md`

## Prüfstand

- `python -m pytest -q test_stage647.py test_stage646.py test_stage645.py test_stage644.py test_stage643.py test_stage642.py test_stage641.py test_stage640.py test_stage639.py`
- PE32 und PE64: der mehrzeilige Originalcode wird kompiliert.
- PE32 und PE64: vollständiger Win32FileRaise-Beispielfall wird durch den
  internen COFF-Assembler verarbeitet; Code wird vor `__ini__` gespeichert.
- Ein nativer **Windows-Laufzeittest der EXE** ist in dieser Umgebung noch
  nicht erfolgt. Runtime-DLLs müssen je nach eingesetztem Build neu erstellt
  bzw. die dBASE-Library neu kompiliert werden.

## Grenzen

- `super()` bezeichnet den unmittelbaren Elterntyp; für Felder wird der
  tatsächlich deklarierende Vorfahr über das bestehende Layout gesucht.
- Weiterhin **kein allgemeiner** beliebiger `super().Methode(...)`-Aufruf:
  der vorhandene `super().__ini__(...)`-Pfad bleibt separat.
- Die numerische Umwandlung in einer nativen Stringverkettung gilt für
  statisch bekannte numerische Klassen-Properties und Zahlenliterale;
  daraus entsteht keine allgemeine dBASE-Typkonversion für jedes FFI-Resultat.
