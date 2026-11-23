# Stage 638 – dBL `TRY … FINALLY … END` (verbindliche Basis: Stage 637)

## Ziel

Die vom Anwender bereitgestellte `.prg`-Quelle mit einem mehrzeiligen `TRY`, `FINALLY` und `END` wird von der produktiven Python-Frontend-Pipeline unter `d64dbase/compiler.py` erkannt und als nativer PE32-/PE64-Code ausgegeben.

```dbase
TRY
    SET DEBUG ON
    SET FORMAT TO SCREEN
    SET BACKGROUND TO 1, 14, 176
    ? "hihi"
    ? "halöo"
FINALLY
    ? "Das Ende"
    ExitProcess(0)
END
```

Der Debug-Transcript der Compiler-Vorschau lautet `hihi\r\nhalöo\r\nDas Ende\r\n`.

## Umsetzung

- `d64dbase/compiler.py`: AST `DBaseTryFinallyStatement`; rekursiver Parser für `TRY`, `FINALLY` und `END`; beidseitige Syntaxvalidierung einschließlich der fehlenden Abschlussmarken und unerwarteter Schlüsselwörter.
- Semantikanalyse der TRY- und FINALLY-Bodies für globale Symbole und Routine-Spezialisierungen.
- PE32/PE64-Codegenerierung: normales Durchlaufen von TRY gefolgt von FINALLY; beim `RETURN` werden alle gerade aktiven FINALLY-Blöcke in umgekehrter Schachtelungsreihenfolge **vor** dem Routinen-Rücksprung ausgegeben. Ein `RETURN` im FINALLY kann einen vorherigen Rückgabewert ersetzen.
- Vorschau und Python-Interpreter werten TRY/FINALLY aus; der Interpreter nutzt ein tatsächliches Python-`finally`, wodurch dort auch bei fehlerhafter Auswertung der FINALLY-Block durchlaufen wird.
- `ExitProcess(code)` als **Statement** wurde eingebaut. Der Compiler wertet den numerischen Exit-Code aus und erzeugt einen Aufruf der ohnehin importierten Win32-Funktion aus `kernel32.dll` für PE32/PE64. Der Aufruf nimmt genau ein numerisches Argument. Er ist kein dBASE-Variablenwert.
- `d64dbase/grammar/DBaseLexer.g4` und `DBaseParser.g4`: gleichlautende lexikalische und syntaktische Definitionen für Generatoren/Referenz.
- Regressionstests `test_stage638.py` mit Beispielen für beide Ziele, IF, verschachtelte Blöcke, RETURN, Makros und ungültige Eingaben.

## Grenzen (wichtig)

Die Implementation deckt **strukturierten Kontrollfluss** ab: Normalfall und `RETURN`. Sie installiert **keinen nativen Windows-SEH-Handler**. Ein harter Prozessabbruch (`ExitProcess()` aus dem TRY-Teil), ein Crash oder die Terminierung durch das Betriebssystem löst deshalb **keine** automatische Ausnahmeabwicklung des FINALLY-Blocks aus. Ebenso existiert noch kein allgemeines `TRY … EXCEPT`/`CATCH`.

`ExitProcess(0)` im gezeigten **FINALLY** beendet die GUI-EXE unmittelbar nach der Ausgabe. Wenn die Meldungen im grünen/DEBUG-Ausgabefenster länger sichtbar bleiben sollen, den expliziten Systemaufruf weglassen und die reguläre Qt5-Ereignisschleife des Programms weiterlaufen lassen.

Die alte dBASE-Regel, dass eine `PROCEDURE` am Ende `RETURN` bzw. eine `FUNCTION` am Ende `RETURN <expr>` benötigt, gilt weiterhin, auch wenn eine Routine bereits innerhalb eines TRY-Blocks zurückkehrt.

## Build

Die Änderung betrifft die Python-Compilerdatei und die beiden ANTLR4-Referenzgrammatiken, **nicht** die Qt5-Runtime-DLL. Die bisherige `libd64_qt5.dll` kann beibehalten werden. Die `.prg`-Datei muss mit Stage 638 neu kompiliert, assembliert und gelinkt werden.

## Prüfungen

- 22 neue Stage-638-Tests: bestanden.
- 139 Tests aus Stage 619/621/628–638: bestanden (Pytest; enthält die 22 neuen Tests).
- Direkte PE32- und PE64-Kompilierung des konkreten Beispiels: bestanden, keine externen Funktionssymbole außer den vorhandenen DLL-Imports.
- Windows-/MinGW32-/Qt5-Laufzeittest: **nicht durchgeführt**.
