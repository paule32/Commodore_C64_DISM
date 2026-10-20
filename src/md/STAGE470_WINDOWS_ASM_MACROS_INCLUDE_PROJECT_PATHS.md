# Stage 470 – Windows-Assembler-Präprozessor und Projekt-Include-Suchpfade

**Verbindliche Basis:** `d64_dism_asm_469.zip`.

## 1. Neue Makroanweisungen (PE32 und PE32+ / PE64)

```asm
%include "extern.inc"
%include "<extern.inc>"        ; alternative, ebenfalls erlaubt
%include <extern.inc>
%define MAKRO 2
%define TEXT "text"
%undef MAKRO

%if MAKRO == 2
    mov eax, MAKRO
%elif MAKRO => 4
    mov eax, 4
%else
    mov eax, 0
%endif

%ifdef TEXT
    ; ...
%endif
%ifndef TEXT
    ; ...
%endif
```

Vergleiche: `==`, `!=`, `<`, `<=`, `>`, `>=` und `=>` (Alias für `>=`).
Numerische und Stringvergleiche sind möglich. Definitionen gelten für die gesamte
aktuelle Assemblyeinheit einschließlich eingebundener Dateien. Bedingungen sind verschachtelbar.

Vordefinierte Makros:

* `__LINE__`: ursprüngliche Quellzeilennummer der jeweiligen ASM-/INC-Datei.
* `__TIME__`: Assemblierzeit als Stringliteral (`"HH:MM:SS"`).
* `__DATE__`: Assemblierdatum als Stringliteral (`"YYYY-MM-DD"`).
* `__FILE__`: aktueller Dateiname als Stringliteral.
* `__BREAK__`: erzeugt `int3` (`0xCC`), wenn diese Anweisung an ausführbarer Stelle steht.

Der neue `windows_asm_macros.py` expandiert Makros *vor* dem internen Assembler,
ohne externe Assemblertools. Er erhält die Dateinamen und Ursprungszeilennummern
für Fehlermeldungen. Zyklische Includes und zu tiefe Verschachtelung werden erkannt.

## 2. Projekt-Einstellungen → Compiler → Eingabe-Verzeichnis

Für die jeweils gewählte Windows-Architektur (`PE32` / `PE64`) wird die schon
vorhandene Liste `project_windows_search_paths` verwendet. Es werden keine
zusätzlichen Settings eingeführt; gespeicherte Projekte funktionieren weiterhin.

**Suchpriorität für jedes `%include`:**

1. Verzeichnis der ASM-Datei, in der das Include steht – auch bei verschachtelten Includes.
2. Projekt-Eingabeverzeichnisse der jeweiligen Architektur, in **derselben Reihenfolge** wie im Einstellungsdialog.

Bei einem fehlenden Include meldet der Assembler die anfordernde Datei und
Zeile sowie alle geprüften Dateipfade. Der Mechanismus wird bei direkten
Windows-ASM-Dateien, kompilierten Windows-Quellen im Assembler-Editor,
COFF-Objekterzeugung und Pascal-UNIT-COFF verwendet. Auch die Qt-Runtime-
Kompatibilitätsprüfung expandiert projektbezogene Includes.

Beispiel:

```text
Projekt-Einstellungen → Windows → 32-Bit → Compiler → Eingabe-Verzeichnis
  C:\MeinProjekt\asm\include
  C:\MeineBibliotheken\extern
```

```asm
%include "extern.inc"
section .text
entry _start
_start:
    mov eax, 2
    ret
```

## 3. WFM-/dBase-Importlisten verkleinert

Bei der dBase-/WFM-Kompilierung aus der GUI werden `import`-Direktiven in eine
separate `.extern.inc` neben der generierten ASM-Datei geschrieben, zum Beispiel:

```text
Form1.generated.pe32.asm
Form1.generated.pe32.extern.inc
```

Der generierte ASM-Quelltext enthält stattdessen:

```asm
%include "<Form1.generated.pe32.extern.inc>"
```

Beide Dateien müssen zusammenbleiben. Dadurch sinkt die Länge des angezeigten
ASM-Texts; die Zahl der Imports und die tatsächliche PE-Linksemantik ändern
sich nicht. Die Windows-DLL-Erkennung berücksichtigt die ausgelagerten Imports.

## 4. Tests

Testdatei: `test_stage470_windows_asm_macros.py`

Geprüft:

* 15 neue Testfälle: Includes, Macro-Expansion, Datum/Uhrzeit/Zeile,
  `%if/%elif/%else/%endif`, `%ifdef`, PE32/PE64, `__BREAK__` als `CC`,
  verschachtelte Projekt-Suchverzeichnisse, Suchprioritäten, Fehlerberichte,
  ausgelagerte WFM-Imports und reelles COFF-/PE-Linking.
* 146 vollständige ausgewählte Regressionstests bestanden, darunter Stage 445,
  446, 449, 451, 459–463, 465–470.

Reale Windows-GUI-Interaktion wurde unter Linux nicht ausgeführt. Die Tests
validieren die Compiler-/Assembler-/Linker-Ausgabe und die GUI-Verkabelung.
