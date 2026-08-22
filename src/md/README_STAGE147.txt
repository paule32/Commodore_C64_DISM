Stage 147 – Pascal-Farben und Fensterhöhe

Pascal-Dreieck
--------------
Die dezenten Diagonalmarkierungen wurden leicht aufgehellt.

Dark:
    QColor(154, 181, 207, 116)

Light:
    QColor(122, 142, 162, 96)

Auch die Summenfarben rechts wurden leicht aufgehellt:
    Dark  #B4D4ED
    Light #527EA5

Hauptfenster
------------
Maximalhöhe:
    1000 Pixel

Implementierung:
    MAX_WINDOW_HEIGHT = 1000
    self.setMaximumHeight(self.MAX_WINDOW_HEIGHT)

Die Startgröße bleibt:
    1360 x 860

Es wird kein setFixedHeight() verwendet. Der Benutzer kann die Höhe weiterhin
frei verkleinern und bis maximal 1000 Pixel vergrößern.

Mathematik-Dock
---------------
Das Mathematik-Dock erhält ebenfalls:
    dock.setMaximumHeight(self.MAX_WINDOW_HEIGHT)

Auch das eingebettete Mathematik-Widget erhält dieselbe Obergrenze.
Damit gilt die Grenze ebenfalls, wenn das Dock frei schwebt.

py_compile d64_dism.py: OK
Native PyQt5-GUI-Laufzeitprüfung ist in dieser Umgebung nicht verfügbar.
