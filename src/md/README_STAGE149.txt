Stage 149 – Mathematik-Dock beim Öffnen maximal 1000 Pixel hoch

Ziel:
Beim Öffnen der Mathematik-Arbeitsfläche darf weder das Hauptfenster
noch ein frei schwebendes Mathematik-Dock höher als 1000 Pixel werden.

Neue Laufzeitfunktion:

    _enforce_math_learning_height_limit()

Sie wird ausgeführt:
1. bevor das Mathematik-Dock mit show() eingeblendet wird
2. direkt nach show()
3. beim Expandieren des Docks
4. im visibilityChanged-Handler
5. nochmals per QTimer.singleShot(0, ...) nach dem Qt-Layout-Pass

Die Funktion:
- setzt Hauptfenster-Maximalhöhe = 1000
- entfernt beim Mathe-Öffnen Maximized/Fullscreen, falls nötig
- verkleinert ein Hauptfenster >1000 sofort auf 1000
- begrenzt ein Floating-QDockWidget auf 1000
- begrenzt das eingebettete Mathematik-Widget auf 1000

Außerdem wurde die bisherige vertikale Dock-Anforderung:

    resizeDocks([dock], [100000], Qt.Vertical)

ersetzt durch:

    resizeDocks([dock], [self.MAX_WINDOW_HEIGHT], Qt.Vertical)

Damit fordert das Mathematik-Dock beim Öffnen selbst keine extreme
vertikale Größe mehr an.

Unverändert:
- Programmstart: 800 Pixel Höhe
- Benutzer darf das Fenster kleiner machen
- Benutzer darf bis 1000 Pixel vergrößern
- keine feste Höhe
- alle Mathematik-Funktionen bleiben erhalten

py_compile d64_dism.py: OK
Native Windows/PyQt5-GUI-Laufzeitprüfung ist hier nicht verfügbar.
