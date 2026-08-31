@echo off
setlocal

rem ---------------------------------------------------------------------------
rem File:   build_workstation_runner_mingw32.bat
rem Stage:  243
rem Zweck:  Einmaliger Build des generischen Win32-Workstation-Runners.
rem          Stage 243: direkter CLI-Start einer Anwendung.
rem          Der normale Start in d64_dism.py ruft dieses Skript NICHT auf.
rem ---------------------------------------------------------------------------

where g++ >nul 2>nul
if errorlevel 1 (
    echo FEHLER: g++ wurde nicht im PATH gefunden.
    exit /b 1
)

if not exist d64_workstation.cpp (
    echo FEHLER: d64_workstation.cpp wurde im aktuellen Verzeichnis nicht gefunden.
    exit /b 1
)
if not exist d64_workstation.h (
    echo FEHLER: d64_workstation.h wurde im aktuellen Verzeichnis nicht gefunden.
    exit /b 1
)
if not exist workstation_runner.cpp (
    echo FEHLER: workstation_runner.cpp wurde im aktuellen Verzeichnis nicht gefunden.
    exit /b 1
)

if not exist build-mingw32 mkdir build-mingw32

echo Baue generischen PE32-Workstation-Runner...
g++ -m32 -std=gnu++11 -O2 -municode -mwindows -pthread ^
    workstation_runner.cpp d64_workstation.cpp ^
    -o build-mingw32\d64_workstation_runner.exe ^
    -luser32 -lgdi32
if errorlevel 1 exit /b 1

echo Fertig: %CD%\build-mingw32\d64_workstation_runner.exe
endlocal
