# Stage 45 – vollständige Client-Spiegelung als Char-Stream

Stage 45 baut auf Stage 44A auf und korrigiert die bisher unvollständige Serverdarstellung.
Der Server ist bei einem ausgewählten `SRV-PC n` kein approximierter Viewer mehr, sondern
spiegelt die logische Client-Oberfläche aus Zeichen- und Zellzuständen.

## Kein Pixelstream

Über TCP werden keine Screenshots, Bitmaps, Pixelzeilen oder Pixelkoordinaten des
Client-Fensters übertragen. Der D64CS-Header verwendet Protokollversion 3 und kündigt
explizit an:

- `streamMode = chars`
- `coordinateMode = cells`

Der Arbeitsbereich besteht aus den vom Client verwendeten Zeichenzeilen. Dialoge und
offene Popup-Menüs liefern ebenfalls vollständige Char-Zeilen sowie ausschließlich
Spalten-/Zeilenpositionen. Mausereignisse verwenden Zellkoordinaten plus eine
0..999-Unterposition innerhalb der Zelle; diese Werte sind keine Bildschirm-Pixel.

## Menü 1:1

Der Client serialisiert den vollständigen `QMenuBar`-/`QMenu`-Baum rekursiv:

- Text
- enabled/visible
- Separator
- checkable/checked
- Shortcut
- Untermenüs
- stabiler Aktionspfad

Der Server baut daraus seine Menüleiste mit denselben `AsciiPopupMenu`-Komponenten auf.
Ein Klick auf einen Server-Menüpunkt wird über den Aktionspfad an genau die per
ConnectionID/SessionID gebundene Client-Anwendung gesendet und dort ausgelöst.

## Statusleiste 1:1

Die sichtbaren Statusfelder des Clients werden als Textfelder übertragen und ersetzen
bei ausgewähltem `SRV-PC n` die Server-eigenen Statusinformationen. ConnectionID,
SessionID und Netzwerkdetails bleiben nur als Tooltip verfügbar und verändern die
gespiegelte Statusleiste nicht.

## Rahmenzeichen 1:1

Die Zeichenrahmen werden im Server nicht mehr als Rechtecke oder lokale Ersatzrahmen
gezeichnet. Der Client erzeugt die tatsächlich verwendeten Zeichenzeilen mit:

- `╔` U+2554
- `╗` U+2557
- `╚` U+255A
- `╝` U+255D
- `═` U+2550
- `║` U+2551

Titel wie ` Login ` oder ` Warnung ` liegen direkt in diesen übertragenen Char-Zeilen.
Passwortfelder werden weiterhin nur maskiert (`*`) übertragen.

## Maus

Client→Server und Server→Client verwenden nun `column`, `row`, `subX`, `subY`.
Die Umrechnung in lokale Pixel erfolgt ausschließlich auf der jeweiligen Maschine mit
der dortigen Consolas/Courier-New-Zellgröße. `SendInput` wird weiterhin nicht verwendet.

## Tests

Der vollständige Regressionslauf für Stage 45 umfasst 494 Tests und ist vollständig grün.
