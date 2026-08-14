# Stage 40 – vollständiger Application-Cleanup auf der Workstation

Stage 40 baut auf Stage 39 auf und behebt freischwebende Dialogfenster beim
Schließen einer Anwendung auf der gemeinsamen Workstation.

## Ursache

Seit Stage 38 wurde `DBaseMainWindow::closeEvent()` grundsätzlich als
"verstecken und Runtime behalten" behandelt. Dieses Verhalten ist für den
Workstation-OWNER korrekt, weil das DB-Icon genau dieses Hauptfenster wieder
anzeigen soll. Seit Stage 39 verwenden jedoch auch JOINED-Anwendungen wie
`BTX.exe` dieselbe Runtime. Für sie war `hide()` falsch: ihr Prozess blieb mit
Dialogen, Sessions, Datenbankverbindungen und Runtime-Speicher aktiv.

## Neues Verhalten

- OWNER: unverändert. Fenster-X/Alt+F4 versteckt nur das DB-Hauptfenster.
- JOINED: Fenster-X/Alt+F4 löst einen vollständigen Application-Shutdown aus.
- Fokussierte/modale `QDialog`-Fenster werden zuerst `reject()`t und verborgen.
- Alle weiteren Qt-Top-Level-Fenster der Anwendung werden verborgen und
  geschlossen.
- Zusätzlich werden native Win32-Top-Level-Fenster desselben Prozesses auf dem
  Workstation-Desktop sofort verborgen und per `WM_CLOSE` beendet. Das
  Workstation-Panel des OWNER wird ausdrücklich ausgespart.
- DATABASE/TABLE-Hooks werden vor dem Session-Abbau geschlossen.
- ODBC-Verbindungen werden über den vorhandenen zentralen Close-Pfad getrennt.
- gespeicherte DATABASE-Passwörter werden mit NUL überschrieben und geleert.
- Sessions werden invalidiert; Benutzer- und Gruppenwerte werden geleert.
- Danach wird die Qt-Eventloop beendet.
- Der bereits vorhandene generierte Cleanup ruft `DBaseQtShutdown()` und danach
  `VirtualFree(..., MEM_RELEASE)` für den Runtime-Speicher auf.

Damit bleibt nach dem Schließen einer JOINED-Anwendung kein zugehöriges
Dialog-/Popupfenster freischwebend auf der Workstation zurück.
