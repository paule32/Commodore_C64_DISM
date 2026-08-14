# d64qt5 Win32 Workstation / eigener Desktop - Stage 34

## Ziel

Die dBase-Qt5-Anwendung laeuft auf einem eigenen interaktiven Win32-Desktop
innerhalb der aktuellen Window Station. Auf diesem Desktop wird keine
Explorer-Shell gestartet; dadurch gibt es dort keine normale Windows-Taskleiste.

Beim Beenden wird zuerst der urspruengliche Windows-Desktop wieder sichtbar
gemacht. Danach beendet der bestehende Runtime-Cleanup Dialoge, Datenbanken,
Dateihandles, Qt-Objekte und reservierten Speicher. Erst wenn keine Qt-Fenster
oder Hooks mehr existieren, wird der Workstation-Desktop geschlossen.

## Dateien

- `d64qt5/d64_workstation.h`
- `d64qt5/d64_workstation.cpp`
- `d64qt5/d64qt5_bridge.cpp` (integriert)
- `d64qt5/d64qt5_bridge.pro` (SOURCES/HEADERS erweitert)
- `d64qt5/build_d64qt5_mingw32.bat`
- `d64qt5/workstation_smoke_test.cpp`
- `d64qt5/build_workstation_smoke_test_mingw32.bat`

## Startreihenfolge

`DBaseQtInitialize()` macht vor dem Erzeugen einer neuen `QApplication`:

1. urspruenglichen Thread-/Input-Desktop merken
2. `CreateDesktopW()`
3. `SwitchDesktop()` auf `D64Workstation_<PID>`
4. erst danach `QApplication` und alle Widgets erzeugen

`DBaseQtShowWindow()` installiert nach dem ersten nativen HWND den
`WH_KEYBOARD_LL`-Guard.

## Geblockte Tastenkombinationen

- linke/rechte Windows-Taste und dadurch Win+R, Win+D, Win+E, Win+X, Win+L usw.
- Alt+Tab
- Alt+Esc
- Ctrl+Esc
- Ctrl+Shift+Esc

Alt+F4 bleibt absichtlich erlaubt und nutzt den normalen Shutdown.

Notausgang:

`Ctrl + Alt + Shift + F12`

Er sendet `WM_CLOSE` an das Hauptfenster; es findet kein harter Prozessabbruch
statt.

`Ctrl+Alt+Del` ist die Windows Secure Attention Sequence und wird von dieser
Anwendung nicht abgefangen.

## Taskleiste

Es wird **kein explorer.exe** auf dem Workstation-Desktop gestartet. Die normale
Windows-Taskleiste des Default-Desktops wird weder versteckt noch manipuliert.

## MinGW32 / Qt5 Build

Im Verzeichnis `d64qt5`:

```bat
build_d64qt5_mingw32.bat
```

oder manuell:

```bat
qmake d64qt5_bridge.pro CONFIG+=release
mingw32-make -j4
```

Die Projektdatei linkt bereits:

```text
-luser32 -ladvapi32 -lodbc32
```

## Reiner Win32-Smoke-Test

Ohne Qt kann zuerst nur die Desktop-/Keyboard-Logik getestet werden:

```bat
build_workstation_smoke_test_mingw32.bat
workstation_smoke_test.exe
```

Der Test erzeugt ebenfalls einen eigenen Desktop, zeigt nur sein Testfenster
und kehrt bei Alt+F4 bzw. Ctrl+Alt+Shift+F12 zum urspruenglichen Desktop zurueck.

## Wichtige Betriebsgrenze

Der Win32-Desktop isoliert die sichtbare Arbeitsflaeche und Eingabe, ist aber
keine vollstaendige Windows-Sicherheitsgrenze. Fuer einen administrativ
verriegelten Kiosk-/Single-App-Rechner sind Windows Assigned Access/Shell
Launcher und passende Richtlinien die staerkere Systemebene.

## Build-Hinweis fuer diese Lieferung

Die C++-Quellen wurden in der aktuellen Linux-Laufzeitumgebung nicht gegen
dein MinGW32/Qt5 kompiliert, weil hier kein MinGW32-/Qt5-Windows-Toolchain
installiert ist. Die Python-/Generator-Regression wird dagegen mitgeliefert
und ausgefuehrt.
