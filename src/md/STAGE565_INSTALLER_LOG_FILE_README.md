# Stage 565 – Software Installer: Log-Datei

Verbindliche Basis: `d64_dism_stage564.zip`.

- Der bestehende Button **Einstellungen → Log-Datei** öffnet statt des generischen
  Texteditors den neuen `InstallerLogFileDialog`.
- Dialog mit gleicher Geometrie wie Systemanforderungen: 620 × 550 Pixel,
  Theme und Schwarz-Weiß-Titelverlauf im Dark Mode durch `InstallerThemedDialog`.
- Checkbox **Log-Datei anlegen**; darunter eingerückt **Dateiname:** mit
  `%TempFolder%\%ProductName% Setup Log.txt`, **Schreibmodus:** und die
  exklusiven RadioButtons **Anhängen** / **Überschreiben**.
- Bei deaktivierter Checkbox sind die untergeordneten Eingabeelemente deaktiviert.
- OK übernimmt eine versionierte JSON-Konfiguration in
  `InstallerProject.sections["Log-Datei"]` und speichert wie die bestehenden
  Einstellungsdialoge. Abbrechen verwirft alle Dialogänderungen.
- Hilfe ruft den vorhandenen Installer-CHM-Viewer mit `Log-Datei` auf. Das
  Hilfethema `log_datei.html` ist in Index/HHP/HHC/HHK eingetragen.
- Die Dialogdaten bleiben von der bestehenden Wizard-Seite 7 (`installation_log`)
  getrennt, damit keine nicht angeforderte Wizard-Logik verändert wird.
- Der Dialog konfiguriert das spätere Setup; die tatsächliche Erzeugung und
  Beschreibung der Log-Datei während einer Installation sind nicht implementiert.
- Native GUI-Tests hängen von PyQt5 ab; in der Ausführungsumgebung ist PyQt5
  nicht installiert. Modell-/Strukturtests und ZIP-Prüfung werden separat ausgeführt.
