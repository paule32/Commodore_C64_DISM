int Factorial(int value)
{
    int partial;

    if (value <= 1)
        return 1;

    partial = Factorial(value - 1);
    return value * partial;
}

int PersistentCounter(void)
{
    static int counter = 40;

    counter++;
    return counter;
}
