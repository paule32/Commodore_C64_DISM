# Stage 37 – DPI-genaue Dialograhmen und Workstation-BTX-Panel

## 1. Gemeinsames Raster

Die fruehere Stage-19-Feinkorrektur `g_font_pixel_adjust` mit `-1/0/+1` Pixel
ist entfernt. Die dBase-Konsole erzeugt weiterhin eine logische Schriftgroesse
in Punkt. Die Zellgroesse wird aber nun explizit mit `QFontMetrics(font,
consoleViewport)` gegen den realen `QPlainTextEdit`-Viewport als QPaintDevice
gemessen.

Login-, Warn- und BTX-Dialog verwenden anschliessend dieselbe bereits
DPI-aufgeloeste Konsolenfont und dieselben `cellWidth`/`cellHeight`-Werte.
Rahmenzeichen, Titlebar und Rasterpositionen liegen deshalb immer auf denselben
Zeichenkoordinaten wie die 80x25-Konsole.

Die Lupen bleiben logisch `+1 pt` bzw. `-1 pt`; es gibt keinen separaten
Pixelaufschlag mehr.

## 2. Dialograhmen

Login und Warnung verwenden fuer den Rahmen nicht mehr eine unabhaengige
Terminal-Font mit eigener Punkt-/Pixelrundung. `m_borderFont` ist dieselbe Font
wie die Konsole. Die Baseline jeder Rahmenzeile wird mit
`grid_text_baseline()` innerhalb der zugehoerigen Rasterzelle berechnet.
Arbitraere Offsets wie `m_cellHeight + 2` wurden entfernt.

## 3. Workstation-Panel

Das bisherige einzelne EXIT-Fenster ist zu einem vollhoehen Win32-Panel
erweitert worden:

- X = 0, Y = 0
- Breite = 76 Pixel (identisch zur bisherigen EXIT-Fensterbreite)
- Hoehe = `SM_CYSCREEN`
- `WS_EX_TOPMOST | WS_EX_NOACTIVATE`
- EXIT oben, weiterhin nur per Doppelklick
- BTX darunter, einfacher Linksklick

EXIT sendet weiterhin nur `WM_CLOSE` an das Qt-Hauptfenster. Der komplette
bestehende Shutdown-/DATABASE-/Datei-/VirtualFree-/Desktop-Cleanup bleibt damit
erhalten.

## 4. BTX-Callback

`d64_workstation.cpp` kennt Qt nicht. Deshalb besitzt `d64_workstation.h` nur
einen kleinen C++-Callback-Typ:

```cpp
using D64WorkstationBtxCallback = void (*)(void);
void D64WorkstationSetBtxCallback(D64WorkstationBtxCallback callback);
```

Der Win32-WndProc ruft diesen Callback beim BTX-Klick auf. Die Bridge stellt
dann mit `QTimer::singleShot(0, ...)` die eigentliche Dialogerzeugung in die
Qt-Eventqueue. Es wird kein Qt-Fenster direkt innerhalb des Win32-WndProc
erzeugt.

## 5. BTX-Dialog

Der neue `BtxDialog` ist nicht modal und rastergebunden. Seine eigentliche
`QPlainTextEdit`-Flaeche ist exakt:

```text
80 * cellWidth
25 * cellHeight
```

Der aeussere CP437/Unicode-Zeichenrahmen liegt je eine Rasterzelle ausserhalb,
also insgesamt 82x27 Rasterzellen. Die BTX-Flaeche ist beim ersten Oeffnen auf
die bestehende 80x25-Konsolenflaeche ausgerichtet. Der Dialog kann an seiner
oberen Rahmenzeile in ganzen Zeichenzellen bewegt werden.

Beim Lupen-Zoom wird `BtxDialog::updateForGrid(true)` aufgerufen. Position,
Font, Textflaeche und Rahmen werden gemeinsam aus dem neuen Raster berechnet.

## 6. Build

Es kommen keine weiteren Bibliotheken hinzu. Stage 36 benoetigt weiterhin:

```qmake
win32:LIBS += -luser32 -lgdi32 -ladvapi32 -lodbc32
```

Nach Aenderung der `.pro` bei Bedarf erneut `qmake` ausfuehren und danach
`mingw32-make release`.
