# Stage 468 — dBASE/WFM: LOCAL auf der Top-Level-Ebene und in Prozeduren

## Grundlage

Verbindliche Grundlage: `d64_dism_asm_467.zip`.

## Ursache

Der WFM-Compiler hatte seit Stage 466 einen ausführbaren Top-Level-Block
(`__dbase_wfm_proc___dbase_top_level__`), aber der Statement-Emitter behandelte
`LOCAL A = 9` nicht. Deshalb kam beim Kompilieren eine Meldung wie:

```
WFM-Prozedur __dbase_top_level__: Statement noch nicht als Event-Assembler implementiert: local A = 9
```

## Korrektur

- `LOCAL name`, `LOCAL name = ausdruck` sowie mehrere Deklaratoren
  (`LOCAL a=9, b="rot,blau", c`) werden in Top-Level und WFM-Prozeduren erkannt.
- Variablennamen werden pro Prozedur gebunden, inklusive Auflösung durch
  `STORE`, `name = ausdruck`, `TYPE()`, `VARTYPE()`, `?`, `??` und `IF`.
- Der Compiler reserviert typisierte, voneinander getrennte lokale Slots
  (`__dbase_wfm_local_<prozedur>_<name>_{type,num,ptr,len}`), ohne sie anderen
  Prozeduren als globale Memory-Variablen bekanntzumachen.
- Bei jedem Eintritt in die Prozedur werden die lokalen Slots in einen
  definierten NULL-Ausgangszustand gesetzt. Ein Initialisierer wird an der
  ursprünglichen Stelle der `LOCAL`-Anweisung ausgeführt.
- Fehlende Namen, ungültige Bezeichner, doppelte Deklaration und nicht
  unterstützte Initialisierer werden als Compilerfehler gemeldet.
- Die eingebauten `PARAMETER bmodal`/`LOCAL B`/`B = NEW Form1(...)`-Zeilen
  des Designer-Bootstrap bleiben wie zuvor von der doppelten Ausführung ausgenommen.
- Die `; Quellcode Zeile: N`-Kommentare von Stage 467 bleiben intakt.

## Beleg / Tests

- `python -m pytest -q test_stage468_wfm_local_declarations.py`
- Erweitertes WFM-Regressionspaket Stage 460–468: 94 Tests bestanden.
- Reale interne Assemblierung und Verlinkung für PE32 und PE32+
  in allen vier Slot-Optimierungsmodi erfolgreich.

## Laufzeit-Einschränkung

Die Slots werden pro Prozedur getrennt und bei jedem Eintritt gelöscht,
bleiben aber aktuell statisch (.bss) allokiert. Rekursive bzw. gleichzeitig
reentrante Aufrufe *derselben* WFM-Prozedur verfügen damit noch nicht über
unabhängige Aktivierungsdatensätze. Für vollständige rekursive LOCAL-Semantik
wären stackbasierte Laufzeit-Slots erforderlich.

Windows-Qt5-GUI-Laufzeit nicht im Testcontainer ausführbar; dortige
Ausgabe und Benutzerinteraktion wurden nicht nativ verifiziert.
