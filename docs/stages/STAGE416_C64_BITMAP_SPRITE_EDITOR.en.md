[Deutsch](STAGE416_C64_BITMAP_SPRITE_EDITOR.md) | [English](STAGE416_C64_BITMAP_SPRITE_EDITOR.en.md)

# Stage 416 – C64 Bitmap Sprite Editor

**Basis:** `d64_dism_asm_415.zip` (see the German release notes for the exact baseline).

The Project Information tree gains **New Bitmap Sprite** under **C=64 Sprites**, and the File → New → C=64 menu gains a Bitmap Sprite Editor. Each document opens in its own dock, separately from the hardware sprite editor. New entries use `Bitmap_Sprite_N.bmsprite`; saved `.bmsprite`/`.bmspr` files are tracked through `Category.c64.sprites` and can be reopened from the tree.

Users can paint in any of the 16 C64 palette colors or transparent pixels, drag to draw, and right-click to erase. Document-wide image sizes range from 1×1 to 128×128 (default 24×21); zoom is adjustable. The dedicated **binary** file format uses the `C64BMSP1` header and stores pixel indices, dimensions, and sprite records rather than JSON. Existing hardware-sprite behavior remains unchanged. Code and codec tests were run; native Windows/PyQt5 interaction remains to be checked.
