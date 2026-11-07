# Stage 528 – Debug-Einstellungen in der linken TreeList

Basis: `d64_dism_stage527(1).zip` (unverändertes Stage-527-Archiv als verbindliche Quelle).

## Problem

In Stage 527 lagen die Debug-Einstellungen nur unter einem neuen *Tab* `Debug`
auf der obersten Projekt-Einstellungen-Ebene. Die Windows-TreeList enthielt
lediglich `Umgebung`, `Compiler`, `Assembler` und `Linker`. Deshalb waren die
Einstellungen in der linken TreeList nicht zu finden.

## Korrektur

- Im Projekt-Einstellungen-Dock existiert jetzt der TreeList-Hauptknoten
  `Debug` unter **Windows → 32-Bit** und **Windows → 64-Bit**.
- Ein Klick auf den Eintrag zeigt rechts die bisherige `DebugSettingsPage` mit
  `Enable Debug`, `CES - Check Early Start` und der `DWARF`-Gruppe (Enabled,
  Version 2 / 3).
- Die beiden Windows-Ansichten und der bisherige Top-Level-Tab `Debug` werden
  synchron gehalten, ohne beim Wiederherstellen aus `.pro` falsche
  Änderungsmarkierungen auszulösen. Der Tab bleibt als kompatibler Zweitzugang
  erhalten.
- Alle bisherige Speicherroutinen (`[Settings.Debug]`) und die CES-Logik im
  PE32-MSZIP-Loader bleiben unverändert.
- Hinweis: Die CES-Diagnose ist weiterhin nur für den PE32-D64I-MSZIP-Loader
  angeschlossen. Echte DWARF-Sektionen werden weiterhin nicht erzeugt.

## Prüfungen

- `python test_stage527.py`: 3 vorhandene Prüfungen erfolgreich.
- `python test_stage528.py`: 2 neue Prüfungen erfolgreich (TreeList-Verdrahtung
  im AST und Synchronisierung des Optionszustandes über drei Ansichten mit
  isolierten, Qt-unabhängigen Test-Doubles).
- Ein visueller PyQt5-Test sowie ein Windows-PE32-Laufzeittest waren in der
  Prüf-Umgebung nicht möglich.
- Das ursprüngliche Python-3.15-`lazy from` bleibt unverändert. Eine Ausführung
  der Hauptdatei unter Python 3.11–3.14 ist daher ohne Anpassung dieser
  Imports nicht möglich; die Tests normalisieren sie nur zum Prüfen.
