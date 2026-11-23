# Stage 640 – native TObject-Exception-Objekte; Windows-SEH-Status

Verbindliche Basis: **d64_dism_stage639.zip**. Dies ist eine **Teilimplementierung**
und keine vollstaendige Windows-SEH-Laufzeit.

## Neu implementiert

- `THROW NEW Exception(...)`, `THROW NEW DbException(...)` und benutzerdefinierte
  `Exception`-Unterklassen verwenden nun echte durch `jit_object_instance_new`
  angelegte JitVmt-/TObject-Instanzen, nicht nur einen Integer-Typcode und Text.
- Die Objektgroesse abgeleiteter Klassen enthaelt jetzt **alle geerbten Felder**.
  Das ist besonders fuer `Message` und seinen String-Ownership-Slot kritisch.
- Fehlt in einer abgeleiteten Klasse `__ini__`, wird der naechste geerbte
  Konstruktor aufgerufen und das uebergebene `AMessage` weitergereicht.
- `#include "System.SysUtils"` kann den bestehenden Konstruktor
  `Exception.__ini__(AMessage)` unveraendert verwenden. Damit ist fuer diesen
  Quellstand etwa `Message = "Error.: " + AMessage` der tatsaechliche Objektwert.
- Ohne ein explizites Include werden die benoetigten Basis-VMTs `Exception`
  und `DbException` in den generierten PE-Code eingefuegt.
- Die normalen dBASE-String-Slots sind nicht NUL-terminiert. Vor nativen
  Konstruktor- und Setter-Aufrufen erfolgt deshalb eine temporaere,
  terminierte Kopie mit `malloc`, `memcpy` und `free`.
- Ein typisiertes `CATCH` erhaelt zusaetzlich einen nativen Objektzeiger.
  `THROW e` / erneutes `THROW` gibt genau diesen Zeiger weiter und erhaelt
  dadurch die Identitaet des geworfenen Objekts.
- `e.Message = ...` und `e.error = ...` aktualisieren die geerbte native
  `Message`-Eigenschaft ueber den Klassen-Setter; `e.ClassName` bleibt eine
  schreibgeschuetzte Typansicht.
- Neu erzeugte Exception-Objekte werden in einer Liste bis zum regulaeren
  Programmabschluss gehalten, um keine dangling pointer bei verschachteltem
  `CATCH` und Weiterwerfen zu erzeugen. Anschliessend werden sie mit
  `jit_object_free` freigegeben.
- Die Python-Testauswertung beachtet jetzt die hier verwendeten einfachen
  `Message`-Feldinitialisierer und den geerbten String-Konstruktor.

## Noch NICHT implementiert: vollstaendige native SEH-Ausnahmen

Die in Stage 639 vorhandenen verwalteten `THROW`-Exceptions werden weiterhin
ueber den dBASE-Laufzeitstatus weitergereicht. Das ist **nicht** dieselbe
Technik wie Windows Structured Exception Handling (SEH).

Eine verlaessliche native SEH-Integration erfordert in diesem Compiler:

1. **PE32/x86:** korrekt verkettete SEH-Registrierungsframes mit OS-konformer
   Filter- und Unwind-Behandlung, einschliesslich sicherer Stack-Wiederherstellung.
2. **PE64/x64:** gueltige `.pdata`/`.xdata`-Eintraege und `UNWIND_INFO` fuer
   **alle** nichttrivialen erzeugten Routinen und Methoden; language-specific
   Handler fuer die einzelnen `TRY`-Bereiche und die ordnungsgemaesse
   zweite Unwind-Phase.
3. Laufzeitabbildung von OS-Statuscodes wie `EXCEPTION_ACCESS_VIOLATION`,
   `EXCEPTION_INT_DIVIDE_BY_ZERO` auf geeignete dBL-Exception-Typen und
   Exception-Objekte, pro Thread und mit definiertem Objekt-Lebenszyklus.
4. Garantierte `FINALLY`-Ausfuehrung **auch bei Hardwarefehlern ueber mehrere
   Aufrufrahmen hinweg**, einschliesslich nativer Klassenmethoden und FFI.
5. Separate Windows-Integrationstests, die tatsaechliche Exceptions ausloesen
   und PE32- und PE64-Unwinding unter dem Windows-Loader pruefen.

Ein prozessweiter `SetUnhandledExceptionFilter` oder ein VEH, der einen
Hardwarefehler blind in einen `jmp` zum `CATCH` umwandelt, waere nicht
korrekt und kann Stack, Ressourcen oder Exception-Ketten beschaedigen.
**Es wird daher bewusst kein solcher Schein-Handler installiert.**

Weitere Grenzen: CATCH-Bindungen haben bereits native Objektidentitaet, aber
noch kein beliebiges dBASE-Objektreferenz-/Parameter-/Methoden-Modell. Der
vorhandene Klassenmethoden-Frontendteil bietet noch keine vollstaendige
`TRY/CATCH`-Codegenerierung innerhalb aller CLASS-METHOD-Body-Varianten.
Bei vorzeitigem `ExitProcess` wird der normale Objekt-Cleanup uebersprungen;
der Prozess beendet dann unmittelbar.

## Beispiele

```dbase
#include "System.SysUtils"
CLASS EMyError OF DbException
ENDCLASS

TRY
    THROW NEW EMyError("Datei nicht gefunden")
CATCH (DbException e)
    ? e.ClassName
    ? e.Message
    e.Message = "Bitte Datei pruefen"
    ? e.Message
FINALLY
    ? "Ende"
ENDTRY
```

Die native `Exception.__ini__` aus `System.SysUtils.prg` setzt in diesem
Projekt vorangestellt `Error.: `, solange die Klasse nicht angepasst wird.

## Betroffene Dateien

- `d64dbase/compiler.py` – native Exception-Objekte, CATCH-Bindung, String-Marshalling,
  Objekt-Lifetime, Vorschau-Auswertung.
- `d64dbase/object_abi.py` – geerbte Felder bei Unterklassen ohne eigene Felder.
- `d64dbase/derived_class_abi.py` – Konstruktorvererbung.
- `test_stage639.py` – korrekte Erwartung der vorhandenen `__ini__`-Meldung.
- `test_stage640.py` – neue PE32-/PE64-Compiler- und Runtime-Vorschautests.

## Tests und Installation

Die Python-/Assembler-Generierung laesst sich hier statisch testen.
**Ein nativer Windows-Build/-Ausfuehrungstest wurde nicht durchgefuehrt.**
Bei realen Exception-Objekten wird die architekturrichtige `libd64_runtime.dll`
mit `jit_object_instance_new`/`jit_object_free` benoetigt, zusaetzlich zu den
bereits vorhandenen dBASE-/Qt5-Runtime-DLLs. Eine NEU kompilierte und gelinkte
EXE ist erforderlich. Die Qt5-Bridge selbst wurde nicht veraendert.

Technische Windows-Referenzen:
- https://learn.microsoft.com/en-us/cpp/build/exception-handling-x64
- https://learn.microsoft.com/en-us/windows/win32/debug/vectored-exception-handling
