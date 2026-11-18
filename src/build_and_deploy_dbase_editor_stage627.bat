@echo off
setlocal EnableExtensions DisableDelayedExpansion
rem Stage 627 - Turbo-Vision-C++20-Warnungsbereinigung fuer den Turbo-Vision-Editor in der Qt5-Bridge.
rem Aufruf im Projektverzeichnis: build_and_deploy_dbase_editor_stage627.bat [Ausgabeverzeichnis]
set "BASE=%~dp0"
set "TARGET=%BASE%runtime\dbase\pe32"
if not "%~1"=="" set "TARGET=%~1"

echo [Stage 627] Qt5-Bridge mit C++20-Warnungsbereinigung bauen ...
call "%BASE%d64qt5\build_d64qt5_mingw32.bat"
if errorlevel 1 (
    echo FEHLER: Qt5-MinGW32-Build fehlgeschlagen.
    exit /b 1
)
set "SOURCE=%BASE%d64qt5\release\libd64_qt5.dll"
if not exist "%SOURCE%" (
    echo FEHLER: Qt5-DLL nicht gefunden: "%SOURCE%"
    exit /b 1
)
if not exist "%TARGET%" mkdir "%TARGET%"
if errorlevel 1 exit /b 1
copy /y "%SOURCE%" "%TARGET%\libd64_qt5.dll"
if errorlevel 1 (
    echo FEHLER: DLL konnte nicht kopiert werden; alle EXE-Prozesse vorher beenden.
    exit /b 1
)
echo.
echo DLL installiert: "%TARGET%\libd64_qt5.dll"
echo Editor: Datei -^> Neu oder Datei -^> Oeffnen...
echo Keine neue Compiler-ABI: eine bestehende Stage-625-EXE kann die neue DLL laden.
endlocal
exit /b 0
