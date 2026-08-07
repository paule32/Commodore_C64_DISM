#include <set.h>

CSet SetEmpty(void)
{
    return 0;
}

CSet SetOf(int element)
{
    CSet mask;

    if (element < 0 || element > 15)
        return 0;

    mask = 1;

    while (element > 0)
    {
        mask = mask * 2;
        element--;
    }

    return mask;
}

CSet SetAdd(CSet value, int element)
{
    return value | SetOf(element);
}

CSet SetRemove(CSet value, int element)
{
    return value & ~SetOf(element);
}

CSet SetUnion(CSet left, CSet right)
{
    return left | right;
}

CSet SetIntersection(CSet left, CSet right)
{
    return left & right;
}

CSet SetDifference(CSet left, CSet right)
{
    return left & ~right;
}

bool SetContains(CSet value, int element)
{
    return (value & SetOf(element)) != 0;
}
