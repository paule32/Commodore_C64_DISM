// ---------------------------------------------------------------------------
// (c) 2026 by Jens Kallup - paule32
// Alle Rechte vorbehalten.
// ---------------------------------------------------------------------------
#ifndef C64_STDDEF_H
#define C64_STDDEF_H

/* Das C-Frontend verwendet auf beiden Zielen ein 16-Bit-Datenmodell. */
typedef unsigned int size_t;
typedef signed int ptrdiff_t;
typedef signed int wchar_t;

#define NULL 0

#endif
