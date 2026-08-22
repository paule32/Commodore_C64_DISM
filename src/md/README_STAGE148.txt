Stage 148 – Hauptfenster-Starthöhe 800 Pixel

Problem
-------
Stage 147 setzte zwar:

    self.resize(1360, 860)
    self.setMaximumHeight(1000)

später wurde jedoch in _restore_window_state():

    self.restoreGeometry(geometry)

aufgerufen. Eine alte gespeicherte Fenstergeometrie konnte dadurch die
gewünschte Startgröße wieder überschreiben.

Korrektur
---------
Neue Konstanten:

    DEFAULT_WINDOW_HEIGHT = 800
    MAX_WINDOW_HEIGHT = 1000

Initial:

    self.resize(1360, self.DEFAULT_WINDOW_HEIGHT)

Nach restoreGeometry()/restoreState():

1. 1000-Pixel-Maximalhöhe erneut setzen.
2. eventuell gespeicherten Maximized-/Fullscreen-Zustand entfernen.
3. gespeicherte Breite und Position behalten.
4. Höhe zwingend auf 800 Pixel setzen.
5. im nächsten Qt-Event-Loop-Durchlauf nochmals auf 800 Pixel clampen.

Damit kann eine alte gespeicherte Höhe von z.B. 1200/1400 Pixel die
Startgröße nicht erneut überschreiben.

Der Benutzer kann das Fenster danach weiterhin normal verändern:
- kleiner als 800 Pixel: erlaubt
- größer als 800 Pixel: erlaubt
- maximal 1000 Pixel: erlaubt
- über 1000 Pixel: nicht erlaubt

Das Mathematik-Dock behält ebenfalls seine maximale Höhe von 1000 Pixel.

py_compile d64_dism.py: OK
Native Windows/PyQt5-GUI-Laufzeitprüfung ist in dieser Umgebung nicht verfügbar.
