#include <stdio.h>
#include <set.h>

#define START_VALUE 3
#define TWICE(value) ((value) + (value))

#pragma link "recursive_module.c"

typedef enum TColor
{
    colorBlack,
    colorRed,
    colorGreen,
    colorBlue
} TColor;

typedef set<TColor> TColorSet;

typedef struct TPoint
{
    int x;
    int y;
} TPoint;

struct TCounter
{
    int value;
};

int Factorial(int value);
int PersistentCounter(void);

int main(void)
{
    TPoint point;
    struct TCounter counter;
    TColorSet colors;
    int result;

    point.x = START_VALUE;
    point.y = TWICE(START_VALUE);
    counter.value = 10;

    colors = SET_EMPTY();
    colors = SET_ADD(colors, colorRed);
    colors = SET_ADD(colors, colorBlue);

    {
        int result;
        result = point.x + point.y;
        printf("inner=%d\n", result);
    }

    result = Factorial(5);
    printf("factorial=%d\n", result);
    printf("static=%d,%d\n", PersistentCounter(), PersistentCounter());
    printf("set=%d\n", SET_HAS(colors, colorBlue));
    printf("struct=%d\n", counter.value);
    return 0;
}
