# Stage 665 – Turbo-Hilfecompiler: Zeilennummern, Minimap und weiterer Texteinzug

**Verbindliche Basis:** Stage 664. Alle bisherigen Funktionen (F2, Tab-Wechsel mit
Speicherprüfung, projektbezogene `.hlp`, numerische Themen-IDs) bleiben erhalten.

## 1. Quelltexteditor `.thlp`

Neues Modul `turbo_help_editor_widgets.py`:

- `TurboHelpSourceEditor(QPlainTextEdit)`: direkter Ersatz des bisherigen
  `QPlainTextEdit` in jedem `.thlp`-Tab. Deshalb bleiben die bisherigen
  Dokument-APIs (`document()`, `setPlainText`, `toPlainText`, `setFocus`,
  `textCursor` usw.) kompatibel.
- `TurboHelpLineNumberArea`: linker Zeilennummern-Gutter mit erster Zeile 1,
  Markierung der aktuellen Zeile, vertikaler Scrollsynchronisierung und
  dynamischer Breite ab 1.000/10.000/… Zeilen.
- `TurboHelpMiniMap`: 92 Pixel breite Quelltextübersicht rechts, skaliert auf
  die Dokumentlänge, mit markiertem sichtbarem Scrollbereich. Ein Klick oder
  Ziehen in der Minimap positioniert den echten Editor-Scrollbalken. Ein
  Umbruch innerhalb langer THLP-Quellzeilen wird deaktiviert (`NoWrap`).
- Beide Seitenleisten sind **Kind-Widgets des Editierfensters**, deren Platz
  mittels `setViewportMargins` reserviert wird. Die Tabs enthalten weiterhin
  direkt den editierbaren `QPlainTextEdit`, kein Proxy- oder Wrapper-Objekt.
- Erzeugt wird der Editor in `TurboHelpEditor._append_tab()` aus
  `turbo_help_gui.py`, also sowohl bei "Neu" als auch beim Öffnen jeder `.thlp`.

## 2. Turbo-Vision-Hilfefenster: Text um eine DOS-Spalte weiter rechts

Datei `d64qt5/d64_turbo_help_window.hpp`: Der berechnete Einzug lautet nun
`gridCellWidth_ * 3 - 2` statt `gridCellWidth_ * 2 - 2`.
Damit beginnt der Text **in der vierten DOS-Blockspalte** (einschließlich
Fensterrahmen). Die erste Spalte enthält den Außenrand, dazwischen liegen
zwei freie Blockspalten in Cyan. Die Zwei-Pixel-Rahmenbreite wird bei der
Berechnung berücksichtigt; die aktuelle Konsolen-Zellbreite wird verwendet.
Dies gilt auch nach Schriftgrößenwechsel und für die Meldung
"Hilfethema nicht gefunden". Keine Änderungen an Schatten (+5/+5 Pixel),
gelbem Rahmen (2 Pixel), Titel `Hilfe:  <Hilfethema>` oder Grid-Move/Resize.

## 3. Windows-Build

Für den neuen Quelltexteditor reicht es, die Python-Module zu kopieren.
Für die **native** geänderte Textposition muss `libd64_qt5.dll` neu gebaut
werden:

```bat
build_and_deploy_dbase_editor_stage665.bat
```

Es wird keine separate `turbo_help_host.exe` erstellt. Das `.hlp`-Dateiformat
und dessen Inhalt ändern sich in Stage 665 **nicht**; ein erneuter F2-Lauf
ist deshalb nicht erforderlich.

## 4. Verifikation

- `python -m py_compile turbo_help_gui.py turbo_help_editor_widgets.py`: OK.
- 106 Tests aus Stage 650–659 und 661–665: erfolgreich.
- Neue Funktionstests (`test_stage665.py`) prüfen u. a. den Gutter-Breitenwechsel
  und die bidirektionale Minimap/Scrollbalken-Geometrie mit echten Funktionen
  aus dem Editor-Quelltext.
- ZIP-Archiv vollständig und CRC geprüft.
- **Nicht hier getestet:** visuelles Qt5-/Windows-Rendering, Native-DLL-Build.
  Die GUI sollte dort mit mehrzeiligen `.thlp`-Dateien geprüft werden.
