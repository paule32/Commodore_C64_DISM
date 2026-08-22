Stage 145 – Fibonacci mit QPainter, Pascal-Diagonalsummen und Binet-Rechner

Obere Fibonacci-Grafik:
- vollständig mit QPainter
- Flächen in Pastell-Rot, Gelb, Grün, Cyan, Blau, Violett und Rosa
- dezentes Raster
- Zahlen 21, 13, 8, 5, 3, 2, 1, 1
- Viertelkreise direkt mit QPainter.drawArc()
- blaue Fibonacci-Spirale

Unter der Fibonacci-Grafik:
- Pascal-Dreieck
- flache Diagonalen mit dezenten Linien
- Summen am rechten Rand
- diese Summen ergeben die Fibonacci-Zahlen

Unter dem Bild:
- SpinBox für Fibonacci-Index n
- Minimum = 1
- Maximum = 1000
- Button "Berechnen"
- Ergebnisfeld
- Binet-Formel mit Decimal-Hochpräzision

Validierung:
- py_compile: OK
- Binet gegen exakte Fibonacci-Werte bis F(1000): OK
- Pascal-Diagonalsummen F(1)..F(10): OK

Native PyQt5-GUI-Laufzeitprüfung ist in dieser Umgebung nicht verfügbar.
