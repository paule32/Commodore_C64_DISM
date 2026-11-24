# Stage 693 – Turbo-Hilfe-Umbenennen: Überschreibbestätigung

Basis: `d64_dism_stage692.zip`.

## Konflikt beim Umbenennen

Die Kontextmenüpunkte **Datei umbenennen** und **Ordner umbenennen**
prüfen, ob der gewünschte Zielname im Dateisystem bereits existiert.
In diesem Fall erscheint eine an den aktiven Dark-/Light-Mode angepasste
`QMessageBox` mit **OK**, **Abbrechen** und **Hilfe**:

- **OK** bestätigt das Ersetzen der bestehenden Zieldatei bzw. des
  bestehenden Zielverzeichnisses einschließlich seines bisherigen Inhalts.
  Die Quelle wird unter dem Zielnamen verschoben. Der gewählte Projekteinstieg
  und die Pfade seiner untergeordneten Einträge werden aktualisiert; veraltete
  Projektverweise auf das ersetzte Ziel werden entfernt.
- **Abbrechen** verwirft die Umbenennung. Der erste Namensdialog wurde beim
  Erscheinen dieser Abfrage bereits geschlossen; beide Dialoge sind anschließend
  geschlossen und Dateien wie Projektbaum bleiben unverändert.
- **Hilfe** öffnet den integrierten **CHM-Viewer** mit einem passenden
  Suchkontext. Die Überschreibabfrage bleibt aktiv.

Die bereits existierende zentrale `_create_message_box()`-Routine sorgt
für das einheitliche Farbschema. **Abbrechen** ist die vorausgewählte Taste.

## Sichere Dateioperation

`turbo_help_project_tree.rename_help_path()` verwaltet eine vorübergehende
Sicherung des Zielpfades. Schlägt die eigentliche Umbenennung fehl, wird das
ursprüngliche Ziel wiederhergestellt. Eine erfolgreiche Verzeichnis-Ersetzung
entfernt die bisherigen Dateien und Unterverzeichnisse des Zielordners.
Dateien können keine Ordner ersetzen und umgekehrt. Unabgespeicherte
Änderungen eines offenen Ziel-Tabs verhindern das Überschreiben. Offene,
unveränderte Ziel-Tabs werden danach geschlossen; offene Quell-Tabs erhalten
den neuen Dateipfad. Falls die alte Zieldatei das Hauptdokument war, wird die
Hauptmarkierung auf die umbenannte Quelldatei übertragen.

Kann eine vorübergehende Sicherung nach erfolgreichem Ersetzen nicht entfernt
werden, bleibt diese zur manuellen Wiederherstellung erhalten und Python gibt
eine Warnung mit dem Dateipfad aus.

## Tests

`python -m pytest -q test_stage693.py test_stage685.py test_stage686.py test_stage687.py test_stage688.py test_stage689.py test_stage690.py test_stage691.py test_stage692.py`

Die PyQt5-Dialogdarstellung und CHM-Aufrufe benötigen zusätzlich einen
visuellen Windows-Laufzeittest; im Linux-Container wird die UI mit kontrollierten
Testdoubles ausgeführt.
