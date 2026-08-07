# Amiga-Zebrastreifen: Copper-Fix

## Ursache

Die OCS-Bitplane-DMA erhöht die Register `BPLxPTH/BPLxPTL` während der
Bildausgabe. Die bisherige Implementierung schrieb die vier Startadressen nur
einmal in `InitGraphics`. Nach dem ersten Bild standen die Zeiger deshalb am
Ende der Bitplanes und das nächste Bild wurde aus den nachfolgenden
Speicherbereichen gelesen. Das sichtbare Ergebnis waren horizontale helle und
dunkle Streifen.

## Korrektur

Die Ausgabe verwendet nun eine Copper-Liste bei `$00010000`. Sie schreibt in
jedem Bild erneut:

- `DIWSTRT`, `DIWSTOP`
- `DDFSTRT`, `DDFSTOP`
- `BPLCON0`, `BPLCON1`, `BPLCON2`
- `BPL1MOD`, `BPL2MOD`
- alle vier Bitplane-Zeiger
- die 16 Farbregister

`DMACON` wird danach mit `$8380` aktiviert:

```text
SETCLR + DMAEN + BPLEN + COPEN
```

`DoneGraphics` installiert eine zweite Copper-Liste für die Text-Bitplane.
Damit bleibt auch die Textausgabe nach dem Grafikmodus über mehrere Frames
stabil.

## Speicherlayout

```text
$00010000  Copper-Liste
$00018000  Text-Bitplane, 8000 Byte
$00020000  Grafik-Bitplane 0
$00022000  Grafik-Bitplane 1
$00024000  Grafik-Bitplane 2
$00026000  Grafik-Bitplane 3
$00040000  bootfähiger Programmcode
$0007FFFC  Stack
```

## Weitere Änderungen

- Umschaltung erst im sicheren unteren Vertical-Blank-Bereich
- `SetTextColor` aktualisiert zusätzlich die Farbwerte der Text-Copper-Liste
- Compiler-Textlaufzeit verwendet ebenfalls eine Copper-Liste
- `System.Graphics.generated.amiga.asm` wurde mit der echten Implementierung
  synchronisiert
