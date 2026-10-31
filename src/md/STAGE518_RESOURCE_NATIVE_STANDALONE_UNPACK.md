# Stage 518 – Nativer Custom-Ressourcen-Entpacker für Standalone-EXE und Runtime-DLL

## Basis und Motivation

Verbindliche Basis: `d64_dism_asm_517.zip`. Die Stage-517-Option
`Compress DLL → enable → custom` schreibt weiterhin dieselben regulären
PE32-/PE32+-Ressourcen-DLLs: eigene komprimierte Einträge unter Typ `0xF117`
mit dem **26-Byte-Header `D64PK001`**. Die Erzeugung der DLLs und alle
Projekt-Mapping-Einstellungen bleiben unverändert.

Bisher existierte ein Entpacker in Python. Stage 518 fügt die **native
C-Implementierung** `native/d64resource/d64resource.c` mit öffentlichem
Header `native/d64resource/d64resource.h` hinzu. Das Modul kann entweder
**in eine Standalone-EXE integriert** oder **als separate `d64resource.dll`**
mit `GetProcAddress` geladen werden; **Python wird zur Laufzeit nicht benötigt**.

## Schnittstelle

- `D64ResourceInspect(record, size, info)`: Header prüfen, entpackte Größe,
  Originaltyp, Original-ID, LANGID und Codepage melden (ohne CRC32-Test).
- `D64ResourceDecode(record, size, buffer, capacity, info)`: zlib entpacken,
  Längen- und Streamende-Prüfung, **CRC32 des Originalinhalts** überprüfen.
- `D64ResourceReadModuleW(module, original_type, original_id, language,
  buffer, capacity, info)`: Windows-Ressourcen-DLL mittels
  `LoadLibraryExW(... LOAD_LIBRARY_AS_DATAFILE ...)` öffnen; **ungepackte
  Ressourcen direkt ausgeben**, gepackte Ressourcen anhand des Originaltyps
  und der Original-ID in Typ `0xF117` suchen, entpacken und validieren.
- `D64ResourceInfo` ist eine strukturierte ABI-Ausgabe mit festen uint16-/uint32-
  Feldern (24 Bytes auf x86 und x64). Vor jedem Aufruf ist
  `info.struct_size = sizeof(info)` zu setzen. Ist der Ausgabepuffer `NULL`
  oder zu klein, kommt Code `D64RES_BUFFER_TOO_SMALL` (1), wobei `info.size`
  die nötigen Nutzbytes angibt.
- Für Originaldaten und gepackte Blöcke gilt ein **128-MiB-Limit** beim
  Entpacken; keine über die DLL-Grenze hinweg freizugebenden Speicherblöcke.

Fehlerwerte: 0=OK, 1=Puffer fehlt/zu klein, -1=ungültiges Argument,
-2=Header, -3=Limit, -4=defekter zlib-Stream/Länge, -5=CRC32,
-6=Ressource nicht gefunden, -7=reserviert für Windows-API-Fehler.

## Anwendungsfälle

**Statischer Einbau:** C-Modul `d64resource.c` direkt mit der späteren
Windows-Standalone-EXE kompilieren und mit `-lz` linken (zlib statisch oder
dynamisch). Alternativ erzeugt `build_windows.sh` eine passende `.o`.
Damit wird **keine separate Decoder-DLL** benötigt, sofern zlib ebenfalls
statisch eingebunden wird.

**Externe Funktion:** Mit demselben Skript `d64resource.dll` bauen und die
Exportfunktion `D64ResourceReadModuleW` über `GetProcAddress` beziehen.
Dabei sind **32-Bit und 64-Bit getrennte DLL-Versionen** erforderlich.
Der native Decoder kann unabhängig von der im Ressourcen-Editor gebauten
Ressourcen-DLL ausgeliefert werden.

**Delphi/Free Pascal:** Beispiel für `cdecl; external 'd64resource.dll'`
und den Strukturtyp `TD64ResourceInfo` in
`native/d64resource/README.md`.

Das mitgelieferte `native/d64resource/demo_win.c` enthält zwei Varianten:
`demo_standalone.exe` nutzt statisches C-Linking;
`demo_external_dll.exe` lädt die Decoder-DLL dynamisch.
Die Originaldaten können danach wie zuvor anhand der Codepage interpretiert
werden (ASCII, UTF-8, UTF-16LE oder ein D64-eigenes Format wie `D64STR01`).

## Windows-Build (auf Nutzerrechner)

1. In einer **MSYS2 MINGW32**- oder **MINGW64**-Shell den passenden `gcc`
   sowie zlib-Entwicklungsdateien bereitstellen.
2. `cd native/d64resource && ./build_windows.sh`.
3. Resultate liegen unter `win32/` bzw. `win64/`:
   `d64resource.dll`, `libd64resource.dll.a`, `d64resource.o`,
   `demo_standalone.exe`, `demo_external_dll.exe`.
4. Wenn dynamisch gegen zlib gelinkt wird, muss ggf. zusätzlich `zlib1.dll`
   ausgeliefert werden. Für eine wirklich eigenständige EXE zlib statisch
   einbinden.

**Wichtig:** Die Windows-DLLs wurden in der Linux-Testumgebung **nicht
kompiliert oder unter Windows geladen**. Windows-API-Suche wurde durch eine
native C-Mock-Implementierung geprüft, **kein Ersatz für einen Windows-Integrationstest**.

## Tests / Kompatibilität

- `test_stage518_native_resource_decoder.py`: native Shared-Library aus
  `d64resource.c` per GCC kompilieren und über `ctypes` aufrufen.
  Vergleich mit originalem Stage-517-Packer inklusive drei Codepages,
  mehreren Nutzdatenmustern, kaputtem Magic/Header, CRC32-/zlib-Fehlern,
  falscher Originalgröße und unerlaubten Restbytes.
- Win32-API-Pfad zusätzlich mit einer isolierten, in C implementierten
  Test-Ressourcentabelle ausgeführt: Original-ID statt Pack-ID, Sprachauswahl,
  ungepackte Fallback-Ressource, mehrere interne IDs.
- Bestehende Stage-504–517-Ressourcen- und Compiler-Tests unverändert.
- Python-Syntax und ZIP-Integrität erneut geprüft.

Andere Projektmodule und die vorhandene Python-Entpackfunktion bleiben erhalten;
der native Weg ist eine **zusätzliche Laufzeitfähigkeit** für den späteren
Windows-Compiler und andere Standalone-Programme.
