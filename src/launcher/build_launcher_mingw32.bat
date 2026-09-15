@echo off
setlocal
cd /d "%~dp0"
if "%CXX%"=="" set "CXX=g++"
%CXX% -m32 -std=c++17 -O2 -s -Wall -Wextra -static-libgcc -static-libstdc++ -municode -mwindows d64_dism_launcher.cpp -o ..\start.exe -lshell32
if errorlevel 1 exit /b %errorlevel%
echo Erzeugt: ..\start.exe ^(32 Bit^)
