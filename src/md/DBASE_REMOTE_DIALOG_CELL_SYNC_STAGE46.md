# Stage 46 - identische Remote-Dialoge und rasterfeste Maus-Synchronisation

Stage 46 baut auf Stage 45 auf. Der TCP-Kanal bleibt strikt zeichen- und
zellorientiert. Es werden keine Bildschirm-Pixel, Bitmaps oder Pixelkoordinaten
vom Client an den Server oder umgekehrt uebertragen.

## Dialogdarstellung

Der Client uebertraegt fuer sichtbare Dialoge weiterhin die echten Char-Zeilen
inklusive Rahmenzeichen. Zusaetzlich werden die sichtbaren Controls semantisch
beschrieben:

- role: `label`, `input`, `button`
- `column`, `row`, `columns`, `rows`
- sichtbarer Text
- Focus-/Enabled-Zustand
- Passwortfelder nur maskiert

Der Server rendert diese Daten lokal mit derselben dBase-Chrome wie der Client:

- Consolas, Fallback Courier New
- Standarddialog `#909090`
- Eingabefeld `#008000`, Schrift weiss
- normaler Input-Rahmen weiss, Focus-Rahmen gelb
- Button `#909090`, Schrift schwarz, Rahmen weiss
- Warning-Dialog behaelt den roten Client-Hintergrund
- Rahmenzeichen werden weiterhin 1:1 aus `charLines` uebernommen

Auch die aeussere Konsolenumrandung benutzt die vom Client gemeldete
`consoleBorderColor` und dieselbe 3-Pixel-Lokalrenderung wie der Client. Die
Farbe wird uebertragen, nicht die Pixel.

## Schnelle Mausbewegungen

MouseMove ist ab Stage 46 ein absoluter Rasterzustand und kein Bewegungsdelta.
Jedes Ereignis enthaelt:

- `sequence`
- `column`, `row`
- `subX`, `subY` innerhalb der Zelle
- Button-/Buttons-Zustand

Mehrere Move-Ereignisse innerhalb eines Netzwerk-Ticks werden koalesziert: Nur
die neueste absolute Zellposition bleibt erhalten. Press, Release und Double
Click werden nicht verworfen und bleiben geordnet.

Damit kann bei schneller Mausbewegung kein langer TCP-Rueckstau aus alten
Zwischenpositionen entstehen. Der Netzwerk-Tick laeuft mit 16 ms.

## Remote Capture

Beim Remote-Press wird das Zielwidget gespeichert. Move und Release gehen bis
zum Loslassen an dasselbe Widget, auch wenn ein Dialog unter dem Cursor bereits
verschoben wurde. Das verhindert, dass `widgetAt()` waehrend einer schnellen
Dialogverschiebung ploetzlich ein anderes Widget trifft und die Bewegung
abbricht.

## Protokoll

`D64_REMOTE_PROTOCOL_VERSION = 4`.

Stage-46-Snapshots enthalten weiterhin `streamMode = chars` und
`coordinateMode = cells`. Neue Dialog-Control-Daten sind ebenfalls reine
Zellgeometrie.
