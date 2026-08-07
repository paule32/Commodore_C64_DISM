/*
 * Legacy C reference implementation.
 *
 * The active C64 target is graphics_c64.asm.  This file is intentionally
 * retained for source history and C-subset regression tests, but graphics.h
 * no longer links it.
 */
#define D64_GRAPHICS_IMPLEMENTATION 1
#include <graphics.h>
#include <c64.h>

#define C64_BITMAP_BASE     0x6000u
#define C64_SCREEN_BASE     0x5C00u
#define C64_TEXT_BASE       0x0400u
#define C64_COLOR_BASE      0xD800u

static unsigned char C64GraphicsActive;
static GraphicsColor C64TextColor = 1;
static GraphicsColor C64BackgroundColor = 0;

static unsigned char __GraphicsMask(int x)
{
    unsigned char mask;
    int bit;

    mask = 0x80u;
    bit = x & 7;

    while (bit > 0) {
        mask = mask / 2u;
        --bit;
    }

    return mask;
}

void SetTextColor(unsigned int foreground, unsigned int background)
{
    C64TextColor = foreground & 15u;
    C64BackgroundColor = background & 15u;
    poke(0x0286u, C64TextColor);
    poke(0xD021u, C64BackgroundColor);
}

void ClearScreen(void)
{
    unsigned int i;
    unsigned int color_byte;

    if (C64GraphicsActive) {
        i = 0u;
        while (i < 8000u) {
            poke(C64_BITMAP_BASE + i, 0u);
            ++i;
        }

        color_byte = (C64TextColor * 16u) | C64BackgroundColor;
        i = 0u;
        while (i < 1000u) {
            poke(C64_SCREEN_BASE + i, color_byte);
            ++i;
        }
    } else {
        i = 0u;
        while (i < 1000u) {
            poke(C64_TEXT_BASE + i, 32u);
            poke(C64_COLOR_BASE + i, C64TextColor);
            ++i;
        }
    }
}

void InitGraphics(void)
{
    poke(0xDD00u, (peek(0xDD00u) & 0xFCu) | 0x02u);
    poke(0xD018u, 0x78u);
    poke(0xD011u, peek(0xD011u) | 0x20u);
    poke(0xD016u, (peek(0xD016u) & 0xEFu) | 0x08u);
    C64GraphicsActive = 1u;
    ClearScreen();
}

void DoneGraphics(TextMode mode)
{
    C64GraphicsActive = 0u;
    poke(0xD011u, peek(0xD011u) & 0xDFu);
    poke(0xDD00u, (peek(0xDD00u) & 0xFCu) | 0x03u);

    if (mode == tmUppercase)
        poke(0xD018u, 0x14u);
    else
        poke(0xD018u, 0x16u);

    ClearScreen();
}

void SetPixel(int x, int y, GraphicsColor color)
{
    unsigned int cell;
    unsigned int offset;
    unsigned int address;
    unsigned char mask;
    unsigned char value;
    unsigned char colors;

    if (x < 0 || x >= 320 || y < 0 || y >= 200)
        return;

    cell = (y / 8) * 40u + (x / 8);
    offset = cell * 8u + (y & 7);
    mask = __GraphicsMask(x);
    address = C64_BITMAP_BASE + offset;
    value = peek(address);
    colors = peek(C64_SCREEN_BASE + cell);

    if ((color & 15u) == (colors & 15u)) {
        value = value & ~mask;
    } else {
        value = value | mask;
        poke(
            C64_SCREEN_BASE + cell,
            ((color & 15u) * 16u) | (colors & 15u)
        );
    }

    poke(address, value);
}

GraphicsColor GetPixel(int x, int y)
{
    unsigned int cell;
    unsigned int offset;
    unsigned char mask;
    unsigned char colors;

    if (x < 0 || x >= 320 || y < 0 || y >= 200)
        return 0u;

    cell = (y / 8) * 40u + (x / 8);
    offset = cell * 8u + (y & 7);
    mask = __GraphicsMask(x);
    colors = peek(C64_SCREEN_BASE + cell);

    if ((peek(C64_BITMAP_BASE + offset) & mask) != 0u)
        return colors / 16u;

    return colors & 15u;
}

void __GraphicsHLine(int x1, int y, int x2, GraphicsColor color)
{
    unsigned int cell;
    unsigned int offset;
    unsigned int bitmap_address;
    unsigned char mask;
    unsigned char value;
    unsigned char colors;
    int remaining;
    int temp;

    if (y < 0 || y >= 200)
        return;

    if (x1 > x2) {
        temp = x1;
        x1 = x2;
        x2 = temp;
    }

    if (x2 < 0 || x1 >= 320)
        return;

    if (x1 < 0)
        x1 = 0;

    if (x2 >= 320)
        x2 = 319;

    cell = (y / 8) * 40u + (x1 / 8);
    offset = cell * 8u + (y & 7);
    bitmap_address = C64_BITMAP_BASE + offset;
    mask = __GraphicsMask(x1);
    remaining = x2 - x1 + 1;

    while (remaining > 0) {
        value = peek(bitmap_address);
        colors = peek(C64_SCREEN_BASE + cell);

        if ((color & 15u) == (colors & 15u)) {
            value = value & ~mask;
        } else {
            value = value | mask;
            poke(
                C64_SCREEN_BASE + cell,
                ((color & 15u) * 16u) | (colors & 15u)
            );
        }

        poke(bitmap_address, value);
        --remaining;
        mask = mask / 2u;

        if (mask == 0u) {
            mask = 0x80u;
            ++cell;
            bitmap_address = bitmap_address + 8u;
        }
    }
}
