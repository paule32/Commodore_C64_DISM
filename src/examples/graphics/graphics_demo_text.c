#include <graphics.h>
#include <stdio.h>

int main(void)
{
    GraphicsColor center_color;

    SetTextColor(ColorWhite, ColorBlack);
    InitGraphics();
    ClearScreen();

    FillCircle(
        160, 100, 50,
        ColorGreen,
        ColorWhite,
        2
    );

    center_color = GetPixel(160, 100);

    /*
     * Erst hier wird der Grafikmodus bewusst verlassen. Die gezeichnete
     * Grafik verschwindet; danach ist die Textausgabe sichtbar.
     */
    DoneGraphics(tmUpperLower);
    printf("Graphics demo finished: %d\n", center_color);

    return 0;
}
