# Stage 562 – Software Installer: Dock-Minimierung und Hintergrund-Fenster

**Verbindliche Basis:** Stage 561 (`d64_dism_stage561.zip`). Die Compiler-, Pascal- und bisherigen Installer-Funktionen bleiben unverändert.

## 1. Software-Installer-Dock beim Minimieren behalten

### Fehlerursache
Die bisherige Methode `ExplorerWindow._exclusive_tool_workspace_visibility_changed()` hat jedes `visibilityChanged(False)` als Schließen des Docks interpretiert. Qt/Windows kann das Signal auch beim Minimieren des Hauptfensters senden. Dadurch wurde `_restore_exclusive_tool_workspace()` irrtümlich aufgerufen, das Installer-Dock geschlossen und der vorherige Workspace wiederhergestellt.

### Korrektur

- Das einzige Installer-Dock ist jetzt `InstallerWorkspaceDock(QDockWidget)`.
- Seine `explicitCloseRequested`-Benachrichtigung entsteht über `closeEvent`, nicht über Sichtbarkeitsänderungen.
- Der Ansicht-Umschalter (`toggleViewAction`) kann das Dock ebenfalls ausdrücklich schließen.
- Bei `visibilityChanged(False)` wird **für das Installer-Dock** kein Workspace-Restore mehr durchgeführt.
- Beim `WindowStateChange` zurück aus dem minimierten Zustand prüft `_ensure_installer_workspace_after_restore()`, ob der Installer noch der aktive Workspace ist, und zeigt ihn bei Bedarf wieder an.
- Nach einem ausdrücklichen Schließen ist der Workspace-Snapshot gelöscht; die Wiederherstellung des Hauptfensters öffnet das Dock dann nicht erneut.
- Bei anderen Tool-Docks wird die bisherige Schließlogik beibehalten; die Minimierungsprüfung schützt auch sie vor einem unabsichtlichen Restore.

## 2. Dialog „Hintergrund Fenster“

Aufruf: **Software Installer → Einstellungen → Hintergrund Fenster**.

Der Dialog basiert auf `InstallerThemedDialog` mit eigener verlaufender Titelleiste, Dark-/Light-Mode-Unterstützung und denselben festen Maßen wie **Session Variablen**: **620 × 550 Pixel**. Die bedienbaren Inhalte liegen in einer ScrollArea; die Aktionsbuttons bleiben am unteren Rand sichtbar.

### Linker Bereich

- Checkbox `Hintergrund Fenster anzeigen`.
- GroupBox `Fenster`: RadioButtons `Standard`, `Eingerahmt`, `Kiosk`.
- GroupBox `Aussehen`: `Statische Farbe`, `Verlauf` mit **zwei** unabhängig wählbaren Farben sowie `Bild`.
- Der Bildpfad kann eingegeben oder mit `Durchsuchen` über einen Dateiauswahldialog gewählt werden. Pfadeingabe und Browse-Button sind nur im Bildmodus aktiv.
- Sämtliche ColorComboBoxen unterstützen Standardfarben und eigene Farben über Doppelklick auf das Eingabefeld (Windows-`Select Color`).

### Rechter Bereich – Text

- `Titel-Zeile`: `%ProductName%`, Font-Auswahl, ColorComboBox und Ausrichtung `Links`, `Mitte`, `Rechts`.
- `Version-Zeile`: `%ProductVersion%`, Font-Auswahl, ColorComboBox und Ausrichtung `Links`, `Mitte`, `Rechts`.
- `Fuß-Zeile`: `%Copyright% Alle Rechte vorbehalten.`, Font-Auswahl und ColorComboBox.

Die beiden Ausrichtungsgruppen sind unabhängig (getrennte Eltern-Widgets für ihre RadioButtons).

### Buttons und Speicherung

- **OK** serialisiert die aktuellen Werte und übergibt sie an den Installer-Projekteditor. Bei vorhandenen Projekten erfolgt sofort ein Schreibversuch der `.installer.json`-Datei.
- **Abbrechen** verwirft den aktuellen Dialogstand vollständig. Das Projekt wird nicht geändert.
- **Hilfe** öffnet den vorhandenen CHM-Viewer auf dem neuen Thema `Hintergrund Fenster`.
- Bei unbenannten Projekten wird beim Speichern nach dem Projektnamen gefragt; bei Abbruch bleibt der Projektstand als geändert markiert und kann später mit `Strg+S` gespeichert werden.

### JSON-Projektstruktur

Die Konfiguration wird als JSON-Zeichenkette in `InstallerProject.sections["Hintergrund Fenster"]` hinterlegt. `installer_background_settings.py` verwaltet die Vorgaben, prüft erlaubte Werte und serialisiert Version 1, beispielsweise:

```json
{
  "version": 1,
  "settings": {
    "enabled": true,
    "mode": "framed",
    "appearance": "gradient",
    "static_color": "#20385f",
    "gradient_start": "#2f72d6",
    "gradient_end": "#ffffff",
    "image_path": "",
    "title_text": "%ProductName%",
    "title_font": "",
    "title_color": "#ffffff",
    "title_align": "center",
    "version_text": "%ProductVersion%",
    "version_font": "",
    "version_color": "#ffffff",
    "version_align": "center",
    "footer_text": "%Copyright% Alle Rechte vorbehalten.",
    "footer_font": "",
    "footer_color": "#ffffff"
  }
}
```

Font-Daten werden aus Qt als `QFont.toString()` gespeichert. Die Zeichenketten `%ProductName%` usw. bleiben Platzhalter für spätere Setup-Generierung. Die tatsächliche Erzeugung eines Installer-EXE ist in dieser Stage noch nicht implementiert.

## 3. Geänderte Dateien

- `d64_dism.py`: Sichtbarkeits-/Close-Behandlung und Wiederherstellung des Installer-Docks.
- `software_installer.py`: `InstallerWorkspaceDock` und Dialoganbindung mit Projektpersistenz.
- `software_installer_dialogs.py`: neuer `InstallerBackgroundWindowDialog`, Theme-Styles und Schriftauswahl.
- `installer_background_settings.py`: neues Qt-unabhängiges Modell mit JSON-Validierung.
- `help/software_installer/`: neues HTML-Hilfethema plus Einträge in `.hhc`, `.hhk`, `.hhp` und `index.html`.
- `test_stage562.py`, `test_stage562_qt.py`: neue Regressionen.
- `test_stage554.py`: Erwartung an die neue Dock-Unterklasse angepasst; weiterhin genau ein Dock.

## 4. Windows-Praxistests (noch erforderlich)

1. Installer-Dock öffnen, IDE **minimieren und wiederherstellen** – Installer-Dock muss sichtbar bleiben; vorherige Docks bleiben ausgeblendet.
2. Dock über **X** schließen – vorheriger Workspace muss wieder erscheinen. Minimieren nach dem Schließen darf das Dock **nicht** erneut öffnen.
3. Dialog im Dark Mode öffnen und drei Fenster-Modi, drei Aussehen-Arten, Font-Auswahl und Farbdialoge testen.
4. Dialog abbrechen – keine Änderungen in der Projektdatei.
5. Dialog mit OK speichern und Projekt neu laden – alle Daten müssen wieder erscheinen.
6. CHM-Hilfe über „Hilfe“ auf das neue Thema navigieren.

Die hier verfügbaren automatisierten Tests validieren Quellstruktur, JSON-Modell und die Workspace-Callbacks unabhängig von Qt. Ein echter nativer PyQt5-/Windows-GUI-Test war in dieser Umgebung nicht möglich.
