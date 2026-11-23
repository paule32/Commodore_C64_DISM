# Stage 639 – typisierte dBASE-Exceptions

**Verbindliche Grundlage:** `d64_dism_stage638.zip`

## Syntaxänderung

Die Stage-638-Syntax `TRY … FINALLY … END` ist **entfernt**. Ein TRY-Block wird nun ausschließlich durch `ENDTRY` abgeschlossen.

Unterstützt werden:

- `TRY … CATCH (Exception e) … ENDTRY`
- `TRY … FINALLY … ENDTRY`
- `TRY … CATCH (DbException e) … FINALLY … ENDTRY`
- Mehrere typisierte CATCH-Blöcke; spezifische Klassen müssen vor ihren Oberklassen stehen.
- `THROW NEW Exception("Text")`, `THROW NEW DbException("Text")`, `THROW NEW EigeneKlasse("Text")`, `THROW "Text"`.
- `THROW e` und `THROW` innerhalb eines `CATCH`-Blocks (Weiterwerfen).
- `e.Message`, `e.error`, `e.ClassName` für die im `CATCH` gebundene Exception.
- `FINALLY` beim normalen Verlassen, bei `RETURN`, bei `THROW` und beim Weiterreichen durch dBASE-Prozeduren/Funktionen.
- Verschachtelte `TRY`-Blöcke; Weiterreichen über Funktions-/Prozedurgrenzen innerhalb der generierten dBASE-Laufzeit.

### Beispiel

Das ausführliche Beispiel liegt unter `examples/dbase/try_catch_demo.prg`.

```dbase
#include "System.SysUtils"

CLASS EExample OF DbException
ENDCLASS

PROCEDURE DemoThrow()
    THROW NEW EExample("Demofehler")
    RETURN

TRY
    DemoThrow()
CATCH (DbException e)
    ? e.ClassName
    ? e.Message
FINALLY
    ? "Das Ende"
ENDTRY
```

## Bestehende Exception-Klasse

Die bereits vorhandene `runtime/dbase/src/System.SysUtils.prg` enthält weiterhin die vom Projekt definierte `Exception OF TObject` mit `Message` und `__ini__`. Ergänzt wurde `DbException OF Exception`. Mit `#include "System.SysUtils"` können davon eigene Exception-Klassen abgeleitet werden. Der Compiler prüft die Vererbungsbeziehung für typisierte `CATCH`-Blöcke.

**Technische Grenze:** Die neue Exception-Laufzeit führt für `THROW NEW` die Klasse, deren Vererbungs-ID und die Meldung als verwaltete Metadaten; sie legt dabei **noch kein vollständiges TObject-/Exception-Objekt an und führt dessen `__ini__` nicht aus**. Die Klassenhierarchie wird für die Typauswahl verwendet. Der Konstruktor der vorhandenen `System.SysUtils`-Exception bleibt für gewöhnliche native Klasseninstanziierung bestehen. Dies ist eine Einschränkung gegenüber vollständiger objektorientierter dBASE-Exception-Semantik.

## Laufzeitverhalten und Grenzen

Die native PE32-/PE64-Codegenerierung gibt geworfene dBASE-Exceptions über verwaltete Laufzeit-Slots weiter. Aufrufende dBASE-Routinen prüfen den Pending-Exception-Zustand und führen ihre `FINALLY`-Abschnitte aus. Unbehandelte Exceptions werden im DEBUG-/Runtime-Ausgabekanal mit Klassenname und Meldung ausgegeben.

- **Kein Windows-SEH-Unwinding:** Zugriffsverletzungen und Betriebssystemausnahmen werden noch nicht durch diese `CATCH`-Blöcke abgefangen.
- **Keine Interoperabilität mit nativen C++-Exception-Objekten:** Die Semantik gilt für mit dBASE `THROW` erzeugte verwaltete Exceptions.
- **Keine Exception-Objektidentität:** `e` ist zurzeit eine Compilerbindung für Klasse und Meldung, kein frei mutierbares Objekt.
- **TRY/CATCH innerhalb von Methodenrümpfen der nativen `CLASS`-Syntax** wird von diesem Frontend-Stand noch nicht durchgängig unterstützt. Typisierte Exception-Klassen können dagegen deklariert und in normalen Funktionen/Prozeduren benutzt werden.
- `ExitProcess` beendet den Prozess sofort und überspringt die `FINALLY`-Abarbeitung, sofern der Aufruf im TRY-Teil erfolgt.
- Ein direktes `THROW` ohne Werte ist nur innerhalb eines sichtbaren `CATCH` zulässig.

## Angepasste Dateien

- `d64dbase/compiler.py`: Parser, AST, statische Prüfung, Auswertung und Codegenerierung.
- `d64dbase/__init__.py`: Export der neuen AST-Klassen.
- `d64dbase/grammar/DBaseLexer.g4`, `d64dbase/grammar/DBaseParser.g4`: Grammatikreferenz.
- `runtime/dbase/src/System.SysUtils.prg`: `DbException` ergänzt, bestehende Klasse erhalten.
- `test_stage638.py`: erwartete Syntax auf `ENDTRY` migriert.
- `test_stage639.py`: neue Typ-, Parser-, Codegen- und Laufzeitprüfungen.
- `examples/dbase/try_catch_demo.prg`: neues Beispiel.

## Teststatus

Automatisierte Python- und statische PE32-/PE64-Compilerprüfungen durchgeführt. Native Windows-EXE-Ausführung, Windows-SEH-Integration sowie die Qt5-Dialogausgabe sind **nicht** bestätigt. Eine Änderung oder ein Neubau der Qt5-DLL ist für diese reine Compilererweiterung nicht erforderlich.
