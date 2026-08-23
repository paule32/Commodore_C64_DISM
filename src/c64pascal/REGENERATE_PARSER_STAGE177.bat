@echo off
setlocal EnableExtensions

rem Stage 177 - regenerate Pascal lexer/parser with ANTLR 4.13.2
rem Usage: REGENERATE_PARSER_STAGE177.bat T:\Tools\antlr-4.13.2-complete.jar

if "%~1"=="" (
    echo Usage: %~nx0 ^<antlr-4.13.2-complete.jar^>
    exit /b 2
)
set "ANTLR_JAR=%~f1"
if not exist "%ANTLR_JAR%" (
    echo FEHLER: ANTLR-JAR nicht gefunden: %ANTLR_JAR%
    exit /b 3
)

py -c "import importlib.metadata as m; v=m.version('antlr4-python3-runtime'); print('antlr4-python3-runtime:',v); raise SystemExit(0 if v=='4.13.2' else 4)"
if errorlevel 1 (
    echo FEHLER: Installiere zuerst:
    echo   py -m pip install antlr4-python3-runtime==4.13.2
    exit /b 4
)

py "%~dp0generate_parser.py" "%ANTLR_JAR%"
if errorlevel 1 exit /b %ERRORLEVEL%

echo.
echo OK: C64PascalLexer.py / C64PascalParser.py / Visitor wurden neu erzeugt.
echo Danach d64_dism.py neu starten, damit keine alte Parserkopie im Speicher bleibt.
exit /b 0
