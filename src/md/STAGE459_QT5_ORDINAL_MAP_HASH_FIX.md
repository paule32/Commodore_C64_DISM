# Stage 459 – Qt5-Runtime ABI-Korrektur

**Verbindliche Basis:** Stage 458 (`d64_dism_asm_458.zip`).

## Fehler
Beim Start der aus WFM assemblierten EXE erscheint „libd64_qt5.dll fehlt oder
ist inkompatibel“. Der erwartete Kern-Hash ist
`02c94324ebc9e8373c08011d0f8c5ba5aec95b158087092ed4e741877b1a7cd7`,
der gefundenen vollständigen Exporttabelle entspricht
`4c919b40041b872ee6b083936259e036d06f270005df91dd396b24da170f806f`.
Die fünf Stage-458-UTF8-Namensexporte sowie der Stage-456-JSON-Export änderten
irrtümlich die IDE-seitige SHA-256-Berechnung.

## Änderungen
- `d64_dism.py`: Ein gemeinsamer Filter für den stabilen 64-Export-Kern;
  zusätzlicher Abgleich tatsächlich im generierten WFM-Assembler importierter
  neuer JSON-/UTF8-Funktionen gegen die konkrete Qt5-DLL.
- `d64qt5/generate_runtime_abi.py`: Gleiches Hashschema für Runtime-Header.
- `d64qt5/README.md`: Dokumentation von Kern-ABI und Namensexporten.
- `test_stage459_qt5_ordinal_abi.py`: Tests für Hash, neue und alte DLL,
  Importerkennung, sowie Konsistenz mit ABI-Generator.

## Verwendung
Die neue IDE akzeptiert eine vorhandene neu gebaute Qt5-Runtime mit den
Stage-458-UTF8-Exporten, wenn deren Kern-ABI übereinstimmt. Bei fehlenden
benötigten neuen Exporten wird der fehlende Name explizit angezeigt. Falls die
DLL die benötigten Exporte nicht hat, unter Windows im Ordner `d64qt5`
`build_d64qt5_mingw32.bat` ausführen und die resultierende DLL in das
Projekt-/Ausgabeverzeichnis kopieren. Architektur beachten: PE32 -> 32 Bit,
PE32+ -> 64 Bit.

## Prüfung
- Generator liefert ursprünglichen Hash `02c943...`.
- 84 Tests erfolgreich, 1 Windows-spezifischer Test übersprungen
  (`pytest`-Kombination aus Stage 446–459).
- Python-Syntax und ZIP-Integrität werden separat geprüft.
- Keine native Windows/Qt5-Laufzeitprüfung in dieser Umgebung.
