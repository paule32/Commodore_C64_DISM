# Stage 539 – komprimierter PE32/PE32+ Second-Stage-Loader

Verbindliche Basis: **Stage 538**. Geändert: `d64_dism.py`, neu: `test_stage539.py`, diese Dokumentation.

## Ziel und Umsetzung

Der bislang komplett unkomprimierte Loader enthält den D64I-Importresolver, die Laufzeit-Kompatibilitätsprüfungen und beim **PE32-Ziel mit CES** den Fehlerdialog für fehlende DLLs bzw. Exportsymbole.

Bei Windows-PE32-/PE32+-**EXE-Builds mit MSZIP-Programmkompression und regulärer Bootstrap-IAT** versucht Stage 539 nun zusätzlich eine eigenständige MSZIP-Kompression des **gesamten zweiten Loaders**. Hierzu wird der eigentliche Loader nach seiner endgültigen Zieladresse neu assembliert, damit PE32-Absolute und PE32+-RIP-relative Referenzen passen.

Das resultierende Layout bleibt kompatibel zum bestehenden Stage-538-Packer:

    .text     – virtuell reservierter, beim Start entpackter Programmcode
    .loader   – kleiner unkomprimierter Windows-Entry-Bootstrap;
                anschließend separate MSZIP-Daten des Hauptloaders;
                ggf. unkomprimierte D64L-Versionskennung;
                danach im *virtuellen*, nicht dateigestützten Bereich
                der zur Laufzeit expandierte Hauptloader
    .ztext    – das bisherige, unabhängig komprimierte D64Z-Programmimage
    .idata    – unveränderte Bootstrap-IAT plus ggf. D64I-IAT-Speicher
    .data/.bss – unveränderte RVA-Planung

Die eigentliche PE-Startadresse bleibt am Anfang von `.loader`. Windows führt
immer zuerst den **unkomprimierten Bootstrap** aus (ein komprimierter Entry
Point wäre nicht startbar). Dieser benutzt die bereits im Image vorhandenen
Windows-APIs `CreateDecompressor`, `VirtualProtect`, `Decompress`,
`CloseDecompressor`, `FlushInstructionCache` und `ExitProcess`.

Nach erfolgreichem Dekomprimieren und Prüfung der Bytezahl wird der dynamisch
belegte Loader-Bereich wieder mit den ursprünglichen Seitenrechten versehen
und die Ausführung an den dekomprimierten zweiten Loader übergeben. Dieser
stellt den Programmcode aus `.ztext` wieder her und löst über D64I die
Programmbibliotheken und Symbole auf. Die CES-Fehlermeldungen (PE32) sowie
die Fehlercodes `0xD6400001` / `0xD6400002` bleiben erhalten.

## Strikte automatische Größenauswahl

Die zusätzliche Loaderkompression wird **nur verwendet**, wenn

1. das reguläre IAT-Bootstrap aktiv ist (PEB-/importloser Modus ist ausgenommen),
2. die bestehende `.loader`-Section genügend unbenutzten *virtuellen* Platz vor `.ztext` hat,
3. Bootstrap + komprimierter Loader + rohe `D64L`-Kennung nach PE-Dateialignment **mindestens einen Dateiblock einsparen**,
4. das Rebasen und Komprimieren der zweiten Stufe ein stabiles Layout ergibt.

Andernfalls wird ohne Änderung der bisherigen Adressen und des PE-Formats
**automatisch der vollständige unkomprimierte Loader** aus Stage 538 benutzt.
Dadurch vergrößert diese Änderung ein bereits gepacktes EXE-Image nicht.

Die Auswahl steht programmatisch in `PE_LOADER_COMPRESSION_LAST_DECISION`
pro Ziel (`pe32` bzw. `pe64`), u.a. mit `enabled`, `reason`, `raw_before`,
`raw_after`, und bei Aktivierung `destination_rva`.

Die `D64L`-Identität bleibt unkomprimiert für das bestehende
`read_d64_loader_info()` sichtbar.

## Umfang und Grenzen

- Die vorhandene **PE32 CES**-Diagnose wird mit dem Hauptloader komprimiert
  (falls der Test auf tatsächliche Ersparnis erfolgreich ist).
- PE32+ erhält ebenfalls den komprimierbaren Hauptloader und behält seine
  bereits vorhandene Importfehlerbehandlung/Exit-Codes. Eine **namentliche
  CES-MessageBox für PE32+** wird durch Stage 539 nicht neu hinzugefügt.
- Der importlose **PEB-Resolver** benötigt bereits vor dem Entpacken eine
  Importauflösung und bleibt aus Sicherheits-/Kompatibilitätsgründen unverändert.
- EXE ohne aktiven MSZIP-Packer sowie DLL-/COFF-Ausgaben bleiben unverändert.
- Falls bereits **cabinet.dll oder eine zum Bootstrap erforderliche System-DLL**
  selbst fehlt, kann Windows das Programm vor dem eigenen Bootstrap ablehnen.
- Die MSZIP-Kompression verwendet weiterhin die **Windows Compression API**.
  Linux-Testläufe verwenden lediglich einen isolierten zlib-Ersatz, um
  Layout und Registercodes zu prüfen; daraus entsteht **keine lauffähige
  Windows-EXE mit zlib anstelle von MSZIP**.
- Ein nativer Windows-10/11-Laufzeittest der neu erzeugten gepackten EXE,
  einschließlich absichtlich fehlender DLL und fehlendem Exportsymbol,
  ist noch erforderlich.

## Prüfungen

`python test_stage539.py`: sechs gezielte Prüfungen bestanden.
Geprüft: IA-32-/AMD64-Bootstrap-Code, Rebasing beider Architekturen,
separater komprimierter Code, PE-Section-RVAs und `.bss`,
unkomprimiertes `D64L`, Layout- und Größenauswahl, sichere Fallbacks.
`python test_stage527.py`: drei ältere Prüfungen bestanden.
Eine ältere umfassende Regression lief in dieser Umgebung ins Zeitlimit;
der nicht abgeschlossene Lauf wird nicht als bestanden angegeben.

## Praxistest unter Windows

1. Stage 539 entpacken und `pascal.pro` normal in der IDE öffnen.
2. Für PE32 oder PE32+ **MSZIP-Kompression** aktivieren, regulären
   Bootstrap-Import-Modus verwenden (PEB-Resolver deaktivieren).
3. Aus IDE eine neue EXE bauen; bei Größenersparnis wird der zweite Loader
   automatisch komprimiert, sonst bleibt das alte Layout erhalten.
4. Programm normal aus IDE und Explorer starten; Ausgaben prüfen.
5. Für PE32/CES in einem separaten Test eine benötigte Anwendungs-DLL
   vorübergehend umbenennen: CES muss ihren Namen anzeigen, ohne Programmcode
   zu betreten. Danach die DLL wiederherstellen.
6. Für den Exportfehler-Test mit einer Test-DLL arbeiten, die ein erwartetes
   Symbol nicht exportiert. Die eigentliche Runtime-DLL nicht überschreiben.
