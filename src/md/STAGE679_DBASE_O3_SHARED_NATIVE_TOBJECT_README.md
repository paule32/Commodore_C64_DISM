# Stage 679 — O3: Reduce redundant method tables (dBASE)

## Basis und Ziel

Verbindliche Ausgangsbasis: `d64_dism_stage678.zip`. Die dBASE-Optimierungsstufen unter **Projekt-Einstellungen → Compiler → dBASE → Optimierung** besitzen jetzt eine vierte Auswahl: **`O3  -  Reduce redundant method tables`**. Die bestehende `.pro`-Einstellung `OptimizationLevel` wird weiterhin je Zielarchitektur getrennt gespeichert (`Settings.Windows.32Bit.Compiler.dBASE.Optimierung`, `Settings.Windows.64Bit.Compiler.dBASE.Optimierung`). O0 ist Standard.

Optimierungsreihenfolge:

- **O0**: Unveränderte ASM-Ausgabe.
- **O1**: Konservative Sprungverkürzungen, unter anderem `JNE/JE`.
- **O2**: O1 + statische Textausgaben mit einem Descriptor-Argument und gemeinsamer Qt5-Runtime-Funktion.
- **O3**: O1 + O2 + Eliminierung der Standard-TObject-Methodentabelle je dBASE-Übersetzungseinheit und, sofern unreferenziert, der generierten Standardmethoden-Routinen.

## Native VMT-ABI (PE32/PE32+)

Die kompakte Stage-670-VMT behält sechs pointergroße Header-Einträge und Bit 31 im Feld `instance_size`. Bei O3 bezeichnet ein **Nullzeiger im sechsten VMT-Feld** die gemeinsame native `TObject`-Standardmethodentabelle innerhalb von `libd64_qt5.dll`. Die neun Einträge (Destruktor + Free, FreeInstance, ClassType, ClassParent, ClassNameAddress, ClassName, InstanceSize, InheritsFrom) existieren nur einmal in `runtime/jitObject.cc`. Dafür ist kein importierter Datenzeiger in jeder Objektdatei erforderlich.

Beispiel PE32:

```asm
__dbase_vmt_tobject:
    dd 0                           ; parent
    dd __dbase_vmt_tobject_name
    dd 0x80000004                  ; kompakte VMT, 4-Byte-Instanz
    dd __dbase_cls_tobject___ini__
    dd 0                           ; finalize
    dd 0                           ; DLL-Standardtabelle (O3)
```

- **Standard-TObject ohne eigene Methodenimplementierungen:** Das Assemblerfragment `__dbase_class_object` mit den neun `dd`/`dq`-Einträgen entfällt. Unreferenzierte Standardmethoden werden ebenfalls gelöscht; originale Zeilen werden kommentiert.
- **Abgeleitete Klasse ohne Override:** Erbt die DLL-Tabelle über den Nullzeiger, ohne eine neue Tabelle anzulegen.
- **Abgeleitete Klasse mit echtem virtuellen Override:** Behält ihre individuelle, deduplizierte `__dbase_class_methods_N`-Tabelle; die dafür benötigten vererbten Standardmethoden verbleiben als lokale Thunks.
- **Eigene Implementierungen in `TObject`:** Kein O3-VMT-Fallback. Die ursprüngliche lokale Tabelle und deren Semantik bleiben erhalten. O1 und O2 greifen dennoch.
- **Ältere Stage-600- und Stage-670-VMTs:** Unmarkierte Inline-VMTs sowie kompakte VMTs mit nicht-null Tabellenzeiger bleiben unverändert gültig.

Der Optimierer `dbase_vmt_optimizer.py` prüft das durch den Generator erzeugte Kennzeichen und die genaue Tabellenstruktur. Unbekannte bzw. abweichende Strukturen werden nicht verändert. Bereits bestehende O2-Optimierungen werden nicht rückgängig gemacht. O3 erfordert das **erneute Kompilieren** der dBASE-Quelldatei; ein alter ASM-Stand enthält das erforderliche Eignungskennzeichen nicht.

## ABI- und DLL-Kompatibilität

Neue Runtime-Funktion: `jit_default_tobject_vmt_abi()` (Rückgabewert `1`), neuer Export **Ordinal 2085**, ohne Änderung der vorhandenen Ordinals oder des ursprünglichen ABI-Hashes (1–64). Der O3-Assembler erzeugt einen referenzierten Import und eine kleine, unerreichbare Prüf-Routine `__dbase_o3_abi_guard`. Dadurch schlägt das Laden eines O3-Programms mit einer alten `libd64_qt5.dll` **frühzeitig bei der Importsymbolauflösung** fehl, statt bei einem virtuellen Methodenaufruf auf eine ungültige VMT zuzugreifen. Die Runtime-Bereitstellung fordert denselben Export an.

Die Qt5-DLL **muss neu gebaut werden**. Die aktuellen Stage-678-Buildpfade unterstützen den eingebetteten nativen Runtime-Kern unter **MINGW32 (PE32)**. Die generierte PE32+-ABI und die PE64-COFF/PE-Links sind getestet, aber der native MINGW64-Qt5-DLL-Build ist weiterhin offen.

Build unter MSYS2 MINGW32:

```bash
cd d64qt5
python3 generate_runtime_abi.py
qmake d64qt5_bridge.pro CONFIG+=release
mingw32-make release
```

Danach die neuen `libd64_qt5.dll` und alle neu kompilierten dBASE-EXE-/Module-/Programme-Objekte bereitstellen. Ein altes `.o`- oder EXE-Abbild wird nicht nachträglich optimiert.

## Nachvollziehbare Einsparung

Ein Testprogramm mit `CLASS TChild OF TObject`, einer Instanz, einem virtuellen `Free`-Aufruf und statischer Ausgabe wurde mit dem **realen COFF-Assembler** kompiliert:

| Architektur | O2 `.text` | O3 `.text` | O2 `.data` | O3 `.data` |
| --- | ---: | ---: | ---: | ---: |
| PE32 | 912 B | 737 B | 236 B | 200 B |
| PE32+ | 1.384 B | 1.141 B | 368 B | 296 B |

Alle Werte einschließlich des zusätzlichen ABI-Import-Guards. Die ursprünglich wiederholte Neun-Pointer-Tabelle allein benötigt 36 B unter PE32 und 72 B unter PE32+. Für zehn **separat** kompilierte Dateien ist die reine Brutto-Tabellenersparnis folglich 360 bzw. 720 B, zuzüglich nicht mehr benötigter Methodenimplementierungen und abzüglich Import-/Link-Overheads. PE-Sektionsausrichtung kann verhindern, dass die vollständige EXE-Dateigröße im gleichen Umfang sinkt.

## Tests

`test_stage679.py`: GUI- und Level-Auswahl, O1/O2-Vererbung, Null-Tabellen für PE32 und PE32+, 64-Bit-Datenslots, individuelle Overrides und eigene TObject-Methoden, wiederholbare Code-Optimierung, echte COFF32-/COFF64-Assemblierung und PE-Link, native Win32-C++-Syntax und Linux-nativer VMT-Dispatchtest (inkl. Legacy-VMT). Für einen zusätzlichen Mehr-Objekt-Test wurden PE32/PE32+ Module/Programme mit individuellen O3-DLL-Importen zu einer EXE gelinkt.

Bestehende Regressionen: `test_stage670.py`, `test_stage671.py`, `test_stage672.py`, `test_stage673.py`, `test_stage674.py`, `test_stage678.py`, `test_stage600.py`, `test_stage602.py`, `test_stage639.py`, `test_stage640.py`. Native GUI-/DLL-Laufzeit unter Windows ist hier mangels Windows-MinGW/Qt5-Toolchain nicht bestätigt.
