#include <graphics.h>
#include <amiga.h>

/* Vier 8000-Byte-Bitplanes; die konkrete Chip-RAM-Zuweisung wird beim
 * Amiga-Backend an die vorhandene Boot-/Copper-Runtime angebunden. */
unsigned char *AmigaGraphicsPlanes[4];

void SetPixel(int x, int y, GraphicsColor color)
{
    unsigned int offset;
    unsigned char mask, plane;
    if (x < 0 || x >= 320 || y < 0 || y >= 200) return;
    offset = (unsigned int)y * 40u + ((unsigned int)x >> 3);
    mask = (unsigned char)(0x80u >> ((unsigned int)x & 7u));
    for (plane = 0; plane < 4; ++plane) {
        if (color & (1u << plane)) AmigaGraphicsPlanes[plane][offset] |= mask;
        else AmigaGraphicsPlanes[plane][offset] &= (unsigned char)~mask;
    }
}

GraphicsColor GetPixel(int x, int y)
{
    unsigned int offset;
    unsigned char mask, plane, color = 0;
    if (x < 0 || x >= 320 || y < 0 || y >= 200) return 0;
    offset = (unsigned int)y * 40u + ((unsigned int)x >> 3);
    mask = (unsigned char)(0x80u >> ((unsigned int)x & 7u));
    for (plane = 0; plane < 4; ++plane)
        if (AmigaGraphicsPlanes[plane][offset] & mask) color |= (1u << plane);
    return color;
}
