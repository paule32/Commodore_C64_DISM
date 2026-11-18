# Stage 610 – Optionales Compact für Windows PE32/PE64

**Basis:** Stage 609 (`d64_dism_stage609.zip`). Keine Änderung an anderen Compiler- und Projektfunktionen.

## UI

`Projekt-Einstellungen → Windows → 32-Bit / 64-Bit → Linker → Optionen → PE-Packing`

Unterhalb des vorhandenen Erklärungstexts befindet sich die Checkbox **Compact**. Sie ist unabhängig von der Option **D64Z/MSZIP PE-Packing aktivieren** und für bestehende Projekte standardmäßig deaktiviert.

- PE32 und PE64 haben getrennte Compact-Einstellungen.
- `Settings.Windows.32Bit.Linker.Optionen: Compact = true|false` und analog `64Bit` in der `.pro`-Datei.
- Änderungen werden im Projektmodell synchronisiert und gespeichert.

## Technische Ausführung

Die neue Funktion `d64dbase.pe_image_compact.compact_pe_image(bytes)` wird nach dem internen COFF-Linken von **EXE und DLL** ausgeführt, sofern Compact aktiviert wurde. Der Projekt-Build wendet denselben Durchlauf außerdem nach der Manifest-/Ressourceneinbettung, aber **vor** einer optionalen Authenticode-Signatur auf die Zieldatei an.

Es werden ausschließlich sichere, vollständige `FileAlignment`-Blöcke entfernt, keine beliebigen Nullbytes:

1. Unnötige Dateilücken zwischen den Rohdaten der Sektionen.
2. Nicht benötigter DOS-Stub/Header-Puffer, sofern eine vollständige Alignment-Einheit eingespart wird.
3. Vollständig aus Nullbytes bestehende, nachlaufende Sektions-Rohdatenblöcke, die der Windows-PE-Loader durch den normalen Nullfüllbereich der Sektion wiederherstellt.

Dabei werden `PointerToRawData`, `SizeOfRawData`, `SizeOfHeaders` und die Code-/Datengrößenangaben des optionalen Headers aktualisiert. **RVA, VirtualSize, ImageBase, EntryPoint, DataDirectories und die Bytes aller nichtleeren Sektionsbereiche bleiben erhalten.** Das Ergebnis wird nachvalidiert; ohne tatsächlichen Vorteil wird die Originaldatei verwendet.

Die Optimierung wird **nicht** auf signierte Dateien, Dateien mit gesetzter PE-Prüfsumme, COFF-Symboltabellen, Debug-Verzeichnissen, unbekannten Overlays oder nicht zuordenbaren Offset-Tabellen angewendet. Auch ungültige PE-Dateien bleiben unverändert. Das garantiert nicht die Windows-Lauffähigkeit jedes exotischen externen PE-Images; Ziel sind die vom internen Linker erzeugten Images.

## Untersuchung `RuntimeDB.dll` des Nutzers

4.096 Bytes, PE32, 6 Sektionen `.text`, `.idata`, `.edata`, `.reloc`, `.loader`, `.ztext`, FileAlignment 512 Bytes. 2.701 Nullbytes (65,9 %), zum großen Teil wegen PE-Struktur und Ausrichtung. Die im Archiv vorhandene DLL wurde bereits mit D64Z gepackt und die Rohsektionen sind physisch dicht hintereinander angeordnet. Der neue konservative Compactor spart an genau diesem Exemplar **0 Bytes**. Die in den einzelnen 512-Byte-Sektionsblöcken verbleibenden Nullbytes darf er nicht willkürlich entfernen.

## Protokoll und APIs

In der GUI nach dem Linken:

`PE COMPACT (pe32): RuntimeDB.dll; 4096 -> 4096 Bytes (-0 Bytes); Keine überflüssigen vollständigen FileAlignment-Blöcke.`

Die Python-API `compact_pe_image()` gibt `(bildbytes, bericht_dict)` zurück, u.a. mit `before_size`, `after_size`, `saved_bytes`, `zero_blocks`, `zero_bytes`, `reason`, `changed`. `compact_pe_file()` schreibt eine kompaktierte Fassung nur bei erfolgreich abgeschlossener Validierung.

## Tests

`python -m unittest -q test_stage610`: 9 Tests, einschließlich tatsächlicher PE32-/PE64-Klassen-DLL-Links und EXE-Bereich, Import-/Export-Vergleich, signiertem Image, Overlay, Leerlauf, Idempotenz und Rundlauf eines künstlich eingefügten 512-Byte-Nullblocks.

Weitere erfolgreich einzeln ausgeführte Regressionen: Stage 609 (12), Stage 608 (5), Stage 607 (5), Stage 606 + Stage 604 (11), Stage 605 (5), Stage 605 Link (1). **48 erfolgreich abgeschlossene Tests** insgesamt. Eine größere kombinierte Suite lief in einen Timeout; daraus wird kein Testergebnis abgeleitet.

Ein visueller Qt-Test und ein nativer Windows-`LoadLibrary`-Test sind hier mangels Windows/PyQt5 nicht ausgeführt worden.
