# Stage 608 – D64Z/MSZIP-Packung von dBASE RuntimeDB.dll

Grundlage: `d64_dism_stage607.zip`.

## Problem

Stage 607 stellte das Packen der separaten `c64_dbase_runtime.dll` sicher,
aber prüfte den vollständigen dBASE-Klassenbibliotheks-Build von
`RuntimeDB.dll` nicht bis zur finalen PE-Datei. Ein veralteter
Projekt-Einstellungs-Cache konnte von der sichtbaren Checkbox abweichen;
ebenso fehlte eine verbindliche Prüfung der fertigen DLL.

## Änderungen

- `d64_dism.py`: Bei benannten dBASE-LIBRARY-/Runtime-Projekten wird ein
  aktueller Snapshot aus **Linker → Optionen → D64Z/MSZIP** genommen.
  Zusätzlich aktiviert der separate **pack dll**-Schalter das Packen von
  dBASE-Runtime-Projektbibliotheken. Für PE32 und PE64 getrennt.
- `d64_dism.py`: Der gewählte Zustand wird explizit an den internen
  PE32-/PE64-COFF-Linker (`pack_dll=`) weitergegeben. Die EXE- und Pascal-
  Packwege bleiben in dieser Änderung unberührt.
- `d64dbase/library_packing.py`: Validiert den tatsächlich erzeugten
  PE32/PE64-DLL-Header, Maschinenkennung, `.text`-Raw-Daten,
  `.loader`-Entry-Point, D64Z/MSZIP-Header, Payload-Größen und den
  benötigten Cabinet-Import. Dabei wird sowohl das Linkergebnis im
  Speicher als auch die fertige `RuntimeDB.dll` nach dem Manifest-
  Einbetten geprüft.
- Bei angeforderter Packung wird ein ungepacktes Ergebnis nicht mehr
  als erfolgreicher DLL-Build akzeptiert. Bei deaktivierter Packung darf
  kein alter `.loader`/`.ztext`-Rest im neuen Image verbleiben.
- Das IDE-Protokoll nennt `DBASE DLL PACK-OPTION`, `DBASE DLL LINK` und
  `DBASE DLL DATEI` einschließlich Zielarchitektur und Textgrößen.

## Projektablauf

1. Unter Projektinformationen `Bibliothek: RuntimeDB` wählen und
   `System.Objects.prg` diesem dBASE-Runtime-Projekt zuordnen.
2. Unter dem *tatsächlich verwendeten* PE32-/PE64-Ziel die Option
   **D64Z/MSZIP PE-Packing aktivieren** einschalten; alternativ den
   dBASE-Runtime-Schalter **pack dll** setzen.
3. `System.Objects.prg` neu kompilieren und **erneut assemblieren/linken**.
4. Protokoll prüfen, beispielsweise:

   `DBASE DLL LINK (pe32): RuntimeDB.dll; D64Z/MSZIP .text 1234 -> 567 Bytes`

   Die Zahlen sind Beispiele. Die DLL-Datei kann durch zusätzliche
   Loader-Sektionen und FileAlignment größer als die ungepackte Datei sein.

## Tests und Grenzen

- `python -m unittest -v test_stage608`: 5 Tests erfolgreich.
- `python -m unittest -v test_stage605 test_stage605_link test_stage607 test_stage606`:
  17 bestehende Tests erfolgreich.
- Direkte COFF-/PE32-/PE64-Links mit `System.Objects.prg`, gepackt/ungepackt;
  auf diesem Linux-Host wird **ausschließlich in den Tests** ein zlib-Stub
  für die strukturelle Payloadprüfung eingesetzt. Dieser Stub erzeugt
  keine echte Windows-Cabinet-MSZIP-DLL.
- Echte Windows-Builds benötigen `cabinet.dll` und dessen MSZIP-Kompressor;
  `LoadLibrary` und DLL-Exportaufrufe sind auf einem Windows-Host noch zu testen.

Die PE-DLL-Packung komprimiert die Code-Sektion `.text`, **nicht** automatisch
`.data`, `.idata`, `.edata`, `.reloc` oder das gesamte DLL-Image.
