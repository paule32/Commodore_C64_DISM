# dBase Qt5 Console Chrome – Stage 17

Stage 17 baut auf Stage 16 auf und ändert ausschließlich die Qt5-Bridge-Darstellung. Die dBase-Syntax und der interne PE32/PE32+-Codegenerator bleiben kompatibel.

## Konsolen-Seite

Die Konsole besteht aus einem festen Rahmencontainer:

```text
QFrame dbaseConsoleFrame (3 px, SET BORDERCOLOR TO)
├── QMenuBar dbaseMainMenu        feste erste Zeile
├── QPlainTextEdit dbaseConsole   expandierender Mittelbereich
└── QStatusBar dbaseStatusBar     feste letzte Zeile
```

Damit befindet sich die obere Rahmenkante oberhalb der Menueleiste. Der Editor selbst besitzt keinen eigenen Rahmen mehr.

## Rahmen

- 3 Pixel stark.
- Standardfarbe weiterhin weiss.
- `SET BORDERCOLOR TO ...` ändert den Rahmen.
- Derselbe Rahmen wird auch um die DEBUG-Seite gelegt.
- `CLEAR SCREEN`, `_app.colorNormal` und `SET COLOR TO` überschreiben die Rahmenfarbe nicht.

## Texteditor

Der Texteditor hat auf allen Seiten:

```text
margin = 0 px
padding = 0 px
contentsMargins = 0 px
viewportMargins = 0 px
QTextDocument.documentMargin = 0.0
```

Dadurch beginnen die Zeichen unmittelbar am inneren verfügbaren Rand.

## Statusleiste

Die Statusleiste liegt fest in der letzten Zeile innerhalb des Rahmens:

- Hintergrund `#909090` (grau)
- Text `#000000` (schwarz)
- Schrift `Consolas`
- Fallback `Courier New`
- keine Size-Grip-Ecke
- horizontal `Expanding`, vertikal `Fixed`
- kein Padding/Margin

Sie ist ein echtes `QStatusBar`-Widget und kein Text im `QPlainTextEdit`. Spaetere Status-Widgets bleiben deshalb erreichbar und scrollen nicht mit.

## Menü

Die vorhandene `QMenuBar` liegt fest in der ersten Zeile innerhalb des Rahmens. Auch sie scrollt nicht mit dem Dokument und bleibt jederzeit bedienbar.

## Enter/Return / Leerzeile

Die Bridge enthält `ensure_trailing_blank_line(QPlainTextEdit *)`. Nach einer abgeschlossenen Eingabe wird mindestens ein leerer Dokumentblock am unteren Ende gehalten. Die aktuelle DEBUG-Eingabe verwendet diesen Helfer bereits; ein späterer Konsolen-Eingabepfad kann denselben Helfer direkt verwenden.

## Kompatibilität

Es wurden keine neuen dBase-Anweisungen eingeführt. PE32-/PE32+-Assembler, `CLEAR SCREEN`, `SET COLOR TO`, `SET BORDERCOLOR TO`, `_app`, Menüs und DEBUG bleiben unverändert kompatibel.
