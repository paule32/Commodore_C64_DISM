# Commodore_C64_DISM – externer Crash-Watchdog (Stage 526)

Der Watchdog orientiert sich an der unabhängigen Win32-Implementierung des
Repositories `paule32/PythonBDE`. Die Überwachung läuft in einem **eigenen
Win32-C++-Prozess**, der weder Python noch Qt lädt. Er überwacht das Prozessende
und zeigt bei einem unerwarteten Exit einen nativen Dialog mit mehrzeiligem
`EDIT`-Control, Scrollbars, **Copy Traceback** und **Close**. Ein abgestürzter
Python-/PyQt5-Prozess kann sich nicht selbst reparieren oder sicher fortsetzen.

## Empfohlener Start

Im Verzeichnis `src`:

```cmd
python3.15 __main__.py
```

Oder aus dem Repository-Stammverzeichnis:

```cmd
python -m src
```

**`__main__.py` ist der zentrale Python-GUI-Einstieg.** Der Watchdog und die
frühe Fehlerbehandlung werden **vor dem ersten PyQt5-Import** gestartet.
Anschließend bleiben der C64-Splash sowie der Stage-525-MDX-Selbsttest erhalten.
Der direkte Start von `d64_dism.py` bleibt für ältere Aufrufe verfügbar, führt
aber die neue frühe `__main__.py`-Watchdog-Initialisierung nicht durch.

## Build ohne Python-/Qt-Abhängigkeit

MSYS2 MinGW64 (64-Bit-Python):

```cmd
watchdog\build_mingw64.bat
```

MSYS2 MinGW32 (32-Bit-Python):

```cmd
watchdog\build_mingw32.bat
```

Die Skripte schreiben nach `watchdog/bin/d64_watchdog_x64.exe` bzw.
`watchdog/bin/d64_watchdog_x86.exe`. Es müssen die **passenden** MinGW-Versionen
auf dem `PATH` stehen. Ein nativer C++-Compiler ist nur für den Build nötig.

Fehlt die EXE beim Start, versucht PythonBDE-ähnlich `native_watchdog.py`
einen automatischen Build mit einem passenden MinGW-g++ und speichert das
Ergebnis in `%LOCALAPPDATA%\Commodore_C64_DISM\watchdog\`. Ist MinGW nicht
vorhanden, läuft die IDE weiter; die Ursache wird protokolliert.

## Logs

Unter Windows:

- `%LOCALAPPDATA%\Commodore_C64_DISM\d64_dism_errors.log` – Python-Ausnahmen und stderr
- `%LOCALAPPDATA%\Commodore_C64_DISM\d64_dism_fatal_<PID>.log` – faulthandler für native Abstürze

Die Text-Logdatei rotiert ab 5 MiB; die vorherige Kopie erhält `.old`. Falls
das Benutzerverzeichnis nicht beschreibbar ist, wird für normale Python-Fehler
das temporäre Verzeichnis verwendet. Das per-PID-Fatal-Log bleibt während der
Python-Laufzeit offen. Stacktraces sind von Python-/Windows-Version und der
Art des Absturzes abhängig, nicht bei jedem nativen Fehler verfügbar.

## Crash-Simulation (absichtlich destruktiv für den Testprozess)

Aus `src`:

```cmd
python3.15 watchdog\smoke_test.py
```

Dies startet einen Watchdog und beendet nur den Testprozess mit Code 33.
Alternativ `--native-abort`, um einen absichtlichen nativen Abort auszulösen.
**Nicht** im produktiven GUI-Prozess ausführen; nicht gespeicherte Daten
würden dort verloren gehen.

## Start über start.exe

Der schon vorhandene native C++-Launcher `launcher/d64_dism_launcher.cpp`
überwacht bereits Prozessende und GUI-Heartbeat. Für dessen Python-Fallback
verwendet er ab Stage 526 `__main__.py` statt `d64_dism.py`. Er setzt
`D64_LAUNCHED_BY_WATCHDOG=1`; dann wird kein *zweiter* nativer Wächter
geöffnet. Die frühen Python-Logs sowie faulthandler bleiben aktiviert.
Dies verhindert doppelte Crash-Dialoge.

## Konfiguration

`D64_DISABLE_WATCHDOG=1` deaktiviert den externen nativen Monitor für einen
direkten Start. Die frühe Python-Fehlerbehandlung bleibt aktiviert. Ein
fehlgeschlagener nativer Watchdog-Build verhindert den GUI-Start nicht.

## Optionale Windows Error Reporting (WER) Dumps

Die Datei `enable_wer_dumps.ps1` richtet bei Ausführung mit Administratorrechten
WER LocalDumps ein. Vorher den Prozessnamen prüfen: eine Regel für
`pythonw.exe` betrifft **alle** Anwendungen, die diese EXE benutzen. Dumps
können private Daten enthalten und müssen geschützt werden.

**Grenzen:** Ohne echten Windows-Test kann die Interoperabilität von
Win32-EDIT-Fenster, MSYS2-MinGW32/64 und faulthandler nicht abschließend
bestätigt werden. Es gibt **keinen automatischen Neustart** und keine Garantie,
dass ein vollständig abgestürzter Betriebssystemprozess noch Logdaten schreibt.
MDX/ODBC ist eine unabhängige Stage-525-Startprüfung.
