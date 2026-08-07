program GraphicsDemo;

uses
    System.Graphics;

var
    CenterColor: TColor;

begin
    SetTextColor(ColorWhite, ColorBlack);
    InitGraphics;
    ClearScreen;

    DrawLine(0, 0, 319, 199, ColorWhite);
    DrawRect(10, 10, 90, 60, ColorRed);
    FillRect(100, 10, 200, 60, ColorCyan, ColorWhite, 2);
    DrawCircle(70, 130, 35, ColorPurple);
    FillCircle(165, 130, 35, ColorGreen, ColorWhite, 2);
    DrawTriangle(225, 175, 270, 95, 315, 175, ColorBlue);
    FillTriangle(210, 185, 260, 105, 310, 185, ColorYellow, ColorWhite, 2);
    DrawTriangleAngles(160, 100, 50, 50, 50, 270, 30, 150, ColorWhite);

    CenterColor := GetPixel(165, 130);

    { Kein DoneGraphics: Der Grafikbildschirm bleibt sichtbar. }
    WriteLn('Graphics demo finished: ', CenterColor);
end.
