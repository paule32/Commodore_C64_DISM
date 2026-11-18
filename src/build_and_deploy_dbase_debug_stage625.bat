@echo off
setlocal EnableExtensions DisableDelayedExpansion
rem Stage 625 - SET BACKGROUND zeichnet die 80x25-QPlainTextEdit-Hauptflaeche.
rem Aufruf aus Projektverzeichnis: build_and_deploy_dbase_debug_stage625.bat [Ausgabeverzeichnis]
set "BASE=%~dp0"
set "TARGET=%BASE%runtime\dbase\pe32"
if not "%~1"=="" set "TARGET=%~1"

echo [Stage 625] Qt5-Bridge mit korrigierter Hintergrundebene bauen ...
call "%BASE%d64qt5\build_d64qt5_mingw32.bat"
if errorlevel 1 (
    echo FEHLER: Qt5-Build fehlgeschlagen.
    exit /b 1
)
set "SOURCE=%BASE%d64qt5\release\libd64_qt5.dll"
if not exist "%SOURCE%" (
    echo FEHLER: "libd64_qt5.dll" im Release-Ordner nicht gefunden.
    exit /b 1
)
if not exist "%TARGET%" mkdir "%TARGET%"
if errorlevel 1 exit /b 1
copy /y "%SOURCE%" "%TARGET%\libd64_qt5.dll"
if errorlevel 1 (
    echo FEHLER: DLL konnte nicht kopiert werden. EXE vorher beenden.
    exit /b 1
)
echo.
echo DLL installiert: "%TARGET%\libd64_qt5.dll"
echo Fuer ein bereits mit Stage 624 kompiliertes PRG ist keine
echo erneute EXE-Kompilierung erforderlich; der ABI-Export ist unveraendert.
echo Bitte Anwendung komplett beenden und neu starten.
endlocal
exit /b 0
