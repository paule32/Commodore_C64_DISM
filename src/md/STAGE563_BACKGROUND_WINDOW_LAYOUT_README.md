# Stage 563 – Software Installer: Dialog „Hintergrund Fenster“ Layout

**Verbindliche Basis:** vom Benutzer hochgeladene `d64_dism_stage562(1).zip` (Stage 562).

## Layoutkorrektur

Änderung nur an `InstallerBackgroundWindowDialog` in `software_installer_dialogs.py`:

- Rechts in der GroupBox **Text** haben **Titel-Zeile**, **Version-Zeile** und **Fuß-Zeile** jeweils eine eigenständige, über die gesamte verfügbare GroupBox-Breite gehende Eingabezeile.
- Die zugehörigen **Schriftart-Buttons** und **ColorComboBoxen** stehen jeweils in einer separaten Zeile unterhalb der Eingabe. Der Font-Button ist lesbar beschriftet (**Aa  Schriftart**) und nicht mehr auf 32 Pixel zusammengedrückt.
- Die Farbauswahl erhält den restlichen verfügbaren horizontalen Platz der Optionszeile.
- Die linke Container-Spalte hat keine zusätzlichen Innenabstände mehr. Damit beginnen links **Fenster** und rechts **Text** an derselben Oberkante.
- Die linke Spalte wird wie die rechte über die ganze verfügbare Höhe aufgezogen. **Aussehen** füllt die Resthöhe und schließt unten bündig mit **Text** ab.
- Dialoggröße, feste Breite der linken Spalte, RadioButtons, Signale, Farb- und Schrift-Dialoge sowie JSON-Projektformat bleiben erhalten.

## Prüfung

- `python -m py_compile software_installer_dialogs.py test_stage563.py test_stage563_qt.py`
- `python -m unittest test_stage563 test_stage562 test_stage562_qt test_stage563_qt`
- Die beiden Qt-Offscreen-Testmodule setzen PyQt5 voraus. Falls die Bibliothek fehlt, werden sie übersprungen.
- Sichtkontrolle unter Windows (Light und Dark Mode) bleibt erforderlich.

## Geänderte und ergänzte Dateien

- **Geändert:** `software_installer_dialogs.py`
- **Neu:** `test_stage563.py`, `test_stage563_qt.py`, `STAGE563_BACKGROUND_WINDOW_LAYOUT_README.md`

Alle anderen Inhalte des Stage-562-ZIP bleiben unverändert.
