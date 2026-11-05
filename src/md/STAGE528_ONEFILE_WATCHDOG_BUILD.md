# Stage 528: Windows ONEFILE + nativer Watchdog

## Ziel

Aus dem aktuellen Repository wird eine einzige weitergebbare Windows-EXE
gebaut. Der Python-Einstieg ist **src/__main__.py**, NICHT src/d64_dism.py.
Der Win32-Watchdog bleibt ein eigener Prozess, wird aber **in der EXE**
mitgeliefert und bei jedem GUI-Start automatisch aus dem Bundle geladen.

## Voraussetzungen

- Windows, 32- oder 64-Bit Python passend zur Zielarchitektur.
- pip install pyinstaller PyQt5 PyQtWebEngine
- pyodbc ggf. zusätzlich, falls die dBASE/ODBC-Funktionen genutzt werden.
- MSYS2 MinGW32/MinGW64 g++ passend zur Python-Bitness, auf PATH.
  Optional: Umgebungsvariable D64_WATCHDOG_CXX mit Pfad zur passenden g++.exe.
- Der Zielrechner selbst benötigt **weder Python noch MinGW**. Eventuell
  verwendete ODBC-Treiber müssen für die jeweiligen ODBC-Funktionen separat
  installiert sein.

## Build: Im Repository-Hauptverzeichnis

    python.exe -m PyInstaller --noconfirm --clean d64_dism.spec

Oder mit der Batch-Datei:

    build_onefile_windows.bat

Für Python 3.15 explizit entsprechend:

    python3.15 -m PyInstaller --noconfirm --clean d64_dism.spec

Beide verwenden die Root-Spec. Die gesonderte src/d64_dism.spec bleibt
unverändert und dient weiterhin dem älteren One-Directory-Build.

Ausgabe:

    dist\d64_dism.exe

Die Root-Spec kompiliert vor der PyInstaller-Analyse automatisch
src/watchdog/watchdog.cpp zu einer passenden nativen PE32/PE32+
d64_watchdog_x86.exe bzw. d64_watchdog_x64.exe und bettet sie als Binary
unter watchdog/bin ein. Wenn ein passender MinGW-Compiler fehlt oder die
Compiler-Zielarchitektur nicht zum Python-Prozess passt, bricht der Build
explizit ab (kein irreführendes Bundle ohne Watchdog).

## Laufzeit

Beim Start extrahiert PyInstaller die eingebetteten Dateien nach _MEIPASS.
Der Watchdog-Starter findet dort watchdog/bin/d64_watchdog_<arch>.exe.
Er kopiert diese unverändert nach:

    %LOCALAPPDATA%\Commodore_C64_DISM\watchdog\
        d64_watchdog_<arch>_<sha256prefix>.exe

Das verhindert Windows-Sperren der PyInstaller-Temporärdateien nach einem
Crash. Verschiedene App-Versionen erhalten unterschiedliche
versionsabhängige Cache-Namen. Anschließend läuft der Watchdog als eigener
Windows-Prozess. Er hat **absichtlich kein ständig sichtbares GUI-Fenster**.
Erst bei einem nicht erwarteten Prozess-Ende öffnet er eine native,
kopierbare Fehlermeldung (PythonBDE-Prinzip).

Logs:

    %LOCALAPPDATA%\Commodore_C64_DISM\d64_dism_errors.log
    %LOCALAPPDATA%\Commodore_C64_DISM\d64_dism_fatal_<PID>.log

Das vorhandene start.exe darf NICHT vor die neue Onefile-EXE gesetzt werden:
es verwendet einen eigenen Launcher/Watchdog. Der Direktstart der Onefile-EXE
ermöglicht die interne Watchdog-Überwachung ohne Duplikate.

## Test auf Windows

Erst normal starten:

    dist\d64_dism.exe

In einem zweiten Terminal:

    tasklist /FI "IMAGENAME eq d64_watchdog_x64*.exe"

Der Windows tasklist-Wildcard-Filter kann unterschiedlich arbeiten; alternativ:

    tasklist | findstr /I d64_watchdog

Der absichtliche Funktionstest startet die eingebettete Watchdog-Instanz und
beendet nur diese gerade gestartete Test-Instanz mit Exitcode 33:

    dist\d64_dism.exe --watchdog-self-test

**Nicht** im normalen produktiven GUI-Prozess aufrufen. Bei funktionierendem
Watchdog sollte der native Crash-Dialog erscheinen. Der Exitcode ist im Test
absichtlich ungleich null.

## Hinweise

- console=True in der Spec ist für die erste Diagnose bewusst aktiviert.
  Nach einem bestätigten Windows-Test kann auf console=False umgestellt werden.
- Die QtWebEngine- und zusätzlichen Asset-Pfade aus der bisherigen
  src/d64_dism.spec sind in den Root-Onefile-Build übertragen. Je nach
  lokal benötigten Laufzeittools/Projektdateien können noch zusätzliche
  Daten oder nicht-Python-Executables erforderlich sein.
- Eine Windows-EXE kann hier nicht unter Linux nativ gebaut oder getestet
  werden. Der eigentliche PE32/PE32+ Smoke-Test muss unter Windows erfolgen.
