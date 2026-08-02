// ---------------------------------------------------------------------------
// (c) 2026 by Jens Kallup - paule32
// Alle Rechte vorbehalten.
// ---------------------------------------------------------------------------
#ifndef C64_EXAMPLE_CONFIG_H
#define C64_EXAMPLE_CONFIG_H

#include <stdint.h>

#define SCREEN_CELL(index) (C64_SCREEN + (index))

typedef struct Cursor {
    uint8_t x;
    uint8_t y;
} Cursor;

// ---------------------------------------------------------------------------
// Prototypen dürfen in Headern stehen, auch wenn sie nicht aufgerufen 
// werden.
// ---------------------------------------------------------------------------
void example_hook(Cursor *cursor);

#endif
