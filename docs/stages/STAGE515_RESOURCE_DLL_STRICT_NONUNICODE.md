[Deutsch](STAGE515_RESOURCE_DLL_STRICT_NONUNICODE.md) | [English](STAGE515_RESOURCE_DLL_STRICT_NONUNICODE.en.md)

# Stage 515 – Keine nativen Unicode-Texte in ASCII- und UTF-8-DLLs

Verbindliche Basis: Stage 514. Datei: `d64_dism.py`.

## Verhalten

Der Button **win32 DLL** oder **win64 DLL** erstellt die Dateien `<RC-Basisname>.res`, `.o` und `.dll` weiterhin im entsprechenden Architektur-/Codepage-Ordner:

- `win32/unicode`, `win32/utf8`, `win32/ascii`
- `win64/unicode`, `win64/utf8`, `win64/ascii`

Die gewählte Codepage bestimmt jetzt die **ausschließliche Textkodierung der erzeugten Ressourcen-Nutzdaten**, nicht nur den Ausgabeordner. `UTF-8` ist technisch ebenfalls eine Unicode-Kodierung; die Anforderung „kein UNICODE“ bezeichnet hier **kein UTF-16LE-Standardformat und keine zusätzlich eingebetteten Unicode-Kopien**.

### Unicode (1200)

Keine Veränderung: Native Windows `RT_STRING (6)`, `RT_MENU (4)`, `RT_DIALOG (5)`, `RT_VERSION (16)`, weitere Binärtypen wie bisher.

### ASCII (20127) / UTF-8 (65001)

Die nativen UTF-16LE-basierten Windows-Templates werden aus dem Build **entfernt** und **ersetzt**, nicht gespiegelt oder dupliziert:

| Ursprünglicher Typ | Nur in ASCII-/UTF-8-Ausgabe | Format |
|---|---|---|
| `RT_STRING (6)` | `0xF006` | `D64STR01`: 8-Byte-Magic, DWORD Codepage, 16×(DWORD Länge, Textbytes) |
| `RT_MENU (4)` | `0xF004` | `D64MENU1`: 8-Byte-Magic, DWORD Codepage, DWORD Anzahl, dann je DWORD Länge und Textbytes |
| `RT_DIALOG (5)` | `0xF005` | `D64SRC01`: 8-Byte-Magic, DWORD Codepage, DWORD Textlänge, kodierter RC-Quelltext |
| `RT_VERSION (16)` | `0xF010` | `D64SRC01` (wie oben) |
| `RT_RCDATA (10)` | `10` | Direkt in ausgewählter Codepage kodierter Text bzw. originale Binärdaten |

**Hinweis zu DIALOG und VERSIONINFO:** `D64SRC01` enthält den vollständigen RC-Quelltext (nicht mehr den nativen Windows-Dialog bzw. die native Windows-Versionsstruktur), um sämtliche ursprünglichen Definitionen als Text in der gewünschten Kodierung zu bewahren. Bei ASCII werden nicht darstellbare Zeichen im RC-Quelltext und den kodierten STRINGTABLE-/MENU-Daten als `?` dargestellt. Text in `RCDATA` wird bei nicht darstellbaren ASCII-Zeichen weiterhin mit einem Fehler zurückgewiesen, statt still verfälscht zu werden.

**Ressourcennamen:** Eigene Ressourcen verwenden numerische Typ-IDs, denn Windows würde benannte Ressourcentypen in `.res` und PE als UTF-16LE speichern. Für ASCII/UTF-8 sind auch die Ressourcennamen numerisch erforderlich; andernfalls wird der Build abgebrochen.

**Schutz vor Unicode-Einschlüssen:** Explizite `L"..."`-Literale sind für diese Builds verboten. Bei RCDATA und typischen Textressourcen werden erkannte UTF-16-/UTF-32-BOMs sowie längere typische Unicode-Zeichenfolgen ebenfalls abgewiesen, bevor Dateien geschrieben werden. Bei völlig beliebigen Binärdateien kann grundsätzlich nicht bewiesen werden, dass kein Byte zufällig als Unicode-Text interpretierbar ist. Binäre Bilddaten (Icon/Bitmap/Cursor) werden bytegenau übernommen.

### Windows-Kompatibilität – wichtig

Die Dateien bleiben technisch gültige PE32-/PE32+-Ressourcen-DLLs und können mit `LoadLibraryEx` / `FindResource` geöffnet werden. **Windows-Standardfunktionen `LoadString`, `LoadMenu`, `DialogBox` oder `VerQueryValue` können die eigenen Typen nicht unmittelbar verwenden**, weil diese Funktionen das Win32-spezifizierte UTF-16LE-Format erwarten.

Beispiel, um eine kodierte STRINGTABLE (Block 1) zu laden:

```c
HMODULE mod = LoadLibraryExW(L"Resource32.dll", NULL, LOAD_LIBRARY_AS_DATAFILE);
HRSRC res = FindResourceW(mod, MAKEINTRESOURCEW(1), MAKEINTRESOURCEW(0xF006));
if (res) {
    HGLOBAL loaded = LoadResource(mod, res);
    const unsigned char* raw = (const unsigned char*)LockResource(loaded);
    DWORD count = SizeofResource(mod, res);
    /* raw[0..7] == "D64STR01"; DWORD Codepage ab Offset 8. */
}
FreeLibrary(mod);
```

Diese Trennung ist technisch erforderlich: Eine Standard-Windows-STRINGTABLE/MENU/DIALOG- oder VERSIONINFO-Ressource kann nicht gleichzeitig standardkonform und vollständig ohne UTF-16LE erstellt werden.

## Tests

115 von 115 gezielten Stage-504-bis-Stage-515-Regressionsprüfungen bestanden. Getestet wurden beide Architekturen, alle drei Codepages, PE-/COFF-Strukturen, fehlende UTF-16LE-Textfolgen in `.res/.o/.dll` bei ASCII/UTF-8, Unicode-Nativformat, binäre Codepage-Abgrenzung, Fehlerfälle bei expliziten breiten Literalen und Unicode-RCDATA. Python-Syntaxprüfung und ZIP-Integrität erfolgreich. Native GUI und `LoadLibraryEx` unter Windows nicht ausgeführt.
