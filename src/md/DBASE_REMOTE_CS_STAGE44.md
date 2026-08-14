# Stage 44 – Server/Client-Zeichenstream, IDs und gemeinsame Console-Chrome

Stage 44 baut auf Stage 43A auf.

## Server-Oberfläche

Der Workstation-Server verwendet jetzt dieselbe visuelle Grundstruktur wie die
Client-Hauptanwendungen:

- schwarze Console-Chrome mit festbreiter Schrift,
- Font-Priorität `Consolas`, danach `Courier New`,
- Lupen `+` und `-` mit 9..75 pt,
- `QTabBar` mit `Verbindung` und je einem `SRV-PC n`-Tab,
- Menueleiste, Zeichenbereich und echte Statusleiste,
- Rastergröße aus `gridColumns/gridRows` des verbundenen Clients,
- Default ohne Client: 80 x 25.

Die Server-Lupen skalieren Server-Raster, Menues, Controls und Statusleiste.
Die Client-Statusleiste setzt ihre Font jetzt auch auf alle Kindwidgets explizit,
damit die +/- Lupen unter Windows/Qt5 nicht an einer geerbten Default-Font
vorbeilaufen.

## Dialog-Fonts und Dialog-Zeichenstream

Login-, Warning-, BTX- und Server-Dialog-Controls verwenden dieselbe
festbreite Font-Familie. Passwortfelder werden im Remote-Datenstrom nur als
`*`-Zeichen in gleicher Länge übertragen.

Client-Dialoge werden nicht als Pixelbild übertragen. Der Client erzeugt pro
sichtbarem Dialog ein lokales Zeichenraster (`charLines`, `charColumns`,
`charRows`) aus sichtbaren Labels, Eingabefeldern, Buttons und Comboboxen.
Zusammen mit der Dialog-Geometrie kann der Server dadurch Inhalt und
Verschiebungen nachvollziehen.

## Bidirektionale Maus (CS)

Client -> Server:

- MouseMove
- MouseButtonPress
- MouseButtonRelease
- MouseButtonDblClick

werden als `M`-Frames übertragen und im Server als cyanfarbener Marker im
Client-Koordinatensystem dargestellt.

Server -> Client:

Die gleichen Ereignisse werden als adressierte `C`-Frames übertragen. Der
Client zeigt den Server-Mauspunkt als gelbes Fadenkreuz und reicht das Ereignis
nur an Qt-Widgets der eigenen Hauptanwendung weiter. Es wird kein globales
`SendInput()` benutzt. Remote injizierte Ereignisse werden nicht erneut als
lokale Client-Ereignisse zurückgesendet.

## D64CS TCP-Anwendungsheader

Unmittelbar nach einem TCP-Connect tauschen beide Seiten einen Frame `H` aus.
Er enthält unter anderem:

- `magic = D64CS_TCP_HEADER`
- `protocolVersion = 2`
- `applicationVersion`
- `serverSoftware = D64 Workstation Server/Stage44`
- `software`
- `role` (`client` / `server`)
- `localIp`
- `remoteIp`
- `clientIp`
- `serverIp`
- `connectionId`
- `sessionId`
- `gridColumns`
- `gridRows`

Erst nach einem gültigen gegenseitigen Header werden Snapshot-/Maus-/Command-
Frames verarbeitet.

## ConnectionID / SessionID und Crosslink-Schutz

Jede laufende Client-Hauptanwendung erzeugt eine UUID-basierte ConnectionID.
Der Serverdialog besitzt ebenfalls eine eigene ConnectionID.

Jedes `new SESSION()` erzeugt zusätzlich eine UUID-basierte SessionID. Wird
eine Session erst nach Aufbau der TCP-Verbindung erzeugt, wird die neue ID über
einen `I`-Frame an den Server übertragen.

Server-Steuerbefehle enthalten:

- `sourceConnectionId`
- `targetConnectionId`
- `targetSessionId`

Der Client führt einen Befehl nur aus, wenn die Ziel-ConnectionID genau seiner
eigenen ConnectionID entspricht, die Quell-ID zur verbundenen Serverinstanz
passt und die SessionID exakt zur aktuell zugeordneten Session passt. Snapshots
und Client-Mausframes werden serverseitig analog der bekannten Verbindung und
Session zugeordnet. Damit kann ein `SRV-PC n`-Kanal nicht versehentlich auf
einen anderen Client-/Session-Kanal querverbunden werden.

Diese IDs sind ein Routing-/Zuordnungsschutz gegen Crosslinks; sie ersetzen
keine kryptographische Transportverschlüsselung für ungeschützte öffentliche
Netze. Standardmäßig bleibt der Listener auf `127.0.0.1` gebunden.

## Tests

Stage 44 fügt `tests/test_dbase_remote_cs_stage44.py` hinzu. Der vollständige
Regressionstest des gelieferten Standes umfasst 486 Tests.
