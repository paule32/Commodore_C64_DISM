# Stage 582 – Pascal-Konsole: DLL im quellrelativen pe32/pe64-Ordner

**Verbindliche Basis:** `d64_dism_stage581.zip`.

## Gemeldeter Sachverhalt

Nach dem Linken einer Pascal-EXE meldet die IDE „Pascal-Konsolenruntime fehlt“,
obwohl `libd64_console.dll` in einem von der Pascal-Quelldatei ausgehenden
`pe32`-Verzeichnis liegt. Der Wortlaut der bisherigen Meldung umfasste sowohl
fehlende Dateien als auch fehlende Exporte oder die falsche PE-Architektur.
Die tatsächlich lokal vorhandene DLL wurde nicht hochgeladen und konnte
deshalb nicht auf Exporte/Architektur untersucht werden.

## Ursache und Korrektur

`_stage551_deploy_pascal_console()` prüfte nur das eigentliche Zielverzeichnis
sowie verschiedene Projekt-/Runtime-Buildpfade, **nicht** `quelle/pe32` oder
`quelle/pe64`. Durch konfigurierbare PE-Ausgabeverzeichnisse kann der EXE-Ordner
von diesem quellrelativen Ordner abweichen.

- `assemble_generated_document()` übergibt jetzt `document.path` explizit an
  `_stage551_deploy_pascal_console()`.
- `pascal_console_dependencies.console_library_candidates()` liefert
  deduplizierte, auf die Architektur beschränkte Kandidaten:
  1. Neben dem tatsächlichen Linkziel (die für Windows entscheidende Stelle).
  2. `quelle/pe32` bzw. `quelle/pe64`.
  3. Quellordner und quellrelative `runtime/pascal/<target>`-Pfade.
  4. Projektordner, aktives Verzeichnis und konfigurierte Compiler-Eingabepfade.
  5. Installationsverzeichnis `runtime/compiler/win32` bzw. `win64`.
- Eine **gültige** DLL wird bei Bedarf ins EXE-Verzeichnis kopiert und danach
  erneut geprüft. Fehlerhafte DLLs werden nicht akzeptiert.
- Neue Fehlermeldungen führen Zielordner, Quelldatei, tatsächlich benötigte
  Exporte, den Fehler jeder gefundenen ungeeigneten DLL und die geprüften Pfade
  auf. Alle Details werden im IDE-Protokoll ausgegeben.
- Kein Rückfall von PE64 auf eine PE32-DLL und umgekehrt.

## Beispiel

```
Projekt/src/test_raise.pas
Projekt/src/pe32/libd64_console.dll      # vom Nutzer bereitgestellt
Projekt/out/test_raise.exe                # Linkziel aus Projekt-Einstellungen
Projekt/out/libd64_console.dll           # Stage 582 kopiert hierhin
```

Eine DLL, die nur neben der Quelldatei liegt, wird unter Windows nicht
automatisch im EXE-Suchpfad gefunden. Das finale DLL-Ziel muss bei der
EXE liegen oder anderweitig über die Windows-DLL-Suchregeln erreichbar sein.

## Diagnose bei erneutem Fehler

Die IDE protokolliert im Fehlerfall einen Block
`PASCAL CONSOLE RUNTIME FEHLT/UNGÜLTIG`. Drei mögliche Hinweise sind:

- Keine Datei an den geprüften Pfaden gefunden.
- Architektur falsch (PE32: `0x014C`; PE64: `0x8664`).
- `fehlende Exporte: ...` – DLL wurde gefunden, aber passt nicht zum Linkmanifest.

Die ursprünglichen `build.console.win32.sh` und `build.console.win64.sh` bleiben
unverändert; diese verwenden MSYS2 MINGW32 bzw. MINGW64. Unter Windows kann
man Exporte mit `objdump -p libd64_console.dll` prüfen.

## Tests und Grenzen

- `python -m unittest -q test_stage548 test_stage551 test_stage552 test_stage580 test_stage581 test_stage582`
- **40 von 40 Tests erfolgreich** (synthetische PE-Dateien / strukturelle
  Code- und Pfadprüfungen).
- Source-Code wurde auf Parsbarkeit der betroffenen Funktion geprüft;
  Stage 581 verwendet bereits Python-3.15-`lazy import` und benötigt deshalb
  Python 3.15 für den normalen Programmlauf.
- Ein nativer Windows-PE32/PE64-Laufzeittest und eine Untersuchung der
  tatsächlich auf dem Benutzer-PC vorhandenen DLL waren hier nicht möglich.
