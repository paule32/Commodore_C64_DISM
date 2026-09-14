@echo off
setlocal
cd /d "%~dp0"


where qmake >nul 2>nul
if errorlevel 1 (
    echo FEHLER: qmake wurde nicht im PATH gefunden.
    exit /b 1
)

where mingw32-make >nul 2>nul
if errorlevel 1 (
    echo FEHLER: mingw32-make wurde nicht im PATH gefunden.
    exit /b 1
)

rem Stage 118: den geaenderten Bridge-Quelltext sicher neu kompilieren.
if exist release\d64qt5_bridge.o del /f /q release\d64qt5_bridge.o
if exist debug\d64qt5_bridge.o del /f /q debug\d64qt5_bridge.o

echo [1/3] qmake...
qmake d64qt5_bridge.pro CONFIG+=release
if errorlevel 1 exit /b 1

echo [2/3] Build...
mingw32-make -j4
if errorlevel 1 exit /b 1

echo [3/3] Fertig.
if exist d64qt5.dll (
    echo DLL: %CD%\d64qt5.dll
) else (
    echo Hinweis: Pruefe das von qmake konfigurierte Ausgabeverzeichnis.
)

endlocal
