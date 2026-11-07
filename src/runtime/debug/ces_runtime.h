/* CES - Check Early Start (Win32/Win64, optional bootstrap instrumentation).
 * Include only in CES-enabled bootstrap code before trying its real imports.
 * This code must execute INSIDE the packed EXE loader, not in Pascal _start.
 */
#ifndef D64_CES_RUNTIME_H
#define D64_CES_RUNTIME_H
#include <windows.h>

static void d64_ces_write_raw(const char *s) {
    HANDLE h = GetStdHandle(STD_ERROR_HANDLE);
    DWORD written = 0;
    if (!s) return;
    if (h && h != INVALID_HANDLE_VALUE && GetFileType(h) != FILE_TYPE_UNKNOWN) {
        DWORD n = 0;
        const char *p = s;
        while (*p++) ++n;
        if (WriteFile(h, s, n, &written, NULL)) return;
    }
    /* Console-less launch: emit diagnostic even when stderr unavailable. */
    OutputDebugStringA(s);
}

static void d64_ces_hex32(DWORD value, char output[11]) {
    static const char digits[] = "0123456789ABCDEF";
    output[0]='0'; output[1]='x';
    for (int i=0; i<8; ++i) output[2+i]=digits[(value>>(28-4*i))&15];
    output[10]=0;
}

static void d64_ces_failure(const char *phase, const char *module,
                            const char *symbol, DWORD error) {
    char code[11];
    d64_ces_hex32(error, code);
    d64_ces_write_raw("[CES] Early loader error: ");
    d64_ces_write_raw(phase);
    d64_ces_write_raw("\r\n[CES] DLL: ");
    d64_ces_write_raw(module ? module : "<unknown>");
    if (symbol) { d64_ces_write_raw("\r\n[CES] Symbol: "); d64_ces_write_raw(symbol); }
    d64_ces_write_raw("\r\n[CES] GetLastError: ");
    d64_ces_write_raw(code);
    d64_ces_write_raw("\r\n");
}

static HMODULE d64_ces_load_library(const char *module) {
    SetLastError(0);
    HMODULE h = LoadLibraryA(module);
    if (!h) d64_ces_failure("LoadLibraryA", module, NULL, GetLastError());
    return h;
}

static FARPROC d64_ces_get_proc(HMODULE module, const char *module_name,
                               const char *symbol) {
    SetLastError(0);
    FARPROC p = GetProcAddress(module, symbol);
    if (!p) d64_ces_failure("GetProcAddress", module_name, symbol, GetLastError());
    return p;
}

static FARPROC d64_ces_get_ordinal(HMODULE module, const char *module_name,
                                  WORD ordinal) {
    SetLastError(0);
    FARPROC p = GetProcAddress(module, MAKEINTRESOURCEA(ordinal));
    if (!p) {
        char text[11]; d64_ces_hex32((DWORD)ordinal,text);
        d64_ces_failure("GetProcAddress(ordinal)",module_name,text,GetLastError());
    }
    return p;
}

/* Keep failures fatal so a broken bootstrap cannot branch into invalid code. */
#endif
