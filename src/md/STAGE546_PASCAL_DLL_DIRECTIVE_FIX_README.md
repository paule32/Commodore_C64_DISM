# Stage 546 – {$L Runtime} in der IDE-Vorverarbeitung

## Verbindliche Basis

Stage 545 (`d64_dism_stage545.zip`). Der Pascal-Compiler selbst akzeptierte bereits
`{$L Runtime}` und `{$L Runtime.dll}` als DLL-Verweise. Die vorgelagerte
IDE-Funktion `preprocess_pascal_source()` in `d64_dism.py` erlaubte dort aber
nur `.o`, `.obj`, `.a` und `.lib`. Sie brach deshalb bereits mit
"{$L} erwartet .o/.obj/.a/.lib: Runtime" ab.

## Änderung in d64_dism.py

- `{$L Runtime}` und `{$L Runtime.dll}` werden als DLL-Abhängigkeit erkannt;
  ein fehlender Suffix wird zu `.dll` ergänzt.
- `PascalPreprocessResult.link_dlls` transportiert die DLL-Abhängigkeiten
  über den normalen GUI-/CLI-Pfad an `compile_pascal_to_assembly()`.
- COFF-Eingaben (`{$L inttostr.o}`, `{$LINK ...obj}`, `{$LINKLIB ...a}`)
  bleiben getrennt in `link_files`, damit keine DLL als Objektdatei im
  COFF-Linker landet.
- DLL-Namen werden zuerst neben der Quelle und dann in konfigurierten
  Link-Suchverzeichnissen gesucht. Der Verweis wird auch dann registriert,
  wenn die DLL noch nicht vorhanden ist; später prüft der PUI-/DLL-Vertrag
  die tatsächliche DLL-Datei und Exporttabelle.
- Wiederholte gleiche DLL-/Objektverweise werden dedupliziert.
- `{$export TFoo}` in aktiven Quellzweigen wird nicht mehr im IDE-
  Vorverarbeiter entfernt. Der Klassenexport-Scanner kann die Direktive
  damit auch im IDE-Build sehen.
- Inaktive bedingte Direktiven bleiben ignoriert; der Quellzeilenbezug
  der Fehlermeldungen wird beibehalten.

## Beispiel

```pascal
program test_raise;
{$L Runtime}
{$L inttostr.o}
{$L strtoint.o}
uses System, Windows;
begin
end.
```

Benötigt für den vollständigen DLL-Import anschließend die zur Architektur
passenden `Runtime.dll`, `Runtime.paslib.json` und `.pui`-Metadaten (Stage 545),
auffindbar über Ausgabeverzeichnisse beziehungsweise die konfigurierten
Link-Suchverzeichnisse. Die DLL muss beim Programmstart über die Windows-
DLL-Suchreihenfolge erreichbar sein (üblich: neben der EXE).

## Tests

`python -m unittest -v test_stage542 test_stage543 test_stage544 test_stage545 test_stage546`

34/34 Tests bestanden. Die sieben neuen Tests prüfen die IDE- und Compiler-
Vorverarbeitung, beide DLL-Schreibweisen, COFF-Input-Trennung, Suchpfade,
bedingte Direktiven, Klassenexport-Markierungen und die Übergabe an den
Compiler-Frontend-Pfad. Zusätzlich wurde die Python-Syntax des Hauptmoduls
nach einer rein temporären Ersetzung seiner Python-3.15-Lazy-Imports geprüft.

Nicht durchgeführt: Vollständige native Windows-IDE-/DLL-Kompilierung und
Laufzeittest. Es wurden keine DLL- oder COFF-Binärdateien neu erstellt.
