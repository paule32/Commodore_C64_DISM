# Stage 556 – Software Installer: vier Wizard-Seiten und verlaufende Titelleiste

Verbindliche Basis: `d64_dism_stage555.zip` (1.447 Dateien). Die Änderungen
betreffen ausschließlich den Software-Installer-Wizard und seine Hilfe-/Tests.

## Projektstart

- Der Dialog „Neues Projekt starten“ verwendet im Dark Mode einen sichtbaren
  Qt-Titelbalken mit Farbverlauf Schwarz → Weiß. Er ist per Maus (auch direkt
  auf der Überschrift) verschiebbar; `×` und `Escape` brechen ab.
- Windows-DWM lässt bei nativen Standardtitelleisten keinen echten horizontalen
  Schwarz-Weiß-Verlauf zu. Deshalb ist dieser Dialog (wie der Wizard) frameless
  mit eigener Titelleiste; der Eingabedialog „Speichern unter“ verwendet weiter
  die native, per DWM dunkel eingefärbte Titelleiste.
- „Suchen“ steht linksbündig unter der Projektliste.
- Die bestehende Radiobutton-Sperre für Projektliste, Suchen und Wizard bleibt.

## Wizard – gemeinsames Layout

Alle vier Wizard-Dialoge verwenden exakt **780 × 620 px** Fenstergröße,
eine **140 px** breite Image-Box links (Qt-Standard-Computericon als zunächst
neutrales Bild), rechts das Formular und 20 px Abstand zwischen Bildende und
Trennlinie. Darunter stehen Zurück, Weiter/Fertigstellen, Abbrechen und Hilfe.
Jeder Dialog erhält denselben Dark-/Light-Style und denselben verschiebbaren
Gradiententitel. Zum Zurückblättern werden bereits vorgenommene Eingaben in
einem gemeinsamen `values`-Dictionary gehalten und wieder eingelesen.

1. **Allgemeine Informationen:** Firma, Produkt, Produkt Version, Webseite.
   Bei leeren Eingaben wird der jeweilige Platzhalter als tatsächlicher Wert
   gespeichert: „Ihre Firma“, „Ihr Produkt“, „1.0“, „https://www.firma.de“.
   Zurück ist deaktiviert.
2. **Platform:** 32 - Bit Setup (Standard) oder 64 - Bit Setup. Zustand wird
   als `general.platform`: `"32"` oder `"64"` gespeichert.
3. **Quelldateien:** Quellenverzeichnis mit Ordner-Wählen-Button und Option
   „Einbeziehung der Unterverzeichnisse“. Speicherung als
   `general.source_directory` und `general.include_subdirectories` (`"true"`/
   `"false"`).
4. **Fenster Einstellungen:** Wizard oder Wizard mit Hintergrund-Fenster;
   Hintergrund mit statischer Farbe, Verlauf mit zwei separaten Farben oder
   Bilddatei. `InstallerColorComboBox` zeigt Farb-Swatches, akzeptiert
   benutzerdefinierte Hex-Farben und öffnet bei Doppelklick auf das Eingabefeld
   `QColorDialog.getColor(..., "Select Color")` (Windows-Standarddialog).
   Der Abschlussbutton heißt auf der vierten/derzeit letzten Seite
   **Fertigstellen** und übernimmt die Einstellungen in das ungespeicherte
   Projekt „Unbenannt“. Erst `Strg+S` vergibt den Projektnamen und speichert.

## Projektdatei / Registry

Die bestehende `.installer.json`-Struktur (format `d64-software-installer`,
version 1) wird unverändert weiterverwendet. Alle Wizardwerte liegen unter
`general`; sie bleiben damit kompatibel zur Stage-555-Projektverwaltung und
werden auch in `software_installer_projects.json` unter `settings.general`
registriert:

```
company, product, version, website,
platform, source_directory, include_subdirectories,
window_mode, appearance_style,
static_color, gradient_start, gradient_end, background_image
```

Für Felder ohne Auswahl werden die angegebenen Standardwerte benutzt.
Farben werden in der Form `#rrggbb` gespeichert. Bereits vorhandene Projekte
können unverändert geladen werden. Die alte Klasse `InstallerDestinationDialog`
bleibt vorerst für externe Aufrufer erhalten, ist aber nicht mehr Bestandteil
des vierstufigen Wizard-Ablaufs.

## Hilfe

`help/software_installer/wizard_seite_{1,2,3,4}.html` sind in Index (`.hhk`),
Inhaltsverzeichnis (`.hhc`), CHM-Projekt (`.hhp`) und `index.html` erfasst.
Die vorhandene `show_software_installer_help`-Route wird genutzt.

## Tests und Einschränkungen

- Quellsyntax, GUI-Struktur, State-Weitergabe und JSON-Roundtrip:
  `python -m unittest -v test_stage553 test_stage554 test_stage555 test_stage556`.
- Native PyQt5-Tests (Windows oder QT_QPA_PLATFORM=offscreen):
  `python -m unittest -v test_stage553_qt test_stage555_qt test_stage556_qt`.
- Auf der hier verwendeten Umgebung ist PyQt5 nicht vorhanden. Die Qt-Tests
  werden deshalb als **übersprungen**, nicht als bestanden ausgewiesen.
- Die vier Wizard-Seiten erfassen und speichern **Konfiguration**, sie bauen
  noch keine eigenständige Setup-EXE. Nächste Wizard-Seiten sind noch nicht
  spezifiziert; vorläufig beendet „Fertigstellen“ die Eingabe auf Seite 4.
