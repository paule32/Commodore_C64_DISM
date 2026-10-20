# Stage 467 – WFM-Quelltext und Assembler gleichzeitig anzeigen

**Verbindliche Basis:** `d64_dism_asm_466.zip` (unveränderte Projektbasis, nur gezielte Erweiterungen in `d64_dism.py`).

## Quellcode-Layout

Der bisher nach dem Kompilieren eingeblendete eigenständige Tab „Assembler“ im
Formular-Designer wurde entfernt. Der Tab „Quellcode“ enthält jetzt:

- oben den bestehenden horizontalen Splitter **Quellstruktur | Quelltext**,
- unten den vorhandenen Editor der generierten Assembler-Ausgabe,
- dazwischen einen **vertikalen QSplitter** (`dbase_form_source_assembly_splitter`,
  Breite des Handles 7 Pixel, beide Bereiche nicht zusammenklappbar), dessen
  Größen der Benutzer direkt mit der Maus anpassen kann.

Der Editor wird **nicht dupliziert**: Der bestehende
`DocumentEditor.generated_assembly_editor_container` mitsamt
Assembler-Syntaxhervorhebung, F2-Build-Signal und MiniMap wird aus dem
versteckten Hilfseditor in die untere Splitter-Seite eingebettet.

„Compile“ wechselt jetzt zum Tab „Quellcode“, nicht mehr zum nicht vorhandenen
Assembler-Tab. Der Build-Ablauf „Compile → Assemble → Start“ bleibt unverändert.

## Original-Quellzeilen im WFM-Assembler

Beim Kompilieren jedes unterstützten Statements im WFM-Top-Level oder innerhalb
einer WFM-Prozedur/Funktion wird ein separater Kommentar erzeugt, beispielsweise:

    ; Quellcode Zeile: 3
    ; ? TYPE("xyz")
    ...

Der Compiler erhält die Original-Quellzeilen auch für die vor `** END HEADER`
stehenden Anweisungen. Die ersten Methoden-Statements befinden sich ab der
Zeile **nach** der `PROCEDURE`/`FUNCTION`-Deklaration. Blank- und Kommentarzeilen
behalten ihren Platz; ihnen wird kein Marker für ausgeführten Code zugeordnet.

Die Quellzeilen-Kommentare sind gültige Assembler-Kommentare; sie verändern keine
Instruktionsbytes und bleiben im `.asm` erhalten.

## Klick-Navigation

Ein linker Mausklick auf eine Zeile `; Quellcode Zeile: <n>` im unteren WFM-ASM-
Editor markiert Zeile `<n>` im darüber liegenden WFM-Quelltext und scrollt dorthin.
Der Mauszeiger wird auf dem Marker zur Zeigehand. Andere Kommentare oder normale
Assembler-Befehle lösen keinen Sprung aus. Die zuvor existierende Navigation
innerhalb des Assembler-Editors zu ASM-Labels bleibt bestehen.

Das Mapping wird nur dort erzeugt, wo eine **konkrete dBASE-Quellanweisung**
vorliegt: der automatisch erzeugte GUI-Startcode, Qt-Runtime-Aufrufe und
Designer-Initialisierung besitzen naturgemäß nicht immer eine eindeutige
Einzelanweisungs-Zeilenzuordnung.

## Tests

- Neues `test_stage467_wfm_asm_splitter_navigation.py`: 5 Tests (beide
  Windows-Ziele, Assembler/COFF/PE-Linking, Top-Level- und Methoden-Zeilen,
  Mehrzeilen-Kommentare, Layout-Struktur und ASM-Kommentar-Erkennung).
- `test_stage466_wfm_top_level_program.py`, `test_stage465_wfm_event_comments_type.py`,
  `test_stage464_dbase_type_vartype.py`, `test_stage463_wfm_modal_and_german_source_context.py`,
  `test_stage460_wfm_typed_slot_optimization.py`: zusammen 41 Tests bestanden.
- Laufende Windows-/Qt5-Oberfläche und Mausinteraktion nicht nativ getestet,
  da in der Testumgebung keine PyQt5-Installation vorhanden ist.
