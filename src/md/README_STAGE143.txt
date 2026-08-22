Stage 143 – Pascal-Dreieck und Fibonacci-Spirale

Fakten-Baum:

Cantor
├── Diagonal Argument
├── Pascal Dreieck
└── Fibonacci Spirale

Pascal Dreieck
--------------
- eigene QGraphicsScene
- SpinBox "Tiefenlevel"
- Wertebereich 1..18
- Default = 8
- Tiefenlevel bedeutet Anzahl sichtbarer Reihen
- Änderung der SpinBox zeichnet sofort neu
- jeder innere Wert = Summe der zwei Werte darüber
- ungerade/gerade Einträge werden zur besseren Orientierung unterschiedlich
  hinterlegt
- Dark-/Light-Mode

Bei Default 8 endet das Dreieck mit:
1 7 21 35 35 21 7 1

Fibonacci Spirale
-----------------
- eigene QGraphicsScene
- Fibonacci-Quadrate:
  1, 1, 2, 3, 5, 8, 13, 21, 34
- spiralförmige Anordnung der Quadrate
- jeder Wert wird im Quadrat angezeigt
- Viertelkreisbögen bilden die Fibonacci-Spirale nach
- Dark-/Light-Mode

Das bestehende Cantor-Diagonalargument und alle Mathematik-Spiele bleiben
erhalten.

py_compile d64_dism.py: OK
Native PyQt5-GUI-Laufzeitprüfung ist in dieser Umgebung nicht verfügbar.
