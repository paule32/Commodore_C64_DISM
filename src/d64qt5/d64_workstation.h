#ifndef D64_WORKSTATION_H
#define D64_WORKSTATION_H

#ifdef _WIN32
#  define WIN32_LEAN_AND_MEAN
#  include <windows.h>
#else
typedef void *HWND;
struct RECT { long left; long top; long right; long bottom; };
#endif

/*
 * Eigener interaktiver Win32-Desktop fuer die d64qt5-Runtime.
 *
 * Stage 39: Windows-globaler Workstation-Singleton innerhalb des Global\-
 * Kernelobjekt-Namensraums. Die erste Runtime ist OWNER; weitere Prozesse
 * werden JOINED und erzeugen ihre Fenster auf demselben Desktop.
 *
 * Stage 42: Zusaetzlich besitzt jede Hauptanwendung einen eigenen globalen
 * Instance-Mutex, abgeleitet aus dem kanonischen EXE-Pfad. BTX/DB koennen
 * deshalb jeweils nur einmal gleichzeitig auf der Workstation existieren.
 *
 * Stage 43: Zweites horizontales Bottom-Panel (52 px), Server/SRV-PC-Icons,
 * 4-Pixel-Arbeitsbereichsgrenzen und feste Minimize-Position oberhalb des
 * Bottom-Panels. Der Zeichen-Remote-Server selbst lebt in d64qt5_bridge.cpp.
 *
 * Sichere Reihenfolge (Stage 35/39):
 *   1. D64WorkstationPrepare() VOR QApplication/QWidget/Hook.
 *      -> Desktop erzeugen UND GUI-Thread per SetThreadDesktop binden,
 *         aber noch NICHT sichtbar schalten.
 *   2. QApplication + Hauptfenster auf dem gebundenen Desktop erzeugen.
 *   3. Hauptfenster show()/winId(), dann D64WorkstationActivate(hwnd).
 *      -> erst jetzt SwitchDesktop(), wenn ein sichtbares HWND existiert.
 *   4. Aktivierung erzeugt vorher das EXIT-Icon oben links; ohne Icon kein
 *      SwitchDesktop(). Keyboard-Guard erst danach installieren.
 *   5. D64WorkstationBeginLeave() beim Runtime-Shutdown:
 *      -> Guard entfernen und urspruenglichen Windows-Desktop anzeigen.
 *   6. D64WorkstationFinalizeLeave() erst nachdem alle Qt-Fenster weg sind:
 *      -> GUI-Thread zurueckbinden und Workstation-Desktop schliessen.
 */
using D64WorkstationCallback = void (*)(void);
using D64WorkstationBtxCallback = D64WorkstationCallback;
using D64WorkstationServerClientCallback = void (*)(int clientIndex);

void D64WorkstationSetExitCallback(D64WorkstationCallback callback);
void D64WorkstationSetBtxCallback(D64WorkstationBtxCallback callback);
void D64WorkstationSetDbCallback(D64WorkstationCallback callback);
void D64WorkstationSetServerCallback(D64WorkstationCallback callback);
void D64WorkstationSetServerClientCallback(D64WorkstationServerClientCallback callback);
void D64WorkstationSetServerClientCount(int count);
bool D64WorkstationPrepare();
bool D64WorkstationActivate(HWND mainWindow);
bool D64WorkstationInstallKeyboardGuard(HWND mainWindow);
void D64WorkstationBeginLeave();
void D64WorkstationFinalizeLeave();
bool D64WorkstationIsActive();
bool D64WorkstationIsVisible();
bool D64WorkstationOwnsDesktop();
bool D64WorkstationJoinedExisting();
bool D64WorkstationExitIconVisible();
bool D64WorkstationPanelVisible();
int D64WorkstationLeftPanelWidth();
int D64WorkstationBottomPanelHeight();
void D64WorkstationConstrainMovingRect(RECT *rect);
void D64WorkstationConstrainMaximizeInfo(void *minMaxInfo);
void D64WorkstationPositionMinimizedWindow(HWND mainWindow);
void D64WorkstationCloseApplicationWindows(HWND mainWindow);
bool D64WorkstationLaunchProgram(
    const wchar_t *applicationPath,
    const wchar_t *workingDirectory
);
bool D64WorkstationApplicationInstanceOwned();
const wchar_t *D64WorkstationApplicationMutexName();
const wchar_t *D64WorkstationDesktopName();

#endif
