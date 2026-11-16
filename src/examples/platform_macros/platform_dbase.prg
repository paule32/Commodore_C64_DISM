// Stage 603: automatic target macros. WIN32 is defined on PE32 AND PE64.
#ifdef WINDOWS
    ? "Windows-Ziel"
#endif
#ifdef WIN32
    ? "Windows API verfuegbar"
#endif
#ifdef WIN64
    ? "64-Bit Windows"
#endif
#ifdef LINUX
    ? "Linux-Ziel"
#endif
#if LINUX == 0
    ? "Kein Linux-Ziel"
#endif
