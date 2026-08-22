Stage 138 - Zahlenmauer QGraphicsScene Fix

Behoben:
AttributeError:
'QGraphicsScene' object has no attribute 'addRoundedRect'

PyQt5 QGraphicsScene besitzt keine addRoundedRect()-Methode.

Neu:
    block_path = QPainterPath()
    block_path.addRoundedRect(QRectF(...), 8.0, 8.0)
    rect = graphics_scene.addPath(block_path, pen, brush)

Das erzeugte QGraphicsPathItem unterstützt weiterhin:
- setPen()
- setBrush()
- setData()

Damit bleiben Stufenfarben sowie Dark-/Light-Mode unverändert erhalten.

py_compile d64_dism.py: OK
Native PyQt5-GUI-Laufzeitprüfung ist in dieser Umgebung nicht verfügbar.
