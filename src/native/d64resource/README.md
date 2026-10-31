# D64-Ressourcen entpacken – native C-ABI (Stage 518)

Dieser Decoder liest **das vorhandene Stage-517-Format `D64PK001`**, ohne Python.
Er kann **direkt in eine Standalone-EXE** gelinkt **oder als separate
`d64resource.dll`** über `LoadLibrary`/`GetProcAddress` aufgerufen werden.
Die Ressourcen-DLL (beispielsweise `Resource32.dll`) bleibt eine **eigene Datei**:
Sie enthält die Packdaten. `d64resource.dll` ist die **optionale Decoder-Runtime**.
Beide DLLs dürfen nicht verwechselt werden.

## Quell- und Build-Dateien

- `d64resource.h` — versionierbare C-API, Aufrufkonvention `cdecl`, 32/64 Bit
- `d64resource.c` — zlib/DEFLATE und CRC32 mit strenger Größenkontrolle
- `build_windows.sh` — baut im MSYS2-Terminal unter MINGW32 oder MINGW64
  die Decoder-DLL, die Importbibliothek `.dll.a`, die direkt linkbare `.o`
  und zwei Standalone-Demoprogramme
- `demo_win.c` — `LoadLibraryExW(..., LOAD_LIBRARY_AS_DATAFILE | LOAD_LIBRARY_AS_IMAGE_RESOURCE)`
  und Suche nach der **ursprünglichen Ressourcen-Typ-ID und Ressourcen-ID**.
  Die interne Pack-ID unter `0xF117` wird automatisch ermittelt.
- `Makefile` — lokale Shared-Library zur automatisierten ABI-/Regressionstestung.

MSYS2-Build (getrennte MINGW32- und MINGW64-Terminals):

```bash
# MSYS2-Pakete für die jeweilige Zielplattform: gcc, zlib
./build_windows.sh
# -> win32/d64resource.dll bzw. win64/d64resource.dll
# -> win32/demo_standalone.exe oder win64/demo_standalone.exe
# -> win32/demo_external_dll.exe oder win64/demo_external_dll.exe
```

**Abhängigkeit:** `-lz` bindet zlib. Abhängig vom installierten MinGW-Paket
benötigt die Decoder-DLL `zlib1.dll` als externe Laufzeitdatei. Eine statische
zlib-Variante kann per Linker eingebunden werden; die erzeugte **Standalone-EXE**
kann so unabhängig von Python und einer zusätzlichen Decoder-DLL sein.
Das Beispiel `demo_standalone.exe` enthält den Decoder-Code direkt, während
`demo_external_dll.exe` den Decoder über die C-ABI nutzt.
Die Architektur der Decoder-Runtime muss zur Architektur der EXE passen.
Eine 32-Bit-EXE kann weiterhin über die Windows-Ressourcen-APIs die Daten
von einer passend vorliegenden Datei laden, nicht aber eine 64-Bit-Decoder-DLL
im selben Prozess aufrufen.

## C API

```c
D64ResourceInfo info = {0};
info.struct_size = sizeof(info);
int rc = D64ResourceReadModuleW(hResourceModule, 10, 200, 0,
                                 NULL, 0, &info);
if (rc == D64RES_BUFFER_TOO_SMALL) {
    void *buf = malloc(info.size ? info.size : 1);
    info.struct_size = sizeof(info);
    rc = D64ResourceReadModuleW(hResourceModule, 10, 200, 0,
                                buf, info.size, &info);
    /* rc == D64RES_OK: buf enthält ORIGINAL-Bytes der RCDATA-Ressource. */
    free(buf);
}
```

- `D64ResourceInspect()` analysiert einen im Speicher vorliegenden Packblock;
  hier wird noch **nicht** entpackt oder eine CRC geprüft.
- `D64ResourceDecode()` überprüft den zlib-Datenstrom, die **exakte entpackte
  Länge**, das **vollständige Streamende** und den **CRC32-Wert**.
- `D64ResourceReadModuleW()` sucht unter dem originalen Typ/ID/Sprachwert.
  Für **ungepackt gebliebene** Ressourcen liefert die Funktion die Originalbytes,
  für gepackte Ressourcen entpackt sie den korrespondierenden `0xF117`-Eintrag.
  `language=0` wählt eine verfügbare Sprache; sonst wird die Sprache exakt gesucht.
- Speicher wird vom Aufrufer verwaltet; keine Allokation wird über eine DLL-Grenze
  hinweg freigegeben. Rückgabe `1` signalisiert zu kleinen bzw. fehlenden Puffer.
- Maximal **128 MiB** Nutzdaten pro Packblock.

**Benutzerdefinierte Formate:** Für Stage-515-Typen (`0xF006`, `0xF004` usw.)
ist nach der Entpackung weiterhin deren eigener Inhalt (z.B. `D64STR01`) zu
interpretieren. `RT_STRING`, `RT_MENU` und andere native Windows-Ressourcen
bleiben für die Windows-Funktionen `LoadStringW`, `LoadMenuW` unverändert.

## Delphi / Free Pascal: statische Importdeklaration

```pascal
type
  TD64ResourceInfo = record
    StructSize: Cardinal;
    OriginalType: Word;
    OriginalId: Word;
    Language: Word;
    Reserved: Word;
    Codepage: Cardinal;
    Size: Cardinal;
    CRC32: Cardinal;
  end;

function D64ResourceDecode(RecordData: Pointer; RecordSize: Cardinal;
  OutputData: Pointer; OutputCapacity: Cardinal;
  var Info: TD64ResourceInfo): Integer; cdecl;
  external 'd64resource.dll' name 'D64ResourceDecode';

// Vor dem Aufruf: Info.StructSize := SizeOf(Info);
// 1 = Puffergröße aus Info.Size entnehmen und erneut aufrufen.
```

Der Decoder wird **nicht automatisch** in die mit dem Ressourcen-Editor
produzierte Ressourcen-DLL injiziert. Er ist bewusst eine getrennte Bibliothek
bzw. ein statisch linkbares C-Modul für den späteren nativen Compiler.
Die Komprimierungs- und Mapping-Einstellungen von Stage 517 bleiben bestehen.

**Tests:** Native ABI (Linux-Shared-Library via `ctypes`), originaler Stage-517-
Packer, absichtlich beschädigte Daten, fehlender/zu kleiner Puffer und CRC32.
Windows-Build und `LoadLibraryExW` müssen auf einem Windows-Rechner mit
MSYS2 bzw. Visual Studio separat ausgeführt werden.
