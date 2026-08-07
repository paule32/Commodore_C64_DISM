#ifndef D64_GRAPHICS_H
#define D64_GRAPHICS_H

#include <stdint.h>

#if defined(__D64_TARGET_C64__) && !defined(D64_GRAPHICS_IMPLEMENTATION)
#pragma d64_link_asm "../c64/graphics_c64.asm"
#endif

#if defined(__D64_TARGET_AMIGA__) && !defined(D64_GRAPHICS_IMPLEMENTATION)
#pragma d64_link_asm "../amiga/graphics_amiga.asm"
#endif

#if defined(__D64_TARGET_PE32__) && !defined(D64_GRAPHICS_IMPLEMENTATION)
#pragma d64_link_asm "../windows/graphics_windows.pe32.asm"
#endif

/* Gemeinsame Bildschirmgröße des Grafikmodus. */
#define GRAPHICS_WIDTH  320
#define GRAPHICS_HEIGHT 200

/* DoneGraphics()-Textmodi. */
#define tmUppercase  0
#define tmUpperLower 1

/* Kompatible Großschreibungsvarianten für C-Projekte. */
#define TM_UPPERCASE   tmUppercase
#define TM_UPPER_LOWER tmUpperLower

/* Gemeinsame 16-Farben-Indizes, identisch zu System.Graphics. */
#define ColorBlack       0
#define ColorWhite       1
#define ColorRed         2
#define ColorCyan        3
#define ColorPurple      4
#define ColorGreen       5
#define ColorBlue        6
#define ColorYellow      7
#define ColorOrange      8
#define ColorBrown       9
#define ColorLightRed    10
#define ColorDarkGray    11
#define ColorGray        12
#define ColorLightGreen  13
#define ColorLightBlue   14
#define ColorLightGray   15

typedef uint8_t GraphicsColor;
typedef uint8_t TextMode;

/*
 * Auf dem C64 werden nur die unteren vier Bits benutzt.  Der C64-Zielcode
 * verwendet den VIC-II-Multicolor-Bitmapmodus: Die API-Koordinaten bleiben
 * 0..319, jeweils zwei benachbarte X-Koordinaten teilen sich jedoch ein
 * zweifach breites Farbpixel. Dadurch stehen pro 8x8-Zelle Hintergrund plus
 * drei lokale Farben zur Verfügung.
 * Beim Amiga sind Vorder- und Hintergrund 12-Bit-OCS-$RGB-Werte.
 */
void SetTextColor(unsigned int foreground, unsigned int background);

void ClearScreen(void);
void InitGraphics(void);
void DoneGraphics(TextMode mode);

void SetPixel(int x, int y, GraphicsColor color);
GraphicsColor GetPixel(int x, int y);

void DrawLine(
    int x1, int y1,
    int x2, int y2,
    GraphicsColor color
);

void DrawRect(
    int x1, int y1,
    int x2, int y2,
    GraphicsColor color
);

void FillRect(
    int x1, int y1,
    int x2, int y2,
    GraphicsColor fill_color,
    GraphicsColor border_color,
    unsigned int border_width
);

void DrawCircle(
    int center_x,
    int center_y,
    int radius,
    GraphicsColor color
);

void FillCircle(
    int center_x,
    int center_y,
    int radius,
    GraphicsColor fill_color,
    GraphicsColor border_color,
    unsigned int border_width
);

void FloodFill(
    int x,
    int y,
    GraphicsColor fill_color
);

void DrawTriangle(
    int x1, int y1,
    int x2, int y2,
    int x3, int y3,
    GraphicsColor color
);

void FillTriangle(
    int x1, int y1,
    int x2, int y2,
    int x3, int y3,
    GraphicsColor fill_color,
    GraphicsColor border_color,
    unsigned int border_width
);

/*
 * Winkel werden in Grad angegeben. In dieser Compilerstufe müssen die drei
 * Winkel und Radien konstante Ausdrücke sein; Mittelpunkt und Farbe dürfen
 * Laufzeitwerte sein.
 */
void DrawTriangleAngles(
    int center_x,
    int center_y,
    int radius1,
    int radius2,
    int radius3,
    int angle1,
    int angle2,
    int angle3,
    GraphicsColor color
);

#endif
