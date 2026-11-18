# Stage 598 – Projekt-Auswahl als QToolButton/QMenu

**Verbindliche Grundlage:** `d64_dism_stage597.zip`.

## Änderung

Die beiden Projekt-Auswahlarten im Projekt-Informationen-Dock verwenden statt
`QComboBox` jetzt `ProjectTargetMenuButton`:

1. `Projektname:` oberhalb der TreeList (aktives EXE-/DLL-Ziel).
2. Rechte Spalte `Projekt` neben Dateien, Pascal-Modulen/-Units und dBASE-Modulen.

`ProjectTargetMenuButton` ist ein `QToolButton` mit rechter Dropdown-Anzeige
(standardmäßiger Qt-`menu-indicator`, `InstantPopup`) und separatem `QMenu`.
Die Menü-Popup-Geometrie hängt **nicht** von der Breite der TreeList-Zelle ab:
`QFontMetrics.horizontalAdvance()` misst den längsten vollständigen Menüeintrag,
und die Menübreite erhält einen passenden Mindestwert (bis zur Bildschirmbreite).
Bei zu schmaler Zelle kürzt **nur die Button-Beschriftung** den Text mit `…`;
der Tooltip zeigt den vollständigen Wert an.

Die **Popup-Schrift ist um exakt 1 pt größer** als die Schrift des jeweiligen
Buttons. Der Menü-Stil (Dark/Light) wird bei jedem Öffnen anhand des
Hauptfenster-Themas aktualisiert. Der ausgewählte Eintrag ist markiert.
Ein `&` in einem Projektnamen wird nicht als Menü-Tastenkürzel interpretiert.

Die für das Projektmodell benötigte bisherige ComboBox-Schnittstelle
(`addItem`, `itemData`, `findData`, `setCurrentIndex`, `currentData`,
`currentIndexChanged`, `blockSignals`) ist bewusst beibehalten. Es gibt
**keine Änderungen** am `.pro`-Format, der Modul-Zuordnung oder der
Build-Selektion aus Stage 597.

Der QMenu-Parent ist das Hauptfenster (nicht der Tree-Viewport). Als eigenes
Qt-Popup kann das Auswahlmenü über Dock-/TreeList-Grenzen ragen. Beim Löschen
eines Zell-Buttons wird das Fenster-Menü mit `deleteLater()` freigegeben.

## Dateien

- **Neu:** `project_target_menu.py` – wiederverwendbarer Qt-Dropdown-Button.
- **Geändert:** `d64_dism.py` – Projektname und TreeList-Projektspalte,
  aktualisierte Dark-/Light-Styles.
- **Neu:** `test_stage598.py` – Tests für Menüs, Schriftgröße, Breite,
  Wertebindung, Farbe, Zeichen `&` und Lebensdauer.

## Teststatus

- `test_stage598.py`, `test_stage597.py`, `test_stage596.py`: **28 Tests bestanden**.
- `test_stage595.py`, `test_stage594.py`, `test_stage593.py`, `test_stage592.py`:
  **40 Tests bestanden** (separater Lauf).
- Gesamt: **68 separat nachgewiesene Tests**, einschließlich 9 neuer Stage-598-Tests.
- Python-Syntax geprüft. `d64_dism.py` benötigt Python 3.15 für die
  `lazy import`-Syntax; zur lokalen Syntaxprüfung wurden diese Imports
  nur im AST-Prüftext temporär in normale Imports umgewandelt.
- **Nicht durchgeführt:** native Windows-/PyQt5-Interaktion (PyQt5 im
  Test-Container nicht installiert). Insbesondere Positionierung und
  Darstellung des Dropdown-Pfeils sollten unter Windows geprüft werden.

## Windows-Test

1. Projekt-Informationen-Dock öffnen; obere Projektauswahl anklicken.
2. Sehr lange Projektnamen in Pascal DLL und dBASE DLL setzen.
3. Menü über eine schmale Projekt-Spalte öffnen: kompletter Name sollte
   im Menü sichtbar sein, obwohl der Button den Text kürzt.
4. Datei-Zuordnung wechseln; Projekt speichern, erneut laden und prüfen.
5. Dark/Light wechseln, Menü erneut öffnen und Schriftgröße prüfen.
6. ESC im offenen Menü darf Zuordnungen nicht verändern.
