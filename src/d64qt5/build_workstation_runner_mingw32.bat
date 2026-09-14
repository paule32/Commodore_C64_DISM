@echo off
setlocal
cd /d "%~dp0"


rem ---------------------------------------------------------------------------
rem File:   build_workstation_runner_mingw32.bat
rem Stage:  118
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

rem Stage 117: immer einen frischen qmake-Build erzeugen. Der Runner war vor
rem Stage 116 eine reine Win32-Anwendung; ein altes Makefile kompiliert ihn
rem sonst ohne QtWidgets-Includepfade und fuehrt zu "QApplication: No such file".
if exist build-mingw32 rmdir /s /q build-mingw32
if errorlevel 1 (
    echo FEHLER: build-mingw32 konnte nicht entfernt werden.
    exit /b 1
)
mkdir build-mingw32
if errorlevel 1 exit /b 1

echo Qt/qmake:
qmake -query QT_VERSION
if errorlevel 1 exit /b 1
qmake -query QT_INSTALL_HEADERS
if errorlevel 1 exit /b 1

pushd build-mingw32

echo [1/2] qmake Qt5 Widgets Projekt...
qmake ..\workstation_runner.pro CONFIG+=release -spec win32-g++
if errorlevel 1 (
    popd
    exit /b 1
)

rem Sicherheitspruefung: Das frisch erzeugte Makefile muss QtWidgets enthalten.
findstr /I /C:"QtWidgets" Makefile.Release >nul 2>nul
if errorlevel 1 findstr /I /C:"QtWidgets" Makefile >nul 2>nul
if errorlevel 1 (
    echo FEHLER: qmake hat keine QtWidgets-Includepfade erzeugt.
    echo Bitte eine Qt5-MinGW-qmake.exe im PATH verwenden.
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
