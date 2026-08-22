Stage 154 – Fibonacci-Ansicht mit scrollbarer QGraphicsScene

Neu:
- QGraphicsScene 1240 x 1100
- QGraphicsView mit horizontalem und vertikalem Scrollbalken
- QPainter-Canvas 1220 x 1080 als QGraphicsProxyWidget
- keine Viewport-Streckung mehr

Pascal/Fibonacci:
- Reihen weiter auseinander
- Spalten weiter auseinander
- Diagonalen weiter von Zahlen abgesetzt
- 250 px eigener Raum fuer Fibonacci-Summen rechts
- kein weisser Panel-Hintergrund
- transparenter Canvas; Scene-Hintergrund folgt Dark/Light
- Pascal-Zahlen folgen fuer Lesbarkeit dem Theme

Dark Mode:
- Fibonacci-Ansicht startet dunkel
- Mathematik-Menuebereich startet dunkel
- Fakten/Spiele/Informationen-Tabs erhalten expliziten Theme-Hintergrund

Beibehalten:
- Mathe-Dock max. 900 px
- Floating-Dock resizebar
- Binet 1..1000
- korrekte Fibonacci-Diagonalsummen

py_compile: OK
Native PyQt5-GUI-Laufzeitpruefung hier nicht verfuegbar.
