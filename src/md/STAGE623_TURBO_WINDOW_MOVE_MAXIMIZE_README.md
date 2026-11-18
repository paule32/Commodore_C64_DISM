# Stage 623 – Turbo-Vision-Ausgabefenster verschieben / maximieren

**Verbindliche Basis:** `d64_dism_stage622(1).zip`. Stage 623 ändert die Bedienbarkeit des vorhandenen grünen dBASE-Ausgabefensters. dBASE-Compiler und DEBUG-Ausgabewege werden nicht verändert.

## Umsetzung

Datei: `d64qt5/d64_turbo_output.hpp`, Klasse `D64TurboOutputWidget`.

- Fensterposition: Maustaste links in der **grünen Titelleiste** drücken, ziehen und loslassen. Der Abstand wird anhand der aktuellen `QFontMetrics` auf volle DOS-Zeichenzellen (`cellWidth_`, `cellHeight_`) gerundet.
- Der Fensterrahmen samt Schatten bleibt innerhalb des `QAbstractScrollArea`-Viewports. Die Ausgabe und Scrollbalken sind vom Verschieben ausgenommen.
- Oben rechts befindet sich eine Qt5-`QToolButton`-Schaltfläche zum **Maximieren/Wiederherstellen**. Ein Doppelklick auf die Titelleiste löst dieselbe Aktion aus.
- Maximiert nimmt das Fenster den kompletten verfügbaren Viewport ein. Die angezeigte Anzahl Spalten/Zeilen wird aus der tatsächlichen Viewportgröße und dem aktuellen Font-Zeichenraster neu berechnet; der manuelle Größenanfasser wird ausgeblendet.
- Beim Wiederherstellen werden die zuvor gespeicherte Position und die zuvor sichtbare Größe in Zeichenspalten/-zeilen verwendet. Falls das Hauptfenster inzwischen kleiner ist, werden diese Werte auf die verfügbare Fläche begrenzt, damit das Fenster bedienbar bleibt.
- Bei einem Zoomwechsel wird die maximal nutzbare Zeichenanzahl erneut ermittelt; im Normalzustand bleibt die angeforderte Zeichenrastergröße erhalten, soweit der Viewport Platz bietet.
- Keine neuen `Q_OBJECT`-Klassen oder MOC-Schritte. Das bestehende Qt5-Widget wird erweitert.

## Bauen und installieren (Windows / MinGW32 / Qt5)

Zunächst alle Programme schließen, die `libd64_qt5.dll` geladen haben. Dann im Projektroot:

```bat
build_and_deploy_dbase_debug_stage623.bat
```

Bei anderem dBASE-EXE-Verzeichnis:

```bat
build_and_deploy_dbase_debug_stage623.bat "T:\mein\ausgabe\verzeichnis"
```

Danach die dBASE-EXE **neu starten**. Ausschließlich die DLL wurde auf C++-Seite geändert; `? "hihi"` muss nicht allein für die Fensterbedienung neu kompiliert werden, sofern die EXE bereits korrekt ausgibt.

## Bedienungstest

1. Mit `? "hihi"` das grüne Fenster öffnen.
2. Titelleiste gedrückt halten und nach rechts/unten ziehen: die Position rastet auf das Zeichenraster ein.
3. Button rechts oben anklicken: das Fenster füllt den verfügbaren Bereich, der Resize-Griff verschwindet.
4. Button erneut anklicken: ursprüngliche Position / Zeichenzellgröße werden wiederhergestellt, Griff ist sichtbar.
5. Beide Aktionen nach Zoom und nach Verkleinern/Vergrößern des Qt5-Konsolenfensters ausprobieren.
6. Doppelklick auf die Titelleiste als alternativen Maximieren/Wiederherstellen-Weg testen.

## Prüfstatus

Die Quelle und das Archiv wurden statisch und durch deterministische Raster-/Restore-Logiktests geprüft. Eine native Windows-/MinGW32-Qt5-Übersetzung und die tatsächliche GUI-Bedienung sind in dieser Umgebung nicht möglich; sie bleiben für die Zielumgebung offen.
