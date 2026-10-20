# Stage 444 – Römische Zahlen: Dark-Mode und Spaltenkorrektur

**Verbindliche Basis:** `d64_dism_asm_443.zip`

## Umsetzung

- Echte Dark-Mode-Darstellung der schreibgeschützten, kopierbaren `QPlainTextEdit`-Lernseite:
  dunkelblauer Hintergrund, helle Zahlentexte, hellblaue Überschrift, kontrastreiche Trennlinien/Markierungsfarben.
- Light-Mode bleibt hell, die Schrift wechselt zurück nach dunkel.
- Die vorherigen fünf **festen** Tabstopps für die Datentabelle wurden ersetzt. Sechs Tabellenspalten (drei Zahlen-/Römerzeichen-Paare) verwenden jetzt die **breiteste Zeichenfolge jeder Spalte** und die tatsächliche Schriftmetrik. Dadurch werden besonders längere Ziffern wie `XXXVIII` und die rechts folgenden Werte nicht ineinander gezeichnet.
- Die **sieben** Kopfspalten `I, V, X, L, C, D, M` (mit `1, 5, 10, 50, 100, 500, 1000`) besitzen einen eigenen, passenden Satz aus sechs metrisch berechneten Tabstopps; insbesondere die Spalten 6/7 bleiben im Blatt sichtbar.
- Der Editor bleibt schreibgeschützt, reiner Text und bei engem Dock horizontal scrollbar. Beim Theme-Wechsel bleiben vertikale und horizontale Scrollpositionen erhalten.
- An der bestehenden Mathematik-Baumstruktur und den restlichen Projektmodulen wurden keine Änderungen vorgenommen.

## Hinweise zum Testumfang

Automatisierte Syntax-, Layout-Struktur- und Regressionstests; unter der hier verfügbaren Umgebung kann die native Windows-PyQt5-Darstellung nicht visuell verifiziert werden.
