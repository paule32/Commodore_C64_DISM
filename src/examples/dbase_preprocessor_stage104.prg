#define VERSION 104
#define FEATURE_LOGGING 1
#define DOUBLE(x) ((x) * 2)

#info dBase preprocessor Stage VERSION

#if 0
    THIS CODE IS SKIPPED COMPLETELY
    #error inactive error must not stop compilation
#endif

#if defined(FEATURE_LOGGING) && DOUBLE(5) == 10
    ? "Makro-Ausdruck aktiv"
#elif VERSION < 100
    ? "Alter Compiler"
#else
    ? "Fallback"
#endif

#ifdef FEATURE_LOGGING
    ? "Logging definiert"
#endif

#ifndef NOT_DEFINED
    ? "NOT_DEFINED fehlt wie erwartet"
#endif

* Beispiel fuer einen echten Include:
* #include "include/common.prg"
