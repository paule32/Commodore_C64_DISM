Stage 162 – CTRL+F Quelltextsuche

CTRL+F
------
Alle SourceTextEdit-basierten Quellcode-Editoren öffnen jetzt denselben
nicht-modalen Suchdialog. Dazu gehören normale Quelltexte, der erzeugte
ASM-Editor sowie die eingebetteten WFM-Quellcode-/ASM-Editoren.

Dialog
------
Der Dialog ist nicht modal und bleibt über der Anwendung:

    setModal(False)
    setWindowModality(Qt.NonModal)
    Qt.WindowStaysOnTopHint

Der Editor kann währenddessen weiterhin mit Maus und Tastatur benutzt werden.

Suchrichtung
------------
RadioButtons:

    Von vorne nach unten
    Von unten nach vorn

Suchoptionen
------------
Die Optionen sind bewusst kombinierbare CheckBoxen:

    Ganze Wörter
    Groß-/Kleinschreibung beachten
    RegExpr

Bei RegExpr wird darunter ein separates Eingabefeld
"Regulärer Ausdruck" aktiviert.

Projekt
-------
Die Checkbox

    Im Projekt suchen

wird nur angezeigt, wenn mindestens zwei durchsuchbare Text-/Quelldateien
in der Projekt-TreeList vorhanden sind.

Durchsuchbar sind BASIC, Assembler, Pascal, C/C-Header, LISP, PROLOG, LOGO,
dBase/WFM, Markdown sowie TXT/TEXT/LOG.

Binär-/Archiv-/Projektdateien werden nicht als Quelltext gelesen.

Wenn eine Projektdatei bereits im Editor geöffnet und verändert ist, wird
der aktuelle Editorinhalt durchsucht und nicht der ältere Dateistand auf
dem Datenträger.

Suchen / Nächste
----------------
Suchen:
- Vorwärts: beginnt am Textanfang
- Rückwärts: beginnt am Textende
- stoppt beim ersten gefundenen Treffer

Nächste:
- beginnt an der aktuellen Cursorposition
- stoppt wieder beim ersten Treffer

Bei Vorwärtssuche liegt der Cursor nach der Auswahl hinter dem Treffer.
Bei Rückwärtssuche liegt er davor. Dadurch wird derselbe Treffer beim
nächsten Klick nicht erneut gefunden.

Projekttreffer öffnen die betreffende Datei und markieren den Treffer.
Bei WFM wird direkt in den Quellcode-Tab des Formdesigners gewechselt.

Abbrechen
---------
Setzt die laufende Projektsuche zurück. Während der Dateisuche werden
Qt-Events verarbeitet, so dass der Abbrechen-Button ausgewertet werden kann.

Schließen
---------
Schließt nur den Suchdialog.

Dark/Light
----------
Der Suchdialog besitzt einen eigenen Dark-/Light-Stil und folgt dem
globalen Theme.

Tests
-----
py_compile d64_dism.py: OK
Statische + Suchalgorithmus-Prüfungen: alle erfolgreich.
Native Windows/PyQt5-GUI-Laufzeitprüfung ist in dieser Umgebung nicht verfügbar.
