@echo off
setlocal EnableExtensions DisableDelayedExpansion
rem Stage 633: MessageBox, ASCII-Pfeile und Kontextmenues verbessert.
rem Aufruf: build_and_deploy_dbase_editor_stage632.bat [Ausgabeverzeichnis]
set "BASE=%~dp0"
set "TARGET=%BASE%runtime\dbase\pe32"
if not "%~1"=="" set "TARGET=%~1"
echo [Stage 633] Qt5-Mingw32-Bridge mit Turbo-Vision-Werkzeugen bauen ...
call "%BASE%d64qt5\build_d64qt5_mingw32.bat"
if errorlevel 1 (
    echo FEHLER: Qt5-MinGW32-Build fehlgeschlagen.
    exit /b 1
)
set "SOURCE=%BASE%d64qt5\release\libd64_qt5.dll"
if not exist "%SOURCE%" (
    echo FEHLER: DLL nicht gefunden: "%SOURCE%"
    exit /b 1
)
if not exist "%TARGET%" mkdir "%TARGET%"
if errorlevel 1 exit /b 1
copy /y "%SOURCE%" "%TARGET%\libd64_qt5.dll"
if errorlevel 1 (
    echo FEHLER: DLL konnte nicht installiert werden. EXE-Prozesse schliessen!
    exit /b 1
)
echo.
echo DLL installiert: "%TARGET%\libd64_qt5.dll"
echo Stage 633: Turbo-Dialog und Werkzeugfenster aktualisiert.
echo Eine vorhandene dBASE-EXE muss fuer diese Qt5-DLL-Korrektur nicht neu gelinkt werden.
endlocal
exit /b 0
