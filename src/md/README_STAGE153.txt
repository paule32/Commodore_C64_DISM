Stage 153 – Pascal-Dreieck nicht gestreckt

Ziel
----
Die Pascal/Fibonacci-Grafik im Fibonacci-Bereich sollte nicht mehr in
Breite und Höhe unabhängig verzerrt werden, weil dadurch die blauen
Diagonalen schwer verfolgbar wurden.

Umsetzung
---------
Die untere Pascal-Grafik wird jetzt in eine feste Entwurfsfläche
(760 x 430) mit konstanter Aspect-Ratio eingepasst. Danach werden
alle Koordinaten relativ zu dieser eingepassten Zeichenfläche berechnet.

Dadurch gilt:
- keine freie X/Y-Streckung mehr
- Diagonalen bleiben optisch stabil
- blaue Fibonacci-Summen bleiben an der richtigen Diagonale
- Schrift- und Linienstärken skalieren leicht mit

Beibehalten
-----------
- schwarze Pascal-Zahlen
- blaue Summenwerte
- helles Panel
- Mathe-Dock maximal 900 Pixel hoch
- freistehend weiterhin resizebar

py_compile d64_dism.py: OK
