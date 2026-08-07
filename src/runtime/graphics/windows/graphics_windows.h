#ifndef D64_WINDOWS_GRAPHICS_H
#define D64_WINDOWS_GRAPHICS_H

#include <stdint.h>

#if defined(_WIN32)
# if defined(D64_GRAPHICS_RUNTIME_EXPORTS)
#  define D64_GRAPHICS_API __declspec(dllexport)
# else
#  define D64_GRAPHICS_API __declspec(dllimport)
# endif
#else
# define D64_GRAPHICS_API
#endif

#ifdef __cplusplus
extern "C" {
#endif

#define GRAPHICS_WIDTH  320
#define GRAPHICS_HEIGHT 200

typedef uint8_t GraphicsColor;
typedef uint8_t TextMode;

D64_GRAPHICS_API void SetTextColor(unsigned int foreground, unsigned int background);
D64_GRAPHICS_API void ClearScreen(void);
D64_GRAPHICS_API void InitGraphics(void);
D64_GRAPHICS_API void DoneGraphics(TextMode mode);
D64_GRAPHICS_API void SetPixel(int x, int y, GraphicsColor color);
D64_GRAPHICS_API GraphicsColor GetPixel(int x, int y);
D64_GRAPHICS_API void DrawLine(int x1, int y1, int x2, int y2, GraphicsColor color);
D64_GRAPHICS_API void DrawRect(int x1, int y1, int x2, int y2, GraphicsColor color);
D64_GRAPHICS_API void FillRect(int x1, int y1, int x2, int y2,
                              GraphicsColor fillColor,
                              GraphicsColor borderColor,
                              unsigned int borderWidth);
D64_GRAPHICS_API void DrawCircle(int centerX, int centerY, int radius, GraphicsColor color);
D64_GRAPHICS_API void FillCircle(int centerX, int centerY, int radius,
                                GraphicsColor fillColor,
                                GraphicsColor borderColor,
                                unsigned int borderWidth);
D64_GRAPHICS_API void FloodFill(int x, int y, GraphicsColor fillColor);
D64_GRAPHICS_API void DrawTriangle(int x1, int y1, int x2, int y2,
                                  int x3, int y3, GraphicsColor color);
D64_GRAPHICS_API void FillTriangle(int x1, int y1, int x2, int y2,
                                  int x3, int y3,
                                  GraphicsColor fillColor,
                                  GraphicsColor borderColor,
                                  unsigned int borderWidth);
D64_GRAPHICS_API void DrawTriangleAngles(int centerX, int centerY,
                                        int radius1, int radius2, int radius3,
                                        int angle1, int angle2, int angle3,
                                        GraphicsColor color);

#ifdef __cplusplus
}
#endif

#endif
