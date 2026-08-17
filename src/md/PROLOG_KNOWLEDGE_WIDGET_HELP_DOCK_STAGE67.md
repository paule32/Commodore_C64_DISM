# Stage 67 – Widget-Property/F1, Knowledge-Dock-Vollfläche und sichtbare Alternativen

## Grundlage

Stage 67 basiert vollständig auf Stage 66. Bestehende Compiler-, Editor-, Multi-Scroll-,
PROLOG- und F2-Funktionen bleiben erhalten.

## 1. Widget-Property-ID für F1 / spätere CHM-Zuordnung

Jedes sichtbare `QWidget` erhält die dynamische Qt-Property:

```text
d64WidgetPropertyId
```

Die ID wird bevorzugt aus `objectName()` aufgebaut. Für Widgets ohne expliziten
Objektnamen wird ein deterministischer Pfad aus Widget-Klasse und Geschwisterindex
erzeugt, ohne `objectName()` zu verändern und damit ohne QSS-Selektoren zu beeinflussen.

Bei F1 wird das Widget unter dem Mauszeiger bestimmt:

```python
QApplication.widgetAt(QCursor.pos())
```

Die Property-ID wird derzeit nur in Protokoll und Statuszeile ausgegeben:

```text
F1 Widget-Property-ID: <ID>
```

F1 wird absichtlich nicht konsumiert, damit die bestehende Editor-Kontexthilfe
weiterarbeiten kann. In einer späteren Stufe kann dieselbe ID auf CHM-Themen gemappt
werden.

Dynamisch erzeugte Widgets erhalten ihre ID beim `QEvent.Show` automatisch.

## 2. Wissensdatenbank-Dock verwendet den gesamten freien Arbeitsbereich

Beim Anzeigen des Wissensdatenbank-Docks werden weiterhin das linke Dock
`Dateisystem und Dateien` sowie zusätzlich temporär der normale zentrale Dokumentbereich
ausgeblendet. Dadurch reserviert `QMainWindow` keinen leeren Mittelstreifen mehr.

Das Wissens-Dock wird anschließend mit `resizeDocks()` auf den vollständig verfügbaren
Bereich expandiert. Das rechte Projekt-Dock und das untere Protokoll-Dock bleiben bestehen.

Beim Schließen des Wissens-Docks werden die zuvor sichtbaren Bereiche wiederhergestellt.

## 3. Alternativen-ComboBox exakt unter `[Wert ▼]`

Stage 66 führte nach `setParent()` bereits `show()` aus. Unter Windows konnte der
Custom-`KnowledgeFlowLayout` den Level-Container trotzdem mit der alten Einzeilenhöhe
weiterführen, wodurch ComboBox und `Prüfen` abgeschnitten blieben.

Stage 67 erzwingt nach dem Einbetten:

- `layout.invalidate()`
- `layout.activate()`
- neue Mindestgröße des `KnowledgeLevelButton`
- `updateGeometry()` für Button und Flow-Host
- einen zweiten Geometry-Pass über `QTimer.singleShot(0, ...)`

Die sichtbare Struktur ist damit:

```text
[ apfel ▼ ]
[ Alternativen zu apfel: ]
[ gesund                 ▼ ]
[ Prüfen                    ]
```

Die ComboBox wird nicht mehr während des Re-Layouts per `showPopup()` zwanggeöffnet.
Sie bleibt als normales Widget sichtbar und öffnet ihr Dropdown erst beim Benutzerklick.

Die Schriftvorgabe aus Stage 66 bleibt erhalten:

- Consolas 9 pt
- Fallback Courier New 9 pt

## Tests

- Stage-61..67 Wissen-Browser-Regressionen: 61/61 OK
- Gesamtsuite: 681/681 OK
- `py_compile`: OK
- keine `.pyc`/`__pycache__` im finalen Archiv

Die native Windows/PyQt5-Oberfläche konnte in der Containerumgebung nicht visuell
ausgeführt werden. Die Änderung wurde deshalb über Quell-/Strukturtests und die komplette
Regressionstest-Suite abgesichert.
