# Stage 569 – Kontextmenü der rechten Software-Installer-Tabelle

**Verbindliche Ausgangsbasis:** `d64_dism_stage568.zip`

## Oberfläche

Im Dock **Software Installer** enthalten jetzt sowohl die rechte Tabelle **Archiv** als auch **Extern** folgende Aktionen im Kontextmenü (Rechtsklick auf eine Tabellenzeile oder leeren Tabellenbereich):

| Aktion | Tastenkürzel | Umsetzung |
|---|---|---|
| Wiederherstellen | Strg+Z | Letzte Änderung im jeweiligen Tab rückgängig machen (Undo) |
| Rückgängig | Strg+Y | Rückgängig gemachte Änderung wiederholen (Redo) |
| *Trennlinie* | | |
| Ausschneiden | Strg+X | Gewählte vollständige Zeilen in Zwischenablage kopieren und entfernen |
| Kopieren | Strg+C | Gewählte vollständige Zeilen kopieren |
| Einfügen | Strg+V | Zeilen aus Zwischenablage **vor** der aktuellen Zeile einfügen, sonst anhängen |
| Entfernen | Entf | Gewählte Zeilen entfernen |
| *Trennlinie* | | |
| Hinzufügen: Datei | Einfg | Bestehende Dateiauswahl verwenden |
| Hinzufügen: Pfad | Strg+Einfg | Bestehende Ordnerauswahl verwenden |
| *Trennlinie* | | |
| Datei: öffnen | Strg+D | Lokalen Pfad mit dem zugeordneten Windows-Programm öffnen |
| Eigenschaften | Strg+Enter | Bestehenden Eigenschaften-Dialog für die aktuelle Zeile öffnen |

**Hinweis zu den Begriffen:** Die Beschriftungen und Shortcuts wurden wie vorgegeben umgesetzt. `Strg+Z` führt fachlich Undo und `Strg+Y` Redo aus; die Namen „Wiederherstellen“/„Rückgängig“ bleiben unverändert.

Die Aktionen sind als `QAction` auf `InstallerTable` registriert. Daher funktionieren die Shortcuts auch **ohne zuvor geöffnetes Kontextmenü**. Rechtsklick auf eine unselektierte Zeile selektiert sie, Rechtsklick auf bereits selektierte Zeilen erhält die Mehrfachauswahl. Einträge werden je nach Auswahl/Undo-Zustand automatisch aktiviert oder deaktiviert.

Bei Dark-Mode wird das Kontextmenü mit den vorhandenen dunklen Farben des Installer-Docks gestaltet.

## Daten und Undo-/Redo-Verhalten

* Undo und Redo arbeiten **tabweise getrennt** und berücksichtigen Zelländerungen, Dateihinzufügungen, Pfadhinzufügungen, Eigenschaftenänderungen, Einfügen, Ausschneiden und Entfernen.
* Die Undo-Historie umfasst die letzten 100 Änderungen pro Tab. Beim Laden/Neuanlegen eines Projekts wird sie gelöscht, um Zustände aus fremden Projekten nicht zu übernehmen.
* Zwischenablage: proprietäres MIME-Format (`application/x-d64-installer-rows+json`) zur verlustfreien Übernahme aller neun Eintragsfelder und zusätzlich UTF-8-Text als tab-separierte Zeilen für Fremdprogramme. Externe einspaltige bzw. neunspaltige TSV-Texte werden unterstützt; abweichende Spaltenzahlen werden mit Fehlermeldung abgelehnt.
* Änderungen erfolgen nur im bisherigen `InstallerProject.entries`-Modell und markieren das Projekt als geändert. Der bestehende zentrale Speichern-Mechanismus bleibt unverändert. Die Projektdatei-Struktur wird **nicht** geändert.
* Der bisherige interne API-Aufruf `add_blank_row` bleibt für andere Codepfade erhalten, erscheint aber nicht mehr im neuen Kontextmenü.

## Dateien

* `software_installer.py` – neue `QAction`/`QMenu`-Konstruktion, Aktionen mit History und Clipboard sowie Datei-Öffnen
* `installer_table_editing.py` – Qt-unabhängige TSV-/MIME-Verarbeitung und Undo-/Redo-Datenstruktur
* `test_stage569.py` – Quellcode- und Datenmodelltests
* `test_stage569_qt.py` – native GUI-Tests unter Windows bzw. Qt-Offscreen
* `test_stage553.py` – eine überholte Erwartung zum früheren Kontextmenü auf die neue Struktur aktualisiert

## Teststand

`python -m unittest -q test_stage553 ... test_stage569_qt` (Installer-Stages 553 bis 569, ohne nicht existierende Testmodule):

* **222 Tests ausgeführt**
* **178 erfolgreich**
* **44 übersprungen**, weil PyQt5 in dieser Umgebung fehlt
* **0 Fehler / 0 Fehlschläge**

Die neuen Qt-Tests müssen unter Windows mit PyQt5 ausgeführt werden, bevor eine native GUI-Bedienprüfung als abgeschlossen gelten kann. Die Qt-freien Undo-, Clipboard- und JSON-Roundtrip-Tests sind gelaufen.
