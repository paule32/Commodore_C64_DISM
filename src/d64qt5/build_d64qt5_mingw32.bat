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

rem Stage 213: ABI-/Ordinal-Hash immer aus der expliziten DEF-Tabelle regenerieren.
where python >nul 2>nul
if errorlevel 1 (
    echo FEHLER: python wurde fuer generate_runtime_abi.py nicht im PATH gefunden.
    exit /b 1
)
python generate_runtime_abi.py
if errorlevel 1 exit /b 1

rem Stage 118: den geaenderten Bridge-Quelltext sicher neu kompilieren.
if exist release\d64qt5_bridge.o del /f /q release\d64qt5_bridge.o
if exist debug\d64qt5_bridge.o del /f /q debug\d64qt5_bridge.o
if exist release\libd64_qt5.dll del /f /q release\libd64_qt5.dll
if exist debug\libd64_qt5.dll del /f /q debug\libd64_qt5.dll

echo [1/3] qmake...
qmake d64qt5_bridge.pro CONFIG+=release
if errorlevel 1 exit /b 1

echo [2/3] Build...
mingw32-make -j4
if errorlevel 1 exit /b 1

echo [3/3] Fertig.
if exist release\libd64_qt5.dll (
    echo DLL: %CD%\release\libd64_qt5.dll
) else if exist release\d64_qt5.dll (
    copy /y release\d64_qt5.dll release\libd64_qt5.dll >nul
    echo DLL: %CD%\release\libd64_qt5.dll
) else if exist libd64_qt5.dll (
    echo DLL: %CD%\libd64_qt5.dll
) else (
    echo Hinweis: Pruefe das von qmake konfigurierte Ausgabeverzeichnis.
)

endlocal
