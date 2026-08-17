# d64_dism Stage 48 – bidirektionale Editor-Mini-Map

Stage 48 ergänzt rechts neben dem vorhandenen `SourceTextEdit` des Rohdaten-Tabs
eine interaktive Mini-Map. Die bestehende Editor-Klasse wird nicht ersetzt und der
linke Gutter mit Zeilennummern, Breakpoints und Bookmarks bleibt unverändert.

## Aufbau

```text
SourceEditorWithMiniMap
  ├─ SourceTextEdit       (bestehender Editor)
  └─ SourceMiniMap        (92 px breit)
```

`DocumentEditor.raw_editor` verweist weiterhin auf den vorhandenen
`SourceTextEdit`. Zusätzlich gibt es:

```python
self.raw_editor_container
self.raw_minimap
```

Damit bleiben bestehende Aufrufer, Syntax-Highlighter, Build-Signale,
Breakpoint-Logik und Kontext-Hilfe kompatibel.

## Synchronisation

Die Mini-Map besitzt keinen eigenen vertikalen Scrollzustand. Sie liest und
schreibt direkt:

```python
editor.verticalScrollBar()
```

Editor -> Mini-Map:

```text
verticalScrollBar.valueChanged
        -> SourceMiniMap.update()
```

Mini-Map -> Editor:

```text
Mausposition des Mini-Map-Viewports
        -> QStyle.sliderValueFromPosition()
        -> verticalScrollBar.setValue()
```

Die Gegenrichtung benutzt `QStyle.sliderPositionFromValue()`. Dadurch wird in
beiden Richtungen dieselbe Qt-Abbildung benutzt und es entsteht kein separater
Scrollwert, der vom Editor wegdriften könnte.

## Bedienung

- Scrollrad über dem Editor: Mini-Map folgt sofort.
- Scrollrad über der Mini-Map: Editor scrollt.
- Klick außerhalb des Viewport-Rechtecks: sichtbarer Bereich springt dorthin.
- Linke Maustaste auf dem Viewport-Rechteck halten: Viewport kann vertikal
  gezogen werden; der Editor folgt unmittelbar.

## Darstellung

Die Mini-Map zeichnet eine kompakte Übersicht aus den Zeilenlängen des
QTextDocument. Es wird keine zweite Kopie des vollständigen Quelltextes gehalten.
Der sichtbare Editorbereich wird mit der aktuellen Qt-Highlight-Farbe markiert.
Damit passt sich die Mini-Map automatisch an das aktive helle/dunkle Palette an.

## Unverändert

- `d64_dism.py` bleibt Startprogramm.
- `SourceTextEdit` bleibt der eigentliche Editor.
- linker Gutter bleibt erhalten.
- Breakpoints/Bookmarks bleiben erhalten.
- Autocomplete/Completion bleibt erhalten.
- Syntax-Highlighter bleibt erhalten.
- Build/Start-Verhalten wird nicht geändert.
