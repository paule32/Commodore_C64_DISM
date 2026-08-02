// ---------------------------------------------------------------------------
// (c) 2026 by Jens Kallup - paule32
// Alle Rechte vorbehalten.
// ---------------------------------------------------------------------------
#include <stdbool.h>
#include <stdio.h>
#include <c64.h>

int main(void)
{
    unsigned char i;

    clrscr();
    printf("C64 C\n");

    for (i = 0; i < 26; i++) {
        poke(0x0400 + i, 1 + i);
        poke(0xD800 + i, 1);
    }

    return 0;
}
