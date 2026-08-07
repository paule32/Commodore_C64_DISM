#include "math_module.h"

static int module_counter;

int AddValues(int left, int right)
{
    return left + right;
}

int ClampValue(int value, int minimum, int maximum)
{
    if (value < minimum) {
        return minimum;
    }
    if (value > maximum) {
        return maximum;
    }
    return value;
}

void IncrementCounter(void)
{
    module_counter += 1;
}

int GetCounter(void)
{
    return module_counter;
}
