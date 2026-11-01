@echo off
setlocal
cd /d "%~dp0"
if not exist "bin" mkdir "bin"
where g++ >nul 2>&1
if errorlevel 1 (
    echo MinGW32 g++ nicht gefunden. In MSYS2 MINGW32-Shell ausfuehren.
    exit /b 1
)
for /f "delims=" %%T in ('g++ -dumpmachine') do set "TARGET=%%T"
echo Target: %TARGET%
echo %TARGET% | findstr /i "i686" >nul
if errorlevel 1 (
    echo Falscher Compiler: bitte die passende MSYS2 MinGW-Shell verwenden.
    exit /b 1
)
g++ -std=c++17 -O2 -Wall -Wextra -municode -mwindows -D_WIN32_WINNT=0x0601 -static -static-libgcc -static-libstdc++ -o bin/d64_watchdog_x86.exe watchdog.cpp -lshell32 -luser32
if errorlevel 1 exit /b 1

where strip >nul 2>&1 && strip bin/d64_watchdog_x86.exe
echo Fertig: bin/d64_watchdog_x86.exe
