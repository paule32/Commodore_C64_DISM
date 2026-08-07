#define D64_GRAPHICS_IMPLEMENTATION 1
#include <graphics.h>

/*
 * Gemeinsame, separat kompilierte Grafikalgorithmen.
 * __GraphicsHLine wird vom jeweiligen Zielmodul bereitgestellt und vermeidet
 * die teure komplette Pixel-Adressberechnung innerhalb gefuellter Formen.
 */
void __GraphicsHLine(int x1, int y, int x2, GraphicsColor color);

static int gfx_abs(int value)
{
    if (value < 0)
        return -value;
    return value;
}
static int gfx_min(int a, int b)
{
    if (a < b)
        return a;
    return b;
}
static int gfx_max(int a, int b)
{
    if (a > b)
        return a;
    return b;
}

void DrawLine(int x1, int y1, int x2, int y2, GraphicsColor color)
{
    int dx;
    int sx;
    int dy;
    int sy;
    int error;

    dx = gfx_abs(x2 - x1);
    dy = -gfx_abs(y2 - y1);

    if (x1 < x2)
        sx = 1;
    else
        sx = -1;

    if (y1 < y2)
        sy = 1;
    else
        sy = -1;

    error = dx + dy;

    for (;;) {
        SetPixel(x1, y1, color);
        if (x1 == x2 && y1 == y2) break;
        {
            int e2 = error * 2;
            if (e2 >= dy) { error += dy; x1 += sx; }
            if (e2 <= dx) { error += dx; y1 += sy; }
        }
    }
}

void DrawRect(int x1, int y1, int x2, int y2, GraphicsColor color)
{
    int left = gfx_min(x1, x2), right = gfx_max(x1, x2);
    int top = gfx_min(y1, y2), bottom = gfx_max(y1, y2);
    __GraphicsHLine(left, top, right, color);
    __GraphicsHLine(left, bottom, right, color);
    DrawLine(left, top, left, bottom, color);
    DrawLine(right, top, right, bottom, color);
}

void FillRect(int x1, int y1, int x2, int y2,
              GraphicsColor fill_color, GraphicsColor border_color,
              unsigned int border_width)
{
    int left = gfx_min(x1, x2), right = gfx_max(x1, x2);
    int top = gfx_min(y1, y2), bottom = gfx_max(y1, y2);
    int y;
    unsigned int border;

    if (left < 0) left = 0;
    if (right >= GRAPHICS_WIDTH) right = GRAPHICS_WIDTH - 1;
    if (top < 0) top = 0;
    if (bottom >= GRAPHICS_HEIGHT) bottom = GRAPHICS_HEIGHT - 1;
    if (left > right || top > bottom) return;

    for (y = top; y <= bottom; ++y)
        __GraphicsHLine(left, y, right, fill_color);

    for (border = 0; border < border_width; ++border) {
        if (left + border > right - border ||
            top + border > bottom - border) break;
        DrawRect(left + border, top + border,
                 right - border, bottom - border, border_color);
    }
}

void DrawCircle(int cx, int cy, int radius, GraphicsColor color)
{
    int x = radius, y = 0, decision = 1 - radius;
    while (x >= y) {
        SetPixel(cx+x, cy+y, color); SetPixel(cx-x, cy+y, color);
        SetPixel(cx+x, cy-y, color); SetPixel(cx-x, cy-y, color);
        SetPixel(cx+y, cy+x, color); SetPixel(cx-y, cy+x, color);
        SetPixel(cx+y, cy-x, color); SetPixel(cx-y, cy-x, color);
        ++y;
        if (decision < 0) decision += y * 2 + 1;
        else { --x; decision += (y - x) * 2 + 1; }
    }
}

void FillCircle(int cx, int cy, int radius,
                GraphicsColor fill_color, GraphicsColor border_color,
                unsigned int border_width)
{
    int x = radius, y = 0, decision = 1 - radius;
    unsigned int border;

    if (radius < 0) return;

    while (x >= y) {
        __GraphicsHLine(cx-x, cy+y, cx+x, fill_color);
        __GraphicsHLine(cx-x, cy-y, cx+x, fill_color);
        __GraphicsHLine(cx-y, cy+x, cx+y, fill_color);
        __GraphicsHLine(cx-y, cy-x, cx+y, fill_color);
        ++y;
        if (decision < 0) decision += y * 2 + 1;
        else { --x; decision += (y - x) * 2 + 1; }
    }

    for (border = 0; border < border_width; ++border) {
        if (radius - border < 0) break;
        DrawCircle(cx, cy, radius - border, border_color);
    }
}

void DrawTriangle(int x1, int y1, int x2, int y2,
                  int x3, int y3, GraphicsColor color)
{
    DrawLine(x1, y1, x2, y2, color);
    DrawLine(x2, y2, x3, y3, color);
    DrawLine(x3, y3, x1, y1, color);
}

/* Die restlichen Primitive folgen darunter und verwenden denselben
 * plattformspezifischen Pixel-/Spannweitenpfad. */

/* ------------------------------------------------------------------------- */
/* Weitere plattformunabhaengige Primitive                                   */
/* ------------------------------------------------------------------------- */

#define GFX_FLOOD_STACK_SIZE 256

/*
 * Das C64-Backend adressiert statische Arrays derzeit mit einem 8-Bit-Index.
 * Deshalb darf ein einzelnes Array höchstens 256 Byte belegen. Eine direkte
 * Deklaration
 *
 *     unsigned int GfxFloodX[256];
 *
 * wäre 512 Byte groß. Die 16-Bit-X-Koordinate wird daher in getrennten Low-
 * und High-Byte-Arrays gespeichert. Jedes Array bleibt exakt 256 Byte groß.
 */
static unsigned char GfxFloodXLow[GFX_FLOOD_STACK_SIZE];
static unsigned char GfxFloodXHigh[GFX_FLOOD_STACK_SIZE];
static unsigned char GfxFloodY[GFX_FLOOD_STACK_SIZE];

static void gfx_flood_store(
    unsigned int index,
    int x,
    int y)
{
    GfxFloodXLow[index] = x & 255u;
    GfxFloodXHigh[index] = (x >> 8) & 255u;
    GfxFloodY[index] = y & 255u;
}

static int gfx_flood_load_x(unsigned int index)
{
    return GfxFloodXLow[index] |
           (GfxFloodXHigh[index] << 8);
}

static void gfx_draw_thick_line(
    int x1, int y1, int x2, int y2,
    GraphicsColor color, unsigned int width)
{
    int dx;
    int dy;
    int half;
    int offset;

    if (width <= 1u) {
        DrawLine(x1, y1, x2, y2, color);
        return;
    }

    dx = gfx_abs(x2 - x1);
    dy = gfx_abs(y2 - y1);
    half = (width / 2u);

    if (dx >= dy) {
        for (offset = -half; offset <= half; ++offset)
            DrawLine(x1, y1 + offset, x2, y2 + offset, color);
    } else {
        for (offset = -half; offset <= half; ++offset)
            DrawLine(x1 + offset, y1, x2 + offset, y2, color);
    }
}

void FloodFill(int x, int y, GraphicsColor fill_color)
{
    GraphicsColor source_color;
    unsigned int top;

    if (x < 0 || x >= GRAPHICS_WIDTH || y < 0 || y >= GRAPHICS_HEIGHT)
        return;

    source_color = GetPixel(x, y);
    if (source_color == fill_color)
        return;

    top = 0u;
    gfx_flood_store(top, x, y);
    ++top;

    while (top > 0u) {
        int current_x;
        int current_y;

        --top;
        current_x = gfx_flood_load_x(top);
        current_y = GfxFloodY[top];

        if (GetPixel(current_x, current_y) == source_color) {
            SetPixel(current_x, current_y, fill_color);

            if (current_x > 0 && top < GFX_FLOOD_STACK_SIZE) {
                gfx_flood_store(top, current_x - 1, current_y);
                ++top;
            }
            if (current_x + 1 < GRAPHICS_WIDTH && top < GFX_FLOOD_STACK_SIZE) {
                gfx_flood_store(top, current_x + 1, current_y);
                ++top;
            }
            if (current_y > 0 && top < GFX_FLOOD_STACK_SIZE) {
                gfx_flood_store(top, current_x, current_y - 1);
                ++top;
            }
            if (current_y + 1 < GRAPHICS_HEIGHT && top < GFX_FLOOD_STACK_SIZE) {
                gfx_flood_store(top, current_x, current_y + 1);
                ++top;
            }
        }
    }
}

void FillTriangle(
    int x1, int y1, int x2, int y2, int x3, int y3,
    GraphicsColor fill_color, GraphicsColor border_color,
    unsigned int border_width)
{
    int swap_value;
    int y;

    /* Eckpunkte aufsteigend nach Y sortieren. */
    if (y1 > y2) {
        swap_value = y1; y1 = y2; y2 = swap_value;
        swap_value = x1; x1 = x2; x2 = swap_value;
    }
    if (y2 > y3) {
        swap_value = y2; y2 = y3; y3 = swap_value;
        swap_value = x2; x2 = x3; x3 = swap_value;
    }
    if (y1 > y2) {
        swap_value = y1; y1 = y2; y2 = swap_value;
        swap_value = x1; x1 = x2; x2 = swap_value;
    }

    if (y1 == y3) {
        __GraphicsHLine(gfx_min(x1, gfx_min(x2, x3)), y1,
                        gfx_max(x1, gfx_max(x2, x3)), fill_color);
    } else {
        for (y = y1; y <= y3; ++y) {
            int edge_a;
            int edge_b;

            if (y < y2 && y2 != y1)
                edge_a = x1 + ((x2 - x1) * (y - y1)) / (y2 - y1);
            else if (y3 != y2)
                edge_a = x2 + ((x3 - x2) * (y - y2)) / (y3 - y2);
            else
                edge_a = x2;

            edge_b = x1 + ((x3 - x1) * (y - y1)) / (y3 - y1);
            __GraphicsHLine(gfx_min(edge_a, edge_b), y,
                            gfx_max(edge_a, edge_b), fill_color);
        }
    }

    if (border_width > 0u) {
        gfx_draw_thick_line(x1, y1, x2, y2, border_color, border_width);
        gfx_draw_thick_line(x2, y2, x3, y3, border_color, border_width);
        gfx_draw_thick_line(x3, y3, x1, y1, border_color, border_width);
    }
}

/* 5-Grad-Sinustabelle als Entscheidungsbaum, Festkommafaktor 256. */
static int gfx_sine_quarter(unsigned int index)
{
    if (index == 0u) return 0;
    if (index == 1u) return 22;
    if (index == 2u) return 44;
    if (index == 3u) return 66;
    if (index == 4u) return 88;
    if (index == 5u) return 108;
    if (index == 6u) return 128;
    if (index == 7u) return 147;
    if (index == 8u) return 165;
    if (index == 9u) return 181;
    if (index == 10u) return 196;
    if (index == 11u) return 210;
    if (index == 12u) return 222;
    if (index == 13u) return 232;
    if (index == 14u) return 241;
    if (index == 15u) return 247;
    if (index == 16u) return 252;
    if (index == 17u) return 255;
    return 256;
}

static int gfx_sin_deg(int angle)
{
    unsigned int quadrant;
    unsigned int remainder;
    unsigned int index;
    int value;

    while (angle < 0) angle += 360;
    while (angle >= 360) angle -= 360;

    quadrant = angle / 90u;
    remainder = angle % 90u;
    if (quadrant == 1u || quadrant == 3u)
        remainder = 90u - remainder;

    index = (remainder + 2u) / 5u;
    if (index > 18u) index = 18u;
    value = gfx_sine_quarter(index);

    if (quadrant >= 2u)
        value = -value;
    return value;
}

static int gfx_cos_deg(int angle)
{
    return gfx_sin_deg(angle + 90);
}

void DrawTriangleAngles(
    int center_x, int center_y,
    int radius1, int radius2, int radius3,
    int angle1, int angle2, int angle3,
    GraphicsColor color)
{
    int x1 = center_x + (gfx_cos_deg(angle1) * radius1) / 256;
    int y1 = center_y + (gfx_sin_deg(angle1) * radius1) / 256;
    int x2 = center_x + (gfx_cos_deg(angle2) * radius2) / 256;
    int y2 = center_y + (gfx_sin_deg(angle2) * radius2) / 256;
    int x3 = center_x + (gfx_cos_deg(angle3) * radius3) / 256;
    int y3 = center_y + (gfx_sin_deg(angle3) * radius3) / 256;

    DrawTriangle(x1, y1, x2, y2, x3, y3, color);
}
