# Stage 443 – WFM-Ereignisassembler: LEN() als echter Laufzeitausdruck

## Verbindliche Grundlage
`d64_dism_asm_442.zip`. Alle sonstigen Projektbestandteile bleiben erhalten.

## Gemeldete Reproduktion
Im WFM-Formular `Form1.wfm` (unter `PushButton1_onClick`) schlug `? LEN(Text)`
mit `WFM Event-Assembler Stage 203: Ausdruck für ? wird im Event-Code noch nicht unterstützt`
fehl, obwohl die Funktion seit Stage 441 im normalen dBASE-PRG-Compiler existiert.

## Korrektur
- Der WFM-Ereignisassembler benutzt jetzt einen eigenen typisierten Laufzeitpfad
  für `LEN(...)`; Werte von Memory-Variablen werden **zur Laufzeit** aus dem
  WFM-Variant-Slot (`_type`, `_ptr`, `_len`) ermittelt.
- Der WFM-Stringspeicher ist UTF-8-kodiert. Der neue LEN-Code zählt Zeichen
  anhand der UTF-8-Startbytes, nicht Byteanzahlen; Zugriffe sind durch `_len`
  begrenzt. Bei NULL/uninitialisierten Laufzeitslots ergibt sich 0.
- WFM unterstützt damit außerdem die Kombinationen `STORE LEN(Text) TO N`,
  `N = LEN(Text)`, `IF LEN(Text)>0`, `RETURN LEN(Text)`, Ausgaben via `?` / `??`
  und Verkettungen wie `? "Länge: " + LEN(Text)`.
- LTRIM/RTRIM/TRIM aus Stage 441 sind für WFM-Ausdrücke desselben Pfads
  integriert. Der PE32+-WFM-Ereignisprolog reserviert bereits Shadow Space;
  die trim-basierte malloc-Aufrufsequenz reserviert diesen nicht erneut.
- Die Behandlung von nicht unterstützten Ausdrücken bleibt ansonsten wie bisher;
  es werden keine unbekannten Funktionen stillschweigend ausgeführt.

## Dateien
- `d64_dism.py`: WFM-Laufzeitgenerierung und Eventausdrücke
- `d64dbase/string_length_trim.py`: optionales Shadow-Space-Handling
- `examples/dbase_wfm_len_event_stage443.wfm`: reproduzierbare Quelle
- `test_stage443_wfm_len_event.py`: PE32-/PE32+-WFM-Kompilierungstests

## Tests/Abgrenzung
Die WFM-Compilerfunktion wird in den Tests ohne PyQt5 per Codeextraktion
aufgerufen. Die Assemblerschreibweise und die Variant-Datenpfade werden geprüft.
Eine Ausführung der erzeugten PE32-/PE32+-EXE unter Windows bzw. ein echter
Qt5-OnClick-Laufzeittest ist in dieser Umgebung nicht erfolgt.
