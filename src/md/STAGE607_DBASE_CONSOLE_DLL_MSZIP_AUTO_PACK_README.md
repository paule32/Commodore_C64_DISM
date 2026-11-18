# Stage 607 – D64Z/MSZIP-Kompaktierung der c64_dbase_runtime.dll

**Verbindliche Grundlage:** `d64_dism_stage606.zip`.

## Problemursache

Beim Linken einer dBASE-EXE wurde `c64_dbase_runtime.dll` durch
`_prepare_dbase_console_runtime()` bereitgestellt. Die vorhandene
D64Z/MSZIP-Packroutine war allerdings ausschließlich mit der separaten
Checkbox **„pack dll“** unter `Projekt-Einstellungen → Umgebung → Eingabe →
dBASE Runtime` verbunden. Die allgemeine Projektoption **„Linker → Optionen
→ D64Z/MSZIP PE-Packing aktivieren“** bewirkte bislang keine Packung der
automatisch bereitgestellten Konsolen-DLL.

## Neue Schalterlogik (separat pro PE32/PE64)

| PE-Packing | „pack dll“ | Konsolen-DLL |
|---|---|---|
| aus | aus | ungepackt |
| an | aus | D64Z/MSZIP-gepackt |
| aus | an | D64Z/MSZIP-gepackt |
| an | an | D64Z/MSZIP-gepackt |

Diese Verknüpfung gilt sowohl für das automatische DLL-Deployment beim
EXE-Linken/Starten als auch für den Button **„dBASE Runtime DLL erstellen“**.
Die EXE benutzt weiterhin ihren **eigenen**, unveränderten Pack- und
Startpfad. Die Konsolen-DLL erhält den vorhandenen DLL-spezifischen Loader,
der beim `DLL_PROCESS_ATTACH` den komprimierten `.text`-Bereich aus `.ztext`
wiederherstellt. **NTFS-Dateiattribute** sind hierfür nicht erforderlich.

Ist die Konsolen-DLL nicht importiert, muss sie auch nicht bereitgestellt
werden. Bei deaktivierten beiden Optionen wird eine zuvor gepackte DLL
nicht weiterverwendet: Der vorhandene ungepackte Quellstand wird kopiert
oder eine neue ungepackte DLL erzeugt.

## Überprüfung im GUI-Protokoll

Die automatisch bereitgestellte DLL wird nach dem Deployment überprüft.
`is_payload_packed()` validiert die Sektionen `.loader` und `.ztext`, den
PE-Einstiegspunkt, den D64Z-Header und die dort eingetragenen Payloadgrößen.
Ein Eintrag kann folgendermaßen aussehen (Zahlen nur beispielhaft):

```
DBASE CONSOLE DLL (pe32): .../c64_dbase_runtime.dll
(D64Z/MSZIP gepackt); .text 2066 -> 1131 Bytes (MSZIP)
```

Die **gesamte DLL-Dateigröße** muss dabei nicht sinken, weil die
`.loader`-Sektion, DLL-Importtabelle und `FileAlignment` zusätzlichen
Platz benötigen. Relevant ist die Komprimierung der `.text`-Nutzdaten.

Alternative lokale Kontrolle (aus dem Quellcodehauptverzeichnis):

```bash
python -c "from d64dbase.pe_dll_payload import packed_payload_info; from pathlib import Path; print(packed_payload_info(Path('c64_dbase_runtime.dll')))"
```

## Dateien

- `d64_dism.py`: einheitliche projekt-/architekturabhängige Packentscheidung,
  sowohl bei manuellem Erstellen als auch automatischem Deployment; Prüfung
  und Statusprotokoll; UI-Tooltips an die tatsächliche D64Z-Funktionsweise
  angepasst.
- `d64dbase/console_runtime.py`: bei ausgeschalteter Packung eine bereits
  gepackte DLL zuverlässig ersetzen; vorhandene Packroutine weiterverwenden.
- `d64dbase/pe_dll_payload.py`: tatsächliche D64Z-Payloadstruktur statt bloß
  `.ztext`-Sektionsname validieren; Payload-Größen für das Protokoll auslesen.
- `test_stage607.py`: neue Regressionstests inklusive echter interner
  PE32-/PE64-Assembler-/COFF-Linker-Strecke.

## Tests und Grenzen

Auf dem Testhost wurden die Packoptionen, die COFF-/PE32-/PE64-Sektionen,
Exports, Cabinet-Imports und das Umschalten von gepackt auf ungepackt
geprüft. Für diese **strukturellen** Tests wird `zlib` als injizierter
Kompressor verwendet; **dieser Testpayload ist nicht mit der Windows-
Cabinet-MSZIP-Routine lauffähig und wird nicht ausgeliefert**.

Bei echten Windows-Builds bleibt der vorhandene native Kompressor
`cabinet.dll:CreateCompressor(COMPRESS_ALGORITHM_MSZIP)` maßgeblich.
Ein nativer Windows-`LoadLibrary`- und Exportaufruf-Test der gepackten
PE32-/PE64-DLLs konnte hier nicht ausgeführt werden. Vor produktiver
Verwendung bitte beide Ziele unter Windows testen.
