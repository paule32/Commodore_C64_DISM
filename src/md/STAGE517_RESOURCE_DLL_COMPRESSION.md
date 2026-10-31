# Stage 517: Ressourcen-DLL-Komprimierung (Stage 516 als Basis)

## Projekt-Einstellungen

`Windows → 32-Bit / 64-Bit → Umgebung → Ressourcen`

Neben `Mapping:` steht die neue Gruppe **Compress DLL:**:

- `enable` (Standard: aus)
- `transparent` (Standardmodus)
- `custom`

Die RadioButtons sind nur bei aktivem `enable` bedienbar. Die Werte gelten unabhängig pro Architektur und werden mit anderen Projektoptionen automatisch bzw. explizit in der `.pro`-Datei gespeichert:

```ini
[Settings.Windows.32Bit.Environment]
ResourceDLLCompressEnabled = true
ResourceDLLCompressMode = custom

[Settings.Windows.64Bit.Environment]
ResourceDLLCompressEnabled = true
ResourceDLLCompressMode = transparent
```

Ältere Projekte ohne diese Einträge starten mit `enable = false` und `transparent`.

## Build / Speicherort

Der bestehende Button **win32 DLL** bzw. **win64 DLL** verwendet die jeweilige Projekteinstellung. Die Codepage-Ordner bleiben `win32/ascii`, `win32/utf8`, `win32/unicode`, entsprechend unter `win64`. Pro Build werden `.res`, `.o` und `.dll` geschrieben; **komprimiert wird ausschließlich die `.dll`**, damit RES/COFF weiterhin frei linkbar und nutzbar sind. Deaktiviertes `enable` schreibt eine unveränderte PE-Ressourcen-DLL. Das erneute Schreiben ersetzt eine ehemals auf NTFS gepackte DLL durch eine *frische* Datei ohne die alte Kompressionsmarkierung.

### transparent (Variante A)

- Windows/NTFS-Verfahren über `compact.exe /C /EXE:LZX /F /I`.
- Das sichtbare PE-Abbild und `.rsrc` bleiben binär unverändert. Windows entpackt die Datei beim Zugriff automatisch; `LoadStringA/W`, `LoadMenu`, `DialogBox`, `FindResource` usw. funktionieren entsprechend den gewählten Mapping-Optionen.
- Benötigt Windows 10+ und ein NTFS-Laufwerk mit LZX-/CompactOS-Unterstützung. Unter Linux oder auf inkompatiblen Volumes schlägt der Build explizit fehl, **statt stillschweigend eine ungepackte DLL als komprimiert zu melden**. Das bereits vorhandene DLL-Ziel wird bei einer Kompressionsfehlermeldung nicht überschrieben.
- Die Komprimierung spart Speicherplatz auf NTFS; beim Kopieren auf andere Dateisysteme geht sie möglicherweise verloren. Kleine DLLs profitieren möglicherweise gar nicht.

### custom (Variante B)

- Komprimiert geeignete Daten von **RT_RCDATA (10)** und den Stage-515-Sonderformaten `D64_CP_STRING (0xF006)`, `D64_CP_MENU (0xF004)`, `D64_CP_DIALOG (0xF005)`, `D64_CP_VERSION (0xF010)` mit zlib/DEFLATE (level 9).
- Nur wenn das Original mindestens 64 Bytes groß ist **und** Header + komprimierter Inhalt tatsächlich kürzer sind, wird die Ressource ersetzt.
- Resultierende komprimierte Ressourcen stehen in `.dll` unter numerischem Typ **`0xF117`** mit jeweils neu vergebener numerischer ID. Der ursprüngliche Typ, die ursprüngliche ID, Sprache und Codepage sind im Header enthalten.
- Windows-Standardressourcen (`RT_STRING`, `RT_MENU`, `RT_DIALOG`, `RT_VERSION`, `RT_ICON`, `RT_BITMAP`, usw.) bleiben unverändert; ihre Win32-Funktionen sind weiterhin nutzbar.
- Die DLL selbst bleibt eine regulär ladbare PE32-/PE32+-DLL; Windows kann die **gepackten** Nutzdaten jedoch nicht selbst dekomprimieren. Dafür muss die Anwendung `FindResource` + `LoadResource` auf Typ `0xF117` anwenden und das Datenformat dekodieren. **`LoadString` und `LoadMenu` können komprimierte *Custom*-Ressourcen nicht direkt lesen.**
- Bei kleinen oder inkompressiblen Ressourcen kann eine mit `custom` gebaute DLL nahezu oder ganz so groß wie eine ungepackte DLL bleiben; ein Decoder ist nicht in der DLL eingebettet, um keinen zusätzlichen Platz zu verbrauchen.

### D64PK001-Header

```
Byte  Länge  Beschreibung
0     8     ASCII-Magic D64PK001
8     2     original resource type (uint16 LE)
10    2     original resource id (uint16 LE)
12    2     LANGID (uint16 LE)
14    4     codepage (uint32 LE)
18    4     original payload byte length (uint32 LE)
22    4     CRC32 of original bytes (uint32 LE)
26    ...   zlib compressed byte stream
```

Python-API zur Rückgewinnung: `unpack_resource_dll_record(payload) -> (type, id, lang, codepage, bytes)`. Längen-, Streamende- und CRC32-Kontrolle sind eingebaut, Entpacklimit: 128 MiB. Für C/C++ kann die Nutzlast z.B. über `zlib` entpackt werden. Bei älteren Programmen, die das Stage-515-Format direkt per `FindResource(..., 0xF006)` nutzen, sind gepackte Einträge unter `0xF117` zu suchen und zu entpacken.

## Testnachweise

- Python-Syntax (`python -m py_compile d64_dism.py`) und ZIP-Integrität geprüft.
- Automatische Tests für die neuen Optionen, Win32/Win64 × ASCII/UTF-8/Unicode, ZLIB-Decoder und Manipulationserkennung, fehlende NTFS-Unterstützung, unveränderte `.res`/`.o`.
- Die native PyQt5-Oberfläche und echte `compact.exe`-Ausführung unter Windows sind in der aktuellen Linux-Testumgebung **nicht getestet**. Die GUI-Logik wurde strukturell abgesichert.
