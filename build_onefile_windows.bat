@echo off
setlocal
cd /d "%~dp0"

rem Stage 528: BUILD FROM REPOSITORY ROOT. The spec uses src\__main__.py.
rem A matching MSYS2 MinGW compiler must be available on PATH.
if not defined D64_PYTHON set "D64_PYTHON=python.exe"

echo.
echo === d64_dism ONEFILE + native watchdog ===
"%D64_PYTHON%" -m PyInstaller --noconfirm --clean d64_dism.spec
if errorlevel 1 (
    echo.
    echo ERROR: Build failed. Check Python dependencies and MinGW compiler.
    exit /b 1
)
echo.
echo ONEFILE created: %CD%\dist\d64_dism.exe
echo Native watchdog is embedded; it has no visible window until a crash.
echo Test: dist\d64_dism.exe --watchdog-self-test
exit /b 0
