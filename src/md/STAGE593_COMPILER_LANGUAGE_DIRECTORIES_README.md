# Stage 593 – sprachabhängige Compiler-Verzeichnisse (PE32 / PE64)

**Verbindliche Basis:** vom Benutzer hochgeladenes `d64_dism_stage592(1).zip`.

## Oberfläche

Sowohl unter Windows 32-Bit (PE32) als auch Windows 64-Bit (PE32+) zeigt die
Projekt-Einstellung den folgenden Teilbaum:

```text
Compiler
├─ dBASE
│  ├─ Eingabe-Verzeichnis
│  ├─ Ausgabe-Verzeichnis
│  └─ Optimierung
├─ Pascal
│  ├─ Eingabe-Verzeichnis
│  ├─ Ausgabe-Verzeichnis
│  ├─ Optimierung
│  └─ Importe / Cache
├─ Prolog
│  ├─ Eingabe-Verzeichnis
│  ├─ Ausgabe-Verzeichnis
│  └─ Optimierung
├─ Parallelisierung
└─ Sicherheit
```

Die bisher direkt unter `Compiler` liegenden globalen Verzeichnisblätter sind
nicht mehr im Tree sichtbar. Pro Sprache existiert eine unabhängige,
priorisierte Eingabepfaddateiliste, ein EXE-/DLL-Ausgabeordner und ein eigener
Assembler-Zwischenspeicher mit relativ/absolut einstellbarer Anzeige.

Das separate Verzeichnis für Pascal-Unit-Dateien (`*.pui`/`*.o`) liegt nur
unter `Compiler -> Pascal -> Ausgabe-Verzeichnis`.

## Wirksamkeit beim Build

* **dBASE:** `.prg`-Programme und `.wfm`-Formulare einschließlich Präprozessor,
  ASM-Includes, erzeugten Assembler-, Objekt- und PE-Dateien nutzen ausschließlich
  die für dBASE hinterlegten PE32-/PE64-Pfade.
* **Pascal:** `.pas`/`.pp`, normale und parallele Unit-Builds, PUI-Dateien,
  COFF-Objekte, Include-/Bibliothekssuche und gelinkte EXE/DLL nutzen die
  Pascal-Einstellungen. Das separate PUI-/Unit-COFF-Ausgabefeld hat für
  Pascal-Units Vorrang vor dem allgemeinen Pascal-Ausgabeordner.
* **Prolog:** `.pl`/`.prolog`, generierte ASM-Dateien sowie Objekt- und
  Programmdateien nutzen die eigenen Prolog-Verzeichnisse.
* **Andere Sprachen:** Bisherige architekturspezifische Legacy-Pfade bleiben
  kompatibel; sie werden nicht als Pascal-/Prolog-Pfade verwendet.

## Projektdateien und Migration

Neue Sektionen beispielsweise für PE32:

```ini
[Settings.Windows.32Bit.Compiler.dBASE.InputDirectories]
RelativePaths = true
Path0001 = src/dbase

[Settings.Windows.32Bit.Compiler.dBASE.OutputDirectory]
RelativePaths = true
Path = build/dbase/pe32
AssemblerCache = build/dbase/asm

[Settings.Windows.32Bit.Compiler.Pascal.InputDirectories]
RelativePaths = true
Path0001 = src/pascal

[Settings.Windows.32Bit.Compiler.Pascal.OutputDirectory]
RelativePaths = true
Path = build/pascal/pe32
AssemblerCache = build/pascal/asm
PascalUnitOutput = build/pascal/units/pe32

[Settings.Windows.32Bit.Compiler.Prolog.InputDirectories]
RelativePaths = true
Path0001 = src/prolog

[Settings.Windows.32Bit.Compiler.Prolog.OutputDirectory]
RelativePaths = true
Path = build/prolog/pe32
AssemblerCache = build/prolog/asm
```

PE64 verwendet analoge Sektionen mit `64Bit` statt `32Bit`.

Wenn eine neue sprachspezifische Sektion im Projekt **fehlt**, wird beim
Laden einmalig der vorherige gemeinsame Verzeichniswert in dieses
Sprachprofil kopiert. Existiert die neue Sektion explizit, ist sie
maßgeblich – auch wenn keine Pfade darin stehen. Alte Verzeichnisse werden
nicht eigenmächtig entfernt oder in bestehende Ordner verschoben.

Die allgemeinen alten PE32-/PE64-Abschnitte bleiben für die Migration und
Kompatibilität mit weiteren Projekteinstellungen lesbar. Der Build für
dBASE/Pascal/Prolog verwendet nur die neuen Sprachwerte.

## Prüfungen

* Syntaxanalyse der 6,5-MB-`d64_dism.py` mit Neutralisierung von Python-3.15-
  `lazy`-Imports für die hier verfügbare Python-3.13-Umgebung: **OK**.
* `test_stage593.py`: 6 Tests für Sprach-/Zieltrennung, Quelltyp, Ausgabepfade,
  Includes, Legacy-Migration und explizit leere neue Sektionen: **OK**.
* `test_stage593_format.py`: 1 Test für tatsächliche sechs Eingabe- und sechs
  Ausgabesektionen (beide ABIs): **OK**.
* Bestehende Tests: `test_stage592` (12), `test_stage590` (10), `test_stage589`
  (8), `test_stage588` (6): **OK**.
* `test_stage591` ist wegen fehlender Datei `test_stage532.py` in der hochgeladenen
  Basis nicht ausführbar.
* Ein nativer PyQt5-GUI-/PE32-/PE64-Windows-Buildtest war in der
  Arbeitsumgebung nicht möglich; deshalb keine Laufzeitbestätigung behauptet.
