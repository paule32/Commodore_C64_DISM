unit System.Graphics;

interface

const
    GraphicsWidth  = 320;
    GraphicsHeight = 200;

    tmUppercase  = 0;
    tmUpperLower = 1;

    ColorBlack       = 0;
    ColorWhite       = 1;
    ColorRed         = 2;
    ColorCyan        = 3;
    ColorPurple      = 4;
    ColorGreen       = 5;
    ColorBlue        = 6;
    ColorYellow      = 7;
    ColorOrange      = 8;
    ColorBrown       = 9;
    ColorLightRed    = 10;
    ColorDarkGray    = 11;
    ColorGray        = 12;
    ColorLightGreen  = 13;
    ColorLightBlue   = 14;
    ColorLightGray   = 15;

type
    TColor = Byte;
    TTextMode = Byte;

procedure SetTextColor(Foreground, Background: Integer);
procedure ClearScreen;
procedure InitGraphics;
procedure DoneGraphics(Mode: TTextMode);

procedure SetPixel(X, Y: Integer; Color: TColor);
function GetPixel(X, Y: Integer): TColor;

procedure DrawLine(X1, Y1, X2, Y2: Integer; Color: TColor);
procedure DrawRect(X1, Y1, X2, Y2: Integer; Color: TColor);
procedure FillRect(X1, Y1, X2, Y2: Integer; FillColor, BorderColor: TColor; BorderWidth: Integer);
procedure DrawCircle(CenterX, CenterY, Radius: Integer; Color: TColor);
procedure FillCircle(CenterX, CenterY, Radius: Integer; FillColor, BorderColor: TColor; BorderWidth: Integer);
procedure FloodFill(X, Y: Integer; FillColor: TColor);
procedure DrawTriangle(X1, Y1, X2, Y2, X3, Y3: Integer; Color: TColor);
procedure FillTriangle(X1, Y1, X2, Y2, X3, Y3: Integer; FillColor, BorderColor: TColor; BorderWidth: Integer);
procedure DrawTriangleAngles(CenterX, CenterY, Radius1, Radius2, Radius3, Angle1, Angle2, Angle3: Integer; Color: TColor);

implementation

end.
