# Stage 431 – dBASE-Projektknoten: acht „Neu: …“-Aktionen

## Verbindliche Basis
`d64_dism_asm_430.zip`; keine anderen Entwicklungszweige gemischt.

## Projekt-Informationen → dBASE Programme (Rechtsklick)

Im Kontextmenü des dBASE-Hauptknotens stehen nun:

- `Neu:  Formular` → `Formulare`, `.wfm`, Formular-Designer
- `Neu:  Programm` → `Programme`, `.prg`, dBASE-Texteditor
- `Neu:  Tabelle` → `Tabellen`, `.dbf`, Tabellen-Designer
- `Neu:  Abfrage` → `Abfragen`, `.d64sql`, SQL-Builder
- `Neu:  Bericht` → `Berichte`, `.d64report`, Bericht-Builder
- `Neu:  Etikett` → `Etiketten`, `.d64label`, Etiketten-Designer
- `Neu:  Windows PE32 Ressource` → `Windows PE32/Resourcen`, `.rc`/`.res`, Resourcen-Editor
- `Neu:  Windows PE32+ Ressource` → `Windows PE32+/Resourcen`, `.rc`/`.res`, Resourcen-Editor

Jede Aktion öffnet einen `QFileDialog` im **Open-Modus** (`AcceptOpen`, `AnyFile`).
Dies erlaubt die Auswahl einer existierenden Datei oder die Eingabe eines neuen
Dateinamens. Die Dateiendung wird geprüft und bei fehlender Endung ergänzt.
Neue Dateien erhalten gültige Grundinhalte für den jeweiligen Designer;
Tabellen werden über den bereits integrierten DBF-Writer geschrieben. `.res`
ist ein binäres Ergebnisformat und kann nur **vorhanden** ausgewählt werden;
eine neue Ressourcendatei wird als `.rc` angelegt.

Bereits vorhandene Dateien werden nicht überschrieben; sie werden ins Projekt
eingetragen und im bestehenden Editor/Designer geöffnet. Dateiknoten öffnen
bereits bei einfachem Mausklick. Die zweite Doppelklick-Ausführung für diese
Blätter ist unterdrückt, damit Formulare nicht versehentlich zweimal geladen
werden. Shift/Strg unterstützen weiterhin Mehrfachauswahl.

## Binäre `.prg`-Dateien

Bei Auswahl, Gruppen-„Hinzufügen“ sowie beim Öffnen eines dBASE-Programmblatts
wird die vollständige Datei blockweise auf Steuer- und NUL-Bytes geprüft.
C64-Binär-PRGs, UTF-16-Daten und binäre Container werden zurückgewiesen.

**Warntext (wörtlich):** `Datei ist keine gültige Programm-Datei`.

Keine Editor-Instanz für ungültige dBASE-PRGs; der separate C64-Binärdateipfad
bleibt unverändert. ANSI/OEM-Texte mit deutschen Umlauten werden akzeptiert.

## Dateien
- `d64_dism.py` – Kontextmenü, Dateiauswahl, Baum/Editor-Integration
- `dbase_project_new.py` – Menüdefinition, reine Dateiprüfung und Vorlagen
- `test_stage431_dbase_project_new.py` – PyQt-freie Unit- und Integrationschecks
- `STAGE431_DBASE_PROJEKT_NEU_DATEIAUSWAHL.md` – Dokumentation

## Grenzen der automatischen Prüfung
PyQt5 ist hier nicht installiert: daher kein echter interaktiver Qt5-Fenstertest
unter Windows. GUI-Wiring wird durch Quelltext-/Syntaxprüfungen erfasst;
Dateierzeugung, WFM-Parser, Validierung und Nichtüberschreiben sind funktional geprüft.
