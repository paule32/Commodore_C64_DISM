# Stage 559 – Session Variablen im Software Installer

## Verbindliche Basis

Stage 558 (`d64_dism_stage558.zip`), kein verworfener Entwicklungszweig.

## Geometrie

- Alle sieben Wizard-Dialoge benutzen nun **760 × 590 px** statt 780 × 620 px.
- Dialog **Session Variablen**: **620 × 550 px** (140 px schmaler und 40 px niedriger als der Wizard).
- Dark-/Light-Theming und die verlaufende Qt-Titelleiste werden aus `InstallerThemedDialog` übernommen.

## Aufruf

`Software Installer` → linkes Panel `Einstellungen` → `Session Variable`.

## Bedienung

Ein `QScrollArea` enthält drei unabhängig aufklappbare Container, jeweils mit
Pfeil **links** von der Überschrift:

### Produkt Informationen

| Variable (nicht editierbar) | Standardwert in Spalte 2 |
|---|---|
| `%ProductName%` | Wizard-Produkt oder `Ihr Produkt` |
| `%CompanyName%` | Wizard-Firma oder `Ihre Firma` |
| `%ProductVersion%` | Wizard-Version oder `1.0` |
| `%Copyright%` | `Copyright (c) #CURRENTYEAR# %CompanyName%` |
| `%CompanyURL%` | Wizard-Webseite oder `https://www.firma.de` |
| `%WindowTitle%` | `%ProductName% Setup` |
| `%WindowTitleUninstall%` | `%ProductName% Uninstaller` |

**Anmerkung:** Die syntaktisch geschlossene Schreibweise `%ProductVersion%` wird verwendet (analog zu allen anderen Variablennamen).

### Standard-Verzeichnisse

| Variable | Standardwert |
|---|---|
| `%AppFolder%` | `%ProgramFilesFolder%\%ProductName%` |
| `%AppShortcutFolderName%` | `%ProductName%` |

### Benutzerdefiniert

Initially empty; `Hinzufügen` öffnet einen modalen Dark-Mode-Eingabedialog mit zwei Eingaben
(Platzhalter `%VariableName%` und `Wert`) und `OK` / `Abbrechen`. Ein Variablenname
muss `'%Name%'` entsprechen; unklammerte gültige Namen werden automatisch ergänzt.
Duplikate werden ohne Unterscheidung der Groß-/Kleinschreibung gegen alle System- und
Benutzervariablen geprüft. `Entfernen` und `Umbenennen` bearbeiten ausschließlich
benutzerdefinierte Variablen. Die erste Spalte ist in **allen drei Tabellen**
schreibgeschützt, die zweite editierbar.

## Speichern und Lebenszyklus

Der Inhalt liegt in `InstallerProject.sections["Session Variable"]` als JSON-Text
im bestehenden `.installer.json`-Projektformat (`version` 1) und wird weiterhin
von der globalen Installer-Projektliste erfasst. Beispiel:

```json
{
  "version": 1,
  "overrides": {
    "%WindowTitle%": "Mein Setup"
  },
  "custom": {
    "%LICENSE%": "DEMO-2026"
  }
}
```

Die aktuellen Systemstandardwerte ergeben sich aus `InstallerProject.general`
und werden nicht mehrfach gespeichert: Nach späteren Wizard-Änderungen
aktualisieren sich alle **nicht ausdrücklich überschriebenen** Variablen
automatisch. `overrides` sichern manuell geänderte Werte.

Bei Dialog-`OK` wird die Konfiguration in den Projektzustand übernommen und
bei bestehenden Projekten direkt mit `save_configuration` in die Projektdatei
geschrieben. Bei neuen Projekten wird – wie bisher – zuerst ein Projektname
abgefragt. Bei Abbruch oder Dateifehler bleibt die Projektänderung als
ungespeichert markiert; `Strg+S` kann später erneut speichern. Der
Dialogbutton `Abbrechen` verwirft die Bearbeitung, ohne das Projekt zu ändern.

Ungültige ältere reine Textinhalte im Feld `Session Variable` werden *nicht*
stillschweigend überschrieben: der Benutzer erhält eine Fehlermeldung.

Die Hilfe ist als `help/software_installer/session_variablen.html` registriert.

## Tests

- `python -m unittest test_stage559 test_stage559_qt`
- `python -m unittest test_stage553 test_stage554 test_stage555 test_stage556 test_stage557 test_stage558 test_stage559`

In der hier verwendeten Testumgebung ist PyQt5 nicht installiert; native
Offscreen-/Windows-GUI-Tests werden daher übersprungen. Die Qt-freie
Modelllogik, Geometrie-Referenzen und JSON-Roundtrips sind getestet.

## Modifizierte Dateien

- `software_installer_dialogs.py`
- `software_installer.py`
- `test_stage556.py` (neue Geometrie)
- `test_stage558.py` (neue Geometrie)
- `help/software_installer/{installer.hhc,installer.hhk,installer.hhp,index.html}`

## Neue Dateien

- `installer_session_variables.py`
- `help/software_installer/session_variablen.html`
- `test_stage559.py`
- `test_stage559_qt.py`
- `STAGE559_SOFTWARE_INSTALLER_SESSION_VARIABLES_README.md`
