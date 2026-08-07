// ---------------------------------------------------------------------------
// (c) 2026 by Jens Kallup - paule32
// Alle Rechte vorbehalten.
// ---------------------------------------------------------------------------
#ifndef C64_STDINT_H
#define C64_STDINT_H

/* Exakte Typen des derzeitigen 8-/16-Bit-Datenmodells. */
typedef signed char int8_t;
typedef unsigned char uint8_t;
typedef signed int int16_t;
typedef unsigned int uint16_t;

typedef int8_t int_least8_t;
typedef uint8_t uint_least8_t;
typedef int16_t int_least16_t;
typedef uint16_t uint_least16_t;

typedef int16_t int_fast8_t;
typedef uint16_t uint_fast8_t;
typedef int16_t int_fast16_t;
typedef uint16_t uint_fast16_t;

typedef int16_t intptr_t;
typedef uint16_t uintptr_t;
typedef int16_t intmax_t;
typedef uint16_t uintmax_t;

#define INT8_MIN       (-128)
#define INT8_MAX       127
#define UINT8_MAX      255
#define INT16_MIN      (-32767 - 1)
#define INT16_MAX      32767
#define UINT16_MAX     65535

#define INT_LEAST8_MIN INT8_MIN
#define INT_LEAST8_MAX INT8_MAX
#define UINT_LEAST8_MAX UINT8_MAX
#define INT_LEAST16_MIN INT16_MIN
#define INT_LEAST16_MAX INT16_MAX
#define UINT_LEAST16_MAX UINT16_MAX

#define INT_FAST8_MIN  INT16_MIN
#define INT_FAST8_MAX  INT16_MAX
#define UINT_FAST8_MAX UINT16_MAX
#define INT_FAST16_MIN INT16_MIN
#define INT_FAST16_MAX INT16_MAX
#define UINT_FAST16_MAX UINT16_MAX

#define INTPTR_MIN     INT16_MIN
#define INTPTR_MAX     INT16_MAX
#define UINTPTR_MAX    UINT16_MAX
#define INTMAX_MIN     INT16_MIN
#define INTMAX_MAX     INT16_MAX
#define UINTMAX_MAX    UINT16_MAX

#define INT8_C(value)  value
#define UINT8_C(value) value
#define INT16_C(value) value
#define UINT16_C(value) value
#define INTMAX_C(value) value
#define UINTMAX_C(value) value

#endif
