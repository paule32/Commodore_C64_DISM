# Stage 466 – ausführbarer dBASE-Code außerhalb von CLASS Form1

**Verbindliche Basis:** vom Benutzer hochgeladenes `d64_dism_asm_465(1).zip`.

## Fehlerursache

Der WFM-Parser in Stage 465 betrachtete Quelltext vor `CLASS ... OF FORM`
vorwiegend als Designer-Header und erkannte daraus nur Sonderanweisungen,
beispielsweise `SET DEBUG`, `B = NEW Form1(...)` und die Konstruktorargumente.
`STORE`, `?`, `??`, `TYPE()`, `VARTYPE()`, `IF/ELSE/ENDIF` usw. vor
`** END HEADER -- do not remove this line` wurden im WFM-Programmstart
**nicht ausgeführt**. Die ursprüngliche dBASE-Laufzeitshell arbeitete nur
mit dem Dummyprogramm `?? ""` und war nicht der WFM-Programmeinstieg.

## Korrektur

- `d64dbase/wfm.py`: `wfm_executable_preamble()` extrahiert alle Zeilen vor
  der Formularklasse, entfernt dBASE-Kommentare mit dem bestehenden Scanner
  und behält die originalen Zeilenpositionen bei. Die vom Designer erzeugten
  Bootstrap-Zeilen `PARAMETER bmodal`, `LOCAL B`, `B = NEW Form1(...)` und
  die zusammengehörige `bmodal/ReadModal/Open`-Verzweigung werden nur dann
  herausgefiltert, wenn das bekannte Bootstrap-Muster übereinstimmt.
  Historische Einstiege mit `Form1 = NEW Form1()` werden ebenso erkannt.
- `d64_dism.py`: Der restliche Top-Level-Code wird als interne Methode
  `__dbase_top_level__` über den bestehenden WFM-Statement-Assembler
  umgesetzt, der auch Event-Code compiliert. Der PE32-/PE32+-Einstieg ruft
  diese Methode nach `DBaseQtRuntimeStartup`, aber **vor**
  `DBaseQtFormCreate` auf, genau einmal pro Programmstart.
- Hier und in Event-Methoden werden dieselben globalen typisierten
  Memory-Slots verwendet. Ein `STORE ... TO xyz` vor `CLASS` ist deshalb
  bei nachfolgenden `TYPE("xyz")`-, `VARTYPE(xyz)`- und Event-Aufrufen sichtbar.
- `SET DEBUG ON/OFF` in einem ausführbaren Preamble wird jetzt in dessen
  Anweisungsreihenfolge ausgeführt und nicht noch einmal aus der
  zuvor verwendeten Debug-Vorab-Liste erzeugt.
- Nicht unterstützte Anweisungen vor der Klasse erzeugen nun einen
  **Compilerfehler mit Quellzeile** statt unbemerkt verloren zu gehen.

## Tests

- `test_stage466_wfm_top_level_program.py`:
  exaktes Beispiel mit Typwechsel N→C und undefiniert U, dynamische und
  statische WFM-Slots, PE32 + PE32+, WFM-Entry-Aufrufreihenfolge,
  COFF-Assemblierung und PE-Linking, Kommentarregeln, Debug-Anweisungen,
  Legacy-Konstruktor und Fehlerdiagnose.
- 167 ausgewählte Compiler-, Runtime- und WFM-Regressionstests bestanden,
  darunter 10 neue Stage-466-Tests. Die vollständige Projekttestsuite
  konnte wegen Timeout nicht abgeschlossen werden.
- Ein älterer Stage-450-DLL-Packer-Test ist nicht bestanden:
  `test_real_pe_dll_build_with_mocked_transparent_filesystem_pack` –
  der Test-Kompressor erwartet zwei Parameter, erhält aber nur einen.
  Diese von Stage 466 unabhängige Schnittstelle wurde nicht geändert.

**Nicht geprüft:** native Ausführung/Anzeige des Qt5-Ausgabedialogs unter
Windows 11. Die Tests belegen Codegenerierung, Assemblierung und Linken,
aber keinen interaktiven GUI-Lauf.
