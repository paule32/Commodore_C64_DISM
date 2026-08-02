// ---------------------------------------------------------------------------
// (c) 2026 by Jens Kallup - paule32
// Alle Rechte vorbehalten.
// ---------------------------------------------------------------------------
#define USE_WHITE
#include "config.h"
#include <stdio.h>
#include <c64.h>

#ifndef CHARACTER_COUNT
#define CHARACTER_COUNT 26
#endif

#ifdef USE_WHITE
#define TEXT_COLOR C64_WHITE
#else
#define TEXT_COLOR C64_YELLOW
#endif

#note C64-Präprozessorbeispiel wird kompiliert

int main(void)
{
    Cursor cursor;

    cursor.x = 0;
    cursor.y = 0;
    poke(SCREEN_CELL(cursor.x), 1);
    poke(C64_COLOR + cursor.x, TEXT_COLOR);
    printf("A");
    return 0;
}
