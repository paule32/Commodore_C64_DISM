@echo off
setlocal

rem ---------------------------------------------------------------------------
rem File:   build_workstation_runner_mingw32.bat
rem Stage:  116
rem Zweck:  Qt5-Workstation-Runner + zentraler QPlainTextEdit-Ausgabedialog.
rem ---------------------------------------------------------------------------

where qmake >nul 2>nul
if errorlevel 1 (
    echo FEHLER: qmake wurde im PATH nicht gefunden.
    exit /b 1
)

where mingw32-make >nul 2>nul
if errorlevel 1 (
    echo FEHLER: mingw32-make wurde im PATH nicht gefunden.
    exit /b 1
)

if not exist workstation_runner.cpp (
    echo FEHLER: workstation_runner.cpp wurde im aktuellen Verzeichnis nicht gefunden.
    exit /b 1
)
if not exist d64_workstation.cpp (
    echo FEHLER: d64_workstation.cpp wurde im aktuellen Verzeichnis nicht gefunden.
    exit /b 1
)
if not exist workstation_runner.pro (
    echo FEHLER: workstation_runner.pro wurde im aktuellen Verzeichnis nicht gefunden.
    exit /b 1
)

if not exist build-mingw32 mkdir build-mingw32

pushd build-mingw32

echo [1/2] qmake...
qmake ..\workstation_runner.pro CONFIG+=release
if errorlevel 1 (
    popd
    exit /b 1
)

echo [2/2] Build...
mingw32-make -j4
if errorlevel 1 (
    popd
    exit /b 1
)

popd

echo Fertig: %CD%\build-mingw32\d64_workstation_runner.exe
endlocal
