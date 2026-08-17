# PROLOG Wissen-Datenbank Dock – Stage 66

Stage 66 baut auf Stage 65 auf und ändert den Wissen-Datenbank-Browser in zwei Punkten.

## Docking im Hauptfenster

`open_prolog_knowledge_browser()` erzeugt den Browser nicht mehr als freies Top-Level-Fenster. Stattdessen wird er in ein `QDockWidget` mit dem Titel `PROLOG – Wissen-Datenbanken` eingebettet und in `Qt.LeftDockWidgetArea` eingesetzt.

Beim Öffnen wird das bisherige linke Dock `Dateisystem und Dateien` ausgeblendet. Beim Schließen des Wissen-Docks wird es wieder eingeblendet, sofern es vor dem Öffnen sichtbar war. Der Browser kann über die normalen QDockWidget-Funktionen weiterhin verschoben, abgedockt und wieder eingedockt werden.

Die bestehende Klasse `PrologKnowledgeDialog` bleibt erhalten. Sie besitzt nun den Parameter `embedded=True`; in diesem Modus wird sie mit `Qt.Widget` als Dock-Payload betrieben. Der interne Schließen-Button blendet dann das Dock aus, statt den eingebetteten Browser als eigenständiges Fenster zu schließen.

## Fix: Alternativ-ComboBox unter dem Parent-Button

Stage 65 hat die Alternativ-Steuerelemente korrekt unter den angeklickten Level-Button reparentet, aber Qt versteckt sichtbare Widgets bei `setParent(...)` automatisch. Deshalb konnte die ComboBox nach einem Klick auf `▼` unsichtbar bleiben.

Stage 66 ruft nach dem Reparenting explizit `show()` für

- Alternativen-Label,
- Alternativen-ComboBox,
- lokalen `Prüfen`-Button,
- den darunterliegenden Alternative-Host

auf. Zusätzlich wird die dynamische Höhe der aktiven inneren ScrollArea nach dem Einblenden sofort und nochmals per `QTimer.singleShot(0, ...)` berechnet.

Das sichtbare Ergebnis ist damit:

```text
[ apfel ▼ ]
[ Alternativen zu apfel: ]
[ gesund              ▼ ]
[       Prüfen          ]
```

## Schrift der Alternativen

Die Alternativen-ComboBox und ihre Dropdown-Einträge verwenden 9 pt Monospace:

1. `Consolas`
2. Fallback `Courier New`

Bei einer durchsuchbaren ComboBox (>10 Alternativen) verwendet auch das Popup des `QCompleter` dieselbe Schrift.

## Regression

Der vollständige Projekt-Testlauf umfasst 670 Tests und ist erfolgreich.

Die PyQt5-Oberfläche kann in der Linux-Containerumgebung nicht nativ visuell gestartet werden. Der Fix basiert auf dem dokumentierten Qt-Reparenting-Verhalten und wird durch Quell-/Strukturregressionen abgedeckt.
