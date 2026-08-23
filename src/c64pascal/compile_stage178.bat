:: ----------------------------------------------------------------------------
:: file: compile_stage178.bat
:: author: (c) 2026 Jens Kallup - paule32
:: purpose: regenerate Stage-178 Pascal lexer/parser with ANTLR 4.13.2
:: ----------------------------------------------------------------------------
@echo off
setlocal EnableExtensions
set "ANTLR_VERSION=4.13.2"
pushd "%~dp0"

set "GRAMMAR_DIR=c64pascal\grammar"
set "GENERATED_DIR=c64pascal\generated"

where antlr4.exe >nul 2>nul
if errorlevel 1 (
    echo FEHLER: antlr4.exe wurde im PATH nicht gefunden.
    popd
    exit /b 1
)

if not exist "%GRAMMAR_DIR%\C64PascalLexer.g4" (
    echo FEHLER: %GRAMMAR_DIR%\C64PascalLexer.g4 fehlt.
    popd
    exit /b 2
)
if not exist "%GRAMMAR_DIR%\C64PascalParser.g4" (
    echo FEHLER: %GRAMMAR_DIR%\C64PascalParser.g4 fehlt.
    popd
    exit /b 3
)
if not exist "%GENERATED_DIR%" mkdir "%GENERATED_DIR%"

antlr4.exe -v %ANTLR_VERSION% ^
    -Dlanguage=Python3 ^
    -Xexact-output-dir ^
    -o "%GENERATED_DIR%" ^
    "%GRAMMAR_DIR%\C64PascalLexer.g4"
if errorlevel 1 (
    echo FEHLER: Lexer konnte nicht erzeugt werden.
    popd
    exit /b 10
)

antlr4.exe -v %ANTLR_VERSION% ^
    -Dlanguage=Python3 ^
    -Xexact-output-dir ^
    -o "%GENERATED_DIR%" ^
    -visitor ^
    -no-listener ^
    -lib "%GENERATED_DIR%" ^
    "%GRAMMAR_DIR%\C64PascalParser.g4"
if errorlevel 1 (
    echo FEHLER: Parser konnte nicht erzeugt werden.
    popd
    exit /b 20
)

if not exist "%GENERATED_DIR%\C64PascalParser.py" (
    echo FEHLER: C64PascalParser.py wurde nicht erzeugt.
    popd
    exit /b 21
)
if not exist "%GENERATED_DIR%\C64PascalParserVisitor.py" (
    echo FEHLER: C64PascalParserVisitor.py wurde nicht erzeugt.
    popd
    exit /b 22
)

echo.
echo OK: Stage-178 Parser/Lexer erzeugt.
dir "%GENERATED_DIR%\C64Pascal*"
echo.
echo WICHTIG: d64_dism.py jetzt komplett neu starten.
popd
exit /b 0
