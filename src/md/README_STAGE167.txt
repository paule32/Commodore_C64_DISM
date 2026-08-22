Stage 167 – Ansicht -> Sprache / 4-spaltiges Flaggenmenü
=========================================================

Basis
-----
- Stage 166 d64_dism.py bleibt vollständig erhalten; die Änderungen sind additiv.
- Die vom Benutzer gelieferte flags_rc.qrc wurde übernommen.

Ansicht -> Sprache
------------------
- Im Hauptmenü "Ansicht" befindet sich nun der Eintrag "Sprache".
- Das Untermenü wird als QWidgetAction mit QGridLayout aufgebaut.
- Datenquelle ist ausschließlich LANGUAGE_CODES aus d64_dism.py.
- LANGUAGE_CODES enthält 68 Einträge; dargestellt werden exakt 17 Zeilen x 4 Spalten.
- Reihenfolge entspricht exakt der Reihenfolge in LANGUAGE_CODES.

Eintragsdarstellung
-------------------
Jeder Eintrag besitzt:

    (o) [Flagge] - CODE - Name

Beispiel aus LANGUAGE_CODES:

    (o) [deu.png] - DEU - German

- (o) ist ein echter QRadioButton.
- Die Flagge wird ausschließlich über den Qt-Resource-Pfad geladen:

    :/flags/deu.png

- Die RadioButtons liegen in einer exklusiven QButtonGroup.
- Die aktuelle Auswahl wird unter QSettings-Key view/language_code gespeichert.
- Standardauswahl ist DEU, sofern kein gültiger gespeicherter Code vorliegt.

Resource-Abgleich
-----------------
- LANGUAGE_CODES: 68 Einträge
- flags_rc.qrc: 68 aliases
- Fehlende Aliase: 0
- Zusätzliche Aliase: 0

Die QRC enthält z.B.:

    <file alias="deu.png">flags/deu.png</file>

und die GUI lädt entsprechend:

    QPixmap(":/flags/deu.png")

Wichtig: d64_dism.py importiert bereits "from flags_rc import *". Für die
Laufzeit muss daher wie im bisherigen Projekt die aus flags_rc.qrc erzeugte
flags_rc.py bzw. die registrierte Qt-Resource vorhanden sein. Die PNG-Dateien
selbst waren in der aktuellen Übergabe nicht enthalten und wurden deshalb nicht
künstlich ersetzt.

Tests
-----
- 20/20 Stage-167-Quell-/Strukturtests OK
- python -m py_compile d64_dism.py: OK
- Alle 68 LANGUAGE_CODES besitzen genau einen passenden QRC-Alias.
- Stage-166-Zeilenfolge vollständig erhalten.
