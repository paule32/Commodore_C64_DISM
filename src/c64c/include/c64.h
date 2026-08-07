// ---------------------------------------------------------------------------
// (c) 2026 by Jens Kallup - paule32
// Alle Rechte vorbehalten.
// ---------------------------------------------------------------------------
#ifndef C64_H
#define C64_H

#include <stdint.h>

#define C64_SCREEN 0x0400
#define C64_COLOR  0xD800

#define C64_BLACK        0
#define C64_WHITE        1
#define C64_RED          2
#define C64_CYAN         3
#define C64_PURPLE       4
#define C64_GREEN        5
#define C64_BLUE         6
#define C64_YELLOW       7
#define C64_ORANGE       8
#define C64_BROWN        9
#define C64_LIGHT_RED   10
#define C64_DARK_GREY   11
#define C64_GREY        12
#define C64_LIGHT_GREEN 13
#define C64_LIGHT_BLUE  14
#define C64_LIGHT_GREY  15

void clrscr(void);
void halt(void);
void poke(uint16_t address, uint8_t value);
uint8_t peek(uint16_t address);
uint8_t lo(uint16_t value);
uint8_t hi(uint16_t value);

void c64_clrscr(void);
void c64_halt(void);
void c64_poke(uint16_t address, uint8_t value);
uint8_t c64_peek(uint16_t address);

#endif
