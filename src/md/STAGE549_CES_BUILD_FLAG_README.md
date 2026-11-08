# Stage 549 – CES optional im finalen PE32-Image

**Basis:** `d64_dism_stage548.zip`. Keine Änderung an Runtime-DLLs oder Pascal-Quellen.

## Fehlerbild

Nach Abwahl von `Windows → 32-Bit → Debug → CES - Check Early Start`
konnte bei einem erneuten Build weiterhin CES-Diagnosecode in der erzeugten
PE32-Datei enthalten sein. Der PE32-Loader fragte die CES-Option über
`stage527_debug_options()` als veränderlichen globalen Zustand ab; ein
bereits assembliertes EXE-Ergebnis wurde beim Ändern der Checkbox nicht
als veraltet markiert. Bei der mehrstufigen Loader-Erzeugung werden
Probe- und finale Loader mehrmals neu generiert.

## Korrekturen

1. Der Generator `_build_pe32_mszip_loader()` akzeptiert `ces_enabled`
   ausdrücklich. Der Wert wird ausschließlich für die CES-Codepfade benutzt;
   der reguläre D64I-Resolver und sein Fehlercode `0xD6400001` bleiben.
2. Alle realen PE32-Buildpfade übernehmen einen CES-Snapshot pro Linkvorgang:
   den Stage-169-Rebuildpfad, die COFF32-BSS-Layoutplanung, den
   Stage-209-D64I-Packer, die Loaderprobe und die Stage-539-Neubasierung
   des optional komprimierten zweiten Loaders.
3. Direkt vor dem Assemblieren/Linken übernimmt die IDE den aktuell
   sichtbaren Debug-Zustand der ausgewählten Architektur in den Loader.
4. Ein CES-Wechsel invalidiert bereits assemblierte PE32-/PE32+-Ergebnisse;
   die vorhandene EXE wird nicht kommentarlos erneut als aktueller Build
   verwendet. Erneutes Assemblieren/Linken ist notwendig.
5. Legacy-Aufrufer des Low-Level-Loader-Generators ohne `ces_enabled`
   behalten aus Kompatibilitätsgründen das bisherige Default-Verhalten.

## CES OFF

Bei `CheckEarlyStart = false` und einem neuen PE32-Build fehlen die
CES-spezifischen Fehlerpfade, die `user32.dll`-/`MessageBoxA`-Nachladung
für den CES-Dialog und folgende Daten im Loader:

- `CES: LoadLibraryA failed (DLL)`
- `CES: GetProcAddress failed (symbol)`
- `Ordinal import failed` (CES-spezifischer Meldungstext)

Das **normale** dynamische `LoadLibraryA`/`GetProcAddress` des D64I-Resolvers
wird dadurch nicht entfernt: Der Loader muss die echten DLL-Abhängigkeiten
des Programms weiterhin auflösen. Das D64L-Metadatenfeld bleibt ebenfalls.

## CES ON

Bei `CheckEarlyStart = true` bleibt der bisherige PE32-Diagnosepfad aktiv.
Die Einstellung für PE32 ist weiterhin unabhängig von PE32+; für PE32+
existiert in Stage 548 noch kein gleichwertiger CES-MessageBox-Pfad.

## Tests

`python -m pytest -q test_stage549.py test_stage527.py test_stage539.py`

Der neue Test `test_stage549.py` überprüft CES ON/OFF auf Maschinenbyte-Ebene,
den OFF-Fall trotz absichtlich veraltetem globalem Zustand, die
Neubasierung des Loaders, die Architekturtrennung und die Weitergabe der
Option in allen entscheidenden Buildpfaden. Die Stage-527-/Stage-539-
Regressionstests sind ebenfalls erfolgreich ausgeführt worden.

**Nicht hier möglich:** Native Ausführung des neu gepackten Programms unter
Windows und Prüfung mit realer Windows `cabinet.dll`-Komprimierung.

## Windows-Prüfung

1. Projekt `pascal.pro` laden.
2. `Windows → 32-Bit → Debug → CES - Check Early Start` abwählen.
3. Pascal-Programm **neu assemblieren und linken**; bloßes Starten einer
   alten EXE reicht nicht.
4. Erzeugte EXE auf CES-Meldungstexte kontrollieren. Bei einem
   komprimierten zweiten Loader muss dessen Payload vor der Binärsuche
   dekomprimiert werden; Rohbyte-Suchen in der EXE sind nicht ausreichend.
5. Für einen Gegencheck CES aktivieren, neu linken und die CES-Diagnose
   vergleichen.
