# Stage 72 – PROLOG Wissen-Browser: Predicate/Lane-State Fix

## Ursache

Der sichtbare Faktenbutton und der interne Predicate-Zustand konnten in Stage 65–71 auseinanderlaufen.

Beim Klick auf einen Fakt lief der Code sinngemäß so:

1. `selected_predicate = KnowledgePredicate(...)`
2. `_rebuild_level_buttons()` zeichnet z. B. `[apfel ▼]`
3. `_restart_decision()` bestätigt die Teilabfrage
4. `_predicate_selected()` ruft `query_edit.setFocus(...)` auf
5. `FocusIn` wird vom Lane-`eventFilter()` abgefangen
6. `_activate_query_lane()` lud dieselbe Lane erneut aus ihrem noch alten Snapshot
7. `lane.selected_predicate` war zu diesem Zeitpunkt noch `None`
8. damit wurde `self.selected_predicate` wieder `None`

Der Button blieb sichtbar, aber der ▼-Handler brach wegen

```python
if self.knowledge_base is None or self.selected_predicate is None:
    return
```

ab. Dasselbe erklärte die spätere Meldung „Zuerst links einen Fakt bzw. eine Regel auswählen.“ trotz sichtbarem `[apfel ▼]`.

## Korrektur

### 1. Predicate zuerst speichern, Fokus danach

`_predicate_selected_for_active_lane()` speichert den frisch aufgebauten Zustand nun vor dem Fokuswechsel:

```python
self._predicate_selected(item, column)
self._store_active_query_lane()
self.query_edit.setFocus(Qt.OtherFocusReason)
```

`_predicate_selected()` selbst setzt den Fokus nicht mehr.

### 2. Aktive Lane bei FocusIn nicht erneut laden

`_activate_query_lane()` erkennt nun:

```python
if current is lane:
    ...
    return
```

Die aktive Dialog-/Lane-State-Kopie ist in diesem Moment die gültige Live-Version und darf durch einen älteren Snapshot nicht überschrieben werden.

Ein Wechsel zu einer *anderen* Lane speichert weiterhin zuerst die alte Lane und lädt danach die neue Lane. Die Multi-ScrollArea-Logik bleibt daher erhalten.

## Alternativen

Der Stage-71-Aufbau bleibt unverändert:

- Klick auf `[apfel ▼]`
- Alternativen werden über `PrologKnowledgeBase.alternatives_for_level()` ermittelt
- ComboBox wird als Viewport-Overlay direkt unter dem Parent gezeigt
- lokaler `Prüfen +`-Button bleibt darunter
- bei erfolgreicher Prüfung wird der neue Wert rechts an den Pfad angehängt

Beispiel:

```prolog
apfel(gesund).
apfel(essbar).
apfel(obst).
```

liefert für `apfel/1`:

```text
essbar
gesund
obst
```

## Tests

- Stage-72-spezifisch: 5/5
- Wissen-Browser gezielt: 97/97
- kompletter Projektlauf: 717/717

Die native PyQt5-Windows-GUI konnte in der Containerumgebung nicht visuell gestartet werden.
