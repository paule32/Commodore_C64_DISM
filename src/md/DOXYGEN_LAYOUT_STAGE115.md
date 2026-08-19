# Stage 115 – Doxygen Dock Layout

Basis: die vom Benutzer zuletzt hochgeladene/geänderte `d64_dism.py`, nicht Stage 114.

Änderungen:
- Beim Öffnen von Doxygen wird zuerst `left_dock` (Dateisystem) ausgeblendet.
- Die zentrale Dokumentfläche wird danach ausgeblendet, damit QMainWindow den gesamten freien Bereich freigibt.
- Doxygen wird in `Qt.LeftDockWidgetArea` eingesetzt und liegt damit links neben `right_dock` (Projekt / Informationen).
- `right_dock` bleibt sichtbar.
- Doxygen wird horizontal und vertikal mit `resizeDocks(..., 100000, ...)` auf den maximal verfügbaren Restplatz erweitert.
- Beim Schließen werden Dateisystem und zentrale Dokumentfläche nur restauriert, wenn Doxygen sie selbst ersetzt hatte.
- Bereits aktive große Localize-/PROLOG-Docks werden vor Doxygen ausgeblendet.
- `d64qt5`-Quellen bleiben im ZIP ausschließlich unter `d64qt5/`.

Native PyQt5-GUI-Ausführung ist in der Containerumgebung nicht verfügbar; Syntax- und Strukturtests wurden ausgeführt.
