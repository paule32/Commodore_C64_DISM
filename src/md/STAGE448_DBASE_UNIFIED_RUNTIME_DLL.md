# Stage 448 – Gemeinsame dBASE Runtime-DLL

Verbindliche Basis: `d64_dism_asm_447.zip`.

## DLL
- Einziger Runtime-Dateiname: **`c64_dbase_runtime.dll`**.
- 32 Bit: `d64dbase/bin/pe32/c64_dbase_runtime.dll`.
- 64 Bit: `d64dbase/bin/pe64/c64_dbase_runtime.dll`.
- Weiterhin durch `d64dbase.console_runtime.build_dll` und `d64dbase.runtime_builder.create_runtime_dll` mit internem PE/COFF-Linker erzeugt.
- Bereits vorhandene Menüeinträge **Werkzeuge -> dBASE Runtime PE32 DLL erstellen** und **Werkzeuge -> dBASE Runtime PE32+ DLL erstellen** bleiben. Keine neuen Menüeinträge.
- Die Projekt-Einstellungen unter PE32/PE32+ -> Umgebung speichern weiterhin ihre jeweils eigenen Ausgabe-Verzeichnisse; Button und Verzeichnis-Auswahl bleiben.
- Build, direktes Assemblieren und Start prüfen dieselbe DLL und stellen sie ggf. neben der EXE bereit. Die bisherige separate `d64_dbase_console.dll` wird nicht mehr als aktuelle Runtime ausgeliefert.

## Exporte (beide Architekturen)
- `DBaseConsoleEnsure`
- `DBaseConsoleWrite`
- `DBaseConsoleShutdown`
- `DBaseConsoleSetTitle`
- `DBaseCharIsLowerCP1252`, `DBaseCharIsUpperCP1252`
- `DBaseCharIsLowerUtf8`, `DBaseCharIsUpperUtf8`

## Zeichen-ABI
`int export(const char *ptr, uint32_t byte_length)` -> 0 oder 1 in EAX.
PE32: cdecl, Parameter auf dem Stack, Aufrufer bereinigt 8 Byte.
PE32+: Windows-x64-ABI, RCX = Pointer, EDX = Byte-Laenge.
Der PRG-Compiler verwendet CP1252, WFM-Ereignisse UTF-8. Wie zuvor wird genau ein Zeichen (CP1252: ein Byte, WFM: ein UTF-8-Codepoint mit einem oder zwei Bytes) klassifiziert; andere Laengen liefern 0. Der bisherige Zeichenklassifikationsumfang wurde nicht erweitert.

Der Compiler berechnet konstante Ausdruecke wie `ISLOWER("a")` weiterhin zur Compilezeit. Dynamische Variablen und benutzerdefinierte Funktionen erzeugen einen DLL-Call. Die bisherigen langen pro-Aufruf-Pruefsequenzen werden nicht mehr ausgegeben. WFM-Methoden mit bereits reserviertem 40-Byte-Shadow-Space reservieren nicht erneut Aufrufspeicher.

## Geaenderte Dateien
- `d64dbase/console_runtime.py`: erweiterte DLL-Erzeugung, einheitlicher Dateiname, acht Exporte.
- `d64dbase/char_case_runtime.py`: neue intern assemblierte Pruefroutinen.
- `d64dbase/char_case.py`: kurze Call-Stubs fuer normale PRG-/WFM-Nutzungen.
- `d64dbase/compiler.py`: Imports in gemeinsame Runtime.
- `d64_dism.py`: WFM-Imports, DLL-Deployment/Start-Pruefung, korrigierte PE32+-Shadow-Space-Behandlung.
- `d64dbase/bin/README.txt`, Architektur-DLLs, neue Tests und Beispiel.

## Grenzen
PE32/PE32+ wurden mit dem internen Toolchain real assembliert und gelinkt und die Exporte ueber die PE-Header geprueft. Ein Laufzeittest der erzeugten Anwendungen unter Windows ist in dieser Umgebung nicht moeglich.
