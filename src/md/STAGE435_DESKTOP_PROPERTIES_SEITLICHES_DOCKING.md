# Stage 435 – Desktop Properties horizontal neben Projekt/Informationen

## Verbindliche Basis
`d64_dism_asm_434.zip` (unveränderte übrige Projektdateien übernommen).

## Anforderungen und Umsetzung

- **Ansicht → Einstellungen → Desktop** öffnet weiterhin das Dock `Desktop Properties`.
- Steht das Dock `Projekt/Informationen` **rechts**, belegt `Desktop Properties` den freien Bereich **links**. Steht Projekt/Informationen **links**, öffnet `Desktop Properties` **rechts**.
- Das Desktop-Dock akzeptiert während des Workspaces nur den Dockbereich **gegenüber** dem Projekt-Dock. Es wird nicht mit Projekt/Informationen vertikal gestapelt. Wechsel der Projektseite bewirkt eine entsprechende Neuanordnung.
- Das Dateisystem-Dock wird nur für den geöffneten Desktop-Workspace ausgeblendet und beim Schließen gemäß seinem vorherigen Sichtbarkeitszustand restauriert. Projekt/Informationen und das Protokoll bleiben während der Desktop-Einstellungen sichtbar.
- Die ursprüngliche feste Dock-/Panel-Mindestgröße `720 × 500` ist entfernt. Inhalte bleiben über die bestehende QScrollArea erreichbar, wenn der Dockbereich schmal wird.
- Die vorherigen `resizeDocks`-Anforderungen mit **100000 Pixeln** und der **vertikale** Vergrößerungsaufruf sind entfernt. Das Dock beansprucht gezielt die verbleibende horizontale Breite.
- Die Hauptfenstergeometrie (Position und Größe) wird beim Öffnen, beim Dock-Reflow sowie beim Verlassen des Desktop-Workspaces gesichert; maximierte und Vollbildfenster werden dabei nicht per `setGeometry()` verändert.
- Keine Änderung an der Fenstergeometrie bzw. Dock-Position des Projekt/Informationen-Docks durch eigene Positionierungsvorgaben.

## Betroffene Datei
- `d64_dism.py`

## Tests
- `test_stage435_desktop_properties_side_docking.py` (9 Tests): Zuordnung links/rechts, Reflow nach Projekt-Seitenwechsel, kein vertikales Stapeln, schwebende Fenster, Mindestgröße, vorübergehende Ausblendung des Dateisystems und Schutz der Hauptfenstergeometrie.
- Regressionen aus Stage 431–434 mitgetestet: Insgesamt **36 Tests bestanden**.
- Python-Syntaxprüfung mit `py_compile` erfolgreich.
- Qt-/Windows-Sichtprüfung muss noch auf dem Zielsystem durchgeführt werden (PyQt5 steht in der Testumgebung nicht zur Verfügung).
