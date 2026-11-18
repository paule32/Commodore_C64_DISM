@echo off
setlocal EnableExtensions DisableDelayedExpansion
rem Stage 622 - Turbo-Vision-DEBUG-Fenster als internes gruenes Zeichenfenster.
rem Aufruf vom Stage-622-Projektroot: build_and_deploy_dbase_debug_stage622.bat [Ausgabeverzeichnis]
set "BASE=%~dp0"
set "TARGET=%BASE%runtime\dbase\pe32"
if not "%~1"=="" set "TARGET=%~1"

echo [Stage 622] Qt5-PE32-Build fuer das Turbo-Vision-Ausgabefenster
call "%BASE%d64qt5\build_d64qt5_mingw32.bat"
if errorlevel 1 (
    echo FEHLER: Build der Qt5-Bridge fehlgeschlagen.
    exit /b 1
)
set "SOURCE=%BASE%d64qt5\release\libd64_qt5.dll"
if not exist "%SOURCE%" (
    echo FEHLER: Neue libd64_qt5.dll nicht gefunden: "%SOURCE%"
    exit /b 1
)
if not exist "%TARGET%" mkdir "%TARGET%"
if errorlevel 1 exit /b 1
copy /y "%SOURCE%" "%TARGET%\libd64_qt5.dll"
if errorlevel 1 (
    echo FEHLER: Die alte DLL konnte nicht ersetzt werden. EXE schliessen und erneut versuchen.
    exit /b 1
)
echo.
echo Neue DLL liegt unter: "%TARGET%\libd64_qt5.dll"
echo SHA-256 des kopierten Ergebnisses:
certutil -hashfile "%TARGET%\libd64_qt5.dll" SHA256
if errorlevel 1 echo (certutil nicht verfuegbar; Kopie wurde trotzdem erstellt)
echo.
echo Teste mit einer NEU gestarteten EXE: ? "hihi"
echo Hinweis: Eine laufende EXE haelt die bisherige DLL noch geladen.
endlocal
exit /b 0
