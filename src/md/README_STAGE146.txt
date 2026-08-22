Stage 146 – Fibonacci Fokusfehler behoben

Fehler:
    AttributeError:
    'FibonacciSpiralFactWidget' object has no attribute 'view'

Ursache:
Stage 145 hat die alte QGraphicsView-basierte Fibonacci-Darstellung durch
FibonacciPascalPainterCanvas mit direktem QPainter-Zeichnen ersetzt.
Der alte Fokus-Aufruf auf:

    self.fibonacci_spiral_widget.view

war im open_fact()-Zweig noch vorhanden.

Korrektur:
Beim Öffnen von "Fibonacci Spirale" erhält jetzt die interaktive SpinBox:

    self.fibonacci_spiral_widget.index_spin

den Fokus.

Die Stage-145-Funktionen bleiben unverändert:
- QPainter-Fibonacci-Flächen
- QPainter-Viertelkreise
- Pascal-Diagonalsummen
- Binet-SpinBox 1..1000
- Berechnen-Button
- Decimal-Hochpräzisionsberechnung

py_compile d64_dism.py: OK
Native PyQt5-GUI-Laufzeitprüfung ist in dieser Umgebung nicht verfügbar.
