# Stage 112 – QRectF-Startfix für den dBase-Formulardesigner

Beim Erzeugen von `DBaseFormWindowItem` rief Stage 111 in `_sync_scene_geometry()` folgendes auf:

```python
mapped = self.mapRectToScene(self.boundingRect()).boundingRect()
```

Unter PyQt5 liefert `mapRectToScene(QRectF)` bereits ein `QRectF`. `QRectF` besitzt keine Methode `boundingRect()`, daher stürzte der Formulardesigner bereits beim Öffnen ab.

Stage 112 normalisiert den Rückgabewert jetzt für beide möglichen Fälle:

```python
mapped = self.mapRectToScene(self.boundingRect())
if hasattr(mapped, "boundingRect"):
    mapped = mapped.boundingRect()
else:
    mapped = QRectF(mapped)
```

Damit bleibt die Stage-111-Form-Scene vollständig erhalten. Es wurden keine Designer-Features oder d64qt5-Runtime-Dateien entfernt. Die d64qt5-Quellen bleiben im ZIP unter `d64qt5/`.
