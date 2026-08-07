# Projekt-Kontextaktion „Neu“ und Hilfe-Toolbar

## Änderungen

- `Neu` ist der erste Eintrag im Kontextmenü der Projekt-TreeList.
- Die angeklickte Kategorie bestimmt Dateityp, Standarderweiterung und Editor.
- Neue Dateien heißen `Unbenannt_<nummer>.<erweiterung>`.
- Projektknoten und vorhandene Dateien werden vor der Namensvergabe geprüft.
- Character-, Paletten-, Char-Screen- und Pixel-Screen-Dateien werden mit
  gültigen leeren Binärdaten erzeugt.
- Der passende Editor wird direkt nach dem Anlegen geöffnet.
- Eine adaptive Hilfe-Schaltfläche steht links neben `Zoom +`.
- Der Projekt-Öffnen-Button ist im Dark Mode explizit dunkel gestaltet.

## Root-Schutz

Die neue Aktion verändert den bestehenden Schutz nicht. `Umbenennen` und
`Löschen` bleiben für alle Kategorie-Root-Knoten deaktiviert.
