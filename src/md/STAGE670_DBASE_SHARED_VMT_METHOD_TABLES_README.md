# Stage 670 – Gemeinsame dBASE-VMT-Methodentabellen

**Verbindliche Ausgangsbasis:** `d64_dism_stage669.zip`

## Ziel

Die bisherige dBASE-VMT enthielt nach `parent`, `class_name`,
`instance_size`, `initialize_instance`, `finalize_instance` und `destroy`
**acht wiederholte native TObject-Methodenzeiger**. Zusammen mit `destroy`
sind das die neun bei allen nicht überschreibenden Unterklassen identischen
Methoden, die sich auslagern lassen.

Stage 670 speichert diese neun Zeiger **einmal pro erzeugter Assembler-Einheit**
als `__dbase_class_object`. Jede kompatible Klasse enthält nur noch eine
Referenz darauf. Klassen mit kompatiblen Overrides erhalten eine eigene Tabelle;
Klassen mit identischer Belegung teilen sie. Die Tabellen werden durch
Vergleich der vollständigen Symbolfolge dedupliziert.

## Neue Assemblersyntax (PE32)

```asm
__dbase_class_object:
    dd __dbase_cls_tobject___del__
    dd __dbase_cls_tobject_free
    dd __dbase_cls_tobject_freeinstance
    dd __dbase_cls_tobject_classtype
    dd __dbase_cls_tobject_classparent
    dd __dbase_cls_tobject_classnameaddress
    dd __dbase_cls_tobject_classname
    dd __dbase_cls_tobject_instancesize
    dd __dbase_cls_tobject_inheritsfrom

global __dbase_vmt_einouterror
__dbase_vmt_einouterror:
    dd __dbase_vmt_exception
    dd __dbase_vmt_einouterror_name
    dd 0x80000014                  ; Bit 31 = kompakte VMT, reale Groesse = 20
    dd __dbase_cls_einouterror_fields_init
    dd __dbase_cls_einouterror_fields_done
    dd __dbase_class_object       ; gemeinsame Methoden statt neun Zeigern
```

Bei PE32+ werden `dq`-Einträge verwendet. Der bestehende `JitVmt`-Header wird
**nicht vergrößert**. Die Runtime erkennt die neue Kodierung am höchstwertigen
Bit des 32-Bit-Felds `instance_size` und wertet die `destroy`-Position
als Zeiger auf eine neun Einträge umfassende Methodentabelle aus.

Für **alte VMTs ohne dieses Bit** bleiben `destroy` und die acht direkt hinter
dem Header gespeicherten Slots weiterhin gültig.

### Methodenaufrufe und Destruktion

Die öffentlichen Funktionen `jit_object_instance_new`, `jit_class_instance_size`,
`jit_get_virtual_vmt`, `jit_get_virtual_object` und `jit_object_free` behalten
ihre Signatur. Neue und alte VMTs werden in `runtime/jitObject.cc` behandelt;
der identische Code liegt auch unter `runtime/compiler/`.

- `jit_object_instance_new` maskiert das Flag vor der Speicherallokation.
- `jit_class_instance_size` liefert ausschließlich die tatsächliche Größe.
- `jit_get_virtual_vmt` indiziert die gemeinsamen Methoden ab Index **1**;
  Index **0** enthält den Destruktor.
- `jit_object_free` liest für kompakte VMTs den Destruktor aus dem gemeinsamen Block.
- Für alte VMTs ist der originale direkte Tabellenzugriff unverändert.
- Überschriebene Methoden werden nur dann als virtuelle Overrides eingetragen,
  wenn Aufrufart und Anzahl der Parameter zur Basissignatur passen.

## Speicherersparnis

Ohne Klassennamen und Felddaten, bei 100 Klassen mit gleicher Belegung:

| Architektur | Bisher (14 Zeiger/Klasse) | Neu (6 Zeiger/Klasse + 9 gemeinsam) | Ersparnis |
|---|---:|---:|---:|
| PE32 | 5.600 Byte | 2.436 Byte | 3.164 Byte |
| PE32+ | 11.200 Byte | 4.872 Byte | 6.328 Byte |

Diese Berechnung gilt für die VMT-Methodenbereiche; COFF-Relokationstabellen,
Alignment und PE-Sektionsgrößen können die tatsächliche Dateigröße beeinflussen.

## WICHTIG: Neue Runtime-DLL erforderlich

Das VMT-Format wird **vom erzeugten Programm und der nativen Runtime gemeinsam**
verwendet. Eine ältere `libd64_runtime.dll` **kann kompakte VMTs nicht lesen**:
Sie würde den markierten Größenwert als sehr große Instanzgröße interpretieren.

Deshalb **zuerst die DLL für die Zielarchitektur neu erstellen und neben die
jeweilige PE32-/PE32+-EXE kopieren**, dann alle betroffenen dBASE-Module und
-Programme frisch kompilieren, assemblieren und linken. Alte `.o` und neue `.o`
mit unterschiedlichem VMT-Format sollten nicht ohne passende Runtime gemischt
werden.

Die vorhandene `runtime/build.win32.sh` kompiliert `jitObject.cc` für MinGW32
und erzeugt `runtime/win32/libd64_runtime.dll`. Das im Projekt enthaltene
`runtime/build.win64.sh` erzeugt dagegen **nicht** `libd64_runtime.dll`,
sondern `libdbase2many.64.dll`; für PE32+ ist daher eine gesonderte passende
64-Bit-Runtime-Buildkonfiguration nötig. Die PE64-COFF/PE-Linktests belegen die
Dateierzeugung, **keine native PE64-Runtime-Ausführung**. Eine Windows/MinGW-
Laufzeitverifikation wurde hier nicht durchgeführt.

## Geänderte Dateien

- `d64dbase/object_abi.py`: VMT-Deduplizierung, Vererbung und Overrides.
- `runtime/jitObject.h` / `runtime/jitObject.cc`: Kennzeichnung,
  Allokationsgröße und virtueller Dispatch.
- `runtime/compiler/jitObject.h` / `runtime/compiler/jitObject.cc`: synchronisiert.
- `test_stage670.py`: neue Deduplizierungs-/Overrides-/Native-Runtime-Tests.
- `test_stage600.py`, `test_stage640.py`, `test_stage646.py`: erwartete
  VMT-Kodierung auf neues Format aktualisiert.

## Verifikation

- **87 Tests bestanden**: Stages 600, 602, 605, 639, 640 und 670.
- **8 COFF-/PE-Tests bestanden**: echte PE32-/PE32+-Assemblierungen und
  Modul-/DLL-Verknüpfungen aus Stages 668/669.
- Die echte C++-Implementierung von `runtime/jitObject.cc` wurde unter Linux
  mit kleinen Allocator-Stubs gebaut und für beide Layouts ausgeführt:
  Allokation, Instanzgröße, virtuelle Slots und Destruktoraufruf bestanden.
- Der breitere historische Testlauf enthält einen **nicht durch Stage 670
  verursachten** Alt-Test: `test_stage612.py` erwartet für `Exception` nur
  `Message`, obwohl die aktuelle Quelle außerdem `Code` definiert.
- ZIP- und Python-Syntaxprüfung erfolgt beim Paketieren.

**Keine Änderung an `libd64_qt5.dll`.**
