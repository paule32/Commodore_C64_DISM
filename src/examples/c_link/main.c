#include "math_module.h"

int main(void)
{
    int value;

    value = AddValues(20, 30);
    value = ClampValue(value, 0, 40);

    IncrementCounter();
    IncrementCounter();

    printf("value=%d counter=%d\n", value, GetCounter());
    return 0;
}
