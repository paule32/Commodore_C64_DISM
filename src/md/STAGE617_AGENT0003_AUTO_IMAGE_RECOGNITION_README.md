# Stage 617 — Agent 0003: Automatische Erkennung bei Satz- und Bildprüfung

**Verbindliche Basis:** `d64_dism_stage616.zip`

## Fehler

Nach dem Laden eines Bildes enthielt `self.figures` zunächst keine Elemente.
Der Button **„Satz / Bild prüfen“** führte nur die Sprach-/Bildabfrage aus,
ohne vorher `detect_figures()` aufzurufen. Selbst ein sichtbarer roter Kreis
wurde deshalb mit „Keine passende Figur“ beantwortet. Das eigenständige
**„Erkennung ...“** war zuvor zwingend erforderlich.

## Korrekturen

* `agent_0003.py`: `analyze()` überschrieben: bei geladenem und noch nicht
  analysiertem Bild einmal `detect_figures()` ausführen, dann wie bisher die
  Satzprüfung von Agent 0002 nutzen. Alle vorhandenen Qt-Signalverbindungen
  auf `self.analyze` verwenden den überschriebenen Handler.
* `agent_0003.py`: `_detect_current_image()` führt die Konturerkennung und
  Visualisierung durch, ohne rekursiv eine weitere Satzprüfung zu starten.
  Die Figuren werden bis zum nächsten Laden oder expliziten Neu-Erkennen
  zwischengespeichert. Auch null erkannte Figuren gelten als abgeschlossene
  Analyse, um unnötige erneute Scans zu vermeiden.
* `agent_0003.py`: **„Erkennung ...“** berechnet die Figuren erneut und prüft
  die aktuelle Eingabe. Die Namen **Kreis**, **Dreieck**, **Rechteck**, **Quadrat**
  und **Polygon** werden auf den jeweiligen Figuren in der QGraphicsScene
  dargestellt; zur aktuellen Frage passende Figuren werden orange markiert.
* `agent_0003_language.py` und `data/fragen.dbf`: drei neue Satzmuster,
  z. B. „wo befindet sich das grüne dreieck“ und „wo ist die blaue figur“.
  Die bestehenden 22 Muster bleiben erhalten, die DBF hat nun 25 Einträge.
* `test_stage617.py`: sieben gezielte Regressionstests für automatische
  Erkennung, Frage-Antwort-Kette, Wiederverwendung, explizite Neuerkennung,
  fehlendes Bild, unpassende Farbe und DBF-Muster.

## Reproduzierbare Schritte

1. **Agent → 0003 - Bild-Erkennung** öffnen.
2. **Bild laden ...**, Testbild `examples/agent_0003_testbild.png` auswählen.
3. „wo befindet sich der rote kreis“ eingeben.
4. **Satz / Bild prüfen** klicken (kein vorheriger Klick auf „Erkennung ...“ nötig).
5. Erwartete Ausgabe: `Absicht: position | rot Kreis: links / oben (x=90, y=90)`.
6. In der Bildszene erscheint auf der rot gefüllten Figur der Text **Kreis**;
   ihre Kontur ist orange, andere Konturen standardmäßig grün.
7. Bei „wo befindet sich das grüne dreieck“ oder
   „wo befindet sich das blaue rechteck“ werden die passenden Formen
   unabhängig von einer weiteren Figurenerkennung gefunden und markiert.

## Prüfungen

`python -m unittest -v test_stage615 test_stage616 test_stage617`

Ergebnis im bereitgestellten Testsystem: **29 Tests, 28 erfolgreich,
1 übersprungen**. Das Originalbild `recognition_ref/.../shapes.png` liegt nicht
im ausgelieferten Projekt-ZIP, weshalb genau dieser Test übersprungen wird.
Die Bild- und Satzlogik wurde real mit OpenCV/NumPy ausgeführt. Eine native
PyQt5-Interaktion unter Windows wurde hier mangels Qt-Bindings nicht getestet.

Die bestehende `data/woerter.dbf` (6.348 Wortformen, 17 Felder) wurde nicht
verändert. Der EXE-Startpfad-Fix von Stage 615 bleibt erhalten.
