[Deutsch](STAGE440_C64_ZELLHINTERGRUND_GROUPBOX_DARKMODE.md) | [English](STAGE440_C64_ZELLHINTERGRUND_GROUPBOX_DARKMODE.en.md)

# Stage 440 – C64 Text Screen: Per-Cell Background and Group-Box Titles

**Basis:** `d64_dism_asm_439.zip` (see the German release notes for the exact baseline).

Each of the 40×25 C64 text-screen cells now stores **character code, foreground color, and background color** separately. **Color only** mode changes the selected cell's background without overwriting its glyph or foreground. Normal drawing updates glyph and foreground while retaining the background. The renderer paints each cell's background before its character.

The extended binary `.scr`/`.screen` format contains **3,000 bytes**: 1,000 characters plus their color data. Appropriate compatibility behavior is retained for existing screen files. Dark-mode styling of QGroupBox titles is corrected for readability. Tests cover cell persistence, painting logic, and theme states.
