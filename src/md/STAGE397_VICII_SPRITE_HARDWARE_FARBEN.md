# Stage 397: C64-Sprite-Builder – echte VIC-II-Hardwarefarben

**Verbindliche Grundlage:** `d64_dism_asm_396.zip`.

## Hintergrund

C64 VIC-II Sprites sind **keine** frei zeichnbaren 16-Farben-Bitmaps:

* HiRes: 24 × 21 Pixel, transparent oder genau **eine** Spritefarbe (Register `$D027` bis `$D02E`).
* Multicolor: 12 × 21 Doppelpixel, transparent oder drei sichtbare Farben: **MC1** (`$D025`), individuelle **Spritefarbe** (`$D027 + Nummer`) und **MC2** (`$D026`).
* Alle Farbregister enthalten einen **Index 0–15** der C64-Palette. MC1 und MC2 gelten gemeinsam für alle acht gleichzeitig darstellbaren Sprites.
* Die Bildschirm-Hintergrundfarbe ist **keine** vierte gespeicherte Spritefarbe: Der Null-Pixelwert ist transparent.
* Horizontal und vertikal verdoppelte Sprites nutzen die VIC-II-Größenregister `$D01D` bzw. `$D017`; es entstehen dadurch keine zusätzlichen Bitmap-Pixel.

## Neu in der GUI

In `C64SpriteEditorDialog` unter **16 C64-Palettenfarben**:

1. **Zeichnen mit**: Transparent / MC1 / Sprite / MC2 (je nach Modus).
2. Drei **klar beschriftete Register-Farbauswahllisten** mit allen 16 Farbnummern und Vorschau.
3. Die 16 bisherigen Paletten-Farbkacheln setzen den aktuell ausgewählten Zeichenwert.
4. Multicolor-Register lassen sich im HiRes-Modus nicht bearbeiten, die Spritefarbe schon.
5. Änderungen an `$D025`/`$D026` aktualisieren die Metadaten **aller Sprites** des Dokuments.
6. Der Editor informiert ausdrücklich über 1/3 Farben und die Speichergrenzen von `.spr`/`.bin`.

## Speichern

* `.c64sprite` speichert Bitmap, ausgewählte Hardware-Farbregister, Palette, Modus und Größenattribute.
* `.spr`, `.sprite` und `.bin` speichern weiterhin **nur** die 63/64 Hardware-Byte-Bitmapdaten. Das echte C64-Programm muss die Farb-/Multicolor-Register selbst setzen.
* Beim Laden älterer `.c64sprite`-Dateien mit voneinander abweichenden globalen MC-Registern entscheidet der **erste Sprite-Eintrag** über `$D025` und `$D026`; Inkonsistenzen werden für hardwarekonforme Metadaten ausgeglichen.
* 16 frei unterschiedliche Farben innerhalb eines einzelnen Sprites werden bewusst **nicht** simuliert.

## Tests

Neue Tests `test_stage397_sprite_hardware_colors.py` überprüfen Farbindizes 0–15, Registeradressen, globale MC-Synchronisierung, HiRes/Multicolor-Pixelwerte, Laden/Speichern und die GUI-Methoden ohne Qt5. Die Tests aus Stage 396 bleiben erhalten.

**Einschränkung:** Ein interaktiver Windows-/PyQt5-Test ist in der aktuellen Build-Umgebung nicht möglich.
