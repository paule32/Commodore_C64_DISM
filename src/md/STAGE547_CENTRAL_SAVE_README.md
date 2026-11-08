# Stage 547 – Zentrale Dokument-Speicherung

## Verbindliche Grundlage

Stage 546 (`d64_dism_stage546.zip`), Hauptdatei `d64_dism.py`.

## Problem

Bisher rief die Hauptaktion `Strg+S` nur `save_current_document()` auf. Das
speicherte den gerade selektierten Tab und übersprang geänderte, aber nicht
selektierte Pascal-/C-/ASM-/Text-Dokumente. Zusätzlich hatte der HTML-Editor
einen konkurrierenden eigenen `Strg+S`-Shortcut. Der generierte ASM-Editor
besaß eine eigene Änderungsmarkierung, wurde aber nicht bei `is_modified`
und Projekt-Schließen erfasst.

## Änderungen

1. `ExplorerWindow.save_all_open_documents(...)` ist die zentrale
   Speicherkoordination. Sie erstellt einen Snapshot aller offenen
   `DocumentEditor`-Tabs. Auch unselektierte geänderte Dateien werden
   gespeichert. Die bisherige Auswahl wird anschließend wiederhergestellt.
2. `Strg+S`, Datei → Alle speichern und die zentrale Toolbar-Speichernaktion
   gehen durch `_save_file_contextual` zur zentralen Speicherroutine.
   Der konkurrierende Shortcut des HTML-Editors wurde entfernt; sein lokaler
   Menü-/Toolbar-Speichern-Button funktioniert weiterhin.
3. Die Erkennung berücksichtigt Text-/Hex-Quellen, einen manuell geänderten
   generierten ASM-Editor, dBase-Formular und dessen ASM-Tabs, HTML,
   Windows-Ressourcen, Apache-Konfiguration, E-Baukasten sowie geänderte
   Projektmetadaten. Die Projektdatei wird zuletzt gespeichert.
4. Eine Quelldatei und ihr generierter ASM-Editor werden auf *getrennte*
   Pfade geschrieben. Modifizierte generierte ASM-Dateien werden nicht mehr
   unbemerkt als „gespeichert“ behandelt.
5. Neue Dateischreibvorgänge nutzen ein temporäres Ziel im selben Ordner,
   `flush`, `fsync`, `os.replace` und eine anschließende Prüfung der
   tatsächlich gespeicherten Bytes. Erst danach wird das Änderungsflag
   zurückgesetzt. Ein Fehlvorgang bleibt sichtbar.
6. Fehler/Abbruch bei einem Dokument stoppen nicht die Sicherung anderer
   geänderter Dokumente. Die Zusammenfassung nennt gespeicherte und
   fehlgeschlagene Dateien; bei Fehler bleibt der betroffene Tab aktiviert.
7. Projekt-Schließen verwendet dieselbe Speicherroutine wie `Strg+S`.
8. Der dBase-Tabelleneditor gibt ein boolesches Speichern-Ergebnis an den
   Save-All-Aufrufer zurück, nachdem der offene Grid-Delegate committed wurde.
   Ein DBF-Fehler darf nicht zu einer globalen Erfolgsmeldung führen.

## Abgrenzung

- „Alle speichern“ ist keine transaktionale atomare Operation über mehrere
  Dateien. Bei einem Fehler können andere Dateien bereits gespeichert sein.
- Automatisch neu generierte ASM-Dateien werden nicht ohne Weiteres
  überschrieben; nur Änderungen im zugehörigen Editor werden gesichert.
- Für unbenannte Quelldokumente bleibt der vorhandene Speichern-unter-Dialog
  aktiv. Bei einem Abbruch bleibt dieses Dokument unverändert markiert.
- Native visuelle PyQt5-Tests auf Windows sind noch offen. Die automatisierten
  Tests extrahieren die echten Speichermethoden mittels Python-AST, nachdem
  Python-3.15-Lazy-Import-Syntax temporär für die Testumgebung angepasst wurde.
  `d64_dism.py` selbst wurde NICHT auf andere Importsyntax umgestellt.

## Tests

- `python test_stage547.py`: 14/14 erfolgreich
- `python -m unittest -q test_stage546.py`: 7/7 erfolgreich
- `python -m unittest -q test_stage543.py test_stage544.py test_stage545.py`:
  17/17 erfolgreich
- Die komplette Hauptdatei besteht die Python-AST-Syntaxprüfung nach
  temporärer Umwandlung der beiden `lazy from`-Importzeilen.

### Windows-Praxistest

1. Ein Projekt öffnen (z. B. `pascal.pro`).
2. Mindestens drei verschiedene Pascal-Units/-Programme in separaten Tabs öffnen.
3. In allen drei Tabs Änderungen vornehmen; im ersten Tab bleiben.
4. `Strg+S` drücken.
5. Die drei Quelldateien auf Platte öffnen und deren Inhalt vergleichen.
6. Optional generierte ASM-Ansicht ändern und mit `Strg+S` sichern; Quelltext
   darf nicht mit ASM überschrieben werden.
7. Eine Datei schreibschützen bzw. Schreibzugriff verhindern und prüfen, dass
   sie als ungespeichert markiert bleibt, während andere Dateien geschrieben
   werden.
