:: ----------------------------------------------------------------------------
:: file: compile.bat
:: author: (c) 2026 Jens Kallup - paule32
:: Stage 183: Pascal Lexer + Parser with ANTLR 4.13.2
:: ----------------------------------------------------------------------------
@echo off
setlocal EnableExtensions
pushd "%~dp0"

set "ANTLR_VERSION=4.13.2"
set "GRAMMAR_DIR=c64pascal\grammar"
set "GENERATED_DIR=c64pascal\generated"

if not exist "%GENERATED_DIR%" mkdir "%GENERATED_DIR%"

if defined ANTLR_JAR goto :use_jar

goto :use_launcher

:use_jar
if not exist "%ANTLR_JAR%" (
    echo FEHLER: ANTLR_JAR nicht gefunden: %ANTLR_JAR%
    popd
    exit /b 1
)
java -jar "%ANTLR_JAR%" -Dlanguage=Python3 -Xexact-output-dir ^
    -o "%GENERATED_DIR%" "%GRAMMAR_DIR%\C64PascalLexer.g4"
if errorlevel 1 goto :lexer_error
java -jar "%ANTLR_JAR%" -Dlanguage=Python3 -Xexact-output-dir ^
    -visitor -no-listener -lib "%GENERATED_DIR%" ^
    -o "%GENERATED_DIR%" "%GRAMMAR_DIR%\C64PascalParser.g4"
if errorlevel 1 goto :parser_error
goto :verify

:use_launcher
where antlr4.exe >nul 2>nul
if errorlevel 1 (
    echo FEHLER: antlr4.exe wurde im PATH nicht gefunden.
    echo Alternativ ANTLR_JAR auf antlr-4.13.2-complete.jar setzen.
    popd
    exit /b 2
)
antlr4.exe -v %ANTLR_VERSION% -Dlanguage=Python3 -Xexact-output-dir ^
    -o "%GENERATED_DIR%" "%GRAMMAR_DIR%\C64PascalLexer.g4"
if errorlevel 1 goto :lexer_error
antlr4.exe -v %ANTLR_VERSION% -Dlanguage=Python3 -Xexact-output-dir ^
    -visitor -no-listener -lib "%GENERATED_DIR%" ^
    -o "%GENERATED_DIR%" "%GRAMMAR_DIR%\C64PascalParser.g4"
if errorlevel 1 goto :parser_error

goto :verify

:lexer_error
echo FEHLER: Lexer konnte nicht erzeugt werden.
popd
exit /b 10

:parser_error
echo FEHLER: Parser konnte nicht erzeugt werden.
popd
exit /b 20

:verify
if not exist "%GENERATED_DIR%\C64PascalLexer.py" exit /b 21
if not exist "%GENERATED_DIR%\C64PascalParser.py" exit /b 22
if not exist "%GENERATED_DIR%\C64PascalParserVisitor.py" exit /b 23

echo.
echo OK: Pascal Lexer + Parser Stage 183 erzeugt.
dir "%GENERATED_DIR%\C64Pascal*"
echo.
echo WICHTIG: d64_dism.py danach komplett neu starten.
popd
exit /b 0
