Stage 150 – Mathematik-Dock maximal 900 Pixel hoch

Neue getrennte Höhenlimits:

    DEFAULT_WINDOW_HEIGHT = 800
    MAX_WINDOW_HEIGHT = 1000
    MAX_MATH_DOCK_HEIGHT = 900

Damit gilt:

Hauptfenster:
- Start: 800 Pixel
- Maximum: 1000 Pixel

Mathematik-Dock:
- Maximum: 900 Pixel
- weiterhin frei kleiner einstellbar
- keine feste Höhe

Beim Erzeugen des Mathematik-Docks:
    dock.setMaximumHeight(self.MAX_MATH_DOCK_HEIGHT)

Beim eingebetteten Mathematik-Widget:
    widget.setMaximumHeight(self.MAX_MATH_DOCK_HEIGHT)

Beim Öffnen/Einblenden wird die Höhe erneut aktiv begrenzt.
Ein frei schwebendes Mathematik-Dock wird bei Bedarf sofort auf 900 Pixel
zurückgesetzt.

Auch resizeDocks() fordert vertikal höchstens 900 Pixel an:

    self.resizeDocks(
        [dock],
        [self.MAX_MATH_DOCK_HEIGHT],
        Qt.Vertical,
    )

py_compile d64_dism.py: OK
Native Windows/PyQt5-GUI-Laufzeitprüfung ist in dieser Umgebung nicht verfügbar.
