Stage 156 – Pascal-Dreieck 20 Prozent größer

Geändert wurde ausschließlich die Pascal/Fibonacci-Diagonal-Darstellung
unterhalb des oberen Fibonacci-Bildes.

Neue Konstante:

    PASCAL_DISPLAY_SCALE = 1.20

Stage 155 verwendete auf der festen internen Zeichenfläche effektiv:

    0.90

Stage 156 verwendet:

    0.90 * 1.20 = 1.08

Das entspricht exakt einer Vergrößerung um 20 Prozent.

Mitvergrößert werden:
- Reihenabstände
- Spaltenabstände
- Pascal-Zahlen
- blaue Diagonalen
- blaue Fibonacci-Zahlen
- Abstände und Linienverlängerungen

Zusätzlich wurden die Innenränder der unteren Pascal-Fläche reduziert,
damit das größere Dreieck innerhalb der vorhandenen QPainter-Zeichenfläche
weiterhin sauber Platz findet.

Unverändert:
- oberes Fibonacci-Bild
- Graphics-Scene: 496 x 440
- Scene-Proxy-Skalierung: 0.40
- logischer Canvas: 1220 x 1080
- horizontale/vertikale Scrollbars
- Mathematik-Dock maximal 900 Pixel hoch
- Floating-Dock weiterhin resizebar

py_compile d64_dism.py: OK
Native Windows/PyQt5-GUI-Laufzeitprüfung ist in dieser Umgebung nicht verfügbar.
