@echo off
setlocal

where g++ >nul 2>nul
if errorlevel 1 (
    echo FEHLER: g++ wurde nicht im PATH gefunden.
    exit /b 1
)

echo Baue reinen Win32-Workstation-Test...
g++ -m32 -std=c++11 -O2 -municode -mwindows ^
    workstation_smoke_test.cpp d64_workstation.cpp ^
    -o workstation_smoke_test.exe -luser32 -lgdi32
if errorlevel 1 exit /b 1

echo Fertig: %CD%\workstation_smoke_test.exe
endlocal
