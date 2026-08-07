// ---------------------------------------------------------------------------
// Standalone-Amiga-500: printf über einen 8x8-Bitmapzeichensatz
// ---------------------------------------------------------------------------
#include <stdio.h>
#include <amiga.h>

int main(void)
{
    amiga_set_text_color(AMIGA_GREEN, AMIGA_BLACK);
    printf("Amiga 500 Bitmap-Text\n");
    printf("C printf: Counter = %d\n", 5);
    printf("Farbe: gruen auf schwarz\n");
    return 0;
}
