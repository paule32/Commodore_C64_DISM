@echo off
setlocal EnableExtensions DisableDelayedExpansion
rem Stage 629: mehrfache blaue Turbo-Vision-Editoren, Pfeil-Scrollleisten, VFS.
rem Aufruf: build_and_deploy_dbase_editor_stage629.bat [Ausgabeverzeichnis]
set "BASE=%~dp0"
set "TARGET=%BASE%runtime\dbase\pe32"
if not "%~1"=="" set "TARGET=%~1"

echo [Stage 629] Qt5-Bridge mit Editorfenstern und DOS-Scrollleisten bauen ...
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
    echo FEHLER: DLL belegt? Bitte alle aktiven EXE-Prozesse beenden.
    exit /b 1
)
echo.
echo DLL installiert: "%TARGET%\libd64_qt5.dll"
echo Datei -^> Neu erzeugt jetzt ein eigenstaendiges Editorfenster.
echo Bestehende EXE-Dateien muessen fuer diese GUI-Aenderung nicht neu gelinkt werden.
endlocal
exit /b 0
