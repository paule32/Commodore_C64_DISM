@echo off
setlocal EnableExtensions DisableDelayedExpansion
rem Stage 657: Turbo-Hilfe rastet beim Verschieben auf DOS-Zeichenzellen ein.
rem Es wird ausschliesslich libd64_qt5.dll erstellt, kein Hilfe-Host.
set "BASE=%~dp0"
set "TARGET=%BASE%runtime\dbase\pe32"
if not "%~1"=="" set "TARGET=%~1"
call "%BASE%d64qt5\build_d64qt5_mingw32.bat"
if errorlevel 1 exit /b 1
set "SOURCE=%BASE%d64qt5\release\libd64_qt5.dll"
if not exist "%SOURCE%" (
    echo FEHLER: DLL nicht gefunden: "%SOURCE%"
    exit /b 1
)
if not exist "%TARGET%" mkdir "%TARGET%"
if errorlevel 1 exit /b 1
copy /y "%SOURCE%" "%TARGET%\libd64_qt5.dll" >nul
if errorlevel 1 exit /b 1
for %%F in ("%BASE%d64qt5\release\turbo_help_host.exe" "%TARGET%\turbo_help_host.exe") do (
    if exist "%%~fF" del /f /q "%%~fF"
)
echo Stage 657: Rasterweise verschiebbares Turbo-Hilfefenster bereitgestellt.
exit /b 0
