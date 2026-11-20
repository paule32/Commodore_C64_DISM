@echo off
setlocal EnableExtensions DisableDelayedExpansion
rem Stage 655: Aktualisierte native Turbo-Hilfe im Konsole-Viewport.
rem Es wird NUR libd64_qt5.dll gebaut und installiert, kein Help-Host.
set "BASE=%~dp0"
set "TARGET=%BASE%runtime\dbase\pe32"
if not "%~1"=="" set "TARGET=%~1"
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
copy /y "%SOURCE%" "%TARGET%\libd64_qt5.dll" >nul
if errorlevel 1 (
    echo FEHLER: DLL konnte nicht installiert werden. Laufende EXE beenden!
    exit /b 1
)
for %%F in ("%BASE%d64qt5\release\turbo_help_host.exe" "%TARGET%\turbo_help_host.exe") do (
    if exist "%%~fF" del /f /q "%%~fF"
)
echo Stage 655: libd64_qt5.dll mit Turbo Hilfe im Tab Konsole bereitgestellt.
exit /b 0
