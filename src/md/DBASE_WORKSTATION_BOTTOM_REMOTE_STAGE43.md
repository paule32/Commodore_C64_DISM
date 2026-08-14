# Stage 43 – unteres Workstation-Panel und Zeichen-Remote-Server

Stage 43 baut auf Stage 42 auf.

## Panel-Geometrie

- linkes Panel: 76 px breit
- unteres Panel: gesamte Bildschirmbreite, 52 px hoch
- Hauptanwendungsbereich links: `76 + 4 = 80 px`
- Hauptanwendungsbereich unten: `Paneloberkante - 4 px`
- minimierte Fenster verwenden `WINDOWPLACEMENT.ptMinPosition`
- `WM_MOVING` wird auf denselben freien Bereich begrenzt

Das linke Panel endet an der Oberkante des unteren Panels. Damit existiert kein
ueberdeckter Eckbereich.

## SERVER und SRV-PC n

Das untere Panel besitzt links den Eintrag `SERVER`. Er oeffnet einen
Workstation-weiten Serverdialog im OWNER-Prozess. Aktive TCP-Verbindungen
werden als `SRV-PC 1`, `SRV-PC 2`, ... im unteren Panel dargestellt. Ein Klick
waehlt die zugehoerige Verbindung.

Der Serverdialog ist ein Workstation-Werkzeugfenster und wird deshalb vom
Alt+F4-Hauptanwendungspfad ausgenommen.

## Client-Listener

Jede Hauptanwendung startet waehrend ihrer Laufzeit einen IPv4/TCP-Listener.
Der Standard ist `127.0.0.1`. Der Port wird aus dem Anwendungs-Hash im Bereich
ab 46000 vorgeschlagen; bei Kollisionen wird der naechste freie Port gesucht.
Der wirklich verwendete Endpunkt steht als `NET IPv4:Port` in der Statuszeile.

Optionen:

- `D64_REMOTE_PORT=<port>`: bevorzugter Startport
- `D64_REMOTE_BIND=<ipv4>`: alternative Bind-Adresse, z. B. ein Adapter in
  einem privaten/testweisen LAN

Der Kanal ist als Debug-/Inspektionskanal fuer die Workstation gedacht und
soll nicht direkt ins Internet exponiert werden.

## Protokoll

TCP-Frames bestehen aus einer 4-Byte-Laenge, einem Typbyte und JSON-Nutzdaten.
Der Zustand wird nur bei Aenderungen gesendet.

Snapshot-Inhalt:

1. Hauptfenstergroesse
2. 80 Zeilenzeichen x 25 Rasterzeilen
3. Menueleisten-Eintraege und ihre Rechtecke
4. sichtbare Popup-Menues und Eintraege
5. sichtbare Dialog-/Popupfenster und ihre Geometrie

Passwortfelder oder Pixelbilder werden nicht ausgelesen.

## Remote-Maus

Der Server skaliert seine Vorschau auf die Client-Hauptfensterkoordinaten und
sendet Move/Press/Release/DoubleClick als JSON-Kommandos. Der Client mappt die
Koordinate mit `QApplication::widgetAt()` auf ein eigenes Qt-Widget und stellt
das Ereignis mit `QApplication::sendEvent()` zu. Dadurch bleibt die Steuerung
auf den Clientprozess begrenzt. Windows-weites `SendInput` wird nicht benutzt.

Ein gelbes Fadenkreuz zeigt auf dem Client die aktuelle Server-Mausposition.
Damit ist lokal sichtbar, welche Bewegung der Server ausfuehrt.

## Server geschlossen

`ServerDialog::closeEvent()` trennt alle Serververbindungen und setzt die
Anzahl der unteren `SRV-PC n`-Eintraege auf 0. Die Client-Listener laufen
weiter. Ohne verbundene Peers wird kein Raster-/Menue-/Dialog-Snapshot erzeugt
oder uebertragen.
