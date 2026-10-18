* Stage 446: Konsolenausgabe über d64_dbase_console.dll
SET FORMAT TO CONSOLE
STORE "   Hallo aus der DLL   " TO Text
? "dBASE-Konsolen-Runtime"
? LEN(Text)
? "[" + TRIM(Text) + "]"
?? "  Fertig"
