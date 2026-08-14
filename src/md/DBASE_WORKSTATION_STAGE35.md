# d64qt5 Win32 Workstation - Stage 35 GUI/Return Fix

## Fehlerbild aus Stage 34

Beim Start einer bestehenden dBase-EXE wurde auf `D64Workstation_<PID>`
umgeschaltet, aber das Qt-Hauptfenster blieb unsichtbar. Ursache war die
Startreihenfolge: `CreateDesktopW()` erzeugt einen Desktop, bindet den bereits
laufenden GUI-Thread aber nicht automatisch an ihn. Stage 34 rief
`SwitchDesktop()` auf, bevor der Qt-GUI-Thread mit `SetThreadDesktop()` an den
neuen Desktop gebunden war. QApplication/QWidget konnten dadurch auf dem alten
Desktop entstehen, waehrend der leere neue Desktop sichtbar war.

## Stage-35-Reihenfolge

### DBaseQtInitialize

1. urspruenglichen Thread-Desktop mit `GetThreadDesktop()` merken
2. aktuell sichtbaren Input-Desktop mit `OpenInputDesktop()` merken
3. `CreateDesktopW("D64Workstation_<PID>")`
4. **`SetThreadDesktop(g_work_desktop)`**
5. pruefen, dass der aktuelle GUI-Thread wirklich auf diesem Desktop liegt
6. **noch kein `SwitchDesktop()`**
7. QApplication und Hauptfenster auf dem unsichtbaren Workstation-Desktop
   erzeugen

Dadurch bleibt der normale Windows-Desktop sichtbar, solange noch kein
Hauptfenster bereit ist.

### DBaseQtShowWindow

1. `g_window->show()`
2. `g_window->winId()` erzwingt das native HWND
3. `QApplication::processEvents()`
4. pruefen: `IsWindow(hwnd)` und `IsWindowVisible(hwnd)`
5. **erst jetzt `SwitchDesktop(g_work_desktop)`**
6. Hauptfenster nach vorn holen
7. erst danach den Keyboard-Guard installieren

Wenn die Aktivierung fehlschlaegt, wird `request_runtime_shutdown()` gesetzt.
Der normale Windows-Desktop wurde zu diesem Zeitpunkt noch nicht verlassen.

## Rueckkehr beim Beenden

`DBaseMainWindow::closeEvent()` laeuft weiter durch den zentralen
Stage-29+-Shutdown.

`D64WorkstationBeginLeave()`:

1. Keyboard-Hook entfernen
2. sofort zum beim Start gespeicherten Input-Desktop zurueckschalten
   (`OpenInputDesktop`-Handle; normalerweise `WinSta0\\Default`)
3. falls dieser Handle ausnahmsweise nicht mehr schaltbar ist: gespeicherten
   Desktopnamen erneut oeffnen, danach Fallback `Default`

Danach werden Dialoge, DATABASE-/TABLE-Kontexte, Dateien, Qt-Fenster und
reservierter Speicher abgebaut.

`D64WorkstationFinalizeLeave()`:

1. erst jetzt `SetThreadDesktop(g_original_thread_desktop)`
2. Workstation-Desktop schliessen
3. gespeicherten Input-Desktop-Handle schliessen

Damit erscheint der normale Windows-Desktop bereits am Anfang des Shutdowns,
waehrend die unsichtbaren Qt-Objekte sauber zerlegt werden.

## Neue interne Workstation-Funktion

```cpp
bool D64WorkstationActivate(HWND mainWindow);
```

Sie wird nicht aus `d64qt5.dll` exportiert; sie ist ein interner C++-Helper.
Die bestehende C-ABI fuer alte bereits erzeugte EXE-Dateien bleibt daher
unveraendert. Eine `shutdown_cleanup_stage29.exe`, die die bekannten
`DBaseQtInitialize`/`DBaseQtShowWindow`/`DBaseQtExec`/`DBaseQtShutdown`-Exports
verwendet, muss nicht neu kompiliert werden, sofern sie die neue DLL neben sich
laedt.

## Wichtiger Test vor der produktiven DLL

Zuerst den reinen Win32-Test bauen:

```bat
cd d64qt5
build_workstation_smoke_test_mingw32.bat
workstation_smoke_test.exe
```

Er erzeugt sein Fenster zunaechst auf dem noch unsichtbaren Workstation-Desktop
und schaltet erst danach um. `Alt+F4` und `Ctrl+Alt+Shift+F12` muessen wieder zum
urspruenglichen Windows-Desktop zurueckfuehren.

Danach DLL bauen:

```bat
build_d64qt5_mingw32.bat
```

Die neue `d64qt5.dll` neben die zu testende EXE kopieren.

## Tastatur-Guard

Wie Stage 34:

- Windows-Taste / Win-Kombinationen
- Alt+Tab
- Alt+Esc
- Ctrl+Esc
- Ctrl+Shift+Esc

`Alt+F4` bleibt als normaler Shutdown erlaubt.
`Ctrl+Alt+Shift+F12` sendet `WM_CLOSE` an das Hauptfenster.
`Ctrl+Alt+Del` bleibt Windows selbst vorbehalten.

## Build-Hinweis dieser Lieferung

Die Python-/Generator-Regression wurde ausgefuehrt. Die Windows-C++-Quellen
konnten in der aktuellen Linux-Umgebung nicht gegen deinen MinGW32-/Qt5-
Toolchain kompiliert werden, da dieser Toolchain hier nicht installiert ist.
