# Stage 605 – dBASE RuntimeDB: echte PE32/PE64-Klassen-DLLs

**Verbindliche Grundlage:** `d64_dism_stage604.zip`.

## Ursache des Fehlers

In Stage 604 produziert `compile_dbase_to_assembly(...)` auch für
`System.Objects.prg` ausschließlich den EXE-Quelltyp `program` mit `_start`.
Das Projekt-Informationen-Dock ordnet dieselbe Datei dagegen dem ausgewählten
`dBASE: RuntimeDB`-Bibliotheksziel zu. Die berechtigte Schutzprüfung in
`assemble_generated_document()` meldet daher
`Aktiv ist Bibliothek, aber 'System.Objects.prg' erzeugt PROGRAM`.

Die Schutzprüfung bleibt bestehen; stattdessen generiert der dBASE-Compiler
für diese Zuordnung jetzt eine tatsächliche DLL.

## Implementierung

- Der dBASE-Compiler unterstützt den zusätzlichen Parameter
  `source_kind='library'` bei `compile_dbase_to_assembly(...)`.
- Der normale dBASE-EXE-Pfad (`source_kind='program'`) bleibt unverändert.
- Das Projekt ermittelt die DLL-Quellart aus der **aktiven**
  `dBASE: Runtime`-Auswahl und der tatsächlichen Datei-Zuordnung in der
  Projekt-TreeList. Nur dann wird der DLL-Modus eingeschaltet.
- `d64dbase/dll_backend.py` kompiliert die vorhandenen `CLASS`-Methodenkörper
  aus `.prg`, die zugehörigen `extern`-Imports und das JitVmt-Layout.
- Es entstehen `__d64_dll_entry` (`mov eax,1; ret 12` unter PE32,
  `mov eax,1; ret` unter PE64) sowie die `.text`, `.data`, `.bss`-Abschnitte.
  Der EXE-Start `_start`, `DBaseQtRuntimeStartup` und `ExitProcess` fehlen
  im Klassen-DLL-Modus vollständig.
- Die DLL exportiert für jede native Klasse
  `__dbase_cls_<klasse>_create` sowie `__dbase_cls_<klasse>_vmt`.
  Die zweite Funktion liefert **einen VMT-Zeiger**, nicht den VMT-Datensatz:
  Das ist notwendig, weil der bestehende PE64-Linker Exporte nur auf
  `.text`-Symbole erlaubt.
- Für `TObject` werden zusätzlich die zehn Klassenmethoden / Lifecycle-
  Einstiegspunkte unter ihren stabilen `__dbase_cls_tobject_*`-Namen exportiert.
- Der bestehende DLL-Linker kann weiterhin die Projektoption
  `D64Z/MSZIP PE-Packung aktivieren` berücksichtigen; die EXE-Packung bleibt
  unabhängig davon unverändert.

## Bedienung

1. In **Projekt-Informationen** den Namen bei **dBASE DLL** eintragen,
   z. B. `RuntimeDB`.
2. In der oberen Projektliste **Bibliothek: RuntimeDB** auswählen.
3. Das Blatt `System.Objects.prg` unter `dBASE-Programme -> Module` über
   seine Dropdown-Auswahl **dBASE: Runtime – RuntimeDB** zuordnen.
4. Für dieses Blatt **Kompilieren** ausführen, danach **Assemblieren/Linken**.
   Der Ausgabename ist `RuntimeDB.dll` (für die ausgewählte Windows-Architektur).
5. Zum Laden unter Windows die architekturpassende `libd64_runtime.dll`
   im DLL-Suchpfad bereitstellen.

Ein `LIBRARY RuntimeDB;`-Header ist in diesem dBASE-CLASS-Modul **nicht**
erforderlich. Die Unterscheidung erfolgt durch die Projektzuordnung.

## Aktuelle Backend-Grenzen

Dieser erste dBASE-DLL-Pfad ist bewusst für native `CLASS ... ENDCLASS`-
Module implementiert, z. B. das bereitgestellte `System.Objects.prg`.
Ausführbare **Top-Level-Anweisungen** außerhalb der Klasse werden mit einer
konkreten Compilerdiagnose abgewiesen. Freie `PROCEDURE/FUNCTION`-Module
und beliebige DLL-Initialisierungsblöcke benötigen noch weitere
Codegenerierung. Nicht verfügbare Funktionen werden **nicht** als
leerer EXE-Einstiegspunkt ausgegeben.

## Prüfung

- Der echte interne COFF-Assembler und DLL-Linker erzeugte aus
  `System.Objects.prg` eine **PE32**-DLL (Machine `0x014C`) und eine
  **PE64**-DLL (Machine `0x8664`).
- Beide Bilder enthalten `libd64_runtime.dll` in der Importtabelle sowie
  zwölf Klassenexports einschließlich `__dbase_cls_tobject_create` und
  `__dbase_cls_tobject_vmt`.
- `test_stage605.py` und `test_stage605_link.py` decken
  Projektcode, DLL/EXE-Trennung, Exportstruktur und echten PE-Link ab.
- Die bisherigen Stage-597/599/600/602/603/604-Tests wurden erfolgreich
  separat ausgeführt.
- Keine native Windows-`LoadLibrary`-/Methodenausführung bestätigt.
