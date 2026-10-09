; Windows PE32 aliases for System.Graphics
bits 32

import SetTextColor, "d64graphics.dll", "SetTextColor"
import ClearScreen, "d64graphics.dll", "ClearScreen"
import InitGraphics, "d64graphics.dll", "InitGraphics"
import DoneGraphics, "d64graphics.dll", "DoneGraphics"
import SetPixel, "d64graphics.dll", "SetPixel"
import GetPixel, "d64graphics.dll", "GetPixel"
import DrawLine, "d64graphics.dll", "DrawLine"
import DrawRect, "d64graphics.dll", "DrawRect"
import FillRect, "d64graphics.dll", "FillRect"
import DrawCircle, "d64graphics.dll", "DrawCircle"
import FillCircle, "d64graphics.dll", "FillCircle"
import FloodFill, "d64graphics.dll", "FloodFill"
import DrawTriangle, "d64graphics.dll", "DrawTriangle"
import FillTriangle, "d64graphics.dll", "FillTriangle"
import DrawTriangleAngles, "d64graphics.dll", "DrawTriangleAngles"

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
