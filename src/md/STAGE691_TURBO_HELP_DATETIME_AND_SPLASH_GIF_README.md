# Stage 691 – Turbo-Hilfe DateTime-Picker und animierte Splash-Preloader

**Verbindliche Ausgangsbasis:** Stage 690 (`d64_dism_stage690.zip`).

## 1. Turbo-Hilfe → Settings

Die beiden bisherigen Textfelder für **POT-Creation-Date:** und **PO-Revision-Date:**
werden als native `QDateTimeEdit`-Komponenten mit `setCalendarPopup(True)`
dargestellt. Ein Datum kann über den Kalender und die Uhrzeit über das
Zeit-Eingabefeld gewählt werden. Die übrigen PO-Header-Felder bleiben
`QLineEdit`.

Beim Laden wird das vorhandene gettext-Format (z. B. `2026-11-24 19:26+0100`)
in die sichtbare Datum-/Uhrzeit-Auswahl übernommen. Solange eine der beiden
Datumseingaben nicht geändert wurde, bleibt der ursprüngliche Headerwert
exakt erhalten; das ist wichtig, um nicht schon beim Bearbeiten eines anderen
Felds die PO-Header umzuschreiben. Nach Änderung entsteht ein gültiger
`YYYY-MM-DD HH:MM±HHMM`-Wert mit dem zur ausgewählten lokalen Zeit passenden
Zeitzonenversatz. Projektpersistenz und HLP-Generierung nutzen weiterhin die
bestehende `headers`-Struktur. Die bisherige Regel „.po + .hlp, keine .mo“
bleibt unverändert.

Betroffene Module:
- `turbo_help_po_settings_page.py`: QDateTimeEdit-Integration, Änderungserkennung
- `turbo_help_po_metadata.py`: Gettext-Datum/Zeitzonen-Parser und Serializer

## 2. Splash-Screens: `data/loader.gif`

Die vorhandenen **Dock-Lade-Vorspänne** (`D64OperationPreludeDialog`) zeigen
die animierte Datei `data/loader.gif` in der **rechten oberen Ecke** des
Splash-Fensters. Die bisherige Fortschrittsleiste und die Dark-/Light-Mode-
Gestaltung bleiben bestehen. Beim Einblenden startet die Animation, beim
Ausblenden wird sie gestoppt. Auch der separate **C64-Programmstart-Splash**
(`examples/__main__.py`) zeigt dieselbe Grafik oben rechts.

Die Datei wird neben `d64_dism.py` in `data/loader.gif` erwartet. Bei einer
verpackten Windows-Anwendung kann sie auch neben der EXE unter `data/loader.gif`
liegen; der existierende Bundle-Ordner wird ebenfalls berücksichtigt. **Die
benutzerseitige Grafik wird aus dem bestehenden Installationsverzeichnis
geladen und ist nicht in dieser Stage als neue Bilddatei enthalten.** Fehlt die
Datei oder ist das GIF nicht gültig, werden die ursprünglichen Splash-Screens
unverändert angezeigt, ohne Absturz.

Betroffene Module:
- `d64_dism.py`: operationale Lade-Splashs
- `examples/__main__.py`: separater Startup-Splash

## Prüfungen

- **76 gezielte Regressionstests erfolgreich**, einschließlich Stage 620,
  683–691 (relevante Module).
- Syntaxkontrolle der betroffenen Python-Module erfolgreich.
- `d64_dism.py` wurde für die Syntaxkontrolle mit einer temporären
  Normalisierung der bereits vorhandenen Python-3.15-`lazy`-Imports geprüft;
  die Originaldatei behält diese Imports bei.
- Native grafische Laufzeitprüfung unter Windows mit PyQt5 ist noch offen,
  da PyQt5 hier nicht installiert ist.
