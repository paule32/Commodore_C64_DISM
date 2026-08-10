# dBase Qt5 GUI – Stage 6: Dark console style and synchronized zoom

The Qt5 output runtime keeps the two existing output tabs (`Konsole` and `DEBUG`) and adds a compact zoom control directly to the top-left corner of the `QTabWidget` tab bar.

## Appearance

- Full GUI/background: black (`#000000`)
- Console and DEBUG text: gray (`#A9A9A9`)
- Console and DEBUG editors remain borderless `QPlainTextEdit` widgets
- DEBUG input line uses the same dark palette and monospace font

## Font fallback

The runtime checks installed fonts in this order:

1. `Consolas`
2. `Courier New`
3. `Courier`
4. Qt system fixed-width font

The same font and point size are applied to both `QPlainTextEdit` outputs and the DEBUG `QLineEdit`.

## Zoom controls

Two self-drawn magnifier icons are embedded in the `QTabWidget` top-left corner:

- left magnifier: `+` – increases font size by 1 pt
- right magnifier: `-` – decreases font size by 1 pt

Limits are enforced in the runtime:

- minimum: 9 pt
- maximum: 75 pt

No external icon files are required; the magnifier icons are drawn with `QPainter`.
