#ifndef D64_DBASE_QT5_BRIDGE_H
#define D64_DBASE_QT5_BRIDGE_H

#ifdef _WIN32
#  ifdef D64QT5_BRIDGE_EXPORTS
#    define D64QT5_API __declspec(dllexport)
#  else
#    define D64QT5_API __declspec(dllimport)
#  endif
#else
#  if defined(__GNUC__) || defined(__clang__)
#    define D64QT5_API __attribute__((visibility("default")))
#  else
#    define D64QT5_API
#  endif
#endif

#ifdef __cplusplus
extern "C" {
#endif

/*
 * Stabile C-ABI fuer den internen dBase-Codegenerator.
 * PE32:  cdecl / Argumente auf dem Stack, Caller raeumt auf.
 * PE32+: Windows-x64-ABI (RCX/RDX/R8/R9 + Shadow Space).
 */
/* Stage 213: loader/runtime ABI identity. This export is always resolved by name. */
#pragma pack(push, 1)
typedef struct D64RuntimeAbiInfo {
    unsigned int structSize;
    unsigned short abiMajor;
    unsigned short abiMinor;
    unsigned int ordinalMapVersion;
    unsigned int loaderMinVersion;
    unsigned char ordinalMapHash[32];
    char runtimeName[32];
} D64RuntimeAbiInfo;
#pragma pack(pop)

D64QT5_API const D64RuntimeAbiInfo *D64GetRuntimeAbiInfo(void);
/* Stage 488: Linux ELF dynamic linker entrypoint (UTF-8 WFM JSON). */
D64QT5_API int DBaseQtRunFormJson(const char *utf8Json);
/* Stage 490: native Qt5 output terminal for .prg, no Python subprocess. */
D64QT5_API int DBaseQtRunConsoleJson(const char *utf8Json);
/* Stage 491: Linux-native Win32-compatible Qt message boxes. A HWND is an
 * X11 XID (via DBaseQtGetX11WindowId), not a QWidget pointer. On Wayland
 * use 0/null; the native dialog has no foreign parent. */
#ifndef _WIN32
#include <stdint.h>
D64QT5_API int MessageBoxA(uintptr_t hwnd, const char *message,
                           const char *caption, unsigned int type);
D64QT5_API int MessageBoxW(uintptr_t hwnd, const uint16_t *message,
                           const uint16_t *caption, unsigned int type);
#endif

/* Stage 208/209: immutable lookup tables remain private inside the DLL. */
typedef struct DBaseRuntimeContext {
    unsigned int abiVersion;
    const unsigned char *upperTable;
    const unsigned char *lowerTable;
    unsigned int upperTableSize;
    unsigned int lowerTableSize;
} DBaseRuntimeContext;

D64QT5_API const DBaseRuntimeContext *DBaseGetRuntimeContext(void);
D64QT5_API const unsigned char *DBaseGetUpperTable(void);
D64QT5_API const unsigned char *DBaseGetLowerTable(void);
D64QT5_API unsigned int DBaseUpperBuffer(
    unsigned char *destination, unsigned int destinationCapacity,
    const unsigned char *source, unsigned int sourceLength);
D64QT5_API unsigned int DBaseLowerBuffer(
    unsigned char *destination, unsigned int destinationCapacity,
    const unsigned char *source, unsigned int sourceLength);

/* Stage 458: native UTF-8 substring/case conversion. One caller-owned buffer. */
D64QT5_API unsigned int DBaseUtf8Substring(
    unsigned char *dst, unsigned int cap, const unsigned char *src,
    unsigned int len, const double *start, const double *count);
D64QT5_API unsigned int DBaseUtf8SubstringUpper(
    unsigned char *dst, unsigned int cap, const unsigned char *src,
    unsigned int len, const double *start, const double *count);
D64QT5_API unsigned int DBaseUtf8SubstringLower(
    unsigned char *dst, unsigned int cap, const unsigned char *src,
    unsigned int len, const double *start, const double *count);
D64QT5_API unsigned int DBaseUtf8Upper(
    unsigned char *dst, unsigned int cap, const unsigned char *src,
    unsigned int len);
D64QT5_API unsigned int DBaseUtf8Lower(
    unsigned char *dst, unsigned int cap, const unsigned char *src,
    unsigned int len);

D64QT5_API void DBaseQtSetWorkstationMode(int enabled);
D64QT5_API void DBaseQtSetDebugTheme(int themeMode);
D64QT5_API int  DBaseQtInitialize(const char *title);
D64QT5_API int  DBaseQtInitializeGui(const char *title);
/* Stage 462: caller-owned 96-byte format buffer (out-slot is a pointer). */
D64QT5_API int DBaseQtRuntimeStartup(
    const char *title, int workstationMode, int debugTheme,
    int guiMode, void **formatBuffer);
D64QT5_API void DBaseQtRuntimeShutdown(void **formatBuffer);
D64QT5_API void DBaseQtShowWindow(void);
D64QT5_API void DBaseQtProcessEvents(void);
/* Stage 653: Native Turbo-Vision help viewer resides in libd64_qt5.dll.
 * The legacy export name DBaseQtHelpShowMo is preserved for ABI compatibility.
 * The catalog is a GNU-MO payload stored with the .hlp extension.
 * Absolute paths are read as given; relative paths refer to the EXE folder.
 * NULL or empty string opens <EXE-stem>.hlp alongside the running executable.
 * F1 is installed with Qt::ApplicationShortcut for the Qt5 console/DEBUG UI.
 * No external turbo_help_host.exe or independent viewer is used. */
D64QT5_API int DBaseQtHelpShowMo(const char *utf8File);
/* Stage 664: Show the topic associated with an unsigned 32-bit help number.
 * Searches <EXE-stem>.hlp like F1; returns 1 on success, 0 on failure.
 * The help number is independent of GNU-MO entry positions/offsets. */
D64QT5_API int DBaseQtHelpShowTopicId(unsigned int helpNumber);
D64QT5_API void DBaseQtSetDebugVisible(int visible);
D64QT5_API void DBaseQtAppendConsole(const char *text, int length);
D64QT5_API void DBaseQtAppendDebug(const char *text, int length);
/* Stage 673: one shared O1 runtime text output dispatcher.
 * debugOverride: -1=SET FORMAT, 0=Console, other=Debug.
 * formatScreen: 0=Console, nonzero=Debug.
 * debugVisible points at the caller's BSS state: set to 1 BEFORE showing.
 * PE32: cdecl; PE32+: Microsoft x64 ABI. */
D64QT5_API void DBaseQtRuntimeWrite(const char *text, int length,
                                   int debugOverride, int formatScreen,
                                   int *debugVisible);

/* Stage 674: caller-owned output-state pointers remain live until unbound.
 * ABI: PE32 cdecl and PE32+ Windows-x64. All fields point into EXE memory.
 * On shutdown pass nullptr; bindings are not copied or owned by the DLL. */
typedef struct DBaseQtOutputBindings {
    const int *debugOverride;
    const int *formatScreen;
    int *debugVisible;
} DBaseQtOutputBindings;
/* Word-length and string pointer are stored in read-only EXE descriptors.
 * PE32: 8 bytes; PE32+: 16 bytes with natural pointer alignment. */
typedef struct DBaseQtStaticText {
    unsigned int length;
    const char *text;
} DBaseQtStaticText;
D64QT5_API void DBaseQtBindOutputState(const DBaseQtOutputBindings *binding);
D64QT5_API void DBaseQtRuntimeWriteText(const DBaseQtStaticText *text);

// Stage 675: previously exported from libd64_console.dll.
// Preserve cdecl on Win32 and the original symbol names for Pascal modules.
#ifdef _WIN32
D64QT5_API int __cdecl d64_console_init(void);
D64QT5_API void __cdecl d64_console_restore(void);
D64QT5_API void __cdecl d64_console_write_text(const char *text);
D64QT5_API void __cdecl d64_console_write_int(int value);
D64QT5_API void __cdecl d64_console_write_double(double value);
D64QT5_API void __cdecl d64_console_write_char(int value);
D64QT5_API void __cdecl d64_console_newline(void);
D64QT5_API void __cdecl d64_console_clear(void);
D64QT5_API unsigned __cdecl d64_console_read_line(char *text, unsigned capacity);
D64QT5_API int __cdecl d64_console_read_int(void);
D64QT5_API char *__cdecl d64_console_read_string(void);
#endif


D64QT5_API int  DBaseQtSetColorNormal(const char *name, int length);
D64QT5_API int  DBaseQtSetOutputColor(const char *spec, int length);
D64QT5_API int  DBaseQtFillBackground(int bg, int fg, int code);
D64QT5_API void DBaseQtClearScreen(void);
D64QT5_API int  DBaseQtClearScreenChar(double code);
D64QT5_API int  DBaseQtClearScreenColor(const char *name, int length);
D64QT5_API int  DBaseQtSetBorderColor(const char *name, int length);
D64QT5_API void *DBaseQtSessionCreate(void *parent);
D64QT5_API int  DBaseQtGetLoginSession(void);
D64QT5_API int  DBaseQtSessionLogin(
    void *handle,
    const char *username, int usernameLength,
    const char *password, int passwordLength,
    const char *group, int groupLength
);
D64QT5_API void *DBaseQtDatabaseCreate(void *parent);
D64QT5_API void DBaseQtDatabaseSetPath(void *handle, const char *text, int length);
D64QT5_API void DBaseQtDatabaseSetDatabaseName(void *handle, const char *text, int length);
D64QT5_API void DBaseQtDatabaseSetUserName(void *handle, const char *text, int length);
D64QT5_API void DBaseQtDatabaseSetPassword(void *handle, const char *text, int length);
D64QT5_API void DBaseQtDatabaseSetAlias(void *handle, const char *text, int length);
D64QT5_API void DBaseQtDatabaseSetSession(void *handle, void *sessionHandle);
D64QT5_API int  DBaseQtDatabaseSetActive(void *handle, int active);
/* Virtual documents/shared mount only. 0=readable, otherwise a Win32 DWORD. */
D64QT5_API unsigned int DBaseQtVfsCheckOpenRead(const char *virtualPath, int pathLength);
D64QT5_API int  DBaseQtDatabaseOpen(void *handle);
D64QT5_API void DBaseQtDatabaseClose(void *handle);
D64QT5_API int  DBaseQtDatabaseCommit(void *handle);
D64QT5_API void  DBaseQtEnsureDefaultMenu(void);
D64QT5_API void *DBaseQtMenuCreate(void *owner);
D64QT5_API void DBaseQtMenuSetText(void *handle, const char *text, int length);
D64QT5_API void DBaseQtMenuSetSeparator(void *handle, int separator);
D64QT5_API void DBaseQtMenuSetShortcut(void *handle, const char *text, int length);
D64QT5_API void DBaseQtMenuSetOnClick(void *handle, void (*callback)(void));
// Stage 34/WFM FORM-OOP
D64QT5_API void *DBaseQtFormCreate(const char *className, int classNameLength);
D64QT5_API void *DBaseQtControlCreate(const char *className, int classNameLength, void *parentHandle);
D64QT5_API void *DBaseQtControlCreateEx(
    const char *className, int classNameLength, void *parentHandle,
    const char *text, int textLength
);
D64QT5_API int DBaseQtObjectBindEvent(
    void *handle, const char *eventName, int eventNameLength,
    void *callbackHandle
);
// Stage 503: method dispatch for designer-created WFM SESSION objects.
D64QT5_API int DBaseQtWfmSessionInvoke(
    void *handle, const char *methodName, int methodNameLength,
    const char *argument, int argumentLength);
D64QT5_API void *DBaseQtNonVisualCreate(
    const char *className, int classNameLength, void *parentHandle
);
D64QT5_API void *DBaseQtTimerCreate(void *parentHandle);
D64QT5_API void DBaseQtTimerSetInterval(void *handle, int milliseconds);
D64QT5_API void DBaseQtTimerSetActive(void *handle, int active);
D64QT5_API void DBaseQtConsoleWrite(
    const char *text, int textLength, int newline
);
D64QT5_API void DBaseQtWidgetSetGeometry(void *handle, int left, int top, int width, int height);
D64QT5_API void DBaseQtWidgetSetText(void *handle, const char *text, int length);
D64QT5_API void DBaseQtWidgetSetProperty(void *handle, const char *name, int nameLength, const char *value, int valueLength);
D64QT5_API void DBaseQtWidgetSetProperties(void *handle, const void *records, int count);
D64QT5_API void DBaseQtWidgetSetBackColor(void *handle, const char *text, int length);
D64QT5_API void DBaseQtWidgetSetBorderColor(void *handle, const char *text, int length);
D64QT5_API void DBaseQtWidgetSetBorderWidth(void *handle, int width);
D64QT5_API void DBaseQtWidgetSetRadius(void *handle, int radius);
D64QT5_API void DBaseQtWidgetSetFont(
    void *handle, const char *family, int familyLength, int pointSize,
    int bold, int italic, int underline, int strikeout
);
/* Stage 456: Form-JSON is embedded in the EXE (optionally qCompress). */
D64QT5_API int DBaseQtFormApplyExternalUi(
    const void *const *slotAddresses, int slotCount,
    const unsigned char *payload, int payloadLength, int compressed
);
/* Stage 463: optional command line PARAMETER bmodal, and modal/nonmodal
 * event processing with IDE/Workstation-aware lifetime. */
D64QT5_API int DBaseQtWfmModalParameter(void);
D64QT5_API int DBaseQtFormRun(void *handle, int modal);
D64QT5_API void DBaseQtFormOpen(void *handle);
D64QT5_API void DBaseQtMarkProgramFinished(void);
D64QT5_API int  DBaseQtExec(void);
D64QT5_API int  DBaseQtShutdownRequested(void);
D64QT5_API void DBaseQtShutdown(void);

/* Stage 295: native in-process PROLOG Qt5 frontend.
 * These helpers are resolved by name at runtime by generated PROLOG images,
 * so console-mode EXEs do not acquire a hard Qt5 dependency.
 */
D64QT5_API int DBaseQtPrologInitialize(const char *title, int darkMode);
D64QT5_API void DBaseQtPrologWrite(const char *text, int length, int style);
D64QT5_API int DBaseQtPrologReadLine(char *buffer, int capacity);
D64QT5_API void DBaseQtPrologShutdown(void);

#ifdef __cplusplus
}
#endif

#endif
