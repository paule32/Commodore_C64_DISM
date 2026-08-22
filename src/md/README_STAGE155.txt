Stage 155 – Fibonacci Graphics Scene um 60 % verkleinert

Die sichtbare QGraphicsScene der Fibonacci-Ansicht ist jetzt 40 % so groß
wie in Stage 154.

Vorher:
    Scene: 1240 x 1100

Jetzt:
    Scene: 496 x 440

Skalierung:
    GRAPHICS_SCENE_SCALE = 0.40

Wichtig:
Die interne QPainter-Zeichenfläche bleibt weiterhin 1220 x 1080 Pixel groß.
Sie wird nicht neu gestreckt oder geometrisch zusammengedrückt. Stattdessen
wird das QGraphicsProxyWidget proportional auf 40 % skaliert.

Dadurch bleiben:
- Pascal-Dreieck-Proportionen
- Abstände der Zahlen
- Diagonalwinkel
- Fibonacci-Beschriftungen
- obere Fibonacci-Flächengrafik

geometrisch identisch zu Stage 154.

Horizontaler und vertikaler Scrollbalken bleiben vorhanden.

py_compile d64_dism.py: OK
Native Windows/PyQt5-GUI-Laufzeitprüfung ist in dieser Umgebung nicht verfügbar.
