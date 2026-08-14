# Datei-Öffnen-Arbeitsverzeichnis – Stage 32

Stage 32 baut auf Stage 31 auf.

## Verhalten

Der zuletzt im eigenen `ProjectOpenFileDialog` angezeigte Ordner wird nach dem
Schliessen des Dialogs immer in `ExplorerWindow.current_directory` übernommen.
Das gilt für:

- Öffnen
- Abbrechen
- Schliessen über die Fenster-Titlebar

Die Übernahme erfolgt unmittelbar nach `dialog.exec_()` und vor der Prüfung des
Dialogresultats.

Dadurch verwenden die bestehenden dBase-Pfade automatisch diesen Ordner:

- PE32/PE32+-Ausgabe beim internen Assemble/Link
- Suche der bereits erzeugten EXE durch den Start-Button
- `cwd` des gestarteten Prozesses
- nächster Start des eigenen Datei-Öffnen-Dialogs

Wenn im unteren Dateipfad-Feld ausnahmsweise eine absolute Datei aus einem
anderen Verzeichnis eingegeben und geöffnet wird, folgt `current_directory`
der tatsächlich geöffneten Datei.

Der Start-Button bleibt weiterhin ein reiner Start-Button und erzeugt keine
EXE und baut keine Runtime automatisch.
