# dBase Stage 29 - zentraler Shutdown / Cleanup

## Ziel

Beim Schliessen des generierten dBase-Hauptfensters wird die gesamte Runtime
beendet, auch wenn der Fokus gerade in einem Eingabefeld des Login-Dialogs
steht oder eine lokale Dialog-QEventLoop aktiv ist.

## Ablauf

1. `DBaseMainWindow::closeEvent()` ruft `request_runtime_shutdown()` auf.
2. `g_shutdown_requested` wird gesetzt.
3. Ein offener Login-Dialog wird per `reject()` beendet. Dadurch endet auch
   seine lokale `QEventLoop`.
4. Weitere Qt-Top-Level-/Popup-/Subfenster werden geschlossen.
5. Die QApplication-Eventloop wird mit `quit()` beendet.
6. Der generierte PE32/PE32+-Code prueft `DBaseQtShutdownRequested()` nach
   Top-Level-Anweisungen und springt in einen einzigen Cleanup-Block.
7. `DBaseQtShutdown()` schliesst den Runtime-Datei-Hook und zerlegt Fenster,
   Menues, Sessions und die ggf. von der Bridge erzeugte QApplication.
8. Anschliessend gibt der generierte Code `__dbase_format_buffer` mit
   `VirtualFree(..., MEM_RELEASE)` frei und beendet den Prozess.

## Login-Dialog

Ein fokussiertes `QLineEdit` verhindert den Shutdown nicht mehr. `reject()`
beendet den Dialog unabhaengig davon, ob Benutzer-, Passwort- oder Gruppenfeld
den Fokus besitzt.

## Dateien

Stage 29 definiert `close_runtime_data_files()` als zentralen Dateiclose-Hook.
Die aktuelle Qt-Runtime haelt noch keine persistenten DBF/MDX/NDX/DBT-
Dateihandles; `menuFile` wird zur Compile-Zeit gelesen. Der kommende
DBF/MDX/NDX/DBT-Reader soll seine offenen Handles ueber genau diesen zentralen
Cleanup-Pfad schliessen, statt einen zweiten Beendigungsweg einzufuehren.

## Speicher

Explizit freigegeben werden weiterhin der mit `VirtualAlloc` reservierte
`__dbase_format_buffer` sowie alle Qt-/Session-/Menu-Objekte, die von der
Bridge gehalten werden. Danach beendet `ExitProcess` das erzeugte Programm.

## Neue C-ABI

```c
int DBaseQtShutdownRequested(void);
```

Die Funktion liefert `1`, sobald das Hauptfenster bzw. die Runtime den
Shutdown angefordert hat, andernfalls `0`.

## Tests

Stage 29 ergaenzt `tests/test_dbase_shutdown_cleanup_stage29.py` und prueft
PE32/PE32+ inklusive internem Linker sowie den gemeinsamen Cleanup-Pfad.
