Stage 152 – Pascal-Dreieck bei Fibonacci korrigiert

Referenz
--------
Die hochgeladene Darstellung wurde für den Stil des unteren
Pascal-Diagramms verwendet:

- Pascal-Zahlen schwarz
- diagonale Markierungslinien blau
- Fibonacci-Diagonalsummen blau
- Summe direkt am rechten Ende ihrer zugehörigen Diagonale
- sehr heller, einfacher Hintergrund
- keine Kästen um die Pascal-Zahlen
- kein "Σ =" Präfix vor der Fibonacci-Zahl

Korrektur des bisherigen Zuordnungsproblems
-------------------------------------------
Bisher wurde die Y-Position der Summen mit:

    label_y = top_y + (n - 1) * row_gap

separat erzeugt.

Dadurch konnte eine Summe optisch neben einer anderen Diagonale stehen.

Stage 152 positioniert die Zahl stattdessen relativ zu:

    end_point

also direkt am tatsächlichen rechten Endpunkt derselben blauen
Diagonalmarkierung.

Mathematik
----------
Verwendete Identität:

    F_n = Summe C(n-k-1, k)

Für 12 gezeichnete Pascal-Reihen werden vollständig dargestellt:

    1
    1
    2
    3
    5
    8
    13
    21
    34
    55
    89
    144

Diese Werte wurden gegen eine unabhängige iterative Fibonacci-Berechnung
geprüft.

Unverändert:
- obere Fibonacci-QPainter-Grafik
- Binet-Rechner 1..1000
- Floating Mathe-Dock frei resizbar
- Mathematik-Dock maximal 900 Pixel hoch

py_compile d64_dism.py: OK
Native Windows/PyQt5-GUI-Laufzeitprüfung ist in dieser Umgebung nicht verfügbar.
