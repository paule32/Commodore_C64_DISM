Stage 142 – Fakten / Cantor / Diagonal Argument

Neu links im Mathematik-Dock:

    Fakten | Spiele | Informationen

Der Fakten-Tab enthält:

    Cantor
      └── Diagonal Argument

Doppelklick auf "Diagonal Argument" öffnet rechts eine eigene Ansicht mit:
- SpinBox "Reihen"
- SpinBox "Spalten"
- Button "Berechnen"
- darunter einer QListWidget-Liste

Beide SpinBoxen stehen anfangs auf 0 und zeigen dafür den Text "leer".
Die Liste ist anfangs ebenfalls leer. Eine Dimensionsänderung löscht eine
bereits berechnete Liste wieder. Der Button wird erst aktiv, wenn Reihen
und Spalten beide größer als 0 sind.

Verwendete diagonale Nummerierung:

    π(r,c) = ((r+c) * (r+c+1)) / 2 + c

Intern wird ausschließlich ganzzahlig gerechnet:

    d = r + c
    π = d * (d + 1) // 2 + c

Beispiel 4 x 4:

        c0  c1  c2  c3
r0 |     0   2   5   9
r1 |     1   4   8  13
r2 |     3   7  12  18
r3 |     6  11  17  24

Die vorhandenen Mathematik-Spiele bleiben unverändert erhalten.

py_compile d64_dism.py: OK
Native PyQt5-GUI-Laufzeitprüfung ist in dieser Umgebung nicht verfügbar.
