# Stage 558 – Software Installer: Sprachen und Windows-Zielsysteme

## Basis

Stage 557 (`d64_dism_stage557.zip`) ist die unveränderte Projektbasis für diese Erweiterung. Die bestehenden fünf Wizard-Seiten, das einzelne Installer-Dock und die Installer-JSON-Dateien bleiben erhalten.

## Wizard Seite 6 – Sprachen

- Dieselbe Dialoggeometrie **780 × 620 px** wie auf den Seiten 1 bis 5, einschließlich 140 px Bildbereich, Abstand, Dark-/Light-Styling und Titelverlauf.
- CheckListBox mit Windows-Locale-Sprachen; deutsche Anzeigenamen und BCP-47-Sprachkennungen.
- Anfangs gewählt: **Deutsch** (`de-DE`) und **Englisch** (`en-US`).
- Darunter eine Standardsprachen-ComboBox, die automatisch ausschließlich angehakte Sprachen enthält. Vorgabe **Deutsch**; bei Abwahl erfolgt eine gültige Neuauswahl. Es muss mindestens eine Sprache ausgewählt sein.
- Persistenz in `InstallerProject.general`:
  - `languages`: JSON-kodierte Liste in einem String, z. B. `["de-DE","en-US"]`.
  - `default_language`: z. B. `de-DE`.

## Wizard Seite 7 – System Anforderungen

- Ebenfalls dieselbe Dialoggeometrie.
- Drei Checkboxen mit persistenten Schaltern: `support_uninstall`, `installation_log`, `warn_administrator` (Werte `true`/`false`).
- Windows-Systembaum mit Checkboxen in allen Ebenen. `QTreeWidget.itemChanged` setzt alle untergeordneten Knoten bzw. Blätter auf den Elternzustand. Eine eigene Aktualisierung der Eltern meldet bei gemischter Auswahl `Qt.PartiallyChecked`. Eine Reentrancy-Sperre verhindert rekursives Umschalten.
- Zielkennungen für Windows XP bis Windows 11 sowie Windows Server 2008 R2 bis 2025. Es handelt sich um **Auswahldaten**, keine Zusage, dass der spätere Setup-Build jede Version technisch unterstützt.
- Vorgabe: Windows 10 und Windows 11. Es muss mindestens eine Windows-Version ausgewählt sein.
- `windows_versions`: JSON-kodierte Liste der gewählten **Blatt-IDs** in einem String. Gruppenknoten werden bei Laden aus den Blattzuständen rekonstruiert.
- Nur diese letzte Seite beschriftet den zweiten Navigationsknopf mit **Fertigstellen**. Seite 5 und 6 haben **Weiter >**.

## Implementierung

- `installer_wizard_options.py`: statische Sprach-/OS-Kataloge, sichere JSON-Kodierung und -Dekodierung.
- `software_installer_dialogs.py`: zwei neue Wizard-Dialoge und das Baum-Checkbox-Verhalten.
- `software_installer.py`: Wizard-Ablauf Seite 1 bis 7; Speichern aller Werte im bisherigen `general`-Mapping.
- `help/software_installer/*`: CHM-Quellen für Wizard Seite 6 und 7.
- `test_stage558.py`, `test_stage558_qt.py`: neue Regressionstests und separate native PyQt5-Oberflächentests.

Die Projektformatversion **1** bleibt unverändert; die neuen Werte sind als Strings gespeichert und erfordern keine Migration bestehender Projekte.

## Grenzen

Die Sprachliste ist eine statische Auswahl von Windows-Locale-Kennungen und fragt nicht ab, welche Sprachpakete auf einem konkreten PC installiert sind. Sie erzeugt noch keine Übersetzungen. Der Versionsbaum wird später für echte OS-Kompatibilitätsprüfungen in der Setup-Runtime benötigt. Native Qt-Tests können in einer Windows-Umgebung mit PyQt5 und `QT_QPA_PLATFORM=offscreen` ausgeführt werden.
