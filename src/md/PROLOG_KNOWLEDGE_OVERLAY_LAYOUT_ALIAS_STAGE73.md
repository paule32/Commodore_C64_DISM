# PROLOG Knowledge Browser – Stage 73

## Fehlerbild

Beim Klick auf den Pfeil eines Level-Buttons, z. B. `apfel ▼`, brach Stage 72 mit folgendem Fehler ab:

```text
AttributeError: 'PrologKnowledgeDialog' object has no attribute 'alternative_overlay_layout'
```

## Ursache

Jede `KnowledgeQueryLane` erzeugt ein eigenes `alternative_overlay_layout`. Beim Wechsel/Initialisieren einer aktiven Lane setzte `_load_query_lane()` zwar die Widget-Aliase für Overlay, ComboBox und Prüfen+-Button, vergaß aber den Alias für das zugehörige Layout.

Dadurch war `self.alternative_overlay` vorhanden, `self.alternative_overlay_layout` aber nicht. `_refresh_alternative_overlay_position()` brach daher vor der sichtbaren Anzeige der ComboBox ab.

## Korrektur

`_load_query_lane()` übernimmt nun auch:

```python
self.alternative_overlay_layout = lane.alternative_overlay_layout
```

Zusätzlich verwendet `_refresh_alternative_overlay_position()` einen defensiven Fallback:

```python
overlay_layout = getattr(self, "alternative_overlay_layout", None)
if overlay_layout is None:
    overlay_layout = self.alternative_overlay.layout()
```

Damit bleibt der Overlay-Aufbau auch bei älteren bzw. wiederhergestellten Lane-Zuständen robust.

## Verhalten

Nach Fakt-Auswahl und Klick auf `▼` kann die bestehende Stage-71/72-Logik wieder vollständig ausgeführt werden:

```text
[ apfel ▼ ]
[ gesund / essbar / obst ▼ ]
[         Prüfen +         ]
```

Die Multi-ScrollArea-/Lane-Logik, Parent-Filterung und PROLOG-Prüfung bleiben unverändert.

## Tests

- Stage-73 Regression: 3/3
- direkter Stage-70..73 Pfad: 24/24
- gesamtes Projekt: 720/720
