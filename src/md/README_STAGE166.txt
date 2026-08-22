Stage 166 – Bearbeiten-Menü / Undo / Redo / Zwischenablage
==========================================================

Anforderung
-----------
- Code-Editoren: CTRL+Z = Rückgängig.
- Code-Editoren: CTRL+Y = Wiederherstellen.
- Neues Hauptmenü "Bearbeiten".
- Menüeinträge in dieser Reihenfolge:
  1. Rückgängig
  2. Wiederherstellen
  3. Separator
  4. Kopieren
  5. Einfügen
  6. Ausschneiden

Umsetzung
---------
- SourceTextEdit behandelt CTRL+Z und CTRL+Y zusätzlich explizit.
- Zentrale QAction-Objekte im Hauptfenster:
  - Rückgängig      CTRL+Z
  - Wiederherstellen CTRL+Y
  - Kopieren        CTRL+C
  - Einfügen        CTRL+V
  - Ausschneiden    CTRL+X
- Das Bearbeiten-Menü steht zwischen Datei und Ansicht.
- Aktionen werden an das aktuell fokussierte Text-Widget geroutet; falls kein
  Text-Widget den Fokus besitzt, wird der aktive Editor des aktuellen Dokuments
  verwendet.
- Read-only-Editoren erlauben Kopieren, aber kein Undo/Redo/Einfügen/Ausschneiden.
- Beim Öffnen des Bearbeiten-Menüs werden Undo-/Redo-/Selection-/Clipboard-Zustand
  neu ausgewertet und die Einträge entsprechend aktiviert/deaktiviert.

Basis-Hinweis
-------------
Die gewünschte Basis heißt Stage 165. In der verfügbaren Dateiablage war zum
Zeitpunkt dieser Änderung jedoch kein separates Stage-165-ZIP/README vorhanden.
Der jüngste konkret materialisierbare d64_dism.py-Stand ist Version 40 und trägt
intern Stage 164. Die Änderung wurde deshalb streng additiv auf diesen jüngsten
vorhandenen Stand gesetzt. Ein portabler Unified-Diff mit Stage165/Stage166-
Pfadnamen liegt zusätzlich bei.

Prüfungen
---------
- python -m py_compile d64_dism.py: OK
- 15/15 Stage-166-Quellprüfungen: OK
- Alle ursprünglichen Stage-164-Zeilen im neuen d64_dism.py in gleicher
  Reihenfolge erhalten: OK
- Alle übrigen 38 Dateien des Stage-164-Pakets byte-identisch erhalten: OK
- Native PyQt5-GUI-Ausführung: nicht verfügbar (PyQt5 im Container nicht installiert)
