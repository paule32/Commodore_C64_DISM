# dBase Qt5 Stage 20 - festes Hauptfenster

Das von `d64qt5.dll` erzeugte Hauptfenster ist fuer den Benutzer nicht mehr
mit der Maus skalierbar.

Die 80x25-Rasterlogik aus Stage 19 bleibt erhalten. Deshalb wird die feste
Fenstergroesse bei einem Lupen-Zoom intern kontrolliert neu berechnet:

1. feste Groesse intern kurz loesen,
2. Font um exakt +1 pt oder -1 pt aendern,
3. 80x25-Viewport neu vermessen,
4. ggf. die bekannte +/-1-Pixel-Feinkorrektur anwenden,
5. Fenster auf die neue Rastergroesse setzen,
6. diese Groesse wieder mit `setFixedSize()` sperren.

Fuer den Benutzer gibt es damit keine resizebaren Fensteraussenkanten. Die
Lupen koennen die Anwendungsgroesse weiterhin automatisch an das 80x25-Raster
anpassen.

Alle Stage-19-Funktionen bleiben erhalten: normale Hauptmenueleiste,
ASCII-Rahmen nur um Popup-Untermenues, Konsole/DEBUG-Tabs, 3-Pixel-Aussenrahmen,
2-Pixel-Kante ueber der Statusleiste, CLEAR SCREEN, SET COLOR TO,
SET BORDERCOLOR TO und das `_app`/MENU-Objektmodell.
