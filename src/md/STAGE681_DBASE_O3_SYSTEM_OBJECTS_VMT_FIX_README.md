# Stage 681 — dBASE O3: System.Objects.prg verwendet die gemeinsame DLL-TObject-VMT

## Basis

`d64_dism_stage680.zip` ist die verbindliche Ausgangsbasis. Die vorhandenen
O0/O1/O2-Verhaltensweisen, die Qt5-Runtime-ABI und die Buildkorrektur aus Stage 680
bleiben unverändert.

## Fehlerbild

Auch mit O3 blieb in vielen generierten `.asm`-Dateien die lokale Neuner-Tabelle
`__dbase_class_object` erhalten. Der Generator meldete:

```asm
; Stage 679: TObject custom virtual methods; no DLL fallback
; Stage 670: shared VMT method tables
__dbase_class_object:
    dd __dbase_cls_tobject___del__
    dd __dbase_cls_tobject_free
    ...
```

Grund: `runtime/dbase/src/System.Objects.prg` implementiert die normalen
TObject-Methoden ausdrücklich in dBASE. Die Stage-679-Prüfung wertete **jede**
nichtleere Methodendefinition als Override, obwohl die mitgelieferten Bodies
der Standardimplementierung von `runtime/jitObject.cc` entsprechen. Der
O3-Post-Pass akzeptierte ausschließlich `TObject builtin ... fallback safe`.

## Korrektur

In `d64dbase/object_abi.py` erkennt `_is_native_tobject_default_source()`
die vollständigen, unveränderten Standard-Methodenkörper aus
`System.Objects.prg`: Free, FreeInstance, ClassType, ClassParent,
ClassNameAddress, ClassName, InstanceSize und InheritsFrom. Die vorhandene
Signaturvalidierung bleibt aktiv. Nur für exakt diese Körper bzw.
signaturlose Builtins markiert der Compiler die DLL-Tabelle als sicher.

Der bestehende `dbase_vmt_optimizer.py` kann daraufhin unter O3 die lokale
`__dbase_class_object`-Tabelle durch Assembler-Kommentare ersetzen und in
`__dbase_vmt_tobject` sowie nicht überschriebenen Kind-VMTs den sechsten
Slot auf **0** setzen. Das ist der in Stage 679 festgelegte Sentinel für die
native Tabelle in `libd64_qt5.dll`. Der bestehende ABI-Import-Guard bleibt.

Ein echter benutzerdefinierter Override oder ein veränderter Standardkörper
wird nicht als DLL-Standard erkannt. In diesem Fall bleibt die lokale Tabelle
absichtlich erhalten, um die Benutzersemantik nicht zu ändern.

## Tests

Neue Tests: `test_stage681.py` (6 Tests; PE32 und PE32+ einschließlich
COFF-Assemblierung und PE-Linking). Zusätzlich liefen:

- `test_stage670.py` und `test_stage680.py`: 10 bestanden
- `test_stage679.py` ohne aufwendige native/Mehr-Objekt-Tests:
  11 bestanden, 6 abgewählt

Die vollständige Stage-679-Nativtestsuite wurde hier nicht erneut erfolgreich
abgeschlossen (vorheriger Sammellauf überschritt die Laufzeitgrenze).
Ein realer Windows/MSYS2-Qt5-DLL-/EXE-Laufzeittest ist weiterhin erforderlich.

## Anwendung

Nach dem Einspielen von Stage 681 die dBASE-Quelldateien mit ausgewähltem
`O3 - Reduce redundant method tables` **neu kompilieren**. Bereits vorhandene
Assembler- und Objektdateien werden nicht nachträglich optimiert. Die DLL
benötigt weiterhin den Stage-679/680-Export `jit_default_tobject_vmt_abi`.
