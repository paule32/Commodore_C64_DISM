# Stage 567 – Sicherheit: dunkler Tabellenheader, Serial-Schrift und Druckvorschau

**Verbindliche Basis:** `d64_dism_stage566.zip`.

## Änderungen

- Beide Serial-Tabellen erhalten eigene Qt-Header-Stylesheets. Insbesondere der
  Haupt-Tab **Serial Nummer Liste** verwendet im Dark-Mode einen dunklen
  Header mit hellen Beschriftungen; auch Hover/gedrückte Bereiche werden
  angepasst. Im Light-Mode gelten passende helle Farben. Die Spaltenbreiten
  bleiben per Maus veränderbar, die vertikale Kopfzeile ausgeblendet.
- Einträge der einspaltigen Tabelle im Kinddialog **Serial Nummer - Listen
  Eigenschaften** werden mit einer Schriftfamilienfolge dargestellt:
  **Consolas → Courier New → Courier**. Qt >= 5.13 verwendet dazu
  `QFont.setFamilies()`, bei älteren Qt-Versionen bleibt Consolas mit
  `QFont.TypeWriter`-Fallback. Neue, importierte, generierte und bearbeitete
  Nummern verwenden dieselbe Tabellenschrift.
- **Kommandos → Drucken** öffnet ab jetzt `QPrintPreviewDialog` vor dem
  physischem Druck. In der Vorschau kann gezoomt/geblättert werden; erst die
  dortige Drucken-Schaltfläche ruft den Druckdialog auf. Vorschau und Druck
  erhalten dasselbe `QTextDocument` aus dem aktuellen Tabellenstand.
  Die Ausgabe überträgt Serial-Nummern HTML-escaped, damit `<` / `&` nicht
  als Markup interpretiert werden.

## Herkunft des Druckdialogs

Der bisherige Druckdialog wurde per `PyQt5.QtPrintSupport.QPrintDialog` erzeugt.
Dies ist eine Qt-Komponente, die unter Windows den nativen Druckdialog des
Betriebssystems verwenden kann. Eine integrierte Vorschau ist dort nicht
zwingend vorhanden. Die zusätzliche `QPrintPreviewDialog` stammt ebenfalls
von Qt/PyQt5, nicht von einer Python-Standardbibliothek.

## Unverändert

- Menüeintrag **Drucken** und alle übrigen Kommandos/Shortcuts.
- Beide Dialoggrößen (620 × 550), Dark-Mode-Titelverlauf,
  `Sicherheit`-Projektformat, Speicher-/Abbruch-/Hilfelogik.
- Die spätere Setup-seitige Serial-Prüfung ist weiterhin nicht Bestandteil
  dieser Stage.

## Prüfung

- `test_stage567.py`: Struktur, Styling, Fonts, Druckvorschau und bestehende
  Persistenzpfade ohne Qt.
- `test_stage567_qt.py`: optionale GUI- und Preview-Checks mit PyQt5.
- Bestehende Tests sind unverändert.

Die CHM-Quellseite `help/software_installer/sicherheit.html` beschreibt die
Druckvorschau. Eine bereits kompilierte CHM muss daraus neu erstellt werden.
