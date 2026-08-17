# Stage 68 – Schließen-Dialog Theme + robuste Alternativen-ComboBox

## 1. Schließen über das Hauptfenster-X

Die vorhandene Speicher-/Abbruchlogik bleibt unverändert. Geändert wurde nur die Darstellung der `QMessageBox`.

### Dark Mode

- Dialoghintergrund: `#202630`
- Text: weiß
- Eingebettete MessageBox-Kinder erhalten dieselbe Palette explizit.
- Die bereits vorhandene Button-Darstellung bleibt erhalten.

### Light Mode

- Dialoghintergrund: `#f0f0f0`
- Text: schwarz
- Buttons: `#f5f5f5`

Der Projekt-Speicherdialog `_confirm_project_replacement()` lief bisher an der gemeinsamen Theme-Hilfe vorbei. Stage 68 ruft dort nun `_apply_message_box_theme(box)` vor `exec_()` auf. Die Schaltflächen und ihre Semantik bleiben:

- `Ja, speichern`
- `Nein, nicht speichern`
- `Abbrechen`

Auch die Dokument-Speicherabfrage benutzt weiterhin den bestehenden `_show_message_box()`-Pfad.

## 2. Alternativen direkt unter dem Parent-Button

Die sichtbare ComboBox wird nicht mehr per `setParent()` zwischen den Level-Buttons verschoben. Stattdessen besitzt jeder `KnowledgeLevelButton` dauerhaft seine eigene, zunächst verborgene Auswahlgruppe:

```text
[ apfel ▼ ]
[ Alternativen zu apfel: ]
[ gesund              ▼ ]
[       Prüfen           ]
```

Damit liegt die ComboBox geometrisch immer im selben Widget wie der Button, dessen Pfeil sie öffnet. Das vermeidet den Qt5/Windows-Reparenting-Effekt, bei dem die gemeinsame ComboBox trotz `show()` nicht sichtbar bzw. abgeschnitten blieb.

### Schrift

Für die sichtbare Alternativen-ComboBox und ihr Dropdown gilt weiterhin:

- Consolas 9 pt
- Fallback Courier New 9 pt

Bei mehr als zehn Alternativen bleibt die ComboBox editierbar und verwendet `QCompleter` mit `MatchContains`.

## 3. Prüfen

Der lokale `Prüfen`-Button unter der ComboBox prüft den aktuell gewählten Wert über denselben PROLOG-Pfad wie bisher (`add_query_level()`).

Bei Erfolg:

1. der Wert wird als neuer Level-Button rechts in den Entscheidungsweg aufgenommen,
2. ComboBox + lokaler `Prüfen`-Button verschwinden,
3. der Entscheidungsweg und das grün/rote Alternativen-Label werden neu berechnet.

Bei Fehlschlag bleiben ComboBox und `Prüfen` sichtbar, damit eine andere Alternative gewählt werden kann.

## 4. Regressionen

- Stage-68-spezifische Tests: 8/8
- Stage-61..67 Wissen-Browser-Tests: 61/61
- kompletter Projektlauf: 689/689

Die native PyQt5/Windows-GUI konnte in der Linux-Containerumgebung nicht visuell gestartet werden, weil PyQt5 dort nicht installiert ist. Die Qt-Quellstruktur und Regressionen wurden geprüft.
