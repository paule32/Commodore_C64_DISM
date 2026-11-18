# Stage 600 – dBASE System.Objects / TObject / VMT und native Methoden

## Grundlage

Verbindlicher Ausgangsstand: `d64_dism_stage599.zip`.
Die vom Benutzer vorgelegte dBASE-`System.Objects.prg` und die Pascal-Referenz
`runtime/pascal/system/System.Objects.pas` wurden mit dem Runtime-ABI
`runtime/jitObject.h` und `runtime/jitObject.cc` abgeglichen.

## Umfang der Implementierung

- Der produktive Python-dBASE-Parser akzeptiert in `CLASS TObject OF CUSTOM`
  die angegebenen `PROCEDURE`-/`FUNCTION`-Deklarationen mit `RETURN` bzw.
  `RETURN PVOID`, `RETURN LPCSTR`, `RETURN CINT`, `RETURN BOOL`.
- `CLASS TObject OF CUSTOM` ersetzt weiterhin ausschließlich die eingebaute
  `TObject`-Metadatendefinition (Stage 599).
- Eigene `JitVmt`-Datensätze für PE32 (32-Bit-Zeiger) und PE64 (64-Bit-Zeiger):
  `parent`, `class_name`, `instance_size`, `initialize_instance`,
  `finalize_instance`, `destroy` und acht Methoden-Slots.
- `new TObject()` ruft `jit_object_instance_new` mit dem generierten VMT-Zeiger
  auf. Der Initialize-Callback (`__ini__`) wird durch die Runtime ausgeführt.
- `Obj.Free()` ruft `jit_object_free`; die Runtime führt `destroy` (`__del__`),
  Finalisierung und Freigabe aus. `Obj.FreeInstance()` übergibt die Instanz
  direkt an `jit_object_instance_free`. Beide Wege setzen den dBASE-Handle
  anschließend auf NULL.
- `Obj.ClassType()` -> nativer VMT-Zeiger (unverändert, niemals Double).
- `Obj.ClassParent()` -> Eltern-VMT-Zeiger.
- `Obj.ClassNameAddress()` -> nativer `const char*`.
- `Obj.ClassName()` -> eigener dBASE-String (C-Zeiger wird mit `lstrlenA`,
  `malloc` und `memcpy` kopiert; keine Übergabe eines Pascal-Dynstrings).
- `Obj.InstanceSize()` -> 32-Bit-Ganzzahl in einem dBASE-Zahlenslot.
- `Obj.InheritsFrom(TObject)` und `Obj.InheritsFrom(klass)` -> 0/1 über
  `jit_inherits_from_object` mit Klasse oder vorher gespeichertem TClass-Zeiger.
- Virtueller Methodenaufruf über `jit_get_virtual_object(Self, Slot)`;
  PE32 cdecl (`add esp, ...`), PE64 Windows-x64-Aufrufkonvention.
- NULL- oder fehlgeschlagene VMT-Lookups rufen keinen Null-Funktionszeiger auf.
- Abgeleitete native dBASE-Klassen können einen eigenen VMT mit Elternzeiger
  und den geerbten TObject-Methoden erhalten.
- Vorhandene FORM- und Turbo-Vision-Hierarchien erhalten **kein**
  `JitVmt`-Layout, sondern behalten ihre bisherigen Qt-/TV-Metadaten.
- Die bestehenden dBASE-`extern`-Importe sowie WFM/Qt-Bereiche bleiben intakt.

## Programmbeispiel

Das Beispiel unter `examples/dbase/tobject_demo.prg` verwendet
`#include "System.Objects.prg"`.

```dbase
LOCAL Obj AS TObject
Obj = new TObject()

? Obj.ClassName()
size = Obj.InstanceSize()
? size
? Obj.InheritsFrom(TObject)

klass = Obj.ClassType()
? Obj.InheritsFrom(klass)

Obj.Free()
```

Die Klassendatei liegt unter:

- `runtime/dbase/src/System.Objects.prg` (zur Aufnahme in die Runtime-Quellen)
- `examples/dbase/System.Objects.prg` (für das direkt kompilierbare Beispiel)

## ABI-Details

Aus `runtime/jitObject.h`:

| Feld | PE32 Offset | PE64 Offset |
| --- | ---: | ---: |
| parent | 0 | 0 |
| class_name | 4 | 8 |
| instance_size | 8 | 16 |
| initialize_instance | 12 | 24 |
| finalize_instance | 16 | 32 |
| destroy | 20 | 40 |
| erster virtueller Methodenslot | 24 | 48 |

Der VMT-Header belegt bei PE32 24 Byte und bei PE64 48 Byte.
Die Mindestinstanzgröße ist ein Zeiger (4 bzw. 8 Byte für das VMT-Feld).

## Wichtige Einschränkungen

1. **Nur die fest definierten `TObject`-Methoden** werden derzeit als native
   Instrinsic-/Runtime-Wrapper ausgegeben. Die im Quelltext stehenden
   `RETURN`-/`RETURN Typ`-Zeilen sind hier **Signatur-Platzhalter**, kein
   generischer Interpreter für Klassenmethoden. Andere Methoden oder
   ausführbare Klassenzweige liefern einen expliziten Compilerfehler.
2. Noch **keine eigenen Instanzfelder**, selbst definierten virtuellen
   Methodenkörper, überschriebenen virtuellen Methoden oder generelle
   Ausdruckssyntax `obj.Method() + 3`. Der unterstützte Aufrufweg ist eine
   eigene Anweisung, `? obj.Method()`, `result = obj.Method()` oder
   `STORE obj.Method() TO result`. Die Klasse muss im aktuellen Quellmodul
   oder über `#include` deklariert sein.
3. Rohzeiger-Rückgaben (`PVOID`) werden in Pointer-Slots gespeichert, nicht
   als dBASE-Double dargestellt. Für diese Zeiger ist die Ausgabe mit `?`
   nicht vorgesehen. Der Pointer-Slot kann an `InheritsFrom(klass)` übergeben
   werden.
4. Der aus dem Pascal-Beispiel bekannte Runtime-Export
   `jit_dynstring_from_cstr` erzeugt einen **Pascal-Dynstring**. Dieser
   Zeiger darf nicht ohne Weiteres wie ein dBASE-eigener String verwaltet
   werden. Die dBASE-Methode `ClassName()` benutzt stattdessen `jit_class_name`
   und die bestehende sichere ANSI-String-Kopierlogik aus Stage 595.
5. Die Runtime-DLL muss passend zur Architektur vorhanden und mit den
   `jit_object_*`, `jit_class_*` und `jit_get_virtual_object`-Exports gebaut
   worden sein. Ein vollständiger Windows-PE32-/PE64-Start-/LoadLibrary-Test
   ist in der hier verwendeten Linux-Umgebung nicht möglich.
6. Externe Klassen aus separat kompilierten `.prg`-Objektmodulen erfordern
   weiterhin einen eigenständigen Modul-Linker-/Symbolverweisweg. Das
   Beispiel integriert die Klassendeklaration deshalb via `#include`.

## Prüfungen

- 21 neue Stage-600-Tests (einschließlich Headerlayout, Rückgaben, ABI,
  Aufrufstellen, Include, Vererbung und ungültigen Methodenkörpern).
- Alle 14 Stage-599-Tests sowie die isoliert ausgeführten Tests von
  Stage 590, 592, 593, 594, 595, 596, 597 und 598 erfolgreich.
- `compileall` für die angepassten Python-Module erfolgreich.
- `System.Objects.prg` und `tobject_demo.prg` auf PE32 und PE64 in
  Assemblertext übersetzt.
- **Nicht bestätigt:** tatsächlicher nativer Windows-DLL-Import,
  COFF-Link und Laufzeitausführung auf PE32/PE64.
