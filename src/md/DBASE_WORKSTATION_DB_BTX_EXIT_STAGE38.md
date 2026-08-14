# Stage 38 - DB icon, BTX.exe and confirmed Workstation exit

Stage 38 builds on Stage 37A.

## Left Workstation panel

The full-height Win32 panel keeps its width of 76 pixels and now contains three items:

1. EXIT - red X icon
2. BTX - blue BTX icon
3. DB - green database/cylinder icon with the text DB

All three panel actions are forwarded to the Qt event queue through callbacks; the Win32 WndProc never performs Qt UI work directly.

## Main-window close semantics

Closing the dBase main window no longer stops the runtime. `DBaseMainWindow::closeEvent()` hides the main window and ignores the close event unless a confirmed Workstation EXIT has authorized shutdown.

Therefore title-bar close, Alt+F4 and the existing `Datei -> Beenden` action only hide the main window. The Workstation, sessions, DATABASE objects and allocated runtime memory stay alive.

Clicking DB shows/raises/activates the existing main window again. No second main window is created.

## EXIT confirmation

A single click on EXIT queues `workstation_exit_requested()`.

A frameless, application-modal Qt confirmation is displayed with the buttons:

- `JA`
- `NEIN`

`NEIN` closes only the question. `JA` sets `g_exit_authorized`, closes the main window through the normal close path, calls the existing central shutdown logic, closes dialogs/databases/files, frees the runtime allocations, switches back to the original input desktop and finally releases the Workstation desktop.

There is no `ExitProcess` or `TerminateProcess` path in the Workstation panel.

## BTX.exe

BTX no longer opens the Stage-37 internal BTX test dialog. It looks for `BTX.exe` in this order:

1. directory of the running host EXE (`QCoreApplication::applicationDirPath()`)
2. current process working directory

On Windows the process is launched with `CreateProcessW()` and an explicit `STARTUPINFO.lpDesktop` pointing to:

`WinSta0\\D64Workstation_<PID>`

This ensures BTX.exe is created on the private Workstation rather than accidentally appearing on the normal Windows desktop.

The process id is remembered. During confirmed Workstation shutdown all tracked Workstation child windows receive a normal `WM_CLOSE` through `EnumDesktopWindows()` before the desktop is switched back.

## Build

No additional library beyond the Stage-36 GDI fix is required. The qmake project still links:

`-luser32 -lgdi32 -ladvapi32 -lodbc32`

Rebuild on Windows with:

```
mingw32-make clean
qmake d64qt5_bridge.pro CONFIG+=release
mingw32-make release
```
