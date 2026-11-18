# Stage 618 — Agent 0003: Ausschließlich zur Bildfrage passende Formen markieren

**Verbindliche Grundlage:** `d64_dism_stage617.zip`

## Problem

In Stage 617 führte die Satzprüfung die Bilderkennung aus und färbte die passende
Kontur orange, aber `show_filtered_shapes()` zeichnete weiterhin **alle**
erkannten Konturen mit ihren Beschriftungen (andere Formen grün).

Bei der Frage `wo befindet sich der rote kreis` soll dagegen ausschließlich
der tatsächlich passende rote Kreis mit **Kreis** beschriftet und markiert werden.
Die anderen Formen bleiben als unveränderte Pixel im geladenen Bild sichtbar,
**ohne** zusätzliche Konturen oder Texte.

## Umsetzung

- `agent_0003.py`: Ein expliziter Anzeigemodus `_show_query_only` trennt
  die Visualisierung von Satztreffern vom manuellen ComboBox-Filter.
- `_run_analysis()`: Nach `LanguageEngine.answer(...)` wird die Bildszene anhand
  der tatsächlichen Treffer neu aufgebaut. Das Ergebnislabel wird erst *danach*
  geschrieben, um `selectionChanged`-Nebeneffekte zu vermeiden.
- `show_filtered_shapes()`: Entfernt ausschließlich vorherige Analyse-Overlays;
  die geladene Original-Pixmap bleibt bestehen. Im Frage-Modus entstehen
  Kontur, schwarzer Text-Hintergrund und Text **nur für Treffer**.
- `_on_filter_changed()`: Eine neue explizite ComboBox-Auswahl stellt das
  normale Anzeigen aller bzw. nach Form gefilterten Figuren wieder her.
- `agent_0003_core.py`: `figures_for_overlay()` unterscheidet **None**
  (gewöhnliche ComboBox-Filterung) von der **leeren Menge** (Frage ohne Treffer).
- `test_stage617.py`: Der bestehende UI-Logiktest simuliert den neuen
  Neuaufbau des Overlays anstatt einer reinen Änderung der Stiftfarbe.
- `test_stage618.py`: Sechs neue Tests mit echtem OpenCV-/DBF-Frageergebnis
  und isoliert ausgeführter Zeichenlogik.

## Nachstellen unter Windows

1. **Agent → 0003 - Bild-Erkennung** öffnen.
2. Bild `examples/agent_0003_testbild.png` laden.
3. Frage `wo befindet sich der rote kreis` eingeben, **Satz / Bild prüfen**.
4. **Nur der rote Kreis** erhält eine orange Kontur und den Text **Kreis**.
   Blaues Rechteck, grünes Dreieck und ein eventuell vorhandener schwarzer
   Kreis bleiben ohne Overlay/Beschriftung.
5. Frage `wo befindet sich das grüne dreieck` eingeben; nun steht der
   Text **Dreieck** nur auf dem grünen Dreieck.
6. Frage ohne Treffer: keine Konturen oder Beschriftungen werden gezeichnet.
7. Durch Änderung der Figuren-ComboBox lässt sich die normale Formfilterung
   weiterhin aktivieren.

## Verifikation

`python -m unittest -v test_stage615 test_stage616 test_stage617 test_stage618`

Die OpenCV-/DBF-Logik sowie die Zeichenmethoden wurden mit Qt-Stellvertretern
getestet. Ein vollständiger nativer PyQt5-GUI-Lauf unter Windows ist weiterhin
auf dem Zielsystem durchzuführen. Keine Veränderung an den beiden DBF-Dateien,
Anwendungs-Hauptmodulen oder den vorhandenen Compiler-Startpfaden.
