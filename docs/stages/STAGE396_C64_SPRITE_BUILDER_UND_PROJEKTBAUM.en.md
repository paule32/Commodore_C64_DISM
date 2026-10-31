[Deutsch](STAGE396_C64_SPRITE_BUILDER_UND_PROJEKTBAUM.md) | [English](STAGE396_C64_SPRITE_BUILDER_UND_PROJEKTBAUM.en.md)

# Stage 396 – C64 Sprite Builder and Project Information

**Basis:** `d64_dism_asm_395.zip`.

## Sprite builder

The menu **File → New → C= 64 m68k → Sprite Editor** opens the `c64_sprite_builder_dock`. A 16-color palette may be loaded from `.pal`, `.palette`, or `.bin`. The drawing grid supports 1–24 columns in HiRes or 1–12 columns in Multicolor, and 1–21 rows. HiRes, Multicolor, and horizontal/vertical VIC-II 2× expansion flags are supported. Actual hardware sprites remain 24×21 HiRes pixels or 12×21 Multicolor double pixels; resizing the drawing grid only changes the editing viewport.

The editor supports creating several sprites, switching between them, drawing, erasing, displaying a pixel grid, saving and loading. Raw sprite data have 63 bitmap bytes plus an optional 64th padding byte. `.spr`, `.sprite`, and `.bin` remain binary hardware formats; the project format contains the additional palette and editor metadata. JSON/preview data are kept separate from the raw hardware bytes.

## Project tree and persistence

A new **C= 64 Sprites** branch offers context actions for creating a sprite, adding sprite files, and expanding/collapsing nodes. Sprite leaves support opening in the builder and removing from the project; unsaved leaves also offer **Save As**.

Creating a Sprite Editor document adds an unsaved draft and tree leaf. The first save assigns a filename and path. If the path already exists as a leaf, the existing leaf is reused. Save As on an existing file preserves the old leaf and adds the new file. Clicking or double-clicking a saved sprite file opens its builder.

Project INI files gain `[Category.c64.sprites]`. Only saved paths are persisted; unsaved drafts are not written as fictitious files. Older `.pro` files remain compatible, and the existing BASIC-resource sprite type is retained.

## Validation

Source syntax was checked with `py_compile`. Isolated tests cover HiRes/Multicolor codecs, RAW63/64, palette and JSON formats, menu and dock integration, tree-leaf state, duplicate prevention, INI persistence, discard, and Stage 393–395 regressions. A full Windows/PyQt5 GUI/docking test remains outstanding.

## Source code and command examples (unchanged)

```text
Projekt-Informationen
├─ BASIC - Programme
│  └─ Commodore C= 64
│     └─ Ressourcen
│        └─ (... alte Ressourcen bleiben erhalten ...)
├─ Assembler-Programme
├─ (...)
└─ C= 64 Sprites
   ├─ MeinSprite.c64sprite
   ├─ Gegner.spr
   └─ Sprite_1.c64sprite       (ungespeichert)
```

