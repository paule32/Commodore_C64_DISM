@echo off
setlocal
cd /d "%~dp0"
if "%CXX%"=="" set "CXX=g++"
%CXX% -m64 -std=c++17 -O2 -s -Wall -Wextra -static-libgcc -static-libstdc++ -mwindows d64_dism_launcher.cpp -o ..\d64_dism_launcher.exe -lshell32
if errorlevel 1 exit /b %errorlevel%
echo Erzeugt: ..\d64_dism_launcher.exe ^(64 Bit^)
