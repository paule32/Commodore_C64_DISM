# Stage 455 – D64Z/MSZIP-Payload in der dBASE-Runtime-DLL

**Verbindliche Grundlage:** `d64_dism_asm_454.zip`.

## Änderung der Option `pack dll`

Die Checkbox `pack dll` verwendet keine NTFS-Dateikomprimierung mehr.
Die IDE erstellt die `c64_dbase_runtime.dll` nun in einem eigenen Linklauf mit
zusätzlichen Cabinet-/Kernel32-Imports und bettet den mit **dem bestehenden
D64Z/MSZIP-Verfahren** komprimierten ausführbaren `.text`-Code in die
`.ztext`-Payload-Sektion ein. Eine kleine DLL-spezifische `.loader`-Sektion
übernimmt das Entpacken. Die EXE-Packfunktionen werden nicht verändert.

**Keine neuen Menüs:** Die Einträge `Werkzeuge → dBASE Runtime PE32 DLL erstellen`
und `PE32+ DLL erstellen`, die Buttons in den Projekteinstellungen und die
architekturgetrennte Option `pack dll` bleiben dieselben.

## Ladeverhalten

1. Windows lädt die DLL-Imports sowie `.edata`, `.data`, `.bss` und `.reloc`
   weiterhin in der üblichen Weise. Die ursprüngliche `.text`-Sektion besitzt
   im gepackten Image keinen Raw-Dateianteil, aber weiterhin ihre ursprüngliche
   virtuelle Adresse. Die exportierten RVAs in `.edata` bleiben unverändert.
2. Der neue DLL-Einstieg verarbeitet `DLL_PROCESS_ATTACH` und bewahrt die
   `DllMain`-Parameter. Die Windows-Cabinet-API entpackt den D64Z/MSZIP-Payload
   in den ursprünglichen virtuellen `.text`-Bereich.
3. Anschließend verarbeitet der DLL-Einstieg die HIGHLOW-Relocations (PE32)
   beziehungsweise DIR64-Relocations (PE32+) in `.text`, diesmal bezogen auf
   die *tatsächlich zugewiesene* ImageBase. Nicht ausführbare Daten behalten
   die von Windows bereits verarbeiteten Relocations.
4. Nach `FlushInstructionCache` und Wiederherstellung des Seitenschutzes
   übergibt der Einstieg die ursprünglichen Parameter an den ursprünglichen
   DLL-Einstieg. Weitere Attach-/Detach-Ereignisse entpacken nicht erneut.
5. Ein fehlgeschlagenes Entpacken liefert `FALSE` statt `ExitProcess`.
   Nach einem fehlgeschlagenen Process-Attach darf die Unload-Verarbeitung
   nicht in nicht wiederhergestellten Originalcode springen.

Ein neuer, unabhängiger Kompressionsalgorithmus wurde **nicht** eingeführt:
Verwendet wird dieselbe Cabinet-Compression-API mit MSZIP (Algorithmus 2)
und demselben D64Z-Header wie beim vorhandenen EXE-Verfahren. Nur der
**DLL-spezifische Ladeadapter** ist neu.

## Projektdateien

- `d64dbase/pe_dll_payload.py`: PE-Analyse, Loader, D64Z-Payload, Relocations,
  Sektionserzeugung für PE32 und PE32+.
- `d64dbase/console_runtime.py`: zusätzliche Loader-Imports nur bei aktiviertem
  `pack dll`, DLL-Erzeugung und automatische Bereitstellung.
- `d64dbase/runtime_builder.py`: manuelle Erstellung mit Payload-Loader.
- `d64_dism.py`: Erfolgsprotokoll mit Payload- statt NTFS-Status.
- `test_stage455_d64z_runtime_dll_payload.py`: neue Tests einschließlich
  eines unter Windows ausführbaren `LoadLibrary`-Integrationstests.

## Teststatus und Grenzen

In der verfügbaren Linux-Testumgebung wurden **beide** DLL-Architekturen mit dem
internen Assembler/Linker tatsächlich bis zur PE-DLL erzeugt. Die Tests
verwenden dort eine injizierte zlib-Komprimierungsfunktion, um die Struktur und
das Wiederherstellen des vollständigen `.text`-Blocks kontrollieren zu können.
DAS IST KEIN unter Windows ladbares MSZIP-Testimage: Für die echte Verwendung
benutzt `pack dll` unter Windows die Cabinet Compression API.

Die PE-Strukturprüfungen kontrollieren die 11 Runtime-Exporte, die IAT der
fünf Loader-APIs, die unveränderten Export-/Import-/Relocation-Verzeichnisse,
die exakten Highlow-/Dir64-RVAs und den wiederhergestellten `.text`-Inhalt.

**Nicht bestätigt:** ein tatsächlicher `LoadLibrary`-/`GetProcAddress`-/Export-
Aufruf des gepackten Images auf Windows 32/64 Bit. Ein entsprechender
Windows-only-Pytest ist vorhanden. Die Aussage "direkt ladbar unter Windows"
steht bis zu diesem Laufzeitnachweis unter Vorbehalt.

### Größe

Die aktuelle Runtime ist sehr klein (ungepackt PE32: ca. 4096 Bytes,
PE32+: ca. 4608 Bytes). Ein zusätzlicher Payload-Loader benötigt eigenen
Speicherplatz. Ein gepacktes Image kann deshalb **größer** werden als das
Original; Packing ist nicht gleichbedeutend mit garantierter Dateiersparnis.
Beim Linux-Test mit zlib-Testdaten hatten beide PE-Binärdateien ca. 5120 Bytes.
Die tatsächlichen MSZIP-Dateigrößen können abweichen.

### Windows-Test

Mit installierter Python-/pytest-Testumgebung in der Projektwurzel:

```
python -m pytest -q test_stage455_d64z_runtime_dll_payload.py
```

Der Windows-only-Test erzeugt die zu Python passende PE32-/PE32+-Runtime
mit echtem MSZIP und versucht, sie über `LoadLibrary` zu laden und einen
Zeichenklassifizierungs-Export aufzurufen. Falls dieser Test scheitert, darf
kein ladbarer Runtime-Stand als bestätigt betrachtet werden.

Die bisherigen NTFS-Tests aus Stage 450–453 sind nicht mehr aussagekräftig
für `pack dll`; der alte `pe_dll_pack.py` wird von den Buildwegen nur noch
für sein transaktionales `replace_verified_runtime` genutzt.
