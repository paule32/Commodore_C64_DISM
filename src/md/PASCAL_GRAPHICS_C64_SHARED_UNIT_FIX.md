# Gemeinsame Pascal-Grafik-Unit für Amiga und C64

## Behobener Fehler

Der C64-Pascal-Codegenerator fing `SetTextColor` vor der PUI-Auflösung ab und
meldete:

```text
SetTextColor ist eine Amiga-spezifische Anweisung.
```

Dadurch konnte dieselbe `System.Graphics`-Unit nicht für beide Ziele verwendet
werden.

## Neue Aufteilung

```text
c64pascal/units/System/
├── Graphics.pas
├── Graphics.pui
├── Graphics.amiga.asm
└── Graphics.c64.c
```

Die öffentliche Pascal-Datei ist für beide Ziele identisch. Die PUI enthält:

```json
{
  "implementation": {
    "assembly": {
      "amiga": "Graphics.amiga.asm"
    },
    "c": {
      "c64": "Graphics.c64.c"
    }
  }
}
```

`Graphics.c64.c` fordert zwei getrennte C-Translation-Units an:

```c
#pragma link "../../../runtime/graphics/c64/graphics_target.c"
#pragma link "../../../runtime/graphics/common/graphics_api.c"
```

Der Pascal-Compiler ruft dafür den normalen C-Modulcompiler auf und schreibt:

```text
Graphics.generated.c64.asm
```

## 6510-Aufrufkonvention

Skalare Argumente werden in Quellreihenfolge als High-/Low-Byte auf den
Hardwarestack gelegt. Der Rückgabewert einer Funktion liegt in `A/X`.
Diese ABI ist identisch mit den getrennt kompilierten C64-C-Funktionen.

Die PUI-Symbole werden mit normalen Wrappern verbunden:

```asm
__pas_System_Graphics_SetPixel:
    jmp SetPixel
```

Es werden keine Grafik-Intrinsics verwendet.

## Farbwerte

Die Konstanten `ColorBlack` bis `ColorLightGray` bleiben Indizes `0..15`.

- Amiga: Der Index wird über die OCS-Palette in vier Bitplanes umgesetzt.
- C64: Der Index wird als VIC-II-Farbe verwendet. Im 320×200-Hires-Modus
  gelten weiterhin zwei Farben je 8×8-Zelle.

## Kompilierung

Dasselbe Programm kann mit unterschiedlichen Zielen übersetzt werden:

```powershell
python d64_dism.py --write-amiga examples\graphics\graphics_demo.pas
python d64_dism.py --write-prg   examples\graphics\graphics_demo.pas
```
