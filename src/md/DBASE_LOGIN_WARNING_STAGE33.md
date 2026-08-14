# dBase Login-Warnbox Stage 33

Stage 33 baut auf Stage 32 auf und aendert die Fehlerbehandlung des SESSION-Login-Dialogs.

## Login-Fehler

Wenn `DBaseQtSessionLogin(...)` den Wert 0 liefert, wird der Login-Dialog sofort geschlossen. Anschliessend wird eine Warnbox mit dem Titel `Warnung` und dem Text `Anmeldung fehlgeschlagen.` angezeigt.

Die Warnbox ist nicht modal. Sie blockiert weder das Hauptfenster noch die Zoom-Lupen.

## Warnbox

- Frameless Custom-Dialog
- Titel: `Warnung`
- Hintergrund: rot
- Warntext: schwarz
- Rahmen: weiss
- waehrend des Verschiebens: gelber Rahmen
- Button: `OK`
- Schrift: Consolas, Fallback Courier New/Festbreitenschrift
- 52 x 8 Zeichenzellen
- Position und Bewegung im 80 x 25 Zeichenraster
- Bewegung nur in ganzen Zeichenzellen
- Clipping an der Konsolen-Viewport-Flaeche
- bei Zoom wird Groesse und Position neu aus dem aktuellen Zeichenraster berechnet
- bei Bewegung des Hauptfensters bleibt die Warnbox relativ zum Konsolenraster positioniert

## Ablauf

```text
Login klicken
    -> DBaseQtSessionLogin(...)
       -> 1: Login-Dialog schliesst, LOGINSESSION = 1
       -> 0: Login-Dialog schliesst, LOGINSESSION = 0
             -> nicht-modale Warnbox wird angezeigt
```

`OK` schliesst nur die Warnbox. Ein neuer Login kann danach ueber `Datei -> Login` gestartet werden.

## Shutdown

Die Warnbox bleibt Teil des zentralen Stage-29-Shutdown-Pfades. Beim Schliessen der Hauptanwendung wird sie ebenfalls geschlossen und freigegeben.
