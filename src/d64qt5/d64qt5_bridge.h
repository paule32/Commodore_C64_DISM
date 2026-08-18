#ifndef D64_DBASE_QT5_BRIDGE_H
#define D64_DBASE_QT5_BRIDGE_H

#ifdef _WIN32
#  ifdef D64QT5_BRIDGE_EXPORTS
#    define D64QT5_API __declspec(dllexport)
#  else
#    define D64QT5_API __declspec(dllimport)
#  endif
#else
#  define D64QT5_API
#endif

#ifdef __cplusplus
extern "C" {
#endif

/*
 * Stabile C-ABI fuer den internen dBase-Codegenerator.
 * PE32:  cdecl / Argumente auf dem Stack, Caller raeumt auf.
 * PE32+: Windows-x64-ABI (RCX/RDX/R8/R9 + Shadow Space).
 */
D64QT5_API int  DBaseQtInitialize(const char *title);
D64QT5_API void DBaseQtShowWindow(void);
D64QT5_API void DBaseQtProcessEvents(void);
D64QT5_API void DBaseQtSetDebugVisible(int visible);
D64QT5_API void DBaseQtAppendConsole(const char *text, int length);
D64QT5_API void DBaseQtAppendDebug(const char *text, int length);
D64QT5_API int  DBaseQtSetColorNormal(const char *name, int length);
D64QT5_API int  DBaseQtSetOutputColor(const char *spec, int length);
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
D64QT5_API void DBaseQtWidgetSetGeometry(void *handle, int left, int top, int width, int height);
D64QT5_API void DBaseQtWidgetSetText(void *handle, const char *text, int length);
D64QT5_API void DBaseQtWidgetSetBackColor(void *handle, const char *text, int length);
D64QT5_API void DBaseQtWidgetSetBorderColor(void *handle, const char *text, int length);
D64QT5_API void DBaseQtWidgetSetBorderWidth(void *handle, int width);
D64QT5_API void DBaseQtWidgetSetRadius(void *handle, int radius);
D64QT5_API void DBaseQtWidgetSetFont(
    void *handle, const char *family, int familyLength, int pointSize,
    int bold, int italic, int underline, int strikeout
);
D64QT5_API void DBaseQtFormOpen(void *handle);
D64QT5_API void DBaseQtMarkProgramFinished(void);
D64QT5_API int  DBaseQtExec(void);
D64QT5_API int  DBaseQtShutdownRequested(void);
D64QT5_API void DBaseQtShutdown(void);

#ifdef __cplusplus
}
#endif

#endif
