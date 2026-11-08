# Stage 548 – Projektverzeichnis als Bezugspunkt für Windows-Pascal-Ausgaben

**Basis:** Stage 547. Keine Veränderung an Pascal-Quelltexten oder der Runtime-DLL.

## Ursache

Bei aktivierter Option „relative Pfade“ wurden bereits gegen das Verzeichnis
von `pascal.pro` aufgelöste Compiler-Ausgabepfade teilweise erneut relativ zum
Ordner des jeweils bearbeiteten Pascal-Quelltextes verankert. Das konnte etwa
`runtime/pascal/test/runtime/pascal/test/pe32` erzeugen. Gleichzeitig enthielt
die DLL-Suchliste für `{$L Runtime.dll}` nicht zuverlässig den konfigurierten
finalen EXE-/DLL-Ausgabeordner. Das `.paslib.json`-Manifest blieb deshalb unter
Umständen ebenfalls unauffindbar.

## Sollpfade (Projekt im Verzeichnis `T:\GitHub\dBase2Many\src\asmjit\compiler\frontend\c64`)

| Projekt-Einstellung | Relative Pfadangabe | Aufgelöste Lage |
| --- | --- | --- |
| Assembler-Zwischenablage | `runtime\pascal\test\tmp` | `<Projektordner>\runtime\pascal\test\tmp` |
| EXE-/DLL-Ausgabe | `runtime\pascal\test\pe32` | `<Projektordner>\runtime\pascal\test\pe32` |
| 32-Bit-Unit/COFF-Ausgabe | `runtime\pascal\test\x32` | `<Projektordner>\runtime\pascal\test\x32` |

Die Checkbox „relative Pfade“ beeinflusst die Darstellung bzw. Persistenz der
Projektpfade, **nicht** deren nochmalige Verankerung am Quelltextverzeichnis.
Das gilt pro Architektur; PE64 verwendet seine separat eingestellten Pfade.

## Korrekturen

- `d64_dism.py`: zentraler Projektausgabe- und Objektpfad verwendet jeweils
  den Projektordner als Bezugsverzeichnis, unabhängig vom Quelltextort.
- Neue Methode `_project_windows_pascal_library_search_paths(document)` liefert
  den finalen DLL-Ausgabeordner zuerst, dann die konfigurierte PUI-/COFF-Ablage,
  das Projektverzeichnis und die restlichen Eingabe-Verzeichnisse.
- Normale und parallele Pascal-Kompilierung übergeben dieselbe Suchliste an
  Vorverarbeiter, `.pui`-Unit-Resolver und DLL-Exportprüfung.
- `{$L Runtime.dll}` bevorzugt in beiden Pascal-Vorverarbeitern die im Projekt
  konfigurierte DLL gegenüber einer veralteten Kopie beim Quelltext.
  `{$L foo.o}`/`{$LINK foo.obj}` behalten ihr bisheriges Suchverhalten.
- `pascal_class_exports.py` und `pascal_library_contract.py`: Prüfung von
  `.dll`- und `.paslib.json`-Dateien nutzt konfigurierte Projektpfade zuerst;
  voll qualifizierte DLL-Namen bleiben bindend. Fehlermeldungen nennen
  die geprüften Verzeichnisse.
- `_resolve_project_link_input()` berücksichtigt sowohl Unit-/COFF- als auch
  den finalen EXE-/DLL-Ausgabeordner.

## Tests

`python -m unittest -q test_stage540 test_stage541 test_stage542 test_stage543 test_stage544 test_stage545 test_stage546 test_stage547 test_stage548`

**71 von 71 Tests erfolgreich.** Neue Tests in `test_stage548.py` prüfen
projektbasierte Pfade und drei unterschiedliche Ausgabeverzeichnisse,
32-/64-Bit-Isolation, `.paslib.json`-Suche, explizite `.dll`-Auflösung,
Link-Eingaben und die Priorität des konfigurierten Ausgabeordners.
Die Tests sind plattformunabhängig; eine native GUI- und Linker-Probe unter
Windows ist noch ausstehend.

## Windows-Praxistest

1. Projekt `pascal.pro` öffnen. Für Windows 32-Bit die drei relativen Verzeichnisse
   wie oben angeben.
2. `library Runtime` neu erstellen und kontrollieren, dass `Runtime.dll` und
   `Runtime.paslib.json` in `runtime\pascal\test\pe32` liegen.
3. Prüfen, dass die benötigten `.pui`/`.o`-Dateien in `runtime\pascal\test\x32`
   liegen. Bei geänderten Unit-Quellen Unit-Artefakte neu erzeugen.
4. `program test_raise; {$L Runtime.dll} ...` kompilieren. Der Compiler soll die
   vorhandene DLL inklusive passenden PUI-Vertrags finden, ohne deren Pascal-
   Methodenrümpfe zusätzlich in die EXE zu übernehmen.
5. Für PE32+ getrennte Ausgabepfade konfigurieren, eine 64-Bit-DLL erzeugen und
   denselben Test mit dem PE64-Ziel wiederholen.

Bestehende DLL-Export- und Runtime-Laufzeitregeln wurden nicht verändert.
