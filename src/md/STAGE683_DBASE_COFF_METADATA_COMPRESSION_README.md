# Stage 683 – dBASE COFF-Linker-Metadaten komprimieren

Basis: **Stage 682**. Die bestehende COFF-Assembler-/Linkerlogik bleibt erhalten.

## Projekt-Einstellungen

Navigation: **Windows → 32/64-Bit → Compiler → dBASE → Optimierung**
(ebenfalls auf der dBASE-Übersichtsseite unter „Compiler → dBASE“).

Neue GroupBox **Object Metadata** mit der unabhängig schaltbaren Checkbox
**Compress Meta Informations**. Standard: aus (alte Projekte bleiben unverändert).
PE32 und PE32+ speichern je einen eigenen Zustand.

In der Projektdatei unter
`[Settings.Windows.32Bit.Compiler.dBASE.Optimierung]` bzw.
`[Settings.Windows.64Bit.Compiler.dBASE.Optimierung]` steht:

```ini
CompressMetaInformations=true
```

**Nicht verwechseln** mit „compress json“ unter „Visuelle Elemente“:
Diese bisherige Option packt externe UI/Forms. Die neue Checkbox packt nur
private **COFF-Linker-Metadaten** aus `.o`/`.obj`.

## Byteformat (private `.drectve`-Payloads)

Nur wenn Metadaten vorhanden sind und die Option gesetzt ist:

| Offset | Inhalt |
|---|---|
| 0 (6 Byte) | Magic `D64JZ` plus Formatversion `\x01` |
| 6 (4 Byte, LE) | unkomprimierte Länge in Bytes |
| 10 (4 Byte, LE) | CRC32 der unkomprimierten JSON-Bytes |
| 14 ff. | zlib/DEFLATE-Komprimat, Level 9 |

Die bestehende JSON-Struktur (`d64-coff32-link-v1` bzw.
`d64-coff64-link-v1`) wird **nicht verändert**. Der eigene COFF-Parser
entpackt die `.drectve`-Sektion vor dem JSON-Lesen automatisch. Dies
funktioniert sowohl beim direkten Linken von Objektdateien als auch
bei aus Archiven entnommenen COFF-Membern.

Alte unkomprimierte `.o`-Dateien und gemischte Inputs werden weiterhin
gelesen. Das Headerformat wird anhand der Magic-Bytes erkannt; es braucht
beim **Linken keinen Schalter**. Die Dekompression validiert Formatversion,
Originallänge (Obergrenze 16 MiB), Stream-Ende und CRC32.

**Hinweis:** Die komprimierte `.drectve`-Darstellung ist eine private
Erweiterung für den integrierten dBase2Many-Linker. Allgemeine externe
COFF-Linker erwarten Standard-Direktiven in dieser Sektion und müssen das
Format nicht verstehen.

## Integration

- `d64_coff_metadata.py`: Formatkodierung/Dekodierung und Validierung.
- `d64_dism.py`: COFF32/COFF64 Writer, Parser und Objektgeneratoren;
  Optionen in Projekt-INI und GUI, Signale, Aufrufkette bis zum Writer.
- dBASE Programm-/Modulobjekte und reguläre dBASE F2-Builds verwenden
  den projektbezogenen Wert. Andere Sprachen bleiben standardmäßig beim
  alten unkomprimierten Format.
- Beim Umschalten werden die COFF/Link-Fertigmeldungen vorhandener dBASE
  Moduleditoren invalidiert. Bereits erzeugte `.o`-Dateien sind nicht
  automatisch konvertiert: **Assemble** erneut ausführen.

## Messergebnisse und Tests

Für `? "Hello from Stage683"` (jeweils identische Quellen, Eigenlinker):

| Ziel | unkomprimierte Metadaten | gepackte Metadaten | `.o` vorher | `.o` nachher |
|---|---:|---:|---:|---:|
| PE32 | 4.833 B | 888 B | 13.264 B | 9.319 B |
| PE32+ | 4.833 B | 887 B | 13.669 B | 9.723 B |

Automatische Tests: Stage-683-Roundtrip (PE32/PE32+), alte Objektformate,
Link zu gültiger PE-Datei, Header-/CRC-/Längenfehler und Projektverdrahtung.
Weiterhin Regressionstests aus Stage 680, 681 und 682.
Ein echter Windows-/Qt5-GUI-Laufzeittest wurde in der Entwicklungsumgebung
nicht durchgeführt.
