# Stage 436 – Formular-Designer, CHM-Titelleiste und Toolbar-Hover

**Verbindliche Basis:** `d64_dism_asm_435.zip`

## Änderungen

### Formular-Designer
- Das Fenster `dBase Formular - Designer` verwendet nun eine spezielle `DockTitleBar` mit **nur einer Schließen-Schaltfläche**.
- Die bisherige Schaltfläche zum Abdocken/Maximieren wird für dieses Dock nicht angezeigt; die übrigen Dock-Fenster bleiben unverändert.
- Über `ExplorerWindow._close_dbase_form_designer_pair()` werden **Designer-Dock und Eigenschaften-Dock** geschlossen. Die vorhandene Workspace-Wiederherstellung bleibt aktiv.

### CHM Viewer
- Neue `ChmViewerTitleBar` mit drei weiterhin vorhandenen Buttons: **Minimieren, Maximieren/Wiederherstellen und Schließen**.
- Im Dark-Mode QPainter-Titelhintergrund mit horizontalem Verlauf **#000000 → #707070**, im Light-Mode hell.
- Rahmen in Dark- und Light-Mode **3 px** via `QDialog#chm_viewer_dialog`.
- Eigene Titelleiste, verschiebbar per Drag, Maximieren per Doppelklick; `QStatusBar`-Sizegrip ermöglicht weiterhin Größenänderungen.
- Die vorhandene CHM-Navigation, gespeicherte Fenstergeometrie und CHM-Webinhalte bleiben erhalten.

### Hauptfenster Toolbar
- Die drei rechten Toolbar-Buttons **Help**, **Lupe +**, **Lupe −** erhalten beim Hover einen **grauen Hintergrund (#808080)**.
- Bei aktivem Dark-Mode werden ihre Symbolstriche beim Hover **schwarz (#000000)**, außerhalb des Hovers weiterhin hell dargestellt.
- Die Hover-Icons werden über den existierenden `ExplorerWindow.eventFilter` umgeschaltet und beim Theme-Wechsel synchronisiert.

## Dateien
- `d64_dism.py`: überarbeitet
- `test_stage436_form_chm_toolbar.py`: neu
- `STAGE436_FORM_DESIGNER_CHM_TOOLBAR_DARKMODE.md`: neu

## Überprüfung
- `python -m py_compile d64_dism.py ...`: erfolgreich
- Automatische Tests aus Stage 431–436: **41/41 bestanden**
- Windows-/PyQt5-Sichtprüfung muss auf dem Zielsystem durchgeführt werden; PyQt5 steht in der Testumgebung nicht zur Verfügung.
