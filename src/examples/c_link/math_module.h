#ifndef D64_MATH_MODULE_H
#define D64_MATH_MODULE_H

/* Die Implementierung wird als eigene C-Translation-Unit kompiliert. */
#pragma link "math_module.c"

int AddValues(int left, int right);
int ClampValue(int value, int minimum, int maximum);
void IncrementCounter(void);
int GetCounter(void);

#endif
