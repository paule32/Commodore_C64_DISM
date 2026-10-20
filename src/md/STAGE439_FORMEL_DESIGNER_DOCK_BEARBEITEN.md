# Stage 439 – Formel-Designer: Vollflächen-Dock und Hauptmenü »Bearbeiten«

**Verbindliche Basis:** `d64_dism_asm_438.zip`

## Docking / Arbeitsbereich

Beim Aufruf von **Lernen → Mathe → Formel-Designer** wird der gemeinsame,
reversible Dock-Snapshot aus Stage 438 vor dem Anzeigen aktiviert:

- Vorher sichtbare QMainWindow-Docks ausblenden und deren Sichtbarkeit und
  Dock-Zustand speichern.
- Zentralen Editor vorübergehend ausblenden; Designer nutzt die gesamte freie
  Dock-Fläche, ohne künstliche Hauptfenster-Vergrößerung.
- Beim Schließen die ursprünglichen Docks und die Hauptfenstergeometrie wieder
  herstellen; zuvor versteckte Docks bleiben versteckt.
- Beim Wechsel zwischen Werkzeugen wird der ursprüngliche Snapshot beibehalten.
- Die bestehende Anbindung unter »Ansicht → Zoom« bleibt erhalten.

## Hauptmenü »Bearbeiten«

- **Rückgängig / Wiederherstellen:** Verknüpfung mit dem bereits vorhandenen,
  strukturellen Formel-History-Stack. Nur aktiv, wenn der jeweilige Verlaufsschritt
  möglich ist.
- **Kopieren / Ausschneiden:** Nur aktiv, wenn ein Formelobjekt ausdrücklich
  ausgewählt wurde (nicht bereits bei einem bloßen Texteingabecursor).
- **Einfügen:** Nur aktiv bei explizit gewähltem Ziel und gültigen strukturierten
  Formeldaten mit MIME `application/x-d64-formula-node+json` im Clipboard.
  Fremder reiner Text berechtigt nicht zum Einfügen.
- Die Hauptmenüaktionen werden an die Formel-Designer-Operationen weitergereicht,
  solange dessen Dock sichtbar ist. Sonst bleiben die Texteditor-Operationen
  unverändert.
- Auswahl, Formeländerung, Undo/Redo, Clipboard-Änderung und Öffnen/Schließen
  synchronisieren den Menüzustand. `Strg+C` im Formelfeld wird unterstützt.

## Dateien

- `d64_dism.py` – erweitert
- `test_stage439_formula_designer_workspace_edit_menu.py` – neu
- `STAGE439_FORMEL_DESIGNER_DOCK_BEARBEITEN.md` – neu

## Tests

- Stage 431–434: 27 Tests
- Stage 435: 9 Tests
- Stage 436–437: 11 Tests
- Stage 438–439: 13 Tests
- **Insgesamt 60 Tests erfolgreich**, in getrennten Prozessen ausgeführt.
- Syntaxprüfung von `d64_dism.py` erfolgreich.

**Einschränkung:** Die Laufzeitdarstellung unter Windows/PyQt5 wurde hier nicht
visuell verifiziert; die Tests verwenden Codeanalyse und Qt-freie Simulationen.
