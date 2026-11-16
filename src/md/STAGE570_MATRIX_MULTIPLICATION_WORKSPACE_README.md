# Stage 570 – Mathematik: Matrizenmultiplikation und Dock-Wiederherstellung

Verbindliche Basis: `d64_dism_stage569.zip`.

## Änderungen

1. Unter **Mathematik → Fakten → Matrizen → Rechnen mit ... → Multiplikation**
   wird vor dem Wechsel zur rechten Fakten-Seite ein exklusiver Arbeitsbereich
   aktiviert: andere sichtbare `QDockWidget`-Instanzen werden ausgeblendet,
   das zentrale Editor-Widget verborgen und die Originalzustände für den
   späteren Workspace-Restore vorgemerkt. Bei einem normalen Wechsel zu anderen
   Mathematik-Fakten kann das Protokoll-Dock wieder erscheinen.
2. Beim Minimieren des Hauptfensters führt ein kurzzeitig unsichtbares Dock
   nicht mehr unmittelbar zur Aufhebung des aktiven Matrix-Arbeitsbereichs.
   Ein verzögerter Sichtbarkeitscheck verhindert außerdem, dass ein
   temporäres `visibilityChanged(False)` als bewusstes Schließen gilt.
   `changeEvent()` merkt sich, ob die Multiplikationsseite aktiv war, und
   reaktiviert Dock und Stack-Seite bei der Wiederherstellung.
3. `MatrixMultiplicationPanel` ist **oberhalb** der bestehenden
   `MultiplicationMatrixFactWidget`-QPainter-Seite eingebettet. Das bestehende
   Original-Widget wird nicht ersetzt oder überschrieben.
4. In der `QToolBar` gibt es vier `QSpinBox`-Dimensionen (`m1`, `n1`, `m2`, `n2`)
   sowie die Buttons **Erstellen** und **Berechnen**. Standard: 2×3 und 3×2.
5. `Erstellen` legt zwei editierbare Tabellen in Matrixdarstellung mit dem
   Multiplikationszeichen `×` an. Dimensionen: 1–12 Zeilen/Spalten.
6. `Berechnen` schreibt in leere Eingaben `0`, prüft Werte und
   Kompatibilität (`n1 == m2`) und berechnet mit `decimal.Decimal` die
   Ergebnismatrix. Die Ergebnisse werden zeilenweise als `QLabel` angezeigt;
   unterhalb erscheinen die Produkte und Summen für jede Ergebniskomponente.
   Bei nicht passenden Dimensionen bzw. ungültigen Zahlen folgt ein Hinweis.
7. Dark-/Light-Mode der neuen Widgets orientiert sich am Mathematik-Dock.

## Mathematik

Für A (m1×n1) und B (m2×n2) gilt: nur bei `n1 = m2` ist das Produkt
C (m1×n2) definiert. Jedes Ergebnis ist ein Zeilen-Spalten-Skalarprodukt:
`c[i,j] = sum(a[i,k] * b[k,j] for k in range(n1))`.

Beispiel: `[[1,2,3],[4,5,6]]` mal `[[7,8],[9,10],[11,12]]`
ergibt `[[58,64],[139,154]]`.

## Neue Dateien

- `matrix_multiplication_logic.py`: Qt-unabhängige Rechenlogik und Terme
- `matrix_multiplication_panel.py`: PyQt5-GUI (Toolbar, Eingabematrizen, Ergebnis)
- `test_stage570.py`: Rechen-/Integrationstests
- `test_stage570_qt.py`: optionale PyQt5-GUI-Tests

Geändert: `d64_dism.py` (gezielte Integration, Dock-Restore).

## Testnachweis in dieser Umgebung

`python -m unittest test_stage553 ... test_stage570 test_stage570_qt -q`

**203 Tests: 199 erfolgreich, 4 GUI-Tests übersprungen**
(weil PyQt5 hier nicht installiert ist).

Die `d64_dism.py` aus Stage 569 enthält bereits Python-3.15-PEP-810-`lazy`
Import-Syntax; die Syntaxprüfung unter Python 3.13 erfolgte daher mit
entferntem `lazy`-Präfix ausschließlich im Prüfstring (nicht in der Quelldatei).

Wichtig: Die ursprüngliche Stage-569-ZIP enthält die Referenz auf
`multiplication_matrix_fact.py`, aber **nicht** den Inhalt dieses Moduls.
Die Integration belässt diesen Import unverändert und erhält das Original-
Widget, sofern seine Datei in der tatsächlichen Laufzeitumgebung verfügbar ist.
Der vollständige Windows-/Qt5-Lauf einschließlich Minimieren und Wiederherstellen
ist noch zu überprüfen.
