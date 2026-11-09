# Stage 557 – Software Installer: fünfte Wizard-Seite „Projekt Theme"

Auf Basis von Stage 556 wurde der Installer-Wizard um eine fünfte Seite erweitert.

## Neu

- neue Wizard-Seite **Projekt Theme**
- ComboBox mit den Einträgen **Standard 1** und **Standard 2**
- nicht-interaktive Vorschau innerhalb einer großen Preview-Box
- Speicherung der Auswahl unter `general["project_theme"]`
- Hilfe-Thema **Wizard Seite 5**

## Layout der Vorschau

### Standard 1
- oberes Fünftel: Verlauf von weiß nach blau
- Linie an der Unterkante des oberen Panels
- mittlerer Bereich: weiß, zentrierter Text „Verknüpfung“, ComboBox „Ihr Produkt“, zwei RadioButtons
- unteres Fünftel: weiße Button-Leiste mit `< Zurück`, `Weiter >`, `Abbrechen`

### Standard 2
- oberes und unteres Fünftel: weiße Bereiche mit blau-weißem Verlauf im oberen Drittel
- mittlerer Bereich: blau mit weißem Text
- gleiches gezeichnetes Dialogschema wie bei Standard 1

## Technische Umsetzung

Die Vorschau wird in `software_installer_dialogs.py` durch `InstallerThemePreview(QFrame)` vollständig per `QPainter` gezeichnet. Es werden keine interaktiven Kind-Widgets angelegt; dadurch ist die Vorschau nur grafisch sichtbar und nicht auswählbar.

Der Wizard-Ablauf in `software_installer.py` lautet jetzt:
1. Allgemeine Informationen
2. Platform
3. Quelldateien
4. Fenster Einstellungen
5. Projekt Theme

## Dateien

- `software_installer_dialogs.py`
- `software_installer.py`
- `help/software_installer/index.html`
- `help/software_installer/installer.hhc`
- `help/software_installer/installer.hhk`
- `help/software_installer/installer.hhp`
- `help/software_installer/wizard_seite_5.html`
- `test_stage557.py`
