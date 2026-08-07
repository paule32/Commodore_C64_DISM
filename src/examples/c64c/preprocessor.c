// ---------------------------------------------------------------------------
// (c) 2026 by Jens Kallup - paule32
// Alle Rechte vorbehalten.
// ---------------------------------------------------------------------------
#define TARGET_LEVEL 2
#define COLOR_NAME(suffix) C64_ ## suffix
#include "config.h"
#include <stdio.h>
#include <c64.h>

#ifndef CHARACTER_COUNT
#define CHARACTER_COUNT 26
#endif

#if TARGET_LEVEL >= 2
#define TEXT_COLOR COLOR_NAME(WHITE)
#else
#define TEXT_COLOR C64_YELLOW
#endif

#info C64-Präprozessorbeispiel Stufe TARGET_LEVEL wird kompiliert

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
