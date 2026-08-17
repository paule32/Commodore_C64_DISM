# Stage 89 – Desktop Properties erhält Projekt/Informationen und Log

Basis: Stage 88.

## Änderung

Beim Öffnen von `Werkzeuge -> Desktop-Einstellungen ...` bleiben die normalen
Dock-Fenster sichtbar:

- Dateisystem
- Projekt / Informationen
- Protokoll (Log-Dock)

Der Settings-Workspace blendet weiterhin die zentrale Editorfläche und
konkurrierende Spezial-Workspaces wie Localize, PROLOG-Wissen, Tabellen- und
Formular-Designer temporär aus.

`show_settings_dock()` blendet `right_dock` und `bottom_dock` zusätzlich
explizit ein. Dadurch erscheinen Projekt/Informationen und Log auch dann,
wenn sie unmittelbar vor dem Öffnen der Desktop Properties unsichtbar waren.

Beim Schließen der Desktop Properties greift weiterhin die vorhandene
Workspace-Wiederherstellung.

## Tests

- Stage 87/88/89 gezielt: 11/11 OK
- Gesamtsuite: 815/815 OK
