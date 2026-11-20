@echo off
setlocal EnableExtensions DisableDelayedExpansion
rem Stage 653: Nur libd64_qt5.dll fuer Turbo-Vision-Hilfe erzeugen.
rem KEIN externer Hilfeprozess und KEINE turbo_help_host.exe.
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
rem Optionales Bereinigen alter Stage-651/652-Host-Artefakte.
for %%F in ("%BASE%d64qt5\release\turbo_help_host.exe" "%TARGET%\turbo_help_host.exe") do (
    if exist "%%~fF" (
        del /f /q "%%~fF"
        if exist "%%~fF" echo WARNUNG: Altdatei konnte nicht entfernt werden: %%~fF
    )
)
echo Stage 653: libd64_qt5.dll bereitgestellt; native Turbo-Hilfe per F1.
exit /b 0
