@echo off
setlocal EnableExtensions DisableDelayedExpansion
rem Stage 623 - Turbo-Vision-Ausgabe: verschiebbar und maximierbar.
rem Vom Projektroot aus starten: build_and_deploy_dbase_debug_stage623.bat [Ausgabeverzeichnis]
set "BASE=%~dp0"
set "TARGET=%BASE%runtime\dbase\pe32"
if not "%~1"=="" set "TARGET=%~1"

echo [Stage 623] Qt5-PE32-Build mit Move / Maximieren / Wiederherstellen
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
    echo FEHLER: DLL konnte nicht ersetzt werden. Alle dBASE-EXE-Prozesse vorher schliessen.
    exit /b 1
)
echo.
echo Installierte DLL: "%TARGET%\libd64_qt5.dll"
certutil -hashfile "%TARGET%\libd64_qt5.dll" SHA256
if errorlevel 1 echo Hinweis: Hash-Ausgabe mit certutil nicht verfuegbar.
echo.
echo Neue dBASE-EXE starten und im gruenen Fenster Titelleiste ziehen.
echo Maximieren: Button oben rechts oder Doppelklick auf die Titelleiste.
endlocal
exit /b 0
