# dBase Stage 47 - Turbo-Vision-artiges Terminal-RPC

Stage 47 ersetzt die reine Remote-Snapshot-Idee schrittweise durch ein
deterministisches Terminal-Aufbau-Protokoll. Client und zugeschalteter Server
interpretieren dieselbe kompakte Beschreibung der 80x25-Anwendung. Es werden
keine Pixel, Bitmaps oder Screenshots uebertragen.

## Aufbau von TApplication

Die Template-Reihenfolge ist fest:

1. `T2000` - `TApplication`
2. `T2001` - `TBackground`
3. `T2002` - `TMainMenu`
4. `T2050` - MenuItems des Menuebaums
5. `T2003` - `TStatusBar`
6. sichtbare `T2010` - `TFrame`
7. je Frame eine `T2011` - `TView`
8. Controls der View (`T2040` usw.)
9. `END`

Damit kennt der Server die Anwendungsvorlage, bevor Runtime-Property-RPCs wie
Textaenderungen eines Eingabefeldes verarbeitet werden.

## Feste Typnummern

| Code | Klasse |
|---:|---|
| 2000 | TApplication |
| 2001 | TBackground |
| 2002 | TMainMenu |
| 2003 | TStatusBar |
| 2010 | TFrame |
| 2011 | TView |
| 2040 | TButton |
| 2045 | TLineEdit |
| 2046 | TCheckBox |
| 2047 | TComboBox |
| 2048 | TLabel |
| 2050 | TMenuItem |

Die Typnummer bezeichnet die Komponentenklasse. Jede konkrete Instanz erhaelt
zusaetzlich eine eindeutige `ComponentID`, damit mehrere `T2045`-Felder getrennt
adressiert werden koennen.

## DSL-Record

Ein Komponentenrecord hat die Form:

```text
T<TYPE>_<COMPONENTID>_<PARENTID>_<COL>_<ROW>_<COLS>_<ROWS>_<FG>_<BG>_<PAYLOAD>
```

Beispiel eines gruenen TLineEdit:

```text
T2045_00000105_00000101_012_004_024_001_FFFFFF_008000_NAME%3DUser
```

`COL/ROW/COLS/ROWS` sind ausschliesslich Zeichen-/Zellkoordinaten. `FG` und
`BG` sind sechsstellige RGB-Hexwerte `RRGGBB`. Der Payload ist UTF-8 und wird
percent-escaped, damit der `_`-Separator eindeutig bleibt.

## SCREEN CLEAR und SET COLOR

`SCREEN CLEAR 0xb0` wird nicht als 80x25-Pixelbild uebertragen. `TBackground`
enthaelt nur das CP437-Zeichen und seine Farben, z. B.:

```text
..._A9A9A9_000000_CHAR%3DB0
```

Client und Server erzeugen daraus lokal das 80x25-Zeichenmuster. Die
Aussenbegrenzung des Rasters bleibt die bestehende weisse/bzw. explizit
festgelegte `consoleBorderColor`.

Aenderungen durch `SET COLOR TO`, `SCREEN CLEAR`, `SCREEN CLEAR <char>`,
`SCREEN CLEAR <color>` oder die normale Console-Hintergrundfarbe markieren das
Terminal-Template als geaendert. Wird nach einem Zeichen-CLEAR normaler Text
geschrieben, wird der CharacterPattern-Modus beendet und ebenfalls ein neues
Template erzeugt.

## Frames, Views und Rahmen

Ein sichtbarer Dialog wird als `T2010` erzeugt. Seine innere Arbeitsflaeche ist
eine `T2011`. Der bereits vorhandene Char-Canvas des Clients bleibt fuer die
exakten Rahmenzeichen massgeblich. Der Server zeichnet daher dieselben
`╔ ═ ╗ ║ ╚ ╝`-Zeichen und nicht einen nachgebauten Pixelrahmen.

Bei gedrueckter linker Maustaste auf der Titlebar setzt der Client fuer den
Frame `dbaseRemoteMoving=true`. Client und Server verwenden dann Gelb fuer den
Rahmen. Bei Release wird die Eigenschaft wieder false und der Rahmen weiss.
Die Bewegung selbst bleibt der Stage-46-Zell-Mausstrom und sendet keine
Frame-Pixel.

## TLineEdit Runtime-RPC

Die TLineEdit-Vorlage wird einmal mit `T2045` uebertragen. Laufzeittext wird
danach nicht durch Neuerzeugen des gesamten Frames versendet, sondern ueber
Property-RPC:

```text
P_<ConnectionID>_<SessionID>_<ComponentID>_TEXT_<VALUE>
```

Passwortfelder senden nur Maskierungszeichen. Der Server kann ein gespiegeltes
TLineEdit anklicken und Tastaturereignisse mit dessen ComponentID an den Client
adressieren. Der Client stellt das echte QLineEdit fest, setzt den Fokus und
liefert die KeyEvents ausschliesslich an diese Anwendung. Der anschliessende
`textChanged`-Hook sendet den neuen logischen Text wieder zum Server.

TCheckBox und TComboBox verwenden denselben semantischen Mechanismus:
`CHECKED` bzw. `TEXT` werden als kleine Property-RPCs uebertragen.

## Transport-Reihenfolge

TCP-Frame-Typen:

- `H` - TCP/CS Handshake
- `T` - Terminal-Anwendungsvorlage
- `R` - Terminal-Property-RPC
- `S` - bestehender Char-/Zustands-Snapshot als Synchronisations-/Fallbackpfad
- `M` - Client-Maus in Zellkoordinaten
- `C` - adressierter Server->Client-Befehl/Maus

Auf einem neuen Socket wird `T` vor dem ersten `S` in die Queue gelegt. Vor
einem `R` wird ebenfalls garantiert, dass der zugehoerige aktuelle `T` bereits
auf diesem Peer gesendet wurde.

## TCP-Header und Sicherheit

Stage 47 verwendet:

```text
protocolVersion      = 5
terminalProtocol     = D64TERM/1
terminalRpcVersion   = 1
streamMode           = chars
coordinateMode       = cells
```

ConnectionID und - falls SESSION aktiv ist - SessionID bleiben Teil der
Adressierung. Property- und Steuer-RPCs werden nur fuer die zum Socket
gehoerige ConnectionID/SessionID akzeptiert. Damit bleibt die bisherige
Crosslink-Sperre erhalten.

## Keine Pixeluebertragung

Das Terminal-RPC transportiert keine Pixelkoordinaten, Screenshots, Bitmaps
oder globale Maus-Injektion. Positionen werden in 80x25-Zellen beschrieben;
Pixel entstehen erst lokal beim Qt-Rendering. Auch fuer Remote-Eingaben wird
kein Windows-`SendInput()` verwendet.
