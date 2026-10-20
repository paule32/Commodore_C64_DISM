# Stage 432 – dBASE „Neu: …“ / Open File im Dark-Mode

## Verbindliche Basis
`d64_dism_asm_431.zip`.

## Einbindung
Der bestehende Aufruf `_new_dbase_project_file(...)` im Projekt-Informationen-
Kontextmenü `dBASE Programme` benutzt nun `DBaseProjectOpenFileDialog` für alle
acht `Neu: …`-Aktionen.

Der neue `QDialog` ist frameless und **enthält einen nicht-nativen `QFileDialog`
als QWidget**, damit sämtliche vorhandenen Funktionen des Dateibrowsers erhalten
bleiben. Open-Modus (`AcceptOpen`), Dateimodus (`AnyFile`), Detailansicht,
Dateifilter und Standarddateiname bleiben unverändert. Bei `accepted` bzw.
`rejected` wird der umgebende Dialog bestätigt bzw. abgebrochen.

## Erscheinungsbild

* Sichtbarer **3-Pixel-Rahmen**, realisiert mit `QFrame` und StyleSheet-Border.
* Bestehende `DBaseTableDialogTitleBar` mit draggable Window-Chrome;
  im Dark-Mode wird der vorhandene horizontale Verlauf **Schwarz → Grau**
  (`#000000` → `#707070`) verwendet.
* Oben rechts ein mit QPainter erzeugtes, gut sichtbares **X-Icon**;
  dessen Klick löst `reject()` aus.
* Dark-Mode: dunkler Hintergrund und Dateitabelle, helle Beschriftung,
  angepasste Buttons, Comboboxen, Filter und Selection.
* Dateiansichts-**Tabellen-Header**: eigener dunkler QHeaderView-Style,
  zusätzlich explizit auf der Header-Instanz gesetzt, um Qt5-/Windows-Styles
  zu übersteuern.
* Light-Mode: dazu passende helle Palette für Dialog und Header.

## Unveränderte Funktionalität

* Alle acht Menüeinträge bleiben an dieselben Dateitypen / Zielknoten gebunden.
* Neu anlegen und vorhandene Dateien auswählen, ohne zu überschreiben.
* Binärprüfung für vorhandene dBASE-`.prg`-Dateien mit Warntext
  „Datei ist keine gültige Programm-Datei“.
* Öffnen der Dateien im entsprechenden Editor / Designer und Projektspeicherung.

## Dateien
* `d64_dism.py` – neue Wrapperklasse und Datei-Dialog-Aufruf
* `test_stage432_dbase_file_dialog_theme.py` – vier neue Integrations-/Quelltexttests
* `STAGE432_DBASE_OPEN_FILE_DIALOG_DARKMODE.md` – Dokumentation

## Tests / Einschränkung
* 4/4 neue Stage-432-Tests bestanden.
* 7/7 bestehende Stage-431-Tests bestanden.
* `py_compile` erfolgreich, ZIP-Integrität geprüft.
* PyQt5 steht in der Testumgebung nicht zur Verfügung. Eine interaktive
  Windows-/PyQt5-Sichtprüfung ist daher noch nicht bestätigt.
