@echo off
setlocal EnableExtensions
rem Stage 621: PE32-Qt5-DLL neu bauen und in das dBASE-Ausgabeverzeichnis kopieren.
rem Aufruf: build_and_deploy_dbase_debug_stage621.bat [Zielverzeichnis]
set "BASE=%~dp0"
set "TARGET=%BASE%runtime\dbase\pe32"
if not "%~1"=="" set "TARGET=%~1"

echo [1/2] libd64_qt5.dll (PE32) mit Qt5 / MinGW32 neu bauen ...
call "%BASE%d64qt5\build_d64qt5_mingw32.bat"
if errorlevel 1 (
  echo FEHLER: Qt5-DLL konnte nicht neu gebaut werden.
  exit /b 1
)

set "BUILT=%BASE%d64qt5\release\libd64_qt5.dll"
if not exist "%BUILT%" (
  echo FEHLER: Build-Ausgabe nicht gefunden: "%BUILT%"
  exit /b 1
)

if not exist "%TARGET%" mkdir "%TARGET%"
if errorlevel 1 (
  echo FEHLER: Zielverzeichnis konnte nicht angelegt werden: "%TARGET%"
  exit /b 1
)

echo [2/2] Neue DLL in das dBASE-PE32-Ausgabeverzeichnis kopieren ...
copy /y "%BUILT%" "%TARGET%\libd64_qt5.dll"
if errorlevel 1 (
  echo FEHLER: Neue DLL konnte nicht kopiert werden.
  exit /b 1
)
echo FERTIG: "%TARGET%\libd64_qt5.dll"
echo Danach in d64_dism ? "Hihi" neu assemblieren/linken und Start ausfuehren.
endlocal
exit /b 0
