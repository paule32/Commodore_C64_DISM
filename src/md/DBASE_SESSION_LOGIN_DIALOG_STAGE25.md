# dBase Stage 25 – SESSION Login-Dialog

Stage 25 erweitert die vorhandene Windows-SESSION aus Stage 21 um einen produktiven Login-Dialog und einen globalen Laufzeitstatus `LOGINSESSION`.

## Auslöser

```dbase
_app.security = new Session()
```

Beim Erzeugen einer SESSION wird der Login-Dialog geöffnet. Die Programmausführung wartet in einer lokalen Qt-Ereignisschleife auf Login oder Abbrechen. Das Hauptfenster bleibt dabei aktiv, so dass insbesondere die beiden Lupen weiterhin benutzt werden können.

## Dialog

Der Dialog enthält:

- Benutzer + Eingabefeld
- Passwort + Passwort-Eingabefeld
- Gruppe + Eingabefeld
- Login
- Abbrechen

Die Eingabefelder sind grün mit weißer Schrift. Dialog, Labels und Buttons verwenden einen grauen Grundton; Labels sind schwarz. Die UI-Schrift ist Consolas, anschließend Courier New und danach der System-Fixed-Font. Der Zeichenrahmen verwendet wie die Popup-Menüs Terminal, anschließend Courier New bzw. den Fixed-Font.

Der Dialog besitzt eine eigene frameless Titlebar. Sein normaler Zeichenrahmen ist weiß auf grauem Grund. Während die linke Maustaste auf der oberen Rahmenzeile gehalten wird, wird der gesamte Zeichenrahmen gelb.

## Raster

Der Dialog ist 48 × 12 Zeichenraster groß und wird aus derselben Zeichenzellenbreite/-höhe wie die 80 × 25 Konsole berechnet. Ein Lupenklick ändert die logische Schriftgröße weiterhin um exakt ±1 pt; ein geöffneter Login-Dialog wird danach neu skaliert.

Beim Verschieben wird nicht pixelweise bewegt. Die Position wird auf ganze Textzellen gerundet. Der erlaubte Bereich ist der Konsolen-Viewport:

- oberste Position: direkt unter dem Hauptmenü
- unterste Position: Dialogunterkante mindestens eine Textzeile über der Statusbar
- horizontal: innerhalb der 80-Spalten-Textfläche

## LOGINSESSION

`LOGINSESSION` ist ein schreibgeschützter globaler dBase-Laufzeitwert:

```dbase
IF LOGINSESSION == 1
    ? "angemeldet"
ELSE
    ? "nicht angemeldet"
ENDIF
```

Der Wert wird bei jeder Verwendung über `DBaseQtGetLoginSession()` aus der Runtime gelesen.

- Login erfolgreich: `LOGINSESSION = 1`
- Login fehlgeschlagen: `LOGINSESSION = 0`
- Abbrechen: `LOGINSESSION = 0`

Eine direkte Zuweisung wie `LOGINSESSION = 1` ist ein Compilerfehler.

## Menüschutz

Das Standard-Dateimenü enthält nun:

```text
Neu
Speichern
Speichern unter...
Alle Schließen
----------------
Login
Beenden
```

Nach `new Session()` und solange `LOGINSESSION == 0` gilt:

- andere Hauptmenüs: disabled
- Datei bleibt als Container erreichbar
- innerhalb Datei: nur Login und Beenden enabled
- Beenden terminiert die Anwendung
- Login öffnet den Dialog erneut

Nach erfolgreichem Login werden die zuvor gespeicherten Enabled-Zustände wiederhergestellt.

Die Popup-Menüs behalten den vorhandenen ASCII-/Terminal-Zeichenrahmen und die bisherigen Farben.

## C-ABI

Neu exportiert:

```cpp
int DBaseQtGetLoginSession(void);
```

Die vorhandenen Funktionen bleiben erhalten:

```cpp
void *DBaseQtSessionCreate(void *parent);
int DBaseQtSessionLogin(...);
```
