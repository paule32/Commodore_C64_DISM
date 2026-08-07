// ---------------------------------------------------------------------------
// Direkte Amiga-500-Bildschirmfunktionen des eingebauten 68000-Backends.
// ---------------------------------------------------------------------------
#ifndef D64_AMIGA_H
#define D64_AMIGA_H

#define AMIGA_BLACK   0x000
#define AMIGA_BLUE    0x00F
#define AMIGA_GREEN   0x0F0
#define AMIGA_CYAN    0x0FF
#define AMIGA_RED     0xF00
#define AMIGA_MAGENTA 0xF0F
#define AMIGA_YELLOW  0xFF0
#define AMIGA_WHITE   0xFFF

void amiga_set_text_color(
    unsigned int foreground,
    unsigned int background
);

void clrscr(void);

#endif
