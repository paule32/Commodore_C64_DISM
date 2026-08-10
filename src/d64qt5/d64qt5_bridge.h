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

D64QT5_API int  DBaseQtInitialize(const char *title);
D64QT5_API void DBaseQtShowWindow(void);
D64QT5_API void DBaseQtProcessEvents(void);
D64QT5_API void DBaseQtSetDebugVisible(int visible);
D64QT5_API void DBaseQtAppendConsole(const char *text, int length);
D64QT5_API void DBaseQtAppendDebug(const char *text, int length);
D64QT5_API void DBaseQtMarkProgramFinished(void);
D64QT5_API int  DBaseQtExec(void);
D64QT5_API void DBaseQtShutdown(void);

#ifdef __cplusplus
}
#endif

#endif
