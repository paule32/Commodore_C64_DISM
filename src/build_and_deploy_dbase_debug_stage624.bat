@echo off
setlocal EnableExtensions DisableDelayedExpansion
rem Stage 624 - SET BACKGROUND: erneuert libd64_qt5.dll.
rem Vom Projektroot aus starten: build_and_deploy_dbase_debug_stage624.bat [Ausgabeverzeichnis]
set "BASE=%~dp0"
set "TARGET=%BASE%runtime\dbase\pe32"
if not "%~1"=="" set "TARGET=%~1"

echo [Stage 624] Qt5-PE32-Build mit SET BACKGROUND TO ...
call "%BASE%d64qt5\build_d64qt5_mingw32.bat"
if errorlevel 1 (
    echo FEHLER: Build der Qt5-Bridge fehlgeschlagen.
    exit /b 1
)
set "SOURCE=%BASE%d64qt5\release\libd64_qt5.dll"
if not exist "%SOURCE%" (
    echo FEHLER: libd64_qt5.dll fehlt unter "%SOURCE%"
    exit /b 1
)
if not exist "%TARGET%" mkdir "%TARGET%"
if errorlevel 1 exit /b 1
copy /y "%SOURCE%" "%TARGET%\libd64_qt5.dll"
if errorlevel 1 (
    echo FEHLER: DLL konnte nicht ersetzt werden. EXE-Prozesse vorher schliessen.
    exit /b 1
)
echo.
echo Installierte DLL: "%TARGET%\libd64_qt5.dll"
certutil -hashfile "%TARGET%\libd64_qt5.dll" SHA256
if errorlevel 1 echo Hinweis: Hash-Ausgabe nicht verfuegbar.
echo.
echo WICHTIG: dBASE-PRG mit Stage 624 erneut kompilieren,
echo assemblieren und linken. Erst danach die EXE starten.
endlocal
exit /b 0
