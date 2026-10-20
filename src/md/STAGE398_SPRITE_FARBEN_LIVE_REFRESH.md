# Stage 398 – C64 Sprite-Builder: Live-Farben und richtige Pinselvorschau

**Verbindliche Grundlage:** `d64_dism_asm_397.zip`.

## Fehlerursache

In `C64SpriteCanvas.set_data()` und `set_meta()` wird `normalize_meta(meta)`
aufgerufen. Die Canvas besitzt daher eine **separate Kopie** der
Sprite-Metadaten. Die Auswahl der Hardware-Farbregister (`$D025`, `$D026`,
`$D027+n`) änderte zwar `C64SpriteEditorDialog.metas`, aktualisierte in
`_update_palette_buttons()` aber **nur** `canvas.palette_entries`.
`C64SpriteCanvas.paintEvent()` las somit alte Registerwerte aus `canvas.meta`.

## Änderungen in `d64_dism.py`

1. `C64SpriteCanvas.set_color_registers(meta)` überträgt nach Änderungen die
   drei tatsächlichen Registerfarbindizes in die Canvas-Kopie und löst
   `update()` aus, ohne Bitmapbytes oder Abmessungen zu verändern.
2. `_update_palette_buttons()` synchronisiert jetzt **Palette UND
   Farbregister** mit der Zeichenfläche.
3. Die vorhandene ComboBox **„Zeichnen mit“** erhält für jeden Pixelcode
   ein Farbfeld (`Qt.DecorationRole`) und einen Tooltip mit der effektiven
   Registerfarbe. Im HiRes-Modus sind nur transparent und individuelle
   Spritefarbe möglich; im Multicolor-Modus transparent/MC1/Sprite/MC2.
4. Bei Auswahl einer Farbkachel wechselt ein zuvor transparenter HiRes-Pinsel
   automatisch auf die Spritefarbe – analog zum bereits vorhandenen
   Multicolor-Verhalten.
5. Farbkachel-Markierung wird beim transparenten HiRes-Pinsel nicht mehr
   fälschlich als aktive Zeichenfarbe hervorgehoben.

## Hardware-Verhalten

* HiRes-Pixel 0 = transparent, 1 = `$D027+n`.
* Multicolor-Pixel 0 = transparent, 1 = `$D025`, 2 = `$D027+n`, 3 = `$D026`.
* Alle drei Register dürfen jeden der 16 C64-Farbwerte verwenden.
* MC1/MC2 gelten weiterhin für alle Sprites gemeinsam.
* Eine Farbänderung verändert **keinen einzigen Bitmap-Bytewert**; `.spr`
  und `.bin` bleiben unverändert kompatibel. `.c64sprite` speichert die
  Registerinformationen.

## Testnachweise

`test_stage398_sprite_live_colors.py`: sechs neue isolierte Tests der
**tatsächlichen** Zeichenflächen-/Editor-Methoden aus `d64_dism.py`,
AST-basiert ohne PyQt5. Darunter das vom Benutzer gewünschte Multicolor-
Szenario MC1=Gelb, Sprite=Blau, MC2=Grau, Farbwechsel auf bereits
gezeichneten Pixeln, Brush-Werte 0/1/2/3 und Dateibyte-Unveränderlichkeit.

Weitere 40 Regressionstests aus den Stages 393–397 bestanden.

**Einschränkung:** Ein interaktiver GUI-Test unter Windows mit PyQt5 wurde
hier nicht durchgeführt.
