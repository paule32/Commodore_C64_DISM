# Grafikquellen, PUI und Amiga-Implementierung

Die Grafik-API liegt in getrennten, regulär kompilierten beziehungsweise
assemblierten Dateien. Es werden keine Graphics-Intrinsics verwendet.

## Pascal-Dateien

- `c64pascal/units/System/Graphics.pas`
  - öffentliches Pascal-Interface
  - Konstanten, Typen und Routinedeklarationen
- `c64pascal/units/System/Graphics.pui`
  - vom Pascal-Compiler erzeugte Interface-Informationen
  - Parameter, Rückgabetypen und externe Linkersymbole
  - Verweis auf das zielabhängige Implementierungsmodul
- `c64pascal/units/System/Graphics.amiga.asm`
  - vollständige Motorola-68000-Implementierung für Amiga 500

## PUI erzeugen

```powershell
python d64_dism.py --write-pui c64pascal\units\System\Graphics.pas
```

Die PUI-Version 2 speichert:

- globale Prozeduren und Funktionen,
- Parameternamen und Parametertypen,
- `value`/`const`/`var`,
- Rückgabetypen,
- stabile Linkersymbolnamen,
- zielabhängige ASM-Implementierungsdateien.

Für `System.Graphics` enthält die PUI unter anderem:

```json
{
  "implementation": {
    "assembly": {
      "amiga": "Graphics.amiga.asm"
    }
  }
}
```

## Normale externe Pascal-Aufrufe

Ein Pascal-Programm verwendet die Unit regulär:

```pascal
program GraphicsDemo;

uses
    System.Graphics;

begin
    InitGraphics;
    SetPixel(10, 20, ColorRed);
    DoneGraphics(tmUpperLower);
end.
```

Der Compiler liest `System.Graphics.pui` und erzeugt normale externe Aufrufe:

```asm
bsr __pas_System_Graphics_InitGraphics
bsr __pas_System_Graphics_SetPixel
bsr __pas_System_Graphics_DoneGraphics
```

Die Argumente werden als 16-Bit-Werte von links nach rechts auf den
Motorola-68000-Stack gelegt. Der Aufrufer räumt die Argumente wieder ab.
`GetPixel` liefert den Farbwert in `D0.W` zurück.

## Statisches Zusammenführen der ASM-Module

Da der vorhandene Amiga-Assembler eine zusammenhängende Quelldatei assembliert,
führt der Pascal-Compiler den erzeugten Programm-Assembler und alle über PUI
referenzierten Unit-ASM-Module vor dem Assemblieren zusammen.

Das ist ein normaler Quelldatei-/Modul-Linkschritt und kein Compiler-Intrinsic.
Das ausführbare `System.Graphics.amiga.asm` bleibt eine eigenständige Datei.

## Direkte Pascal-Unit-Kompilierung

```powershell
python d64_dism.py --write-amiga c64pascal\units\System\Graphics.pas
```

Ergebnis:

```text
c64pascal/units/System/Graphics.pui
c64pascal/units/System/Graphics.generated.amiga.asm
```

Die erzeugte ASM-Datei enthält den Unit-Anker und das statisch angefügte Modul
`System.Graphics.amiga.asm`. Für eine Unit wird bewusst kein bootfähiges ADF
erzeugt.

## Implementierte Amiga-Funktionen

- `SetTextColor`
- `ClearScreen`
- `InitGraphics`
- `DoneGraphics`
- `SetPixel`
- `GetPixel`
- `DrawLine`
- `DrawRect`
- `FillRect`
- `DrawCircle`
- `FillCircle`
- `FloodFill`
- `DrawTriangle`
- `FillTriangle`
- `DrawTriangleAngles`

## Amiga-Grafikmodus

`InitGraphics` richtet einen OCS-Bildschirm mit folgenden Eigenschaften ein:

```text
Auflösung: 320 x 200
Farben:    16
Bitplanes: 4
```

Verwendete Chip-RAM-Bereiche:

```text
Text-Bitplane: $00018000
Bitplane 0:    $00020000
Bitplane 1:    $00022000
Bitplane 2:    $00024000
Bitplane 3:    $00026000
```

Das Layout ist für das vorhandene Standalone-Boot-ADF-Backend vorgesehen. Der
Programmpayload wird davon getrennt geladen.

## Aktuelle Grenzen

- `FloodFill` verwendet einen begrenzten Arbeitsstapel mit 2048 Punkten.
- `FillTriangle` füllt über einen inneren Startpunkt und FloodFill; eine
  Randbreite größer als 1 wird gegenwärtig als sichtbarer einfacher Rand
  behandelt.
- Globale Pascal-Routinen mit eigenem Code im `implementation`-Teil beliebiger
  Units werden noch nicht allgemein übersetzt. `System.Graphics` verwendet
  deshalb das getrennte, regulär assemblierte Zielmodul.

## Copper-Korrektur gegen horizontale Streifen

Die Bitplane-Zeiger werden nun durch eine Copper-Liste bei `$00010000` in jedem Frame erneut geladen. Details stehen in `AMIGA_COPPER_ZEBRA_FIX.md`.

## C64-Multicolor-Zielmodul

Für den C64 wird dieselbe öffentliche C-/Pascal-API mit einem getrennten
MOS-6510-Modul umgesetzt:

```text
runtime/graphics/c64/graphics_c64.asm
```

Der C64 verwendet den VIC-II-Multicolor-Bitmapmodus. Die API-Koordinaten bleiben
`320 x 200`; zwei benachbarte X-Koordinaten teilen sich ein zweifach breites
Farbpixel. Dadurch kann jede 8x8-Anzeigezelle neben der globalen
Hintergrundfarbe drei lokale Farben darstellen. Die Amiga-Implementierung
bleibt eine echte 320x200-Ausgabe mit vier Bitplanes.
