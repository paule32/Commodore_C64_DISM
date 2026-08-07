; Windows PE32 aliases for System.Graphics
bits 32

extern SetTextColor
extern ClearScreen
extern InitGraphics
extern DoneGraphics
extern SetPixel
extern GetPixel
extern DrawLine
extern DrawRect
extern FillRect
extern DrawCircle
extern FillCircle
extern FloodFill
extern DrawTriangle
extern FillTriangle
extern DrawTriangleAngles

global __pas_System_Graphics_SetTextColor
__pas_System_Graphics_SetTextColor:
    jmp SetTextColor

global __pas_System_Graphics_ClearScreen
__pas_System_Graphics_ClearScreen:
    jmp ClearScreen

global __pas_System_Graphics_InitGraphics
__pas_System_Graphics_InitGraphics:
    jmp InitGraphics

global __pas_System_Graphics_DoneGraphics
__pas_System_Graphics_DoneGraphics:
    jmp DoneGraphics

global __pas_System_Graphics_SetPixel
__pas_System_Graphics_SetPixel:
    jmp SetPixel

global __pas_System_Graphics_GetPixel
__pas_System_Graphics_GetPixel:
    jmp GetPixel

global __pas_System_Graphics_DrawLine
__pas_System_Graphics_DrawLine:
    jmp DrawLine

global __pas_System_Graphics_DrawRect
__pas_System_Graphics_DrawRect:
    jmp DrawRect

global __pas_System_Graphics_FillRect
__pas_System_Graphics_FillRect:
    jmp FillRect

global __pas_System_Graphics_DrawCircle
__pas_System_Graphics_DrawCircle:
    jmp DrawCircle

global __pas_System_Graphics_FillCircle
__pas_System_Graphics_FillCircle:
    jmp FillCircle

global __pas_System_Graphics_FloodFill
__pas_System_Graphics_FloodFill:
    jmp FloodFill

global __pas_System_Graphics_DrawTriangle
__pas_System_Graphics_DrawTriangle:
    jmp DrawTriangle

global __pas_System_Graphics_FillTriangle
__pas_System_Graphics_FillTriangle:
    jmp FillTriangle

global __pas_System_Graphics_DrawTriangleAngles
__pas_System_Graphics_DrawTriangleAngles:
    jmp DrawTriangleAngles
