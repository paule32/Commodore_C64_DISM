# System.Graphics – Amiga-Implementierung

## Dateien

```text
c64pascal/units/System/Graphics.pas
c64pascal/units/System/Graphics.pui
c64pascal/units/System/Graphics.amiga.asm
```

`System.Graphics.amiga.asm` ist ausführbarer Motorola-68000-Quellcode. Die
Datei wird nicht in den Python-Compiler eingebettet und nicht als Intrinsic
erzeugt.

## ABI

Die Pascal-PUI exportiert Symbole der Form:

```text
__pas_System_Graphics_<Funktionsname>
```

Wertparameter werden von links nach rechts als Words auf den Stack gelegt.
Nach der Rücksprungadresse liegt deshalb der letzte Parameter bei `4(sp)`.
Funktionen liefern skalare 16-Bit-Ergebnisse in `D0.W`.

Beispiel:

```pascal
SetPixel(10, 20, ColorRed);
```

wird sinngemäß zu:

```asm
move.w #$000A,-(sp)
move.w #$0014,-(sp)
move.w #$0002,-(sp)
bsr __pas_System_Graphics_SetPixel
addq.l #6,sp
```

## InitGraphics

`InitGraphics`:

- sperrt zunächst die benötigten DMA-Kanäle,
- richtet das 320×200-DIW-/DDF-Timing ein,
- aktiviert vier Bitplanes,
- trägt die vier Bitplane-Adressen ein,
- lädt die 16-farbige Palette,
- löscht alle Bitplanes,
- aktiviert Master- und Bitplane-DMA.

## DoneGraphics

`DoneGraphics`:

- speichert den gewünschten Textmodus,
- deaktiviert den Grafikzustand,
- schaltet auf die Text-Bitplane zurück,
- stellt Schwarz/Weiß für die Textausgabe ein,
- löscht die Textfläche.

## Pixelzugriff

`SetPixel` berechnet für 320 Pixel je Zeile:

```text
ByteOffset = Y * 40 + X div 8
Bitmaske   = $80 >> (X and 7)
```

Die vier Bits des Farbwertes werden in die vier Bitplanes geschrieben.
`GetPixel` liest dieselben vier Bits und setzt daraus den Farbwert `0..15`
zusammen.

## Zeichenroutinen

- Linien: ganzzahliger Bresenham-Algorithmus
- Rechtecke: Linien beziehungsweise Scanlines
- Kreise: Midpoint-Circle-Algorithmus
- FloodFill: iterativer Punktstapel
- Dreiecke: drei Linien; Füllung über Innenpunkt und FloodFill
- Winkeldreiecke: Festkomma-Sinustabelle ohne Fließkomma-Runtime

## Copper-Korrektur gegen horizontale Streifen

Die Bitplane-Zeiger werden nun durch eine Copper-Liste bei `$00010000` in jedem Frame erneut geladen. Details stehen in `AMIGA_COPPER_ZEBRA_FIX.md`.
