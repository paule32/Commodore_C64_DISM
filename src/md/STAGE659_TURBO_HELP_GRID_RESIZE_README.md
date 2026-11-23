# Stage 659 – Turbo-Hilfe: Groessenänderung nach DOS-Zeichenraster

**Basis:** Stage 658 (`d64_dism_stage658.zip`).

## Geänderte Dateien

- `d64qt5/d64_turbo_grid_motion.hpp`: Qt-unabhängige Funktionen `d64TurboClampGridExtent()` und `d64TurboGridDragExtent()` zur Berechnung von Fensterbreite/-höhe in ganzen DOS-Zellen und unter Beachtung von Minimalgröße und Viewportbegrenzung.
- `d64qt5/d64_turbo_help_window.hpp`: Resize-Griff nutzt Zeichen-/Zeilen-Raster statt Pixel. Konstruktor, Änderungen der Konsolenschrift-/DPI-Zellgröße, Wiederherstellen aus maximiertem Zustand und Größenänderungen des Konsolen-Viewports rasten ebenfalls auf dem Raster ein.
- `test_stage659.py`: Neue Regressionstests, inklusive eines mit g++ kompilierten Tests mit verschieden großen Textzellen, Min-/Max-Grenzen und positivem/negativem Maus-Drag.
- `build_and_deploy_dbase_editor_stage659.bat`: DLL-Only-Build und Bereitstellung.

## Verhalten

Bei einer exemplarischen Zelle von **8 × 16 Pixel** verändert ein Drag die Größe in **8-Pixel-Schritten horizontal** und **16-Pixel-Schritten vertikal**. Bewegungen unter einer halben Zellgröße ändern die Größe nicht. Die tatsächliche Rastergröße stammt von den aktuellen Zeichenmaßen der Konsole.

Die minimale Größe bleibt 320 × 200 Pixel (bei 8 × 16 faktisch mindestens 320 × 208 Pixel wegen der vollen Textzeilen). Die größte erlaubte Größe wird auf die letzte vollständige Zelle innerhalb des verfügbaren Viewports abgerundet. Wenn der Viewport kleiner als die Qt-Mindestgröße ist, wird die Mindestgröße priorisiert, die Rasterausrichtung aber beibehalten.

**Maximieren ist ausgenommen:** Der maximierte Viewer füllt den gesamten Konsolen-Viewport, auch wenn seine Pixelgröße kein exaktes Vielfaches des Rasters ist. Nach dem Wiederherstellen gilt wieder die zeichenrasterweise Größe.

Fensterbewegung nach Stage 657, Tab **Konsole**, Pfeil-Scrollbalken und F1-Hilfe sind unverändert. Der Hilfe-Compiler in Python, `.thlp`-/`.hlp`-Erzeugung und `libd64_qt5.dll`-Schnittstellen bleiben unverändert. Es wird kein `turbo_help_host.exe` erzeugt.

## Prüfungen

```text
python -m pytest -q test_stage659.py test_stage658.py test_stage657.py test_stage656.py test_stage655.py test_stage654.py test_stage653.py test_stage652.py test_stage651.py test_stage650.py
58 passed
```

Die numerischen Raster- und Begrenzungsfunktionen wurden mit g++ unter C++17 und `-Wall -Wextra -Werror` übersetzt und ausgeführt. Ein nativer Windows-/Qt5-Build samt realem Maus-Drag muss noch durchgeführt werden.

## Windows-Build

```bat
build_and_deploy_dbase_editor_stage659.bat
```

Optionales Zielverzeichnis für `libd64_qt5.dll` kann als erstes Argument übergeben werden. Die dBASE-EXE und `App.hlp` müssen nicht neu erzeugt werden.
