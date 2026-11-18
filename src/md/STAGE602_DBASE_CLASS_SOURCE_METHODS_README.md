# Stage 602 – dBASE-Klassenmethoden aus dem Quellcode

**Verbindliche Grundlage:** Stage 601 (`d64_dism_stage601.zip`).

## Ziel

Die dBASE-Implementierung der bekannten `TObject`-Methoden liegt jetzt in
`runtime/dbase/src/System.Objects.prg` (identische Include-Kopie:
`examples/dbase/System.Objects.prg`). Die Methoden enthalten echte dBASE-Anweisungen
statt `RETURN PVOID`-/`RETURN BOOL`-Platzhaltern. Der Compiler liest diese
Anweisungen und generiert die passenden nativen Aufrufe aus dem dBASE-Methodenkörper.

```dbase
procedure Free
    if Self <> NULL
        jit_object_free(Self)
    endif
    return

function ClassParent
    return jit_class_parent(jit_object_class_type(Self))

function ClassName
    return ClassNameAddress()

function InheritsFrom(TClass)
    return jit_inherits_from_object(Self, TClass) <> 0
```

`NULL` bezeichnet in dBASE jetzt den Nullzeiger, numerisch `0`, unabhängig von
der Groß-/Kleinschreibung. `NIL` ist kein Alias und wird hier nicht unterstützt.

## Parser und Codegenerierung

* Die CLASS-Extraktion bewahrt ausführbare Statements (einschließlich
  mehrzeiliger geschachtelter Funktionsaufrufe) samt Quellzeilennummern auf.
* Zulässige native Methodenanweisungen: FFI-Prozeduraufrufe, `IF`/`ELSE`/`ENDIF`,
  `RETURN` mit oder ohne Ausdruck. Ausdrücke: `Self`, deklarierte
  Parameter, `NULL`, ganzzahlige Konstanten, einfache Vergleiche,
  geschachtelte externe Funktionsaufrufe und Aufrufe bekannter TObject-Methoden.
* Unbekannte FFI-Methoden, falsche Parameterzahlen, Rückgaben aus
  Prozeduren oder ein fehlender Funktions-Rückgabewert führen zu
  Diagnosemeldungen statt stillschweigend ignoriertem Code.
* PE32: `Self` ist der erste `cdecl`-Parameter (`[EBP+8]`), danach folgen
  Benutzerparameter. Der Methodencompiler räumt `cdecl`-Aufrufargumente vom
  Stack; bei `stdcall` räumt der Aufgerufene auf.
* PE64: `Self` kommt in `RCX`, der nächste Parameter in `RDX`. Für jeden
  verschachtelten Aufruf werden 16-Byte-Ausrichtung und Win64 Shadow Space
  berücksichtigt. Native Pointer werden niemals über die numerischen
  dBASE-Double-Slots konvertiert.
* Die VMT-Daten und die `new TObject()`-Allokation bleiben ABI-strukturelle
  Compileraufgaben; die Implementierung der übrigen TObject-Methoden erfolgt
  aus dem Quelltext. Alte reine Signatur-Platzhalter behalten zur
  Rückwärtskompatibilität die bisherigen Stage-600-Wrapper.
* Die tatsächlichen DLL-Imports stammen aus den `extern`-Deklarationen. Die
  zusätzliche native Object-Importliste enthält bei Quellimplementierungen nur
  die für Instanzerzeugung und VMT-Dispatch nötigen Aufrufe.

## Besonderheit `ClassName()`

`jit_class_name()` liefert einen nativen `const char*`. In dBASE gibt
`ClassNameAddress()` diesen Rohzeiger zurück, und `ClassName()` ruft
`ClassNameAddress()` auf. **Beim dBASE-Aufruf `obj.ClassName()`** sorgt die
bestehende String-Ergebnisbehandlung aus Stage 595/600 für eine eigene
CP1252-/dBASE-String-Kopie. Es wird bewusst **nicht** die Pascal-Funktion
`jit_dynstring_from_cstr` verwendet – das wäre ein anderes Speicherformat.

## Dateiliste

* `d64dbase/compiler.py`: NULL-Literal, Methodenextraktion,
  Weiterleitung der FFI-Prototypen an das Klassenbackend.
* `d64dbase/object_abi.py`: Quellcode-gestützte native Methodengenerierung,
  gezielte DLL-Imports, unveränderte VMT-Layoutkonvention.
* `d64dbase/grammar/DBaseLexer.g4`, `DBaseParser.g4`: NULL und Klassenmethoden
  auch in der deklarativen ANTLR-Grammatik dokumentiert.
* `runtime/dbase/src/System.Objects.prg`, `examples/dbase/System.Objects.prg`:
  sichtbare dBASE-Methode-Implementierung mit `NULL`.
* `examples/dbase/tobject_demo.prg`: Beispiel.
* `test_stage600.py`: aktualisierte Erwartungen an die nun source-basierten
  Runtime-Aufrufe; `test_stage602.py`: neue Regressionstests.

## Grenzen / Prüfstatus

Die Stufe deckt die `TObject`-Methoden ab, **noch keinen allgemeinen
Klassencompiler** mit beliebigen Instanzfeldern, freien benutzerdefinierten
Methodensignaturen oder beliebiger dBASE-Ausdrucks-/Statement-Syntax.
VMT-Dispatch und abgeleitete Klassen bleiben wie in Stage 600; dadurch werden
überschriebene benutzerdefinierte Methoden noch nicht unterstützt.

Quellcode- und Assemblertext-Tests für PE32/PE64 wurden ausgeführt; ein
nativer Windows-Link-/LoadLibrary-/Funktionsaufruf-Test konnte in dieser
Linux-Umgebung nicht durchgeführt werden. Das Archiv enthält keine neu
gebauten DLLs.
