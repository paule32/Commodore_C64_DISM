# Stage 601 – Flache Pascal-Projektstruktur

**Verbindliche Grundlage:** `d64_dism_stage600.zip`.

## Sichtbare TreeList

Unter `Pascal-Programme` befinden sich nun acht **direkte** Unterknoten:

```text
Pascal-Programme
├── Windows PE32 Module
├── Windows PE32 Units
├── Windows PE32 Tabellen
├── Windows PE32 Ressourcen
├── Windows PE32+ Module
├── Windows PE32+ Units
├── Windows PE32+ Tabellen
└── Windows PE32+ Ressourcen
```

Die bisherige zusätzliche Ebene `Windows PE32`/`Windows PE32+` entfällt. Dateien bleiben unter der zugehörigen Kategorie, d. h. ein Dateiblatt ist nun eine Ebene weniger weit eingerückt. Die Spalte für die Projektzuordnungs-Dropdown-Buttons erhält mehr Platz. Der globale TreeList-Einzug und die vom Benutzer einstellbaren Spaltenbreiten bleiben unverändert.

## Unveränderte Funktionen

- Kategorie und Architektur werden durch `Qt.UserRole + 303`, `+305`, `+306` gespeichert, nicht aus dem sichtbaren Text abgeleitet.
- Module/Units, DBF-Tabellen und RC/RES-Ressourcen bleiben in den bisher verwendeten Dictionary-Zuordnungen und `.pro`-Sektionen erhalten.
- Der bisherige Architektur-Knoten bot `Programm erstellen`, `DLL erstellen` und `Starten`. Diese drei Aktionen sind nun in einem Untermenü `Pascal: Kompilieren / Linken` in den Kontextmenüs der Module-, Units-, Tabellen- und Ressourcen-Knoten erreichbar.
- Der Root-Kontextmenüpunkt für neue Pascal-Module/Units bleibt vorhanden.
- Der generische Löschdialog kann die neuen direkten Pascal-Unterknoten nicht entfernen.
- Die Ressourcenzweige anderer Sprachen bleiben unverändert.

## Kompatibilität alter Projekt-Zuordnungen

Die gespeicherten Datei-Zuordnungsschlüssel enthielten bisher sichtbare Ahnenbezeichnungen, z. B.:

`["pascal-programme", "windows pe32", "module"]`

`project_named_targets.legacy_pascal_ancestry()` normalisiert die neuen sichtbaren Kategorien für die Schlüsselbildung zurück auf diese bisherige Identität. Daher behalten Dateien auch nach Öffnen/Speichern eines älteren Projekts ihre Programm-/DLL-Zuordnung. Die Gruppen-Auswahl verwendet weiterhin die stabilen Schlüssel `@group:pascal:pe32:modules` usw.

## Prüfungen

- `test_stage601.py`: 7 Tests: acht direkte Geschwisterknoten, PE32/PE64-Metadaten, Ressourceneinträge, Legacy-Zuordnungsschlüssel, unveränderte Nicht-Pascal-Hierarchie, Build-Menü-Dispatch sowie geschützte Knoten.
- Weitere erfolgreich separat ausgeführte Tests: Stage 590 (10), 592 (12), 596 (11), 597 (8), 598 (9), 599 (14) und 600 (21). Zusammen mit Stage 601: 92 erfolgreiche Tests.
- Stage 593: ein isolierter Testlauf wurde abgebrochen, da er nicht in angemessener Zeit beendete. Nicht als bestanden gewertet.
- Syntax: Das auf Python 3.15 zielende `d64_dism.py` enthält `lazy from ... import`, daher AST-Validierung nach rein syntaktischer Ersetzung von `lazy from` zu `from` unter Python 3.13. `project_named_targets.py` ist nativ py_compile-geprüft.
- Ein nativer PyQt5-Layouttest unter Windows steht noch aus (PyQt5 hier nicht installiert).

Es sind **keine** Compiler-/Linkeränderungen oder Änderungen an der DLL-Runtime vorgenommen worden.
