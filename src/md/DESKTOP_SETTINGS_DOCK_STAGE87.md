# Stage 87 – Desktop Settings Dock

Basis: Stage 86.

## Aufruf

Der neue Settings-Workspace ist erreichbar über:

```text
Werkzeuge -> Desktop-Einstellungen ...
```

Shortcut:

```text
Ctrl+Alt+S
```

Die Einstellungen werden nicht als modaler Dialog geöffnet, sondern als echtes
`QDockWidget` rechts neben dem Dateisystem-Dock. Für die Dauer des Settings-
Workspaces wird die übrige zentrale Arbeitsfläche freigeräumt. Beim Schließen
wird der vorherige Workspace wiederhergestellt.

## Tabs

Der vom Benutzer vorgegebene Desktop-Properties-Code wurde in die bestehende
Qt5-Anwendung integriert. Enthalten sind:

- Country
- Table
- Data Entry
- Files
- Application
- Programming
- Source Aliases
- User-BDE-Aliases

`share.locales.tr(...)` wurde an den bereits in d64_dism vorhandenen
`tr(...)`-Übersetzungshook angepasst.

## Buttons

- `OK`: Einstellungen speichern und Dock schließen.
- `Cancel`: gespeicherte Einstellungen erneut laden und Dock schließen.
- `Help`: Hilfehinweis anzeigen.
- `Apply`: Einstellungen speichern, Dock geöffnet lassen.

## Persistenz

Die vorhandene `QSettings("paule32", "Qt5D64Explorer")`-Instanz wird verwendet.
Neben Country/Table/Data Entry/Files/Application/Programming werden jetzt auch
beide Alias-Modelle persistent gespeichert:

```text
desktop/aliases/source
desktop/aliases/user_bde
```

Die Alias-Werte werden als JSON in QSettings hinterlegt.

## Alias-Editoren

### Source Aliases

- Alias hinzufügen/entfernen/umbenennen
- Pfad bearbeiten
- Verzeichnis über nicht-nativen Qt-Dateidialog auswählen

### User-BDE-Aliases

- Alias hinzufügen/entfernen/umbenennen
- Driver-Auswahl: dBASE, PARADOX, DB2, ORACLE, ODBC, SQL, FIREBIRD
- Options-Feld
- `PATH:<Verzeichnis>` über nicht-nativen Qt-Verzeichnisdialog

## Kompatibilität

Der Settings-Workspace verlässt aktive dBase-Form-/Tabellen-Workspaces sauber
und stellt den vorherigen Zustand nach dem Schließen wieder her. Der bestehende
Dark/Light-Modus wirkt automatisch auf den Dock-Inhalt; die Stage-86
`DockTitleBar` übernimmt weiterhin die korrekten hellen/dunklen Dock-Symbole.
