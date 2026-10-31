# Stage 502 – dBASE-Formulardesigner: SESSION-Methodenbindungen

**Verbindliche Basis:** `d64_dism_asm_501.zip`, keine anderen Branches gemischt.

## Änderung

Der Doppelklick auf einen Eintrag im Tab `Methoden` einer `Session`-Komponente
legt nun **zwei zusammengehörige Quelltextteile** an:

1. Innerhalb des vorhandenen `WITH (THIS.SESSION1)`-Blocks die Zuweisung
   `deleteAlias = CLASS::SESSION1_DELETEALIAS`.
2. Die zugehörige WFM-Funktion `SESSION1_deleteAlias(param)`, die an
   `SESSION::deleteAlias(param)` weiterleitet.

Beispiel (Auszug; die tatsächliche Serialisierung enthält zusätzliche Eigenschaften):

```dbase
THIS.SESSION1 = NEW SESSION(THIS)
WITH (THIS.SESSION1)
    deleteAlias = CLASS::SESSION1_DELETEALIAS
    Name = "SESSION1"
    Left = 80
    Top = 80
    Width = 42
    Height = 42
    lockRetryCount = 3
    lockRetryInterval = 1000
    Active = .F.
ENDWITH

function SESSION1_deleteAlias(param)
    return SESSION::deleteAlias(param)
```

Alle in Stage 501 angelegten Methoden (`access`, `addAlias`, `addPassword`,
`deleteAlias`, `isAlias`, `login`, `user`) besitzen nun die gleiche Bindungslogik.
Das CLASS-Ziel wird entsprechend der dBASE-Konvention großgeschrieben,
während der Funktionsname die ursprüngliche Methoden-Schreibweise behält.

Die Bindung bleibt am konkreten Session-Objekt, nicht am Formular oder an
anderen Session-Instanzen. Geometrie und weitere Eigenschaften bleiben erhalten.

## Quelltext/Parser

- `d64dbase/session_designer.py`: Typ- und Namensprüfung, kanonische
  Methodenzuweisung, idempotentes Binding sowie Serialisierungshelfer.
- `d64_dism.py`: Klickpfad synchronisiert handgeschriebenen Quelltext vor der
  Bearbeitung, setzt die Bindung am entsprechenden Objekt, fügt nur fehlende
  Funktionen ein und navigiert zum vorhandenen oder neu erzeugten Code.
  Unvollständig editierter, nicht lesbarer Quelltext wird nicht überschrieben.
- `d64_dism.py`: Der WFM-Serializer schreibt die Session-Methodenzuweisungen
  direkt unterhalb von `WITH (THIS.<Session>)` vor der Geometrie, genau einmal.
- `d64dbase/wfm.py`: Der Parser behandelt `deleteAlias = CLASS::...` (analog für
  alle sieben Methoden) einer `SESSION` als Methodenbindung im Event-Dict;
  die Werte bleiben nach Öffnen/Speichern erhalten. Nicht gebundene
  Eigenschaften werden nicht zu Events umgedeutet.

Die eigentliche SESSION-Runtime/Backend-Implementierung ist weiterhin **nicht**
Teil dieser Stage. Die Änderungen betreffen das GUI- und WFM-Quellcode-Modell.

## Verifikation

- `test_stage502_session_method_binding.py`: sieben Methoden; Bindung und
  Wrapper; Idempotenz; Mehrfach-Session; ungültige Namen; WFM-Parser;
  echten Session-Ausgabezweig des vorhandenen Serializers inkl. erneuter
  Parser-Runde; GUI-Klickpfad-Integrationsstellen.
- Stage 501 und WFM-/Event-Regressionen: **69 Tests erfolgreich**
  (`43 + 26` in getrennten pytest-Läufen).
- `py_compile` für die drei geänderten Python-Dateien erfolgreich.
- Native PyQt5-Fenster- und Compilerziel-Tests unter Windows sind nicht
  durchgeführt worden.
