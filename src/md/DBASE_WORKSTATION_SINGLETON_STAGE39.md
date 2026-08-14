# Stage 39 - Windows-globaler Workstation-Singleton

Basis: Stage 38A.

## Ziel

Wenn bereits eine d64qt5-Workstation existiert, darf ein weiteres `BTX.exe`
keine zweite Workstation erzeugen. Es soll sein eigenes Hauptfenster auf dem
bereits vorhandenen Workstation-Desktop starten.

## Umsetzung

`d64qt5/d64_workstation.cpp` besitzt jetzt zwei Rollen:

- **OWNER**: erste Runtime; besitzt Workstation-Lebensdauer, Panel, Desktop-
  Umschaltung und Keyboard-Hook.
- **JOINED**: weitere Runtime; benutzt denselben Desktop und erzeugt nur ihre
  eigenen Programmfenster.

Windows-Synchronisation:

- Lifetime-Mutex: `Global\\dBase2Many.D64Workstation.Singleton`
- Ready-Event: `Global\\dBase2Many.D64Workstation.Ready`
- Desktop: `WinSta0\\D64Workstation`

Der OWNER haelt den Mutex waehrend der gesamten Workstation-Lebensdauer. Das
Ready-Event verhindert das Rennen, bei dem eine zweite Runtime den Mutex schon
sieht, bevor der Desktop fertig erzeugt wurde.

`D64WorkstationPrepare()` wird weiterhin vor `QApplication` aufgerufen. Ein
JOINED-Prozess oeffnet `D64Workstation` und bindet seinen GUI-Thread mit
`SetThreadDesktop()` daran. Ein bereits ueber `STARTUPINFO.lpDesktop`
gestartetes BTX.exe wird als schon gebunden erkannt.

`D64WorkstationActivate()` erzeugt fuer JOINED kein Panel und ruft kein
`SwitchDesktop()` auf. `D64WorkstationInstallKeyboardGuard()` installiert den
Hook ebenfalls nur im OWNER.

## Build

Im Verzeichnis `d64qt5`:

```bat
qmake d64qt5_bridge.pro CONFIG+=release
mingw32-make release
```

oder:

```bat
build_d64qt5_mingw32.bat
```

Die erzeugte `d64qt5.dll` enthaelt `d64_workstation.cpp` bereits ueber das
qmake-Projekt.

## Erwarteter Ablauf

1. Erstes dBase/BTX-Programm startet: OWNER erzeugt und zeigt Workstation.
2. Weiteres `BTX.exe` startet: globaler Mutex ist belegt.
3. Zweite Runtime wird JOINED und oeffnet `WinSta0\\D64Workstation`.
4. Nur das BTX-Hauptfenster erscheint auf der vorhandenen Workstation.
5. Kein zweites EXIT/BTX/DB-Panel und kein zweiter Workstation-Desktop.
