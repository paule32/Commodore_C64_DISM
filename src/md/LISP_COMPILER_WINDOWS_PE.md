# LISP-Compiler für Windows PE32 / PE32+

Basis ist die vom Benutzer hochgeladene `d64_dism(20260809-113117).py`.

## Architektur

Der LISP-Compiler übernimmt **keine** Writer/Emitter aus `generator.py`. Die Datei dient nur als Semantik-Referenz. `d64lisp/compiler.py` parst die mitgelieferte Grammar-Struktur und erzeugt ausschließlich Intel-Assemblertext.

```text
.lisp / .lsp
   -> d64lisp Parser / Codegenerator
   -> IA-32 ASM (Windows PE32)
      oder AMD64 ASM (Windows PE32+ / PE64)
   -> interner d64_dism Assembler
   -> COFF32 / COFF64
   -> interner d64_dism Linker
   -> EXE
```

Es wird kein NASM, GCC, MinGW, MSVC oder externer Linker für diesen Weg benötigt.

## Grammatik

Die ausgelieferten `LispLexer.g4` und `LispParser.g4` liegen unter `d64lisp/grammar/`. Der integrierte Parser bildet deren Regeln direkt ab: Listen, Atome, Quote, Zahlen, Strings, Symbole und `;`-Kommentare.

## Unterstützte Formen

- `defun`
- `start`
- `setq`
- `if`
- `while`
- `break`, `continue`
- `print`, `println`
- `+`, `-`, `*`, `/`
- `=`, `==`, `/=`, `!=`, `<>`, `<`, `<=`, `>`, `>=`
- `nil`, `false`, `t`, `true`
- Integer und Strings
- Funktionsaufrufe und Rekursion mit Integerparametern

Die Funktionsparameter orientieren sich an der Referenz `generator.py` zunächst am Integer-Modell.

## Hauptprogramm / Modul

Hauptprogramm, wenn mindestens eines gilt:

- `(start name)`
- parameterlose `(defun main () ...)`
- ausführbare Top-Level-Formen

Eine Datei mit ausschließlich `defun`-Definitionen ist ein Modul (`source_kind = unit`). F2 erzeugt daraus unter PE32/PE32+ eine `.o`-Datei. Ein LISP-Hauptprogramm kann solche Projektobjekte anschließend über den vorhandenen Projekt-Linkpfad einbinden.

## GUI

- Neuer Projekt-Hauptknoten `LISP-Programme`
- `Datei -> Neu -> LISP-Programm`
- Dateiendungen `.lisp` und `.lsp`
- LISP-Syntaxhighlighting
- Targetauswahl auf `Windows PE32` und `Windows PE64` beschränkt
- Console-Modus für diese erste Runtime-Stufe
- F1 nutzt den CHM-Unterordner `lisp`
- F2: Compile -> interner Assembler -> COFF -> Link -> Start
- reine LISP-Module: F2 -> `.o`

## Runtime

Das Hauptmodul erzeugt `_start`, öffnet eine Konsole und nutzt die vorhandenen internen WinAPI-Imports/Thunks für:

- `AllocConsole`
- `GetStdHandle`
- `WriteFile`
- `wsprintfA`
- `ExitProcess`

Unter PE32+ bleiben die vom Compiler erzeugten Aufrufe im d64-internen Stack-ABI. Der vorhandene COFF64-Linker erzeugt dafür seine Microsoft-x64-ABI-Adapter.

## Einschränkungen der ersten Stufe

- noch keine echten Cons-Zellen/Listenobjekte zur Laufzeit
- Quote von Listen wird noch nicht materialisiert
- noch keine Garbage Collection
- Parameter sind zunächst Integer-orientiert
- noch keine Float-/Double-Werte
- keine C64-/Amiga-Codeerzeugung

## Console / GUI und ASM-Tab (2026-08-09)

LISP-Dokumente koennen in der Windows-Modus-Combo nun zwischen `Console` und
`GUI` wechseln. `Direct2D` und `Direct3D` bleiben fuer LISP bis zu eigenen
Grafik-Builtins deaktiviert.

- Console: PE-Subsystem CUI (3), `AllocConsole` + `GetStdHandle` + `WriteFile`.
- GUI: PE-Subsystem GUI (2), keine Console; `print`/`println` zeigen Werte ueber
  `MessageBoxA` an.
- PE32 und PE32+ (AMD64) werden jeweils vom internen Assembler/COFF-Linker gebaut.
- Der `Assemble`-Button des erzeugten ASM-Tabs akzeptiert LISP jetzt vollstaendig;
  nach erfolgreichem Link wird `Start` aktiviert.

Die Quellcodeeditoren fuer BASIC, C/C-Header, Pascal, LISP und ASM sowie der
generierte ASM-Editor verwenden unabhaengig vom globalen Hell-/Dunkelmodus einen
navyblauen Hintergrund (`#000080`). Syntaxfarben/Gutter verwenden dazu die dunkle
Kontrastpalette.

## READ / Konsoleneingabe

Im Windows-Console-Modus steht jetzt `(read)` als String-Ausdruck zur Verfügung.
Der Aufruf wartet über `ReadFile` auf eine komplette Konsolenzeile (ENTER),
entfernt das abschließende CR/LF und liefert den nullterminierten Text zurück.

```lisp
(defun main ()
  (println "Bitte Text eingeben:")
  (setq text (read))
  (println "Eingabe war:")
  (println text))
(start main)
```

Der Eingabepuffer wird lazy mit `VirtualAlloc(NULL, 4096, MEM_COMMIT|MEM_RESERVE,
PAGE_READWRITE)` angelegt und wiederverwendet. Dadurch liegt kein großer
Nullblock im PE-Image. `(read)` ist im GUI-Modus absichtlich nicht verfügbar,
weil dort keine Konsolen-Standardeingabe existiert.

## ASM-Editorfarben

Der navyblaue Hintergrund bleibt für BASIC, C, Pascal, LISP und ASM erhalten.
Für ASM wurde die frühere Farblogik wiederhergestellt:

- normaler ASM-Text: gelb
- Mnemonics: fett weiß
- Kommentare: grau
- Sprungziele/Links: hellblau
- Hintergrund: Navy `#000080`
