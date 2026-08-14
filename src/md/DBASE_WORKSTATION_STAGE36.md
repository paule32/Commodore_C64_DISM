# DBase Workstation Stage 36 - EXIT-Icon

Stage 36 baut auf Stage 35 auf und fuegt ein eigenes EXIT-Icon direkt auf dem
Win32-Workstation-Desktop hinzu.

## Verhalten

- Das EXIT-Icon ist ein eigenes Win32-Top-Level-Fenster.
- Position: links oben bei (8,8).
- Darstellung: rotes Feld, weisses X, Beschriftung `EXIT`.
- Das Fenster verwendet `WS_EX_TOPMOST | WS_EX_NOACTIVATE`.
  Dadurch bleibt es sichtbar, ohne den Fokus aus der Qt-Anwendung zu nehmen.
- Die Fensterklasse verwendet `CS_DBLCLKS`.
- Ein Doppelklick sendet ausschliesslich `WM_CLOSE` an das Qt-Hauptfenster.
- Es gibt im Icon-Pfad kein `ExitProcess()` und kein `TerminateProcess()`.

## Sichere Aktivierungsreihenfolge

1. `D64WorkstationPrepare()` erzeugt den Desktop und bindet den GUI-Thread.
2. `QApplication` und das Qt-Hauptfenster werden erzeugt.
3. `DBaseQtShowWindow()` macht das Qt-Hauptfenster sichtbar.
4. `D64WorkstationActivate()` erzeugt zuerst das EXIT-Icon.
5. Nur wenn das EXIT-Icon erfolgreich erzeugt wurde, folgt `SwitchDesktop()`.
6. Erst danach wird der Keyboard-Guard installiert.

Wenn das EXIT-Icon nicht erzeugt werden kann, wird der Workstation-Desktop
nicht sichtbar geschaltet. Der Benutzer bleibt auf seinem bisherigen Windows-
Desktop.

## Doppelklick / Cleanup

`WM_LBUTTONDBLCLK` am EXIT-Icon fuehrt aus:

    PostMessageW(g_main_window, WM_CLOSE, 0, 0);

Dadurch laeuft der vorhandene zentrale Shutdown-Pfad der d64qt5-Runtime:

- Shutdown-Status setzen
- Keyboard-Guard entfernen
- EXIT-Icon zerstoeren
- urspruenglichen Input-Desktop wieder anzeigen
- Login-/Warning-/Subfenster schliessen
- DATABASE/TABLE-/Datei-Cleanup
- Qt-Fenster und QApplication abbauen
- reservierten Runtime-Speicher ueber den generierten Cleanup freigeben
- GUI-Thread zum Originaldesktop zurueckbinden
- Workstation-Desktop schliessen

## Smoke-Test

`d64qt5/workstation_smoke_test.cpp` prueft nach erfolgreicher Aktivierung
zusaetzlich `D64WorkstationExitIconVisible()`. Ist das Icon nicht sichtbar,
wird der Test sofort ueber den normalen Rueckweg beendet.

## MinGW32

Der Workstation-Code benoetigt nur Win32/User32. Das vorhandene Build-Skript
`d64qt5/build_d64qt5_mingw32.bat` bzw. das qmake-Projekt bindet
`d64_workstation.cpp` bereits ein.

Der reine Win32-Test kann mit
`d64qt5/build_workstation_smoke_test_mingw32.bat` gebaut werden.
