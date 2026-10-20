# Stage 438: Werkzeuge als wiederherstellbarer Vollflächen-Dock-Arbeitsbereich

**Verbindliche Basis:** `d64_dism_asm_437.zip`

## Vollflächen-Arbeitsbereich

Für die folgenden Menüpunkte wird vor dem Anzeigen des Werkzeug-Docks ein gemeinsamer Snapshot der Hauptfenster-Docks gespeichert. Die zuvor sichtbaren Docks werden verborgen und die zentrale Dokumentansicht temporär auf Platzbedarf null gesetzt:

- Werkzeuge → C64 Character-Editor
- Werkzeuge → C64 Paletten-Editor
- Werkzeuge → C64 Text-Bildschirm-Editor
- Werkzeuge → C64 Pixel-Bildschirm-Editor
- Werkzeuge → Localize PO->MO
- Werkzeuge → Doxygen Dokumentation
- Werkzeuge → HTML Editor

Nach Schließen des aktiven Werkzeug-Docks werden das gespeicherte `QMainWindow.saveState()`, die ursprüngliche Sichtbarkeit jedes Docks sowie Minimal-/Maximalmaße und Sichtbarkeit des zentralen Widgets wiederhergestellt. Ein zuvor versteckter Dock bleibt versteckt; frühere sichtbare Docks erscheinen erneut. Wechselt der Nutzer direkt zwischen mehreren Werkzeugen dieser Gruppe, bleibt **ein** Snapshot des ursprünglichen Zustands aktiv. Dies verhindert eine Wiederherstellung des Zwischenzustands statt der ursprünglichen Arbeitsfläche.

Die Position und Größe des Hauptfensters werden nicht absichtlich verändert; eventuelle unbeabsichtigte Abweichungen durch Qt-Docklayout-Rekonstruktion werden für nicht maximierte Fenster korrigiert. Für C64-Editoren bleiben die `_confirm_discard`-Abfragen beim Schließen erhalten; der alte Sprite-Builder-Lebenszyklus wird nicht umgebaut.

## Resourcen Builder

Werkzeuge → Resource Builder (`alias_builder`) nutzt dieselbe Snapshot-/Restore-Logik, jedoch bleibt das Dock `Projekt/Informationen` sichtbar. Bei rechts angedocktem Projekt erscheint der Builder links; bei links angedocktem Projekt rechts. Nur diese beiden Docks belegen die Arbeitsfläche. Nach Schließen wird auch hier der ursprüngliche Dockzustand restauriert.

## Technische Umsetzung

- `d64_dism.py`: `_activate_exclusive_tool_workspace()`, `_expand_exclusive_tool_workspace()`, `_exclusive_tool_workspace_visibility_changed()`, `_restore_exclusive_tool_workspace()` und Anbindung an die betroffenen Menüaktionen sowie C64-Tool-Docks.
- `HTML Editor` erhält einen `QScrollArea`-Host ohne große erzwungene Mindestmaße.
- `Localize` und `Doxygen` verwenden den gemeinsamen Lifecycle statt früherer Sonderbehandlungen mit teilweise sichtbaren Projekt-/Protokoll-Docks.
- `test_stage438_tool_workspaces.py`: Fünf Simulationstests (Sichtbarkeit und Layout, direkter Werkzeugwechsel, Builder links/rechts, ursprünglich unsichtbares Projekt, Menüanbindung).

## Prüfungen

- `py_compile` für die Hauptdatei und Testdatei: erfolgreich.
- 27 Regressionstests Stage 431–434: bestanden.
- 14 Regressionstests Stage 435–436: bestanden.
- 6 Regressionstests Stage 437 und 5 neue Stage-438-Tests: bestanden.
- **52 Tests insgesamt**. Die Gruppen wurden einzeln ausgeführt, weil der große kombinierte AST-Testlauf in dieser Umgebung zu lange benötigt.
- **Qt-UI-Test unter Windows/PyQt5 steht noch aus**. Die neuen Dock-Lebenszyklus-Tests verwenden simulierte Qt-Docks und testen den Python-Code ohne echte GUI.
