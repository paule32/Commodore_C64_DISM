# Windows PE32 Console / ReadLn Fix

## Fehlerbild

Beim Start eines intern erzeugten Windows-PE32-Konsolenprogramms aus `d64_dism.py`
wurde das Konsolenfenster zwar geöffnet, aber `Write`/`WriteLn` blieben unsichtbar und
`ReadLn` wartete nicht auf Enter. Das Programm erreichte unmittelbar `ExitProcess`.

## Ursache

`_launch_assembled_document()` startete auch Console-Programme mit
`stdin/stdout/stderr = subprocess.DEVNULL`. Dadurch konnten die Win32-Standardhandles
auf NUL zeigen. `WriteFile` schrieb damit ins Leere und `ReadFile` lieferte sofort EOF.

## Korrektur

- Console-Modus wird beim Start nicht mehr auf `DEVNULL` umgeleitet.
- Die interne PE32-Pascal-Runtime öffnet nach `AllocConsole` zusätzlich `CONIN$` und
  `CONOUT$` über `CreateFileA`.
- `ReadLn` verwendet den echten `CONIN$`-Handle.
- `Write`/`WriteLn` verwenden den echten `CONOUT$`-Handle.
- Falls `CreateFileA` fehlschlägt, bleibt `GetStdHandle` als Fallback erhalten.
- `CreateFileA` wurde in die interne PE32-Importtabelle aufgenommen.

Damit bleibt die Console-I/O auch dann korrekt, wenn das Programm aus einer GUI,
einem Prozess mit umgeleiteten Standardhandles oder direkt aus `d64_dism.py` gestartet
wird. Es wird weiterhin kein externer Compiler oder Linker benötigt.
