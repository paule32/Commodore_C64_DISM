Stage 157 – Pascal-Dreieck nochmals um 20 Prozent größer

Geändert wurde erneut nur die Pascal/Fibonacci-Diagonal-Darstellung unterhalb des oberen Fibonacci-Bildes.

Neue Konstante:

    PASCAL_DISPLAY_SCALE = 1.44

Skalierungsweg:

    Stage 155: 0.90
    Stage 156: 0.90 * 1.20 = 1.08
    Stage 157: 0.90 * 1.44 = 1.296

Das bedeutet gegenüber Stage 156 nochmals +20 %.

Zusätzlich wurde die Flächenaufteilung angepasst, damit das größere Pascal-Dreieck mehr vertikalen Platz bekommt:

    upper_height = max(230.0, outer.height() * 0.40)

Damit bleibt das obere Fibonacci-Bild unverändert, während der untere Pascal-Bereich größer nutzbar wird.

Unverändert:
- oberes Fibonacci-Bild
- Graphics-Scene: 496 x 440
- Scene-Proxy-Skalierung: 0.40
- logischer Canvas: 1220 x 1080
- horizontale/vertikale Scrollbars
- Mathematik-Dock maximal 900 Pixel hoch
- Floating-Dock resizebar

py_compile d64_dism.py: OK
Native Windows/PyQt5-GUI-Laufzeitprüfung ist in dieser Umgebung nicht verfügbar.
