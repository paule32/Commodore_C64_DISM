# Grafik-Primitiven: Geschwindigkeitsoptimierung

## Ursache

Die erste Implementierung leitete gefuellte Formen pixelweise ueber die
öffentliche Funktion `SetPixel` weiter. Auf dem Amiga bedeutete dies je Pixel:

- Parameter auf den Stack legen,
- Unterprogrammaufruf,
- Bereichspruefung,
- `Y * 40`,
- Bitmaskenberechnung,
- vier getrennte Bitplane-Zugriffe.

`FillCircle` zeichnete zusaetzlich viele konzentrische Kreislinien. Auf dem C64
wurde `FillRect` ebenfalls Pixel fuer Pixel durch die allgemeine C-Funktion
abgearbeitet.

## Neue schnelle Pfade

### Amiga

- `__gfx_setpixel_fast`: Register-ABI fuer interne Aufrufe.
- `__gfx_getpixel_fast`: Register-ABI fuer FloodFill und Tests.
- `__gfx_hline_fast`: berechnet die Zeilenadresse nur einmal und bewegt
  Bitmaske und vier Bitplane-Zeiger fortlaufend.
- `FillRect`: eine horizontale Spannweite je Zeile.
- `FillCircle`: Midpoint-Kreis mit horizontalen Spannweiten statt
  konzentrischer Einzelpixel-Kreise.
- `DrawRect`: horizontale Kanten verwenden den Spannweitenpfad.

### C64

- `graphics.h` bindet die getrennten C64-Ziel- und Common-Module ein.
- `__GraphicsHLine` berechnet Bitmap-/Zelladresse einmal je Spannweite.
- `FillRect` und `FillCircle` verwenden horizontale Spannweiten.
- `InitGraphics`, `DoneGraphics`, `ClearScreen` und `SetTextColor` liegen im
  getrennt kompilierten C64-Zielmodul.

## Weiterhin teurer

`FloodFill` und `FillTriangle` sind weiterhin komplexer als Rechteck- und
Kreisfuellungen. Sie profitieren bereits von den registerbasierten Pixelpfaden;
eine spaetere zweite Stufe kann FloodFill auf einen vollständigen Span-Stack
und Amiga-Fills zusätzlich auf den Blitter umstellen.
