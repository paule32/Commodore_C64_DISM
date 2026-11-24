// Stage 676: former c64_dbase_runtime.dll exports integrated into libd64_runtime.dll.
// Freestanding C ABI for PE32 cdecl and Microsoft x64, without a Qt dependency.
// No C++ standard library or runtime initialization is required.
#if defined(__i386__) && defined(__GNUC__)
# define DBASE_CDECL __attribute__((cdecl))
# define DBASE_WINAPI __attribute__((stdcall))
#else
# define DBASE_CDECL
# define DBASE_WINAPI
#endif
#if defined(_WIN32)
# define DBASE_DLLIMPORT __declspec(dllimport)
#else
# define DBASE_DLLIMPORT
#endif

typedef unsigned int dbase_u32;
typedef unsigned long long dbase_u64;
typedef unsigned char dbase_u8;
typedef short dbase_i16;

// Win32 declarations are local to avoid pulling a CRT/Win32 header into the
// freestanding runtime. LONG/DWORD are 32-bit on both Windows architectures.
#if defined(_WIN32)
struct DBaseCoord { dbase_i16 x, y; };
struct DBaseRect { dbase_i16 left, top, right, bottom; };
struct DBaseConsoleInfo {
    DBaseCoord size, cursor;
    unsigned short attributes;
    DBaseRect window;
    DBaseCoord maximum_window;
};
extern "C" {
DBASE_DLLIMPORT int DBASE_WINAPI AllocConsole(void);
DBASE_DLLIMPORT int DBASE_WINAPI FreeConsole(void);
DBASE_DLLIMPORT void * DBASE_WINAPI CreateFileA(const char*, dbase_u32, dbase_u32,
                                             void*, dbase_u32, dbase_u32, void*);
DBASE_DLLIMPORT void * DBASE_WINAPI GetStdHandle(dbase_u32);
DBASE_DLLIMPORT int DBASE_WINAPI SetConsoleOutputCP(dbase_u32);
DBASE_DLLIMPORT int DBASE_WINAPI GetConsoleScreenBufferInfo(void*, DBaseConsoleInfo*);
DBASE_DLLIMPORT int DBASE_WINAPI SetConsoleScreenBufferSize(void*, DBaseCoord);
DBASE_DLLIMPORT int DBASE_WINAPI SetConsoleTitleA(const char*);
DBASE_DLLIMPORT void * DBASE_WINAPI GetConsoleWindow(void);
DBASE_DLLIMPORT int DBASE_WINAPI ShowWindow(void*, int);
DBASE_DLLIMPORT int DBASE_WINAPI SetWindowPos(void*, void*, int, int, int, int, dbase_u32);
DBASE_DLLIMPORT int DBASE_WINAPI SetForegroundWindow(void*);
DBASE_DLLIMPORT int DBASE_WINAPI WriteFile(void*, const void*, dbase_u32,
                                         dbase_u32*, void*);
}
#endif

#if defined(_WIN32)
extern "C" char * DBASE_CDECL _gcvt(double, int, char *);
#else
extern "C" char * gcvt(double, int, char *);
#endif

namespace {
static int console_ready = 0;
static void *console_handle = 0;
static const char *console_title = 0;
static const char default_console_title[] = "dBase Console [MODAL TEST]";

static int ensure_console() {
    if (console_ready) return 1;
#if defined(_WIN32)
    // Stage 114: do not FreeConsole before AllocConsole. CONOUT$ works when
    // a console was attached to the process before the runtime was loaded.
    AllocConsole();
    void *handle = CreateFileA("CONOUT$", 0xC0000000u, 3u, 0, 3u, 0u, 0);
    if (!handle || handle == (void*)-1)
        handle = GetStdHandle((dbase_u32)-11);
    if (!handle || handle == (void*)-1) return 0;
    console_handle = handle;
    SetConsoleOutputCP(1252);
    DBaseConsoleInfo info = {};
    DBaseCoord size = {80, 500};
    if (GetConsoleScreenBufferInfo(handle, &info) && info.size.x > 0)
        size.x = info.size.x;
    SetConsoleScreenBufferSize(handle, size);
    SetConsoleTitleA(console_title ? console_title : default_console_title);
    void *window = GetConsoleWindow();
    if (window) {
        ShowWindow(window, 5);
        SetWindowPos(window, (void*)-1, 0, 0, 0, 0, 67u);
        SetForegroundWindow(window);
    }
#else
    // Non-Windows builds exist for ABI/unit testing; they do not create a
    // fake Windows console.
    console_handle = 0;
#endif
    console_ready = 1;
    return 1;
}

static int within(dbase_u32 value, const unsigned short (*ranges)[2], unsigned count) {
    for (unsigned i=0; i<count; ++i)
        if (value >= ranges[i][0] && value <= ranges[i][1]) return 1;
    return 0;
}
#include "dbase_case_ranges.inc"
static int char_case(const char *bytes, dbase_u32 len, bool upper, bool utf8) {
    if (!bytes) return 0;
    dbase_u32 value = 0;
    if (!utf8) {
        if (len != 1) return 0;
        value = (dbase_u8)bytes[0];
        return upper ? within(value,k_cp1252_upper,k_cp1252_upper_count)
                     : within(value,k_cp1252_lower,k_cp1252_lower_count);
    }
    if (len == 1) {
        value = (dbase_u8)bytes[0];
        if (value > 127) return 0;
    } else if (len == 2) {
        dbase_u32 first=(dbase_u8)bytes[0], second=(dbase_u8)bytes[1];
        if (first < 194 || first > 223 || second < 128 || second > 191) return 0;
        value = ((first & 31u) << 6u) | (second & 63u);
    } else return 0;
    return upper ? within(value,k_utf8_upper,k_utf8_upper_count)
                 : within(value,k_utf8_lower,k_utf8_lower_count);
}

static void copy_n(void *out, const void *src, unsigned length) {
    dbase_u8 *d=(dbase_u8*)out;
    const dbase_u8 *s=(const dbase_u8*)src;
    for (unsigned i=0; i<length; ++i) d[i]=s[i];
}
static const char null_text[] = "<null>";
static const char object_text[] = "<object>";
static const char true_text[] = ".T.";
static const char false_text[] = ".F.";

// Do not copy C++ padding: PE64 result size is exactly 12 bytes.
static void format_result(void *dst, const char *p, dbase_u32 len) {
    copy_n(dst, &p, sizeof(p));
    copy_n((dbase_u8*)dst + sizeof(p), &len, sizeof(len));
}
} // namespace

extern "C" {
void DBASE_CDECL DBaseConsoleEnsure() { ensure_console(); }
void DBASE_CDECL DBaseConsoleWrite(const char *text, int length) {
    if (!ensure_console() || !text || length <= 0) return;
#if defined(_WIN32)
    dbase_u32 written=0;
    WriteFile(console_handle, text, (dbase_u32)length, &written, 0);
#else
    (void)text; (void)length;
#endif
}
void DBASE_CDECL DBaseConsoleShutdown() {
#if defined(_WIN32)
    if (console_ready) FreeConsole();
#endif
    console_ready=0;
    console_handle=0;
}
void DBASE_CDECL DBaseConsoleSetTitle(const char *title) {
    if (!title) return;
    console_title=title; // same borrowed-pointer lifetime as previous DLL
#if defined(_WIN32)
    if (console_ready) SetConsoleTitleA(title);
#endif
}
int DBASE_CDECL DBaseCharIsLowerCP1252(const char *text, dbase_u32 length) {
    return char_case(text,length,false,false);
}
int DBASE_CDECL DBaseCharIsUpperCP1252(const char *text, dbase_u32 length) {
    return char_case(text,length,true,false);
}
int DBASE_CDECL DBaseCharIsLowerUtf8(const char *text, dbase_u32 length) {
    return char_case(text,length,false,true);
}
int DBASE_CDECL DBaseCharIsUpperUtf8(const char *text, dbase_u32 length) {
    return char_case(text,length,true,true);
}
dbase_u32 DBASE_CDECL DBaseStringLengthN(const char *text, dbase_u32 maximum) {
    if (!text) return 0;
    dbase_u32 i=0;
    while (i < maximum && text[i]) ++i;
    return i;
}
dbase_u32 DBASE_CDECL DBaseWfmClassifyType(dbase_u32 type) {
    return type==3 || type==6 ? 1u : type==4 ? 2u
         : (type==1 || type==2 || type==5 ? 3u : 0u);
}

// Preserve the exact packed source ABI: 4-byte type + 8-byte number +
// pointer(4/8) + uint32 length; caller-owned scratch capacity >= 96 bytes.
void DBASE_CDECL DBaseWfmFormatValue(const void *slot, char *scratch, void *result) {
    if (!result) return;
    if (!slot) { format_result(result,null_text,6); return; }
    const dbase_u8 *src=(const dbase_u8*)slot;
    dbase_u32 type=0;
    copy_n(&type,src,4);
    if (type==3 || type==6) {
        const char *p=0;
        copy_n(&p,src+12,sizeof(p));
        if (p) {
            dbase_u32 len=0;
            copy_n(&len,src+12+sizeof(p),4);
            format_result(result,p,len);
            return;
        }
    } else if (type==4) {
        const char *p=0;
        copy_n(&p,src+12,sizeof(p));
        if (p) { format_result(result,object_text,8); return; }
    } else if (type==5) {
        dbase_u64 bits=0;
        copy_n(&bits,src+4,8);
        format_result(result,bits ? true_text : false_text,3);
        return;
    } else if (type==1 || type==2) {
        if (scratch) {
            double value=0.0;
            copy_n(&value,src+4,8);
#if defined(_WIN32)
            // Existing DLL used msvcrt.dll!_gcvt(value, 15, scratch).
            _gcvt(value,15,scratch);
#else
            gcvt(value,15,scratch);
#endif
            format_result(result,scratch,DBaseStringLengthN(scratch,96));
            return;
        }
    }
    format_result(result,null_text,6);
}
} // extern "C"
