# Stage 543 – doppelte Implementierungen durch Klassenexport-Unit-Resolver

Verbindliche Basis: `d64_dism_stage542.zip`.

## Problem

Beim Build von `library Runtime; uses System, Windows; begin end.` konnte
`Globale Routine mehrfach implementiert: GlobalWindowProc` auftreten.
`Windows` benutzt `Windows.Application` und `VCL`; beide erreichen
`VCL.Windows`. Diese Unit exportiert die Klassen `TWindow` und `TForm`.

In `c64pascal/compiler.py`, `_PascalUnitResolver.resolve()`, wurde die lokale
Variable `key` zunächst als Unit-Schlüssel (`vcl.windows`) verwendet und dann
innerhalb der Klassenexport-Schleife mit dem Klassenschlüssel (`twindow`,
`tform`) überschrieben. Am Ende wurde folglich `self.resolved[key]` mit dem
**falschen** Schlüssel aktualisiert. Ein zweiter USES-Pfad konnte dieselbe Unit
nochmals in `resolver.programs` aufnehmen. Die globale Routine erschien damit
doppelt beim semantischen Merge.

## Korrektur

Die Schleife für Klassenexporte verwendet nun `class_key` und
`previous_contract`, während `key` ausschließlich für den aktuellen Unit-Namen
reserviert bleibt. Import-/Export-ABIs, `.pui`-Format, generierter Assembler,
DLL-/COFF-Linker und alle bisherigen Klassenmetadaten bleiben unverändert.

Insbesondere wird **keine** globale Routinen-Deduplikation nach Name
vorgenommen. Echte doppelte Implementierungen werden weiterhin korrekt vom
Compiler abgewiesen.

## Prüfungen

- `python -m unittest -v test_stage543`: 3/3 erfolgreich.
- `python -m unittest -v test_stage542 test_stage541 test_stage540 test_stage543`:
  29/29 erfolgreich.
- Der neue Test modelliert die Diamant-Abhängigkeit
  `Windows -> Windows.Application / VCL -> VCL.Windows` einschließlich
  Klassenexport-Metadaten; die exportierte Unit wird genau einmal ausgewertet.
- Ein synthetischer echter Doppelimplementierungsfehler wird weiterhin gemeldet.

Testgrenze: Die Tests für die Unit-Auflösung verwenden `.pui`-Metadaten-Mocks.
Ein vollständiger nativer `Runtime.dll`-Build und ein realer ANTLR-4.13.2-
Quelltextdurchlauf wurden hier nicht ausgeführt (lokal verfügbare ANTLR-Runtime
4.9.3). Unter Windows sollte `Runtime.pas` neu übersetzt werden, einschließlich
der aktuellen `Windows`-/`VCL`-PUI-Dateien.

## Lokal reproduzieren

```pascal
library Runtime;
{$L inttostr.o}
{$L strtoint.o}
uses System, Windows;
begin
end.
```

Die Fehlermeldung über die angeblich doppelte Implementierung von
`GlobalWindowProc` darf im Build mit Stage 543 nicht mehr auftreten, soweit
keine weitere tatsächliche Mehrfachdefinition im Projekt vorhanden ist.
