Stage 163 – DBF Tabellendesigner: Daten-Tab und Datensatzbearbeitung

Speichern unter
---------------
Eine neu angelegte Tabelle besitzt zunächst nur:

    [ Felder ]

Nach erfolgreichem "Speichern unter ..." wird rechts daneben erzeugt:

    [ Felder ] [ Daten ]

Der äußere Tabellen-Tab erhält den Dateinamen ohne .dbf, also z.B.:

    Kunden

für:

    Kunden.dbf

Beim Laden einer vorhandenen DBF wird der Daten-Tab ebenfalls erzeugt.

Daten-Grid
----------
Die horizontalen Header entsprechen exakt den Feldnamen aus dem
Tabellendesigner.

Die festen vertikalen Header zeigen:

    1
    2
    3
    ...

also die Datensatznummer.

Alle Zellen sind editierbar.

Typisierte Editor-Zellen
------------------------
C / Zeichen:
    QLineEdit, maximal Feldlänge

N / F:
    QLineEdit + QDoubleValidator
    keine alphabetischen Zeichen
    Nachkommastellen gemäß Felddefinition
    deutsches Komma wird beim Speichern zu Punkt normalisiert

D / Datum:
    QLineEdit + QIntValidator
    genau 8 Ziffern, Darstellung YYYYMMDD

L / Logisch:
    ComboBox mit leer / True (T) / False (F)

M / Memo:
    in der vorhandenen lokalen DBF-Writer-Basis als begrenztes Textfeld
    entsprechend der bisherigen M-Feldbehandlung

Ungültige Werte werden verworfen und der vorherige Zellwert bleibt erhalten.

Kontextmenü
-----------
    Einfügen
    Kopieren
    Ausschneiden
    ----------------
    Löschen Datensatz
    Neuer Datensatz

Einfügen/Kopieren/Ausschneiden beziehen sich auf die aktuelle Zelle und
verwenden die System-Zwischenablage.

"Löschen Datensatz" entfernt die aktuelle Datensatzzeile.

"Neuer Datensatz" fügt direkt nach dem aktuellen Datensatz eine neue
leere Zeile ein.

Navigation
----------
Oberhalb des Datengrids befindet sich:

    [ Anfang ] [ Zurück ] [ Vor ] [ Ende ]

Anfang:
    erster Datensatz

Zurück:
    einen Datensatz zurück

Vor:
    einen Datensatz weiter

Ende:
    letzter Datensatz

Auto-Save
---------
Nach jeder gültigen Zelländerung sowie nach:
- Ausschneiden
- Einfügen
- Neuer Datensatz
- Löschen Datensatz

wird die komplette DBF über den bereits vorhandenen write_dbase_dbf()
atomar wieder in dieselbe Datei geschrieben.

Der vorhandene Writer schreibt zunächst *.tmp und ersetzt danach mit
os.replace(), daher bleibt der bisherige sichere Schreibpfad erhalten.

Dark Mode
---------
Der Daten-Grid-Header verwendet im Dark-Mode:
    Hintergrund #2A2A2A
    Schrift      #FFFFFF

Grid:
    Hintergrund #111111 / #181818
    Auswahl      #294764

Auch das Navigation-Panel folgt Dark/Light.

Vorhandene DBF-Routinen
-----------------------
read_dbase_dbf() und write_dbase_dbf() bleiben die einzige Lese-/
Schreibbasis. Es wird kein zweites Tabellenformat eingeführt.

Hinweis zu gelöschten DBF-Datensätzen:
Beim Laden werden bereits als gelöscht markierte DBF-Zeilen nicht als
aktive editierbare Zeilen angezeigt. Beim nächsten Speichern wird die
Tabelle dadurch kompakt neu geschrieben.

Tests
-----
py_compile d64_dism.py: OK

Statische/algorithmische Prüfungen: siehe STAGE163_TEST_RESULTS.txt

Native Windows/PyQt5-GUI-Laufzeitprüfung ist in dieser Umgebung nicht
verfügbar.
