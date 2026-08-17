# Stage 76 – Menüfarben Dark/Light und schwarzer Titeltext

Basis: Stage 75.

## Titelbalken

Der Green-&-Beige-Verlauf aus Stage 75 bleibt erhalten. Der Fenstertitel wird nun in beiden Themes schwarz gezeichnet. Eine dezente helle 1-px-Kontur dient nur der Lesbarkeit; die eigentliche Titelschrift ist `#000000`.

## Dark-Mode

Menüleiste und Popup-Menüs:

- Hintergrund: Navy `#0B1F33`
- normale Schrift: Gelb `#FFD84D`
- Menüschrift: Arial, 9 pt
- selektierter Eintrag: Grün `#2E7D32`, Schrift Schwarz `#000000`
- deaktivierter Eintrag: Navy `#0B1F33`, Schrift Grau `#8B949E`

## Light-Mode

Menüleiste und Popup-Menüs:

- Hintergrund: Beige `#F5F0E6`
- normale Schrift: Schwarz `#000000`
- Menüschrift: Arial, 9 pt
- selektierter Eintrag: Grün `#2E7D32`, Schrift Schwarz `#000000`
- deaktivierter Eintrag: Beige `#F5F0E6`, Schrift Grau `#8A8A8A`

## Verhalten

Die vorhandenen QAction-/QMenu-Zustände und die Menüstruktur werden nicht verändert. Beim Dark/Light-Umschalten wird `_apply_green_beige_chrome_style()` erneut ausgeführt, damit auch bereits vorhandene Popup-Menüs sofort das neue Theme erhalten.
