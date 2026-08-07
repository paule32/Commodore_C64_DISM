# C64 FloodFill array limit fix

## Fehler

Beim Übersetzen von `runtime/graphics/common/graphics_api.c` meldete der
C64-Compiler:

```text
Statisches C64-Array ist mit 512 Bytes größer als 256 Bytes.
```

Die Ursache war:

```c
static unsigned int GfxFloodX[256];
```

Auf dem C64 ist `unsigned int` 16 Bit groß. Das Array benötigt deshalb
`256 * 2 = 512` Byte. Der aktuelle Array-Codegenerator verwendet für
statische Arrays einen 8-Bit-Index und begrenzt ein einzelnes Array daher
absichtlich auf 256 Byte.

## Korrektur

Die X-Koordinate wird in zwei bytebreiten Arrays gespeichert:

```c
static unsigned char GfxFloodXLow[256];
static unsigned char GfxFloodXHigh[256];
static unsigned char GfxFloodY[256];
```

Speichern:

```c
GfxFloodXLow[index]  = x & 255u;
GfxFloodXHigh[index] = (x >> 8) & 255u;
```

Laden:

```c
x = GfxFloodXLow[index] | (GfxFloodXHigh[index] << 8);
```

Damit bleibt jedes einzelne statische Array exakt 256 Byte groß. Das
vorhandene C64-Arraylimit muss nicht gelockert werden. X-Koordinaten von
0 bis 319 bleiben vollständig erhalten.
