# Stage 88 – Tabellen-Designer behält Projekt/Informationen und Log sichtbar

Basis: Stage 87.

## Änderung

Beim Öffnen von `Datei -> Neu -> dBase -> Tabelle` wird der Tabellen-Designer weiterhin rechts neben dem Dateisystem-Dock aufgebaut und die zentrale Editorfläche für den Tabellen-Workspace freigeräumt.

Neu in Stage 88:

- `right_dock` (Projekt / Informationen) wird **nicht** mehr ausgeblendet.
- `bottom_dock` (Log) wird **nicht** mehr ausgeblendet.
- Beide Docks behalten ihren aktuellen Sichtbarkeitszustand und ihre Qt-Dock-Anordnung.
- Das Dateisystem-Dock bleibt wie bisher sichtbar.
- Nur konkurrierende Spezial-Workspaces (`localize_dock`, `prolog_knowledge_dock`) werden während des Tabellen-Designers temporär ausgeblendet.
- Beim Schließen des Tabellen-Designers wird weiterhin der zuvor gespeicherte Workspace-Zustand restauriert.

## Sichtbares Layout

```text
+----------------------+------------------------------+----------------------+
| Dateisystem          | dBase Tabelle - Designer    | Projekt/Informationen|
|                      |                              |                      |
|                      |                              |                      |
+----------------------+------------------------------+----------------------+
| Log-Dock bleibt sichtbar                                                   |
+-----------------------------------------------------------------------------+
```

## Tests

- Stage-86/87/88 fokussiert: 14/14 OK
- Gesamtsuite: 812/812 OK
