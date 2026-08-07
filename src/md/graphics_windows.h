#ifndef D64_WINDOWS_GRAPHICS_H
#define D64_WINDOWS_GRAPHICS_H
/* Gemeinsame 320x200-API; PE32 benutzt ein skalierbares Win32-Fenster. */
void InitGraphics(void);
void DoneGraphics(void);
void ClearScreen(unsigned int color);
void SetPixel(int x, int y, unsigned int color);
unsigned int GetPixel(int x, int y);
void DrawLine(int x1, int y1, int x2, int y2, unsigned int color);
void DrawRect(int x1, int y1, int x2, int y2, unsigned int color);
void FillRect(int x1, int y1, int x2, int y2, unsigned int fillColor,
              unsigned int borderColor, int borderWidth);
void DrawCircle(int cx, int cy, int radius, unsigned int color);
void FillCircle(int cx, int cy, int radius, unsigned int fillColor,
                unsigned int borderColor, int borderWidth);
#endif
