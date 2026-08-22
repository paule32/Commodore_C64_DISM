Stage 151 – Floating Mathematik-Dock frei resizbar, maximal 900 Pixel hoch

Gewünschtes Verhalten
---------------------
Mathematik-Dock:
- maximale Höhe: 900 Pixel
- angedockt: normale Qt-Dock-Größenverwaltung
- freistehend/floating: Benutzer kann Breite und Höhe mit der Maus verändern
- kleinere Benutzergrößen werden nicht zurückgesetzt
- nur Höhen über 900 Pixel werden auf 900 zurückgesetzt

Floating-Größenbereich:
    Minimum Breite: 360 px
    Minimum Höhe:   320 px
    Maximum Breite: Qt-üblich praktisch unbegrenzt
    Maximum Höhe:   900 px

QDockWidget-Features bleiben explizit:
    DockWidgetMovable
    DockWidgetFloatable
    DockWidgetClosable

Wichtig:
_expand_math_learning_dock() beendet sich nun im Floating-Zustand vor
resizeDocks(). Dadurch überschreibt ein späterer Qt-Timer/Layout-Durchlauf
nicht mehr die vom Benutzer per Maus eingestellte Floating-Größe.

Die QPainter-Fibonacci-Fläche hatte bisher eine Mindesthöhe von 690 Pixel.
Sie wurde auf 360 Pixel reduziert; die Grafik skaliert ohnehin dynamisch.
Dadurch kann das freistehende Mathematik-Fenster auch tatsächlich kleiner
gezogen werden.

Unverändert:
    Hauptfenster Start: 800 px
    Hauptfenster Max.: 1000 px
    Mathematik-Dock Max.: 900 px

py_compile d64_dism.py: OK
Native Windows/PyQt5-GUI-Laufzeitprüfung ist in dieser Umgebung nicht verfügbar.
