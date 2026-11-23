# Stage 657 – Turbo-Hilfefenster zeichenrasterweise verschieben

Verbindliche Basis: `d64_dism_stage656.zip`.

## Änderung

Das cyanfarbene Turbo-Hilfefenster in `libd64_qt5.dll` wurde bisher beim
Ziehen der Titelleiste um beliebige Pixel verschoben. Jetzt verwendet es
dieselbe Konsolen-Zellengröße wie die übrigen Turbo-Vision-Fenster.

- Die X-Bewegung erfolgt in ganzen Zeichenspalten.
- Die Y-Bewegung erfolgt in ganzen Textzeilen.
- Die Schrittweite wird aus der tatsächlichen Konsolenschrift (Breite `M`,
  `lineSpacing()`) sowie dem DPI-/Zoom-Zustand berechnet. Beispielsweise
  8 × 16 Pixel, nicht hart auf diesen Wert festgelegt.
- Bewegungsdifferenzen werden auf die nächste volle Zellzahl gerundet.
- Die Position wird auf die Konsolengrenzen begrenzt, ohne halbe Zellen am
  rechten oder unteren Rand zuzulassen.
- Nach Größenänderung des Eltern-Viewports und Wiederherstellung eines zuvor
  maximierten Fensters wird die Position erneut am Zeichenraster ausgerichtet.
- Die frei veränderbare Fensterbreite und -höhe, Pfeil-Scrollbalken,
  Fensteraktivierung, Link-Navigation und F1-Anbindung bleiben unverändert.

Die Änderung bezieht sich auf die **Position des Hilfe-Fensters beim Ziehen
seiner Titelleiste**, nicht auf das Scrollen des darin dargestellten Texts.

## Quelldateien

- `d64qt5/d64_turbo_grid_motion.hpp`: unabhängige, Qt-freie Funktionen zur
  Rasterrundung und Begrenzung der Position.
- `d64qt5/d64_turbo_help_window.hpp`: verschiebt das Fenster ausschließlich
  in vollständigen Zeichen- und Zeilenschritten.
- `d64qt5/d64qt5_bridge.cpp`: übergibt die aktuellen Zellabmessungen der
  Konsole beim Öffnen der Hilfe und bei Schriftgrößenänderungen.
- `test_stage657.py`: neue Tests einschließlich nativ kompiliertem
  C++-Rastergeometrietest.
- `build_and_deploy_dbase_editor_stage657.bat`: aktualisierte DLL bauen und
  in das Runtime-Verzeichnis kopieren, ohne separate Hilfe-EXE.

## Tests

`pytest -q test_stage629.py test_stage630.py test_stage631.py test_stage651.py test_stage652.py test_stage653.py test_stage654.py test_stage655.py test_stage656.py test_stage657.py`

Ergebnis: **78 passed**, inklusive C++-Test der Rasterrundung und
Begrenzung. Die native Windows-Qt5-Bridge konnte in der aktuellen Umgebung
nicht kompiliert und visuell getestet werden.

## Windows Build

```bat
build_and_deploy_dbase_editor_stage657.bat
```

Wie in Stage 656 wird nur die `libd64_qt5.dll` ersetzt. Weder die dBASE-EXE
noch die `.hlp`-Dateien müssen neu kompiliert werden.
