:: --------------------------------------------------------------
:: file: compile.bat
:: author: (c) 2026 Jens Kallup - paule32
:: all rights reserved.
:: --------------------------------------------------------------
@echo off
setlocal EnableExtensions

:: set PATH=%CD%;%PATH%
set ANTLR_VERSION=4.13.2
set ANTLR_RUN="T:\GitHub\dBase2Many\src\venv\Scripts\antlr4.exe"
:: winget install EclipseAdoptium.Temurin.21.JDK
:: Immer in das Verzeichnis wechseln, in dem compile.bat liegt.
pushd "%~dp0"

set GRAMMAR_DIR=c64pascal/grammar
set GENERATED_DIR=c64pascal/generated

echo ------------------------------------------------------------
echo Pascal ANTLR Lexer + Parser
echo ------------------------------------------------------------
echo Root      : %CD%
echo Grammar   : %GRAMMAR_DIR%
echo Generated : %GENERATED_DIR%
echo.
:: --------------------------------------------------------------
:: prüfen, ob antlr4.exe gefunden wird
:: --------------------------------------------------------------
where antlr4.exe
if errorlevel 1 (
    echo.
    echo FEHLER:
    echo antlr4.exe wurde im PATH nicht gefunden.
    echo.
    popd
    exit /b 1
)
if not exist %GRAMMAR_DIR%\C64PascalLexer.g4 (
    echo FEHLER:
    echo %GRAMMAR_DIR%/C64PascalLexer.g4 wurde nicht gefunden.
    popd
    exit /b 2
)
if not exist %GRAMMAR_DIR%\C64PascalParser.g4 (
    echo FEHLER:
    echo %GRAMMAR_DIR%/C64PascalParser.g4 wurde nicht gefunden.
    popd
    exit /b 3
)
:: --------------------------------------------------------------
:: Ausgabeverzeichnis sicher anlegen
:: --------------------------------------------------------------
if not exist %GENERATED_DIR% (
    mkdir -p %GENERATED_DIR%
)
if errorlevel 1 (
    echo FEHLER:
    echo Verzeichnis konnte nicht angelegt werden:
    echo %GENERATED_DIR%
    popd
    exit /b 4
)

:: --------------------------------------------------------------
:: Lexer
:: --------------------------------------------------------------
%ANTLR_RUN% -v %ANTLR_VERSION% ^
    -Dlanguage=Python3      ^
    -Xexact-output-dir      ^
    -o c64pascal\generated  ^
    c64pascal\grammar\C64PascalLexer.g4
if errorlevel 1 (
    echo.
    echo FEHLER:
    echo ANTLR konnte den Lexer nicht erzeugen.
    echo ERRORLEVEL=%ERRORLEVEL%
    popd
    exit /b 10
)
if not exist %GENERATED_DIR%\C64PascalLexer.py (
    echo.
    echo FEHLER:
    echo Lexer wurde angeblich erfolgreich erzeugt,
    echo aber folgende Datei fehlt:
    echo.
    echo %GENERATED_DIR%/C64PascalLexer.py
    echo.
    popd
    exit /b 11
)
echo Lexer erstellt:
echo   %GENERATED_DIR%/C64PascalLexer.py

:: --------------------------------------------------------------
:: Parser
:: --------------------------------------------------------------
echo.
echo create: Pascal Parser
echo.
%ANTLR_RUN% -v %ANTLR_VERSION% ^
    -Dlanguage=Python3       ^
    -Xexact-output-dir       ^
    -o   c64pascal\generated ^
    -visitor                 ^
    -lib c64pascal\generated ^
    c64pascal\grammar\C64PascalParser.g4
if errorlevel 1 (
    echo.
    echo FEHLER:
    echo ANTLR konnte den Parser nicht erzeugen.
    echo ERRORLEVEL=%ERRORLEVEL%
    popd
    exit /b 20
)
if not exist %GENERATED_DIR%\C64PascalParser.py (
    echo.
    echo FEHLER:
    echo Parser wurde angeblich erfolgreich erzeugt,
    echo aber folgende Datei fehlt:
    echo.
    echo %GENERATED_DIR%/C64PascalParser.py
    echo.
    popd
    exit /b 21
)
if not exist %GENERATED_DIR%\C64PascalParserVisitor.py (
    echo.
    echo FEHLER:
    echo Visitor wurde nicht erzeugt.
    popd
    exit /b 22
)

echo.
echo ------------------------------------------------------------
echo ANTLR erfolgreich
echo ------------------------------------------------------------
echo.

dir c64pascal\generated\*

popd
exit /b 0
