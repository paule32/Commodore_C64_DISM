# Stage 615 – Agent 0003 / dBASE-Startpfad

Verbindlicher Ausgangsstand: `d64_dism_stage614.zip` (Stage 614).
Bildverarbeitungs-Vorlage: Benutzerdatei `Bild_Recognition-main.zip`, insbesondere
`src/detect_shapes.py` und `src/classes/shapedetector.py`. Die neue Erkennung
ist als eigenständige Qt5-Komponente umgesetzt, ohne `imutils`.

## 1. dBASE-Editor – Start-Button

Der Button **Start** ermittelt die bereits assemblierte/gebaute EXE ab jetzt
über `_document_windows_output_path(document)`. Diese Methode berücksichtigt
**Compiler -> dBASE -> Ausgabe Verzeichnis**, die Zielarchitektur PE32/PE64 und
Projektzuordnungen. Beispielsweise wird die relative Einstellung
`runtime/dbase/pe32` unter dem Verzeichnis der aktiven `.pro`-Projektdatei
ausgewertet:

    <Projektordner>/runtime/dbase/pe32/<Quelldateiname>.exe

Die vorhandene Start-/Workstation-/DOS-/DEBUG-Logik wird anschließend
unverändert genutzt. Der Start-Button assembliert **nicht** erneut. Bei einer
fehlenden EXE wird der vollständige erwartete Pfad angegeben.

## 2. Agent 0003 – Bild-Erkennung

**Agent -> 0003 - Bild-Erkennung** öffnet ein eigenes dockbares Qt5-Fenster
über denselben exklusiven Dock-Workspace wie Agent 0002. Der obere Bereich
übernimmt dessen drei Spalten (Texteingabe/Beispiele; Wort-/Grammatiktabelle;
Prüf- und Antwortansicht). Der editierbare Texteditor bleibt erhalten.

Der untere Bereich enthält oberhalb des horizontalen Splitters eine ComboBox
mit Filtern für **alle Figuren**, **Kreise**, **Dreiecke**, **Rechtecke**,
**Quadrate** und **Polygone**. Links stehen **Bild laden ...** sowie
**Erkennung ...**. Rechts zeigt `QGraphicsView` mit eigenen Scrollbars und
einer `QGraphicsScene` das gewählte Originalbild. Figurenkonturen werden als
selektierbare Qt5-Polygonobjekte darüber gezeichnet und mit `Kreis`,
`Dreieck`, `Rechteck`, `Quadrat` oder `Polygon` beschriftet. Ein Klick auf die
Kontur zeigt den Figurtyp, die erkannte Farbe und Position an. Die Abfragen
können passende Figuren zusätzlich orange hervorheben.

OpenCV/NumPy erkennen einfache geometrische Figuren anhand von Konturen und
Polygonapproximation, auch schwarze Figuren in farbigen Diagrammen bzw.
weiße Figuren auf dunklem Grund. Fotos mit Hintergrundrauschen, überlappende
Figuren, teilverdeckte Objekte und semantische Objekte (Personen, Tiere usw.)
werden **nicht** zuverlässig erkannt; dies ist keine trainierte Objekt-KI.

## 3. Wort-/Fragen-Datenbanken

- `data/woerter.dbf`: dBASE-III+/Windows-1252, **1366 Datensätze mit 1348
  verschiedenen Wortformen**, inklusive Kasus- und Genusflags. Das ist der
  zuletzt separat ausgelieferte korrigierte Bestand. 10.000 qualitätsgesichert
  grammatisch annotierte Wörter sind **noch nicht vorhanden**. Die Zahl wird
  weder künstlich aufgefüllt noch als erreicht behauptet.
- `data/fragen.dbf`: 22 parameterisierte deutsche Bildfragen. Die Muster
  verbinden eine erkannte Figurenform/Farbe mit Absichten wie `position`,
  `farbe`, `anzahl`, `farbfrage` und `zeigen`. Beispiel: `wo befindet sich der
  rote kreis?`, `welcher kreis ist rot?`, `wie viele kreise sind im bild?`.
- `agent_0003_language.py`: DBF-III-Leser und einfacher Wort-/Satzmusterparser.
  Das ist eine begrenzte Plausibilitätsprüfung, **keine** vollständige
  syntaktische, semantische oder logische Grammatik-Engine.

Original-DBF-Attribute aus der korrigierten Datei werden beibehalten (u.a.
`SUBSTANTIV`, `VERB`, `SINGULAR`, `PLURAL`, `DER`, `DIE`, `DAS`, `MALE`,
`FEMALE`, `NEUTRUM`, `NOMINATIV`, `GENITIV`, `DATIV`, `AKKUSATIV`, `KASUS`).
`MALE`/`FEMALE` meinen das **grammatische** Genus, nicht Menschen-Geschlecht.

## 4. Abhängigkeiten

    python -m pip install numpy opencv-python PyQt5

Die Hauptanwendung selbst nutzt bereits PyQt5. Für Stage 615 benötigt Agent
0003 zusätzlich `numpy` und `opencv-python` (`import cv2`). Fehlende
Abhängigkeiten werden beim Menüaufruf mit einem Fehlerdialog benannt.

## 5. Starten und Ausprobieren

1. Projektdatei laden, dBASE-Ausgabepfad unter Compiler einstellen.
2. dBASE-Editor: `Assemble`, dann `Start`. Die EXE wird im Ausgabepfad gesucht.
3. Im Hauptmenü: `Agent -> 0003 - Bild-Erkennung`.
4. `Bild laden ...`: z.B. `examples/agent_0003_testbild.png`.
5. `Erkennung ...`: Kreise/Dreiecke/Rechtecke erscheinen mit Beschriftungen.
6. Im Textfeld: `wo befindet sich der rote kreis?` oder
   `wie viele rote kreise sind im bild?` eingeben, dann `Satz / Bild prüfen`.

Protokollmeldungen werden, wie bei Agent 0002, über die `MainWindow.log()`-
Methode an das vorhandene IDE-Protokoll übergeben. Kein neues DOS-Fenster.

## 6. Prüfungen / Grenzen

- `test_stage615.py`: 12 isolierte Tests – Projektpfad, Startverhalten,
  CV-Formerkennung, schwarze/weiße Figuren, Unicode-Dateinamen,
  DBF-Merkmale, Bildfragen, Menü-/Dock-Verkabelung.
- Python-3.13-Syntaxprüfung der großen `d64_dism.py` **nur** nach temporärer
  Normalisierung ihrer zwei bereits vorhandenen Python-3.15-`lazy from`-
  Imports; der gelieferte Code bleibt im Originalzustand mit `lazy`.
- Natives GUI-Rendering ist in der Paketierungsumgebung mangels PyQt5 nicht
  durchführbar und bleibt unter Windows 10/11 sowie der verwendeten Python-
  Version zu validieren.
- 10.000 annotierte Wörter und echtes freies deutsches Sprachverstehen sind
  offene Ausbauziele, **nicht** Teil einer bestätigten Umsetzung.
