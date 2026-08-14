# d64qt5.dll Qt5 C++ Bridge

Die dBase-EXE importiert nur die stabile C-ABI aus `d64qt5.dll`. Die Bridge
kapselt Qt5 Widgets und kann getrennt als PE32- oder PE32+-DLL gebaut werden.

Wichtig: `d64_dism.py` baut diese DLL beim Start **nicht** automatisch.

GUI-Struktur Stage 12:
- Kopfzeile mit Lupe + / Lupe - und `QTabBar`
- `Konsole` immer sichtbar
- `DEBUG` nur bei `SET DEBUG ON`
- `QStackedWidget` fuer die beiden Ausgabeseiten
- DEBUG-Seite mit `QPlainTextEdit` und `QLineEdit`

PE32: passende 32-Bit-Qt5-Toolchain verwenden.
PE32+: passende 64-Bit-Qt5-Toolchain verwenden.

## Stage 15

`DBaseQtSetColorNormal()` akzeptiert Windows-Systemfarbnamen sowie `#RRGGBB`.
`DBaseQtSetOutputColor()` setzt die Farben fuer nachfolgende dBase-`?`/`??`-Ausgaben.
Die SET-COLOR-Syntax verwendet `<Hintergrund>/<Vordergrund>`; `W/N` bedeutet
hellgrauer Hintergrund und schwarze Schrift.

## Stage 19 / Stage 37: 80x25-Raster

Die Standardgroesse der dBase-Konsole wird aus den realen Fontmetriken fuer
80 Spalten und 25 Zeilen berechnet. Die Zoom-Lupen aendern die logische
Schriftgroesse um genau 1 pt. Ab Stage 37 gibt es keine separate +/-1-Pixel-
Feinkorrektur mehr. Konsole, Login-/Warn-/BTX-Dialoge und deren Rahmen benutzen
dieselbe vom realen Konsolen-Viewport DPI-aufgeloeste QFont-Instanz und exakt
dieselben Zeichenbreiten/Zeilenhoehen.

## Stage 23: CLEAR SCREEN Ausdruck

Zusatzexporte:

- `DBaseQtClearScreenChar(double code)` fuellt das 80x25-Konsolenraster mit einem CP437-Terminalzeichen und den aktuellen `SET COLOR TO`-Farben.
- `DBaseQtClearScreenColor(const char *name, int length)` leert die Konsole und setzt die Flaechenfarbe aus `#RRGGBB`.

Der bestehende Export `DBaseQtClearScreen(void)` bleibt unveraendert erhalten.

## Stage 24: Standardmenue und volle 80x25-Konsole

- Die Konsolen-Scrollbars sind permanent ausgeblendet (`Qt::ScrollBarAlwaysOff`).
- Es wird keine zusaetzliche Leerzeile mehr am unteren Rand reserviert.
- `DBaseQtEnsureDefaultMenu()` erzeugt bei leerem/nicht gesetztem `_app.menuFile` vor dem ersten Show das Standardmenue `=` und `Datei`.
- `Datei` enthaelt `Neu`, `Speichern`, `Speichern unter...`, `Alle Schließen`, Separator und `Beenden`.
- `Beenden` schliesst das Hauptfenster und beendet die Qt-Ereignisschleife.
- Der Datei-Popup behaelt den CP437/Terminal-Zeichenrahmen und die bisherigen Farben.

## Stage 25 – SESSION Login-Dialog

`new SESSION()` öffnet nun den rastergebundenen Windows-Login-Dialog. Der globale Status ist über `DBaseQtGetLoginSession()` verfügbar; solange kein Login besteht, bleiben im Menü nur Login und Beenden aktiv. Der Dialog skaliert mit den Lupen und lässt sich nur in ganzen 80×25-Zeichenzellen-Schritten innerhalb des Konsolenbereichs verschieben.

## Stage 26: Dialograster / CLEAR SCREEN-Zeichen bei Zoom

- Login-Dialog bewegt sich ausschliesslich im realen Konsolen-Viewport zwischen Menue und Statusbar.
- Der untere Dialograhmen darf bis an die letzte Textzeile direkt vor der Statusbar reichen; keine zusaetzliche Leerzeile wird reserviert.
- Dialogposition wird als Zeichenraster-Spalte/-Zeile gespeichert und beim Verschieben des Hauptfensters relativ zum Textbereich wiederhergestellt.
- Ein aktives `CLEAR SCREEN <Zeichen>`-Fuellmuster wird nach Lupen-Zoom mit gleichem CP437-Code und denselben Farben erneut erzeugt.


## DATABASE Stage 30

`DATABASE` besitzt einen nativen Runtime-Lifecycle mit SESSION-Bindung, lokalen DBF-Verzeichniskontexten und ODBC-DSN-Verbindungen. Fehlgeschlagene `open()`-Aufrufe werden ueber einen eigenen, roten 80x25-Raster-Warndialog mit weissem Rahmen und OK-Button gemeldet. Der zentrale Shutdown schliesst alle DATABASE-Instanzen vor dem Abbau von SESSION und GUI.

## Stage 36: EXIT-Icon

Die Workstation erzeugt vor `SwitchDesktop()` ein eigenes EXIT-Icon links oben.
Doppelklick sendet `WM_CLOSE` an das Qt-Hauptfenster und benutzt dadurch immer
den normalen Runtime-Cleanup und die Rueckkehr zum urspruenglichen Desktop.


Stage 36 GDI link note: the Workstation EXIT icon uses Win32 GDI drawing APIs; MinGW32 must link `-lgdi32` in addition to `-luser32`.

## Stage 37: Workstation-Panel und BTX

Links auf der Workstation befindet sich ein vollhoehen Panel mit der Breite
des bisherigen EXIT-Fensters (76 Pixel). Oben bleibt EXIT; darunter sitzt das
BTX-Icon. Ein einfacher Klick auf BTX fordert ueber einen kurzen Win32-Callback
einen nicht-modalen Qt-BTX-Dialog an. Seine eigentliche Textflaeche ist exakt
80 x 25 Rasterzellen gross und skaliert mit denselben Lupen-/DPI-Metriken wie
die Hauptkonsole. Der EXIT-Doppelklick benutzt unveraendert WM_CLOSE und damit
den kompletten Runtime-/Desktop-Cleanup.

## Stage 38: DB / BTX.exe / confirmed EXIT

The Workstation panel now has a third DB icon. Closing the Qt main window only
hides it; DB restores the same window. BTX launches a real `BTX.exe` on the
private Workstation desktop using `CreateProcessW` with an explicit
`STARTUPINFO.lpDesktop`. EXIT is now single-click plus a JA/NEIN confirmation;
only JA authorizes the central runtime/Desktop cleanup. Workstation child
windows are asked to close with `WM_CLOSE` during confirmed shutdown.


## Stage 39: Windows-globaler Workstation-Singleton

Die Workstation wird nicht mehr pro Prozess erzeugt. `d64_workstation.cpp`
verwendet einen benannten Lifetime-Mutex im Windows-Global-Namespace und ein
benanntes Ready-Event:

- `Global\\dBase2Many.D64Workstation.Singleton`
- `Global\\dBase2Many.D64Workstation.Ready`

Der gemeinsame Win32-Desktop heisst `D64Workstation`.

Die erste Runtime ist **OWNER**. Nur sie erzeugt Desktop, linkes EXIT/BTX/DB-
Panel, `SwitchDesktop()` und den Low-Level-Keyboard-Hook. Weitere Prozesse sind
**JOINED**: sie oeffnen denselben Desktop, binden den noch fensterfreien GUI-
Thread vor `QApplication` per `SetThreadDesktop()` und erzeugen dort nur ihr
Programmfenster. Dadurch startet ein weiteres `BTX.exe` auf der vorhandenen
Workstation, ohne eine zweite Workstation zu erzeugen.

Beim Shutdown eines JOINED-Prozesses werden weder Panel noch globaler Desktop
zerstoert oder umgeschaltet. Erst der OWNER gibt beim vollstaendigen Workstation-
Shutdown den Lifetime-Mutex frei.

## Stage 40 – Application-Cleanup

Auf der Stage-39-Singleton-Workstation unterscheiden sich jetzt OWNER und
JOINED auch beim Fensterschliessen:

- OWNER: das DB-Hauptfenster wird weiterhin nur versteckt und kann ueber DB
  wieder eingeblendet werden.
- JOINED (z. B. BTX.exe): ein Close beendet die komplette Anwendung.

Der JOINED-Close verbirgt/rejectet alle Qt-Dialoge, schliesst auch native
Win32-Top-Level-Fenster desselben Prozesses, schliesst DATABASE/ODBC-Ressourcen,
invalidiert Sessions, beendet die Qt-Eventloop und laeuft anschliessend durch
den vorhandenen generierten DBaseQtShutdown/VirtualFree/ExitProcess-Pfad.

## Stage 41: Dialogfokus und Alt+F4

Beim Verbergen der OWNER-Hauptanwendung werden sichtbare zugehoerige Dialoge
mit verborgen und beim DB-Restore gezielt wiederhergestellt. Alt+F4 wird vom
Workstation-Guard auf das Root-Owner-Hauptfenster der aktiven Anwendung
umgeleitet; Workstation-Panels sind davon ausgenommen.

## Stage 42: Hauptanwendungs-Mutex und flackerfreier Restore

Jede Hauptanwendung besitzt einen eigenen globalen, aus dem kanonischen
EXE-Pfad gebildeten Instance-Mutex. BTX/DB starten dadurch nie doppelt. Ein
LaunchGate schliesst auch die Race-Luecke zwischen CreateProcessW und dem
Anlegen des Instance-Mutex. JOINED-Anwendungen werden vor dem ersten sichtbaren
Frame offscreen fertig layoutet.

## Stage 43: unteres Panel und Zeichen-Remote-Server

Die Workstation besitzt nun ein zweites, horizontales Win32-Panel am unteren
Bildschirmrand. Seine Hoehe ist exakt `WORKSTATION_ICON_SIZE` = 52 Pixel. Das
linke 76-Pixel-Panel endet oberhalb dieses Panels. Der freie Bereich fuer
Hauptanwendungen beginnt 4 Pixel rechts vom linken Panel und endet 4 Pixel vor
dem unteren Panel. `WM_MOVING` wird entsprechend begrenzt. Die Windows-
Minimierungsposition wird ueber `WINDOWPLACEMENT.ptMinPosition` auf denselben
linken/unteren 4-Pixel-Abstand gesetzt.

Links im unteren Panel befindet sich `SERVER`. Der Klick oeffnet den
`D64 Workstation Server`-Dialog. Jede laufende d64qt5-Hauptanwendung startet
einen IPv4/TCP-Listener. Der tatsaechliche Listener wird in der Statuszeile als
`NET <IPv4>:<Port>` angezeigt. Standard ist `127.0.0.1`; `D64_REMOTE_PORT` kann
den Startport festlegen. Fuer einen bewusst freigegebenen privaten LAN-Adapter
kann `D64_REMOTE_BIND` gesetzt werden. Eine direkte Internet-Freigabe ist fuer
diesen Debug-/Inspektionskanal nicht vorgesehen.

Der Serverdialog verbindet sich ueber IPv4 + Port mit einem oder mehreren
Clients. Fuer jede aktive Verbindung erscheint im unteren Panel ein
`SRV-PC n`-Feld. Ein Klick waehlt den betreffenden Client im Serverdialog.

Uebertragen werden **keine Pixel**. Der Client serialisiert ausschliesslich:

- das sichtbare 80x25-Zeichenraster,
- Geometrie/Text der Hauptmenueleiste,
- sichtbare Popup-Menueeintraege,
- Position/Groesse/Titel sichtbarer Dialog-/Popupfenster.

Die Daten werden nur gesendet, wenn mindestens ein Server verbunden ist und
sich der Zustand geaendert hat. Nach Schliessen des Serverdialogs werden alle
Server-Sockets getrennt; die Clients bleiben nur im Listenerzustand.

Remote-Mausbefehle werden auf dem Client ausschliesslich ueber
`QApplication::widgetAt()`/`QApplication::sendEvent()` an Widgets der eigenen
Hauptanwendung zugestellt. Es wird **kein** globales Windows-`SendInput`
verwendet. Der Client blendet fuer Serverbewegungen einen sichtbaren
Fadenkreuz-Cursor ein, sodass lokale Benutzer die Remote-Aktion sehen.

## Stage 43A – MinGW32 Winsock/Qt connect build fix

Der Stage-43-Remote-Server qualifiziert native Winsock-Aufrufe jetzt explizit
im globalen C++-Namespace. Insbesondere verwendet `ServerDialog::connectClient()`
`::connect(...)`, damit der Name nicht mit `QObject::connect(...)` kollidiert.
Das qmake-Projekt linkt weiterhin `ws2_32`.

## Stage 46 - Remote-Dialoge und schnelle Rastermaus

Der Remote-Server rendert Dialoge jetzt mit derselben dBase-Chrome wie der
Client. Char-Rahmen bleiben 1:1 Zeichenstrom; Eingabefelder, Buttons und Labels
werden nur als Rolle/Text/Zellrechteck uebertragen. Es gibt weiterhin keinen
Pixelstream.

MouseMove wird mit Sequenznummern als absolute 80x25-Zellposition uebertragen.
Zwischenbewegungen werden pro 16-ms-Netzwerktick koalesziert, Press/Release
bleiben geordnet. Beim Remote-Drag wird das beim Press getroffene Widget bis
zum Release als Capture-Ziel gehalten.

## Stage 47 - Turbo-Vision-artiges Terminal-RPC

Die Remote-Verbindung besitzt jetzt zusaetzlich `D64TERM/1`. Eine laufende
Anwendung wird als kompakte Zell-/Komponentenbeschreibung aufgebaut:
`TApplication -> TBackground -> TMainMenu -> TStatusBar -> TFrame -> TView ->
Controls`. Feste Typcodes beginnen bei `T2000`; `T2045` ist immer `TLineEdit`.
Jede Instanz besitzt daneben eine eindeutige ComponentID.

`SCREEN CLEAR 0xb0` wird als CP437-Zeichen plus Vorder-/Hintergrundfarbe im
`TBackground` beschrieben. Frames und Controls verwenden ausschliesslich
Zellkoordinaten und RGB-Hexfarben. Laufzeitaenderungen wie TLineEdit-Text,
TCheckBox-Zustand und TComboBox-Text laufen als kleine Property-RPCs; die
Anwendungsvorlage wird garantiert vorher gesendet. Passworttexte bleiben
maskiert. Protokollversion: Remote v5, Terminal `D64TERM/1` v1. Keine Pixel-
oder Screenshot-Uebertragung und kein globales `SendInput()`.
