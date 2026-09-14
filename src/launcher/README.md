# d64_dism Launcher / externer Watchdog (Stage 140)

Der Launcher ist absichtlich reines Win32-C++ und benutzt weder Qt noch Python.
Er startet `d64_dism.exe` bzw. als Fallback `python.exe d64_dism.py`, ueberwacht
Exitcode und GUI-Heartbeat und zeigt bei einem harten Absturz eine native
`MessageBoxW` an.

## Konsolenverhalten

Standardmaessig startet der Launcher **ohne sichtbares Konsolenfenster**. Das gilt
auch fuer den Fallback ueber `python.exe`; der Child-Prozess wird dann mit
`CREATE_NO_WINDOW` erzeugt. `stdout` und `stderr` bleiben trotzdem erhalten und
werden nach `d64_dism_console.log` neben der Anwendung geschrieben.

Soll die Konsolenausgabe sichtbar sein:

```text
d64_dism_launcher.exe --console
```

Der Launcher versucht zuerst, sich an die Konsole der aufrufenden Shell
anzukoppeln. Existiert keine, wird eine neue Konsole erzeugt. Alternativ kann
`D64_LAUNCHER_CONSOLE=1` gesetzt werden. Mit `--no-console` wird der stille Modus
explizit erzwungen. Launcher-Optionen werden nicht an `d64_dism` weitergegeben;
nach `--` werden alle weiteren Argumente unveraendert an die Anwendung gereicht.

## Build

MSYS2 MINGW32:

```sh
launcher/build_launcher.sh
# oder launcher\build_launcher_mingw32.bat
```

MSYS2 MINGW64/UCRT64:

```sh
launcher/build_launcher.sh
# oder launcher\build_launcher_mingw64.bat
```

`build_launcher.sh` erkennt die Architektur ueber `g++ -dumpmachine` und benutzt
entsprechend `-m32` oder `-m64`. `CXX` und `ARCH_FLAG` koennen explizit gesetzt
werden. Der Launcher selbst wird mit `-mwindows` als Windows-GUI-Anwendung gebaut.

## Start

Liegt `d64_dism_launcher.exe` neben `d64_dism.exe`, wird die EXE gestartet.
Andernfalls wird `d64_dism.py` ueber `D64_PYTHON`, `python.exe` oder `py.exe`
gestartet.

Explizites Ziel:

```text
d64_dism_launcher.exe --app T:\Pfad\d64_dism.py [--console] [--] [weitere Argumente]
```

Der Launcher setzt fuer das Child temporaer:

- `D64_WATCHDOG_DIR`
- `D64_WATCHDOG_TOKEN`
- `D64_LAUNCHER_PID`
- `D64_LAUNCHED_BY_WATCHDOG=1`

Der Qt-GUI-Thread aktualisiert `heartbeat.txt` jede Sekunde. Bleibt der
Heartbeat >15 Sekunden stehen, bietet der Launcher nativ Abbrechen,
Wiederholen oder Ignorieren an. Bei sauberem Programmende wird der temporaere
Watchdog-Ordner entfernt; nach einem Crash bleibt er zur Diagnose bestehen.
