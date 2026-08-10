# dBase – eingebettete Konsole und DEBUG-Tab

Für `.dbase` und `.dbp` wird der bisher sichtbare **Hinweise**-Tab durch eine eingebettete **Konsole** ersetzt. Die Ausgabe ist ein rahmenloses `QPlainTextEdit`; es wird kein Konsolenfenster in Qt hineingehackt und kein `command.com`/`cmd.exe` gestartet.

## Laufzeitkanäle

Der erzeugte PE32-/PE32+-Code öffnet keine eigene Konsole mehr. Er verwendet die vom Starter geerbten Standard-Handles:

- `STD_OUTPUT_HANDLE (-11)` → IDE-Tab **Konsole**
- `STD_ERROR_HANDLE (-12)` → IDE-Tab **DEBUG**

`d64_dism` startet dBase über `QProcess` mit getrennten stdout-/stderr-Kanälen. Unter Windows wird `CREATE_NO_WINDOW` gesetzt, damit beim F2-Start kein zusätzliches Konsolenfenster erscheint.

## ? und ??

```dbase
? "Text"
?? "ohne NewLine"
```

`?` hängt `CR/LF` an, `??` nicht.

## DEBUG

```dbase
SET FORMAT TO CONSOLE
SET DEBUG ON
? "Diese Zeile geht in DEBUG"
?? "auch DEBUG"
SET DEBUG OFF
? "Diese Zeile geht wieder in Konsole"
```

Der DEBUG-Tab ist verborgen, wenn der kompilierte Ablauf keine `?`/`??`-Ausgabe in den Debugkanal schickt. Sobald Debug-Ausgabe vorhanden ist, liegt der Tab direkt neben **Konsole**.

`SET FORMAT TO SCREEN` bleibt für ältere dBase-Quellen als kompatibler Debug-Ausgabekanal erhalten. Ein explizites `SET DEBUG OFF` erzwingt wieder die normale Konsole.

## F2

F2 führt weiter Compile → Assemble → Link → Start aus. Nach erfolgreichem Linken wird bei dBase automatisch der Tab **Konsole** aktiviert, bevor die EXE gestartet wird.
