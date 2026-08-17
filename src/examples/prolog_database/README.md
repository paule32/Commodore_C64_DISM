# PROLOG External Database - Beispiele

Die Beispiele muessen mit dem Arbeitsverzeichnis `examples/prolog_database` gestartet
werden, weil die Dateinamen absichtlich relativ gehalten sind.

## Beispiel 1 - Patientenakte

`arzt_patient.pl` oeffnet `patient_4711.pl` als `read_write, record`, fragt Werte ab,
fuegt zwei Fakten gezielt in diese Database-ID ein, speichert atomar und entlaedt die
Akte danach mit `database_close/1`.

## Beispiel 2 - Fachwissen + Patientenakte

`arzt_mit_fachwissen.pl` oeffnet gleichzeitig:

- `medizin_wissen.pl` als `read_only, knowledge`
- `patient_4711.pl` als `read_write, record`

Die Regel `kontrolle_empfohlen/1` stammt aus der Wissensdatenbank, die dazu benoetigten
Messwerte aus der Patientenakte. Die normale PROLOG-Suche kann beide Quellen gemeinsam
verwenden. Aenderungen werden dagegen nur der Patienten-Database-ID zugeordnet.

Hinweis: Die Beispiele veraendern beim Ausfuehren die Datei `patient_4711.pl`. Fuer einen
wiederholbaren Test deshalb vorher eine Kopie der Beispieldatei anlegen.
