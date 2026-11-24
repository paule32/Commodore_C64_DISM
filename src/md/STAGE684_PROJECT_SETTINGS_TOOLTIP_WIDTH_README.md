# Stage 684 – ToolTips im Projekt-Einstellungen-Dock begrenzen

**Verbindliche Basis:** `d64_dism_stage683.zip`.

## Verhalten

- Alle normalen Qt-ToolTips im Dock **Projekt-Einstellungen** werden auf die tatsächlich **sichtbare Breite des rechten Einstellungs-Panels** begrenzt. Die linke TreeList zählt nicht zur verfügbaren Tooltip-Breite.
- Unter **Windows → 32-Bit / 64-Bit** wird das gerade aktive `WindowsCompilerDirectorySettingsPage.stack` verwendet, unter **C=64** das aktive `C64CompilerSettingsPage.stack`.
- Eine horizontal abgeschnittene rechte Seite (äußerer Projekt-Einstellungen-Scrollbereich) wird über die globale Schnittmenge des Panel-Rechtecks mit dem Scroll-Viewport berücksichtigt.
- Die Breite wird **bei jedem Tooltip-Ereignis neu berechnet**. Änderungen an der Dockgröße, an Splittern und der ausgewählten Architektur wirken beim nächsten Hover.
- Lange Texte werden anhand der Font-Metrik und der verfügbaren Pixelbreite umbrochen. Lange, untrennbare Pfade/URLs werden nötigenfalls innerhalb des Tokens geteilt. Manuelle Zeilenumbrüche bleiben erhalten.
- HTML-Sonderzeichen werden für die Darstellung escaped. Vorhandene Rich-Text-Tooltips werden für die Neuumbruchberechnung in Plaintext umgewandelt.
- Der Event-Filter greift **nur im Projekt-Einstellungen-Dock** ein. Alle anderen Docks und ToolTips behalten ihr bisheriges Verhalten. Die Funktion verändert keine Projektwerte, Stylesheets oder Compileroptionen.

## Änderung

- `project_settings_tooltips.py` (neu): Pixellängenabhängiger Textumbruch sowie ein auf das Settings-Dock begrenzter `QApplication`-Eventfilter. Berücksichtigt auch `Qt.ToolTipRole` von Einträgen in Item-Views.
- `d64_dism.py`: Filter einmalig am Ende von `_ensure_project_settings_dock` aktivieren.
- `test_stage684.py` (neu): 5 gezielte Prüfungen für Pixelbreite, lange Tokens, Zeilenumbrüche, HTML-Sonderzeichen und die Einbindung.

## Verifikation

`python -m pytest -q test_stage684.py`

Die neue ToolTip-Logik lässt sich hier ohne PyQt5 nur in den unabhängigen Textformatierungsfunktionen testen. Der visuelle GUI-Test unter Windows/Qt5 bleibt erforderlich.
